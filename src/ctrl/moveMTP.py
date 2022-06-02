###############################################################################
# Class for the broad overview of the mtp moves 
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import time
from PyQt5 import QtCore
from ctrl.lib.mtpcommand import MTPcommand
# Ugh. Format has aline, so needs to be in model.py
# can't figure out how to pass that instance of formatMTP
# New instance here should store to the same packetStore
from ctrl.formatMTP import formatMTP
from ctrl.pointing import pointMTP
from EOLpython.Qlogger.messageHandler import QLogger as logger

class moveMTP():    
    
    def __init__(self, parent, serialPort):
        varDict = {
            'Cycling': False,    
            'lastSky': -1, # may be unused
        }
        self.parent = parent
        self.vars = varDict 
        # MAM, fEc, getAngle, checkOverheat
        self.point = pointMTP(self, parent)
        self.serialPort = serialPort
        self.packetStore = self.parent.packetStore
        self.controlWindow = self.parent.controlWindow
        self.formatMTP = formatMTP(self)
        self.commandDict = MTPcommand()

    # if on first move status 6 for longer than expected
    # aka command sent properly, but actual movement
    # not initiated, need a Ctrl-c then re-init, re-home

    # on boot probe sends
    # MTPH_Control.c-101103>101208
    # needs to be caught first before other init commands are sent
    # also response to V
    def initProbe(self):
        # if GUI is True
        if self.parent.gui:
            self.parent.controlWindow.waitForRadiometerWindow(isVisible=True)

        probeResponding = False
        while (1):
            if probeResponding is False:
                while self.probeOnCheck() is False:
                    # if GUI is True
                    if self.parent.gui:
                        self.parent.controlWindow.iwgProcessEvents()
                    # Reporting as error stops program execution, that's an issue
                    # should be an error report or an info, but
                    # continuing to try is prefered
                    logger.printmsg("debug", "probe off or not responding")
                logger.printmsg("debug", "Probe on check returns true")
                probeResponding = True
            self.readEchos(3)
            self.init()
            self.readEchos(3)
            self.moveHome()
            #if (self.isMovePossibleFromHome(maxDebugAttempts=20,
            #                                scanStatus='potato') == 4):
            if self.initForNewLoop():
                # if GUI is True
                if self.parent.gui:
                    self.parent.controlWindow.waitForRadiometerWindow(
                            isVisible=False)
                # start actual cycling
            break


    def initForNewLoop(self):
        # This is an init command
        # but it moves the motor faster, so not desired
        # in initial startup/go home ?
        # Correct, necessary before move-to-angle commands

        # do a check for over voltage
        # first move command in loop errors:
        # status = 6, but no move
        # step 0C
        self.serialPort.sendCommand(b'U/1j128z1000000P10R\r\n')

        self.readEchos(3)
        return True


    def Bline(self, angles, nfreq):

        logger.printmsg("debug", "Bline")
        # All R values have spaces in front
        logger.printmsg("debug", angles)
        numAngles = angles[0]
        zel = angles[1]
        elAngles = angles[2:numAngles+2]
        logger.printmsg("debug",elAngles)
        data = ''
        angleIndex = 0  # 1-10
        for angle in elAngles:
            # if GUI is True
            if self.parent.gui:
                # update GUI
                self.parent.controlWindow.updateAngle(str(angle))
            angleIndex = angleIndex + 1
            logger.printmsg("debug", "el angle: %f, ScanAngleNumber: %f",
                          angle, angleIndex)
            self.parent.controlWindow.iwgProcessEvents()

            # packetStore pitchCorrect should be button
            pitchCorrect = True
            pitchFrame = self.packetStore.getData("pitchavg")
            rollFrame = self.packetStore.getData("rollavg")
            EmaxFlag = False
            # if self.packetStore.getData("pitchCorrect"):
            if pitchCorrect:
                angle = angle + self.point.fEc(pitchFrame, rollFrame,
                                                angle, EmaxFlag)
            else:
                # should also be an info or error
                logger.printmsg("debug", "not correcting Pitch")
                angle = angle + zel

            # get pitch corrected angle and
            # sends move command
            moveToCommand = self.point.getAngle(angle, zel)
            # self.serialPort.sendCommand(str.encode(moveToCommand))
            if angle == elAngles[1]:
                sleepTime = 0.12
                time.sleep(0.002)
            else:
                # 0.01 has many fewer spikes, but average takes too long
                # 0.0045 more spikes, preferred for timing ...
                sleepTime = 0.0075
            self.moveCheckAgain(str.encode(moveToCommand), sleepTime,
                                isHome=False)

            # logger.printmsg("debug", "Bline find the @: %r", echo)
            # wait until Step:\xddff/0@\r\n is received

            data = data + self.integrate(nfreq)
            logger.printmsg("debug", data)

        return data


    def moveCheckAgain(self, sentCommand, sleepTime, isHome):
        # have to check for @ and status separately
        self.serialPort.sendCommand((sentCommand))
        # I really don't like having this process events in here
        # But is currently necessary for 1/s iwg processing
        # as there are at least 2 moves a cycle
        # that take longer than 1 s
        self.parent.controlWindow.iwgProcessEvents()
        i = 0
        while i < 2:
            # Might be possible to reduce this a bit
            echo, sFlag, foundIndex = self.readUntilFound(b'@',
                                                          100, 20, isHome)
            # Only send again if homescan and timeout
            if echo == b'-1' and isHome:
                self.serialPort.sendCommand((sentCommand))
                i = i+1
                logger.printmsg("debug", "moveCheckAgain: sending move again, %r", echo)
            elif echo == b'-1' and sFlag:
                # check to see if empty 'Step' was received
                # in readUntilFound - means motor didn't actually
                # move despite getting the command
                # then remove isHome flag, bline moves
                # that get empty steps wont be stacking
                self.serialPort.sendCommand((sentCommand))
                i = i+1
                logger.printmsg("debug", "moveCheckAgain: timeout")
            else:
                logger.printmsg("debug", "moveCheckAgain: @ recieved %r, i = %s", echo, i)
                i = 5
        logger.printmsg("debug", "sentCommand %s", sentCommand)

        # Too soon and status is always 6: homescan needs longer
        i = 0
        maxLoops = 12
        while i < maxLoops:
            i = i + 1
            time.sleep(sleepTime/2)
            self.serialPort.sendCommand(self.commandDict.getCommand('status'))
            # need readUntilFound to not exit on seeing an s here
            # but also need to keep isHome in this scope as True
            # for when it is actually called by home
            status, sFlag, foundIndex = self.readUntilFound(b'T',
                                                            10, 10, False)
            logger.printmsg("debug", "FindtheT status: %r", status)
            # in case statusNum ==7, S was found, but ST## wasn't
            if status != b'-1':
                findTheT = status.data().find(b'T')
                if findTheT >= 0:
                    # status 04 is correct statu, others require re-prompt
                    statusNum = status[findTheT + 3]
                    logger.printmsg("debug", 'statusnum: %r', statusNum)
                    if statusNum == '4':
                        logger.printmsg("debug", 'status is 4')
                        return True
                    elif statusNum == '7':
                        self.serialPort.sendCommand(
                                self.commandDict.getCommand('count'))
                        self.serialPort.sendCommand(
                                self.commandDict.getCommand('count2'))
                        logger.printmsg("debug", "status 7: send integrate/read to fix")
                    elif statusNum == '6':
                        # i = i + 1
                        time.sleep(sleepTime/2)
                        if i < maxLoops/2:
                            # Longer wait to prevent long homescans,
                            # malset channels (eg. ST:04\r\nS\r\nST:00)
                            time.sleep(sleepTime/2)
                            # three quotes for line break
                            logger.printmsg("debug", '''moveCheckAgain, i<maxLoops/2,
                                          i = %r, mL/2 = %r''', i, maxLoops/2)
                        elif isHome:
                            # Status 6 needs the command (j0f0) sent again
                            self.moveCheckAgain(sentCommand, sleepTime, isHome)
                            logger.printmsg("debug", "moveCheckAgain, isHome %s", isHome)
                        else:
                            # Status 6 with Move commands needs a wait
                            # do the status check again
                            logger.printmsg("debug","moveCheckAgain T found, status 6")
                    else:
                        logger.printmsg("debug", "moveCheckAgain:status not 4,6,7: %s",
                                statusNum)
                        return
                else:
                    logger.printmsg("debug", "moveCheckAgain: T not found")
            else:
                # send status again
                logger.printmsg("debug", "moveCheckAgain: T not found")
                # i = i + 1
        logger.printmsg("debug", "moveCheckAgain timeout %s ", status)


    def m01(self):
        logger.printmsg("debug", "M01")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_M1")))
        # echo will echo "M  1" so have to scan for the : in the M line
        m, sFlag, foundIndex = self.readUntilFound(b'M01:',
                                                   100, 20, isHome=False)
        # set a timer so m01 values get translated from hex?
        m01 = self.formatMTP.decode(m)
        return m01

    def m02(self):
        logger.printmsg("debug", "M02")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_M2")))
        m, sFlag, foundIndex = self.readUntilFound(b'M02:',
                                                   100, 20, isHome=False)
        m02 = self.formatMTP.decode(m)
        return m02

    def pt(self):
        logger.printmsg("debug", "pt")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_P")))
        p, sFlag, foundIndex = self.readUntilFound(b':', 100, 20, isHome=False)
        pt = self.formatMTP.decode(p)

        return pt

    def Eline(self, nfreq):
        data = 0
        logger.printmsg("debug", "Eline")
        # has a loop in small program and init probe
        self.moveHome()
        #self.isMovePossibleFromHome(maxDebugAttempts=10, scanStatus='potato')
        self.initForNewLoop()
        # start actual cycling
        # set noise 1
        # returns echo and b"ND:01\r\n" or b"ND:00\r\n"
        self.serialPort.sendCommand(self.commandDict.getCommand("noise1"))
        echo, sFlag, foundIndex = self.readUntilFound(b'ND:01',
                                                      6, 4, isHome=False)
        data = self.integrate(nfreq)

        # set noise 0
        self.serialPort.sendCommand(self.commandDict.getCommand("noise0"))
        echo, sFlag, foundIndex = self.readUntilFound(b'ND:00',
                                                      6, 4, isHome=False)
        return data + self.integrate(nfreq)

    def moveHome(self):
        errorStatus = 0
        # acutal initiate movement home
        self.serialPort.sendCommand(b'U/1J0f0j256Z1000000J3R\r\n')
        self.readEchos(3)
        # if spamming a re-init, this shouldn't be needed
        # or should be in the init phase anyway
        # serialPort.write(b'U/1j128z1000000P10R\r\n')
        # readEchos(3)
        # Update GUI
        self.parent.controlWindow.atTarget()
        # sets 'known location' to 0
        self.packetStore.setData("currentClkStep", 0)

        # S needs to be 4 here
        # otherwise call again
        # unless S is 5
        # then need to clear the integrator
        # with a I (and wait 40 ms)
        # errorStatus = self.isMovePossibleFromHome(12,True)
        return errorStatus

    def readEchos(self, num):
        # from initMoveHome
        buf = b''
        for i in range(num):
            self.parent.controlWindow.iwgProcessEvents()
            # readline in class serial library vs serial Qt library
            # serial qt is uesd in main probram, so need the timeout
            readLine = self.serialPort.canReadLine(500)
            if readLine is None:
                logger.printmsg("debug", "readEchos: Nothing to read")
            else:
                buf = buf + readLine

        logger.printmsg("debug", "read %r".format(buf))
        return buf


    def sendInit1(self):
        # Init1
        self.serialPort.sendCommand(b'U/1f1j256V50000R\r\n')
        # returns:
        # U/1f1j256V50000R\r\n
        # U:U/1f1j256V50000R\r\n
        # Step:\xff/0@\r\n
        # if already set to this
        # last line replaced by
        # Step:/0B\r\n
        # if too eary in boot phase (?)
        # Have seen this near boot:
        #  b'\x1b[A\x1b[BU/1f1j256V50000R\r\n'
        # And this in cycles
        #  Step:\xff/0@\r\n - makes ascii parser die
        #  Step:/0C\r\n - makes fix for above not work
        #  Step:\r\n
        #

        return self.readEchos(3)

    def sendInit2(self):
        # Init2
        self.serialPort.sendCommand(b'U/1L4000h30m100R\r\n')
        # normal return:
        #
        # U/1f1j256V50000R\r\n
        # U:U/1f1j256V50000R\r\n
        # b'Step:\xff/0@\r\n'

        # error returns:
        # \x1b[A\x1b[BU/1f1j256V50000R
        # Step:\xff/0B\r\n'
        #
        return self.readEchos(3)

    def init(self):
        # errorStatus = 0 if all's good
        # -1 if echos don't match exact return string expected
        # -2 if unexpected status
        #
        errorStatus = 0
        # 12 is arbirtary choice. Will tune in main program.
        while errorStatus < 12:
            answerFromProbe = self.sendInit1()
            # check for errors/decide if resend?
            if self.findChar(answerFromProbe, b'@') != -1:
                errorStatus = 12
                # success
            elif self.findChar(answerFromProbe, b'B') != -1:
                # should be info or warning
                logger.printmsg("debug", " Init 1 status B, resending.")
                errorStatus = errorStatus + 1
            elif self.findChar(answerFromProbe, b'C') != -1:
                # should be logged as an error or warning
                logger.printmsg("debug", "Init 1 status C, resending.")
                errorStatus == errorStatus + 1
            else:
                # should log as warning
                logger.printmsg("debug", "Init 1 status else, resending.")
                errorStatus == errorStatus + 1

        self.serialPort.sendCommand(b'S\r\n')

        buf = self.readEchos(3)
        logger.printmsg("debug", "readEchos, should have no response: ")
        logger.printmsg("debug", buf)

        errorStatus = 0
        # 12 is arbirtary choice. Will tune in main program.
        while errorStatus < 12:
            answerFromProbe = self.sendInit2()
            # check for errors/decide if resend?
            if self.findChar(answerFromProbe, b'@') != -1:
                errorStatus = 12
                # success
            elif self.findChar(answerFromProbe, b'B') != -1:
                # should be a warning
                logger.printmsg("debug", " Init 2 status B, resending.")
                errorStatus = errorStatus + 1
            elif self.findChar(answerFromProbe, b'C') != -1:
                # should log as a warning
                logger.printmsg("debug", " Init 2 status C, resending.")
                errorStatus == errorStatus + 1
            else:
                # should log as warning
                logger.printmsg("debug", " Init 2 status else, resending.")
                errorStatus = errorStatus + 1

        # After both is status of 7 ok?
        # no
        # 4 is preferred status
        # if after both inits status = 5
        # do an integrate, then a read to clear

        return errorStatus

    def integrate(self, nfreq):
        # returns string of data values translated from hex to decimal
        # recepit of the @ from the move command has to occur before
        # entry into this function

        data = ''
        isFirst = True
        for freq in nfreq:
            # tune echos received in tune function
            logger.printmsg("debug", "Frequency/channel:" + str(freq))
            self.tune(freq, isFirst)
            # other channels than the first need resetting ocasionally.
            # isFirst = False
            # clear echos
            self.getIntegrateFromProbe()

            # actually request the data of interest
            echo = b'-1'
            while echo == b'-1':
                self.serialPort.sendCommand((self.commandDict.getCommand(
                    "count2")))
                echo, sFlag, foundIndex = \
                    self.readUntilFound(b'R28:', 10, 20, isHome=False)
                logger.printmsg("debug", "reading R echo %r", echo)

            logger.printmsg("debug", "Echo [foundIndex] = %r, echo[foundIndex + 4] = %r",
                          echo[foundIndex], echo[foundIndex+4])
            # above to get rid of extra find when probe loop time is issue
            findSemicolon = echo.data().find(b'8')
            # logger.printmsg("debug", "r value data: %s, %s, %s",echo[findSemicolon],
            # echo[findSemicolon+1], echo[findSemicolon+6])
            datum = echo[findSemicolon+2: findSemicolon+8]
            # generally 4:10, ocasionally not. up to, not include last val
            logger.printmsg("debug", datum)

            # translate from hex:
            datum = '%06d' % int(datum.data().decode('ascii'), 16)

            # append to string:
            data = data + ' ' + datum
            logger.printmsg("debug", data)
        logger.printmsg("debug", data)
        return data

    def getIntegrateFromProbe(self):
        # Start integrator I 40 command
        self.serialPort.sendCommand((self.commandDict.getCommand("count")))
        # ensure integrator starts so then can
        i = 0
        looptimeMS = 2
        looping = True
        while i < looptimeMS:
            logger.printmsg("debug", "integrate loop 1, checking for odd number")
            if self.waitForStatus(b'5'):
                break
            if i == looptimeMS:
                self.serialPort.sendCommand(
                    self.commandDict.getCommand("count"))
                i = looptimeMS/2
                looptimeMS = i
            i = i+1

        # check that integrator has finished
        i = 0
        while i < 3:
            logger.printmsg("debug", "integrate loop 2, checking for even number")
            if self.waitForStatus(b'4'):
                break
            i = i + 1
            logger.printmsg("debug", "integrator has finished")
        return True



    def waitForStatus(self, status):
        # add timeout?
        i = 0
        # While loop checks to ensure tune has been properly applied
        # VB6 checks for move along status with a
        # "if (status And 4) == 0 goto continue looping"
        # But the find requires a single number
        # most often it's 6, but sometimes it's 2
        # so the while shouldn't be done more than a few times to keep
        # time between packets down.
        # in Tune status 0 is an error that requires resending the C
        #
        while i < 5:
            self.serialPort.sendCommand(
                self.commandDict.getCommand("status"))
            logger.printmsg("debug", "sent status request")
            echo, sFlag, foundIndex = self.readUntilFound(
                    b'S', 37, 55, isHome=False)
            logger.printmsg("debug", "status: %s, received Status: %s, ", status, echo)
            if echo != b'-1':
                statusFound = echo.data().find(status)
                if statusFound >= 0:
                    logger.printmsg("debug", "status searched: %s , found: %s",
                            int(status), int(echo[statusFound]))
                    return True
                else:
                    logger.printmsg("debug", "status searched for: %r , found: %r",
                            status, echo)
                i = i + 1
            else:
                logger.printmsg("debug", "waitForStatus' readUntilFound timeout")
                i = i + 1
        # should log as warning
        logger.printmsg("warning", " waitForStatus timed out: %s", int(status))
        return False
    
    def tune(self, fghz, isFirst):
        # these are static and can be removed from loop
        # fghz is frequency in gigahertz
        fby4 = (1000 * fghz)/4  # MHz
        chan = fby4/0.5  # convert to SNP channel (integer) 0.5 MHz = step size
        logger.printmsg("debug", "tune: chan = %s", chan)

        # either 'C' or 'F' set in packetStore
        # F mode formatting #####.# instead of cmode formatting #####
        # not sure it makes a difference

        # mode = self.parent.packetStore.getData("tuneMode")

        mode = 'C'
        self.serialPort.sendCommand(
            str.encode(str(mode) + '{:.5}'.format(str(chan)) + "\r\n"))
        # \n added by encode I believe
        # logger.printmsg("debug",
        # "Tuning: currently using mode C as that's what's called in vb6")
        # no official response, just echos
        # and echos that are indistinguishable from each other
        # eg: echo when buffer is sending to probe is same
        # as echo from probe: both "C#####\r\n"
        # catch tune echos
        # official response is a status of 4
        echo, sFlag, foundIndex = self.readUntilFound(b'C',
                                                      100, 20, isHome=False)
        # wait for tune status to be 4
        # see comment in waitForStatus for frustration
        isFour = self.waitForStatus(b'4')
        # if it's the first channel, resend C
        # that seems to fail with status 0
        count = 0
        while not(isFour) and count < 3:
            count = count + 1
            self.serialPort.sendCommand(
                str.encode(str(mode) + '{:.5}'.format(str(chan)) + "\r\n"))
            echo, sFlag, foundIndex = self.readUntilFound(b'C',
                                                          10, 8, isHome=False)
            isFour = self.waitForStatus(b'4')


    def readUntilFound(self, binaryString, timeout,
                       canReadLineTimeout, isHome):
        i = 0
        echo = b''
        sFlag = False
        while i < timeout:
            # grab whatever is in the buffer
            # will terminate at \n if it finds one
            self.parent.controlWindow.iwgProcessEvents()

            echo = self.serialPort.canReadAllLines(canReadLineTimeout)  # msec
            logger.printmsg("debug", "read until found: %r", binaryString)
            logger.printmsg("debug", echo)
            foundIndex = -1
            # logger.printmsg("debug", echo)
            if echo is None or echo == b'':
                logger.printmsg("debug", "readUntilFound: none case")
                i = i + 1
            else:
                saveIndex = echo.data().find(binaryString)
                if saveIndex >= 0:
                    logger.printmsg("debug", "received binary string match %r", echo)
                    foundIndex = saveIndex
                    logger.printmsg("debug", "foundIndex: %r", foundIndex)
                    return echo, sFlag, foundIndex
                elif echo.data().find(b'S') >= 0:
                    logger.printmsg("debug", "Found an S, setting sFlag to True")
                    sFlag = True
                    if isHome:
                        return b'-1', sFlag, foundIndex
                else:
                    logger.printmsg("debug", "didn't recieve binary string this loop")
                    i = i + 1
        logger.printmsg("debug", "readUntilFound timeout: returning b'-1'")
        return b'-1', sFlag, foundIndex


    def probeOnCheck(self):
        self.parent.controlWindow.iwgProcessEvents()
        if self.findChar(self.readEchos(3),
                         b"MTPH_Control.c-101103>101208") != -1:
            # should log as info
            logger.printmsg("debug", "Probe on, Version string detected")
            return True
        else:
            logger.printmsg("debug", """No version startup string from probe found,
                          sending V prompt""")
            if self.probeResponseCheck():
                return True
            else:
                if self.truncateBotchedMoveCommand():
                    # should log as warning
                    logger.printmsg("debug", """truncateBotchedMoveCommand called,
                                    ctrl-c success""")
                    return True
                else:
                    # should log as error
                    logger.printmsg("debug", """probe not responding to
                                  truncateBotchedMoveCommand ctrl-c,
                                  power cycle necessary""")
                    return False
        # should log as error
        logger.printmsg("debug", 
            "probeOnCheck all previous logic tried, something's wrong")
        return False
    def probeResponseCheck(self):
        self.serialPort.sendCommand(b'V\r\n')
        if self.findChar(self.readEchos(3),
                         b"MTPH_Control.c-101103>101208") != -1:
            logger.printmsg("debug", "Probe on, responding to version string prompt")
            return True
        else:
            # should log as info or warning
            logger.printmsg("debug", "Probe not responding to version string prompt")
            return False

    def truncateBotchedMoveCommand(self):
        self.serialPort.sendCommand(b'Ctrl-C\r\n')
        if self.findChar(self.readEchos(3), b'Ctrl-C\r\n') != -1:
            logger.printmsg("debug", "Probe on, responding to Ctrl-C string prompt")
            return True
        else:
            logger.printmsg("debug", "Probe not responding to Ctrl-C string prompt")
            return False



    def findChar(self, array, binaryCharacter):
        # status = 0-6, C, B, or @
        # otherwise error = -1
        # saveIndex = echo.data().find(binaryString)
        logger.printmsg("debug", "findChar:array %r", array)
        if array == b'':
            logger.printmsg("debug", "findChar:array is none %r", array)
            # if there is no data
            return -1
        else:
            index = array.data().find(binaryCharacter)
            if index > -1:
                # logger.printmsg("debug", "status: %r, %r", array[index], array)
                return array[index]
            else:
                # should log as error
                logger.printmsg("debug", "status unknown, unable to find %r: %r",
                              binaryCharacter, array)
                return -1


