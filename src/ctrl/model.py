from lib.mtpcommand import MTPcommand
from lib.udp import doUDP
from moveMTP import moveMTP
import logging
import time


class modelMTP():

    # self, MTPdict with iwg(has save) dict ,config dict, serialport)
    def __init__(self, controlWindow, serialPort, configStore,
            dataFile, IWGFile, tempData):
        super().__init__()
        varDict = {
            'Cycling': False,
            'lastSky': -1,  # readScan sets this to actual
        }
        self.controlWindow = controlWindow
        self.dataFile = dataFile
        self.IWGFile = IWGFile
        # Passing instance of command dictionary
        self.commandDict = MTPcommand()
        # Passing instance of moveMTP class
        self.mover = moveMTP(self)
        # Passing instance of UDP (IWG1, send and receive)
        self.udp = doUDP(self, controlWindow, IWGFile)
        # Passing instance of packet store
        self.packetStore = tempData 
        # Passing instance of serialPort
        self.serialPort = serialPort
        # Passing instance of configStore
        self.configStore = configStore

    def readClear(self, waitReadyReadTime, readLineTime):
        # clear a buffer, discarding whatever is in it
        # will read until either the buffer is empty
        # or it finds a \n, whichever is first
        self.serialPort.readLine(readLineTime)
        if self.serialPort.canReadLine(readLineTime):
            self.serialPort.readLine(readLineTime)

    def read(self, waitReadyReadTime, readLineTime):
        logging.debug('waitreadyreadtime = %f', waitReadyReadTime)
        return self.serialPort.canReadLine(readLineTime)

    # will need dataFile, configs and others passed in
    def mainloop(self, isScanning):
        # instantiate dict for commands

        logging.debug("1 : main loop")
        # global storage for values collected from probe
        # storing them in dict introduced slowness
        self.iwgStore = "Waiting for IWG1 ... "

        self.controlWindow.iwgProcessEvents()

        self.initProbe()
        # move home is part of initProbe now
        self.continueCycling = True
        previousTime = time.perf_counter()
        self.cyclesSinceLastStop = 0
        # First element in array is the number of angles
        # to keep the config the same as VB6
        # for integrate
        elAngles = self.configStore.getData("El. Angles", lab=False)
        nfreq = self.configStore.getData("Frequencies", lab=True)
        # logging.debug("Frequencies from config: %r", nfreq)
        nfreq = nfreq[1: len(nfreq)]
        # logging.debug("Frequencies without size: %r", nfreq)

        # loop over " scan commands"
        self.controlWindow.setLEDgreen(self.controlWindow.probeStatusLED)
        self.controlWindow.setLEDgreen(self.controlWindow.scanStatusLED)

        while self.continueCycling:
            self.controlWindow.iwgProcessEvents()
            logging.info(
                "mainloop--------------------------------------------mainloop")
            # check here to exit cycling
            logging.info("mainloop1")
            # use the MTPmove aline
            packetStartTime = time.gmtime()
            self.alineStore = self.Aline()
            logging.info("mainloop2")

            # Bline: long
            self.blineStore = 'B' + self.Bline(elAngles, nfreq)
            self.controlWindow.iwgProcessEvents()
            logging.info("mainloop3")

            self.m01Store = self.m01()
            self.m02Store = self.m02()
            self.ptStore = self.pt()
            self.controlWindow.iwgProcessEvents()
            logging.info("mainloop4")
            # Eline: long
            self.elineStore = 'E' + self.Eline(nfreq)
            self.controlWindow.iwgProcessEvents()
            logging.info("mainloop5")
            # save to file
            # assumes everything's been decoded from hex
            saveData = self.mover.saveData(packetStartTime, self.dataFile)
            self.controlWindow.iwgProcessEvents()
            logging.info("mainloop6")

            # send packet over UDP
            # also replaces spaces with commas and removes start strings
            # speed may be an issue here
            # self.udp.sendUDP(self.mover.formUDP())
            udpPacket = self.mover.formUDP(packetStartTime)
            self.controlWindow.iwgProcessEvents()
            logging.info("mainloop6")
            print(udpPacket)
            self.udp.sendUDP(udpPacket, saveData)
            self.controlWindow.iwgProcessEvents()
            logging.info("mainloop8")
            logging.debug("sent UDP packet")

            # collect, update, display loop stats
            previousTime = self.cycleStats(previousTime)

            # time.sleep(1)

        logging.debug("Main Loop Stopped")
        self.controlWindow.setLEDred(self.controlWindow.scanStatusLED)
        if self.packetStore.getData("quitClicked"):
            controlWindow.exit(0)

    def cycleStats(self, previousTime):
        logging.debug("cycleStats")

        # loop timer
        nowTime = time.perf_counter()
        elapsedTime = nowTime - previousTime
        logging.debug("elapsed Loop Time: %s", elapsedTime)
        previousTime = nowTime

        # total frames(m01,m02,pt,Eline,aline,bline, IWG) taken since startup
        totalCycles = self.packetStore.getData("totalCycles") + 1
        self.packetStore.setData("totalCycles", totalCycles)
        logging.info("cycleStats totalCycles/cycleNumber: %s", totalCycles)

        # frames taken since last "stop probe"
        self.cyclesSinceLastStop = self.cyclesSinceLastStop + 1
        self.controlWindow.updateGUIEndOfLoop(elapsedTime,
                str(totalCycles), str(self.cyclesSinceLastStop))
        return previousTime

        # from initMoveHome
    def readEchos(self, num):
        buf = b''
        for i in range(num):
            self.controlWindow.iwgProcessEvents()
            # readline in class serial library vs serial Qt library
            # serial qt is uesd in main probram, so need the timeout
            readLine = self.serialPort.canReadLine(500)
            if readLine is None:
                logging.debug("Nothing to read")
            else:
                buf = buf + readLine

        logging.debug("read %r", buf)
        return buf



    def moveComplete(self, buf):
        # returns true if '@' is found,
        # needs a timeout if comand didn't send properly
        if buf.find(b'@') >= 0:
            return True
        return False

    def sanitize(self, data):
        data = data[data.data().find(b':') + 1: len(data) - 3]
        placeholder = data.data()  # .decode('ascii')
        place = placeholder.split(' ')
        ret = ''
        for datum in place:
            ret += '%06d' % int(datum, 16) + ' '

        return ret

    def findChar(self, array, binaryCharacter):
        # status = 0-6, C, B, or @
        # otherwise error = -1
        # saveIndex = echo.data().find(binaryString)
        logging.debug("findChar:array %r", array)
        if array == b'':
            logging.debug("findChar:array is none %r", array)
            # if there is no data
            return -1
        else:
            index = array.data().find(binaryCharacter)
            if index > -1:
                # logging.debug("status: %r, %r", array[index], array)
                return array[index]
            else:
                logging.error("status unknown, unable to find %r: %r",
                              binaryCharacter, array)
                return -1

    def probeResponseCheck(self):
        self.serialPort.sendCommand(b'V\r\n')
        if self.findChar(self.readEchos(3),
                         b"MTPH_Control.c-101103>101208") != -1:
            logging.info("Probe on, responding to version string prompt")
            return True
        else:
            logging.info("Probe not responding to version string prompt")
            return False

    def truncateBotchedMoveCommand(self):
        self.serialPort.sendCommand(b'Ctrl-C\r\n')
        if self.findChar(self.readEchos(3), b'Ctrl-C\r\n') != -1:
            logging.info("Probe on, responding to Ctrl-C string prompt")
            return True
        else:
            logging.info("Probe not responding to Ctrl-C string prompt")
            return False

    def probeOnCheck(self):
        self.controlWindow.iwgProcessEvents()
        if self.findChar(self.readEchos(3),
                         b"MTPH_Control.c-101103>101208") != -1:
            logging.info("Probe on, Version string detected")
            return True
        else:
            logging.debug("""No version startup string from probe found,
                          sending V prompt""")
            if self.probeResponseCheck():
                return True
            else:
                if self.truncateBotchedMoveCommand():
                    logging.warning("""truncateBotchedMoveCommand called,
                                    ctrl-c success""")
                    return True
                else:
                    logging.error("""probe not responding to
                                  truncateBotchedMoveCommand ctrl-c,
                                  power cycle necessary""")
                    return False

        logging.error(
            "probeOnCheck all previous logic tried, something's wrong")
        return False

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
                logging.warning(" Init 1 status B, resending.")
                errorStatus = errorStatus + 1
            elif self.findChar(answerFromProbe, b'C') != -1:
                logging.warning(" Init 1 status C, resending.")
                errorStatus == errorStatus + 1
            else:
                logging.warning(" Init 1 status else, resending.")
                errorStatus == errorStatus + 1

        self.serialPort.sendCommand(b'S\r\n')

        buf = self.readEchos(3)
        logging.debug("readEchos, should have no response: ")
        logging.debug(buf)

        errorStatus = 0
        # 12 is arbirtary choice. Will tune in main program.
        while errorStatus < 12:
            answerFromProbe = self.sendInit2()
            # check for errors/decide if resend?
            if self.findChar(answerFromProbe, b'@') != -1:
                errorStatus = 12
                # success
            elif self.findChar(answerFromProbe, b'B') != -1:
                logging.warning(" Init 2 status B, resending.")
                errorStatus = errorStatus + 1
            elif self.findChar(answerFromProbe, b'C') != -1:
                logging.warning(" Init 2 status C, resending.")
                errorStatus == errorStatus + 1
            else:
                logging.warning(" Init 2 status else, resending.")
                errorStatus = errorStatus + 1

        # After both is status of 7 ok?
        # no
        # 4 is preferred status
        # if after both inits status = 5
        # do an integrate, then a read to clear

        return errorStatus

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
        self.controlWindow.atTarget()
        # sets 'known location' to 0
        self.packetStore.setData("currentClkStep", 0)

        # S needs to be 4 here
        # otherwise call again
        # unless S is 5
        # then need to clear the integrator
        # with a I (and wait 40 ms)
        # errorStatus = self.isMovePossibleFromHome(12,True)
        return errorStatus

    def getStatus(self):
        # status = 0-6, C, B, or @
        # otherwise error = -1
        # check for T in ST:0X
        # return status X
        self.serialPort.sendCommand(b'S\r\n')
        answerFromProbe = self.readEchos(4)
        logging.debug("echos from status read: %r", answerFromProbe)
        return self.findCharPlusNum(answerFromProbe, b'T', offset=3)

    def findCharPlusNum(self, array, binaryCharacter, offset):
        # status = 0-6, C, B, or @
        # otherwise error = -1
        logging.debug("findCharPlusNum:array %r", array)
        if array == b'':
            logging.debug("findCharPlusNum:array is none %r", array)
            # if there is no data
            return -1
        else:
            index = array.data().find(binaryCharacter)
            logging.debug("findCharPlusNum array: %r", array.data())
            if index > -1:
                # logging.debug("status with offset: %r, %r",
                #  asciiArray[index+offset], asciiArray)
                return array.data()[index+offset:index+offset+1].\
                    decode('ascii')
            else:
                logging.error(
                    "status with offset unknown, unable to find %r: %r",
                    binaryCharacter, array)
                return -1

    def isMovePossibleFromHome(self, maxDebugAttempts, scanStatus):
        # returns 4 if move is possible
        # otherwise does debugging
        # debugging needs to know if it's in the scan or starting

        # and how many debug attempts have been made
        # should also be a case statement, 6, 4, 7 being most common

        counter = 0
        while counter < maxDebugAttempts:
            s = self.getStatus()
            counter = counter + 1
            if s == '0':
                # integrator busy,
                # Stepper not moving,
                # Synthesizer out of lock,
                # and spare = 0
                logging.debug('isMovePossible status 0')
                return 0
            elif s == '1':
                logging.debug('isMovePossible status 1')
                return 1
            elif s == '2':
                logging.debug('isMovePossible status 2')
                return 2
            elif s == '3':
                logging.debug('isMovePossible status 3')
                return 3
            elif s == '4':
                logging.debug("isMovePossible is 4 - yes, return")
                counter = maxDebugAttempts
                return 4
                # continue on with moving
            elif s == '5':
                # do an integrate
                self.serialPort.sendCommand(b'I\r\n')
                # Integrate takes 40 ms to clear
                time.sleep(.0040)
                self.readEchos(3)
                logging.debug("isMovePossible, status = 5")
            elif s == '6':
                # can be infinite 6's,
                # can also be just wait a bit
                # s = self.getStatus()
                if counter < 12:
                    logging.debug("isMovePossible, status = 6, counter = %r",
                                  counter)
                else:
                    logging.error("isMovePossible, status = 6, counter = %r",
                                  counter)
                    return -1
            elif s == '7':
                logging.debug('isMovePossible status 7')

            else:
                logging.error("Home, status = %r", s)

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

    # if on first move status 6 for longer than expected
    # aka command sent properly, but actual movement
    # not initiated, need a Ctrl-c then re-init, re-home

    # on boot probe sends
    # MTPH_Control.c-101103>101208
    # needs to be caught first before other init commands are sent
    # also response to V
    def initProbe(self):
        self.controlWindow.waitForRadiometerWindow(isVisible=True)

        probeResponding = False
        while (1):
            if probeResponding is False:
                while self.probeOnCheck() is False:
                    self.controlWindow.iwgProcessEvents()
                    logging.error("probe off or not responding")
                logging.info("Probe on check returns true")
                probeResponding = True
            self.readEchos(3)
            self.init()
            self.readEchos(3)
            self.moveHome()
            if (self.isMovePossibleFromHome(maxDebugAttempts=20,
                                            scanStatus='potato') == 4):
                if self.initForNewLoop():
                    self.controlWindow.waitForRadiometerWindow(isVisible=False)
                    # start actual cycling
                    break

    def readUntilFound(self, binaryString, timeout,
                       canReadLineTimeout, isHome):
        i = 0
        echo = b''
        sFlag = False
        while i < timeout:
            # grab whatever is in the buffer
            # will terminate at \n if it finds one
            self.controlWindow.iwgProcessEvents()

            echo = self.serialPort.canReadAllLines(canReadLineTimeout)  # msec
            logging.debug("read until found: ")
            logging.debug(binaryString)
            logging.debug(echo)
            foundIndex = -1
            # logging.debug(echo)
            if echo is None or echo == b'':
                logging.debug(" readUntilFound: none case")
                i = i + 1
            else:
                saveIndex = echo.data().find(binaryString)
                if saveIndex >= 0:
                    logging.debug("received binary string match %r", echo)
                    foundIndex = saveIndex
                    logging.debug("foundIndex: %r", foundIndex)
                    return echo, sFlag, foundIndex
                elif echo.data().find(b'S') >= 0:
                    logging.debug("Found an S, setting sFlag to True")
                    sFlag = True
                    if isHome:
                        return b'-1', sFlag, foundIndex
                else:
                    logging.debug("didn't recieve binary string this loop")
                    i = i + 1
        logging.debug("readUntilFound timeout: returning b'-1'")
        return b'-1', sFlag, foundIndex


    def readScan(self):
        logging.debug("cycle")
        # getcommand read_scan
        self.serialPort.sendCommand(str.encode(
            self.commandDict.getCommand("read_scan")))
        return 0

    def m01(self):
        logging.debug("M01")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_M1")))
        # echo will echo "M  1" so have to scan for the : in the M line
        m, sFlag, foundIndex = self.readUntilFound(b'M01:',
                                                   100, 20, isHome=False)
        # set a timer so m01 values get translated from hex?
        m01 = self.mover.decode(m)
        return m01

    def m02(self):
        logging.debug("M02")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_M2")))
        m, sFlag, foundIndex = self.readUntilFound(b'M02:',
                                                   100, 20, isHome=False)
        m02 = self.mover.decode(m)
        return m02

    def pt(self):
        logging.debug("pt")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_P")))
        p, sFlag, foundIndex = self.readUntilFound(b':', 100, 20, isHome=False)
        pt = self.mover.decode(p)

        return pt

    def Eline(self, nfreq):
        data = 0
        logging.debug("Eline")
        # has a loop in small program and init probe
        self.moveHome()
        self.isMovePossibleFromHome(maxDebugAttempts=10, scanStatus='potato')
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

    def Aline(self):
        logging.debug("View Aline")
        # add current iwg values to running average,
        # send that out instead of instant values
        # made in goAngle for packetStore.savePacket/sendUDP

        # yyyymmdd hhmmss in udp feed
        # yyyymmdd hh:mm:ss in save feed
        # self.currentDate =  "%s%s%s %s%s%s" %( str(t[0]), str(t[1]),
        # str(t[2]), str(t[3]), str(t[4]), str(t[5]))
        # aline = "A " + self.currentDate
        # Note that if iwg is sending, but pitch and roll are
        # not defined, they will be set to NAN
        # (aka testing on the ground)
        # those will be set to 1 in goAngle
        # but not adjusted for Aline
        try:
            logging.debug("before pitch avg")
            pitchavg = self.packetStore.getData("pitchavg")
            logging.debug("after pitch avg")
            pitchrms = self.packetStore.getData("pitchrms")
            logging.debug("after pitch rms1")
            rollavg = self.packetStore.getData("rollavg")
            logging.debug("after pitch rms2")
            rollrms = self.packetStore.getData("rollrms")
            logging.debug("after pitch rms3")
            Zpavg = self.packetStore.getData("Zpavg")
            logging.debug("after pitch rms4")
            Zprms = self.packetStore.getData("Zpavg")
            logging.debug("after pitch rms5")
            oatavg = self.packetStore.getData("oatavg")
            logging.debug("after pitch rms6")
            oatrms = self.packetStore.getData("oatrms")
            logging.debug("after pitch rms7")
            latavg = self.packetStore.getData("latavg")
            logging.debug("after pitch rms8")
            latrms = self.packetStore.getData("latrms")
            logging.debug("after pitch rms9")
            lonavg = self.packetStore.getData("lonavg")
            logging.debug("after pitch rms10")
            lonrms = self.packetStore.getData("lonrms")
            logging.debug("after pitch rms end")
        except Exception as e:
            logging.debug("after pitch rms, in exception")
            logging.error(repr(e))
            logging.error(e.message)
            logging.error(sys.exe_info()[0])
            logging.error("IWG not detected, using defaults")
            pitchavg = 3
            pitchrms = 3
            rollavg = 3
            rollrms = 3
            Zpavg = 3
            Zprms = 3
            oatavg = 3
            oatrms = 3
            latavg = 3
            latrms = 3
            lonavg = 3
            lonrms = 3
            # set from config file eventually
            # other odd constant is in udp.py -
            # sets the recieved values in iwg line to 0
        else:
            logging.debug("else got IWG")

        aline = " " + str(pitchavg)
        aline = aline + " " + str(pitchrms)
        aline = aline + " " + str(rollavg)
        aline = aline + " " + str(rollrms)
        aline = aline + " " + str(Zpavg)
        aline = aline + " " + str(Zprms)
        aline = aline + " " + str(oatavg)
        aline = aline + " " + str(oatrms)
        aline = aline + " " + str(latavg)
        aline = aline + " " + str(latrms)
        aline = aline + " " + str(lonavg)
        aline = aline + " " + str(lonrms)
        aline = aline + " " + str(self.packetStore.getData("scanCount"))
        aline = aline + " " + str(self.packetStore.getData("encoderCount"))
        # self.alineStore = aline

        self.packetStore.setData("angleI", 0)  # angle index
        # update instantanious angle frame?

        # read_scan and read_encode are not used
        # They were to determine location of mirror
        # before the chain was added but since that
        # came about, they no longer have useful data

        # self.serialPort.sendCommand((self.commandDict.getCommand("read_scan")))
        # echo, sFlag, foundIndex = self.readUntilFound(b':',
        # 10, 20, isHome=False)
        # echo, sFlag, foundIndex = self.readUntilFound(b'S',
        # 10, 20, isHome=False)
        # b'Step:\xff/0`1000010\r\n'
        # echo = self.read(200,200)
        # need to implement the better logic counters in bline
        # for scanCount and encoderCount
        # self.packetStore.setData("scanCount", int(
        # self.packetStore.getData("scanCount")) + 1)
        logging.debug("View: Aline end")
        return aline

    def Bline(self, angles, nfreq):

        logging.debug("Bline")
        # All R values have spaces in front
        logging.debug(angles)
        numAngles = angles[0]
        zel = angles[1]
        elAngles = angles[2:numAngles+2]
        logging.debug(elAngles)
        data = ''
        angleIndex = 0  # 1-10
        for angle in elAngles:
            # update GUI
            self.controlWindow.updateAngle(str(angle))
            angleIndex = angleIndex + 1
            logging.debug("el angle: %f, ScanAngleNumber: %f",
                          angle, angleIndex)
            self.controlWindow.iwgProcessEvents()
            # self.controlWindow.iwgProcessEvents()

            # packetStore pitchCorrect should be button
            pitchCorrect = True
            pitchFrame = self.packetStore.getData("pitchavg")
            rollFrame = self.packetStore.getData("rollavg")
            EmaxFlag = False
            # if self.packetStore.getData("pitchCorrect"):
            if pitchCorrect:
                angle = angle + self.mover.fEc(pitchFrame, rollFrame,
                                                angle, EmaxFlag)
            else:
                logging.info("not correcting Pitch")
                angle = angle + zel

            # get pitch corrected angle and
            # sends move command
            moveToCommand = self.mover.getAngle(angle, zel)
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

            # logging.debug("Bline find the @: %r", echo)
            # wait until Step:\xddff/0@\r\n is received

            data = data + self.integrate(nfreq)
            logging.debug(data)

        # self.updateRead("read_scan")
        # self.updateRead("read_enc")
        return data

    def moveCheckAgain(self, sentCommand, sleepTime, isHome):
        # have to check for @ and status separately
        self.serialPort.sendCommand((sentCommand))
        # I really don't like having this process events in here
        # But is currently necessary for 1/s iwg processing
        # as there are at least 2 moves a cycle
        # that take longer than 1 s
        self.controlWindow.iwgProcessEvents()
        i = 0
        while i < 2:
            # Might be possible to reduce this a bit
            echo, sFlag, foundIndex = self.readUntilFound(b'@',
                                                          100, 20, isHome)
            # Only send again if homescan and timeout
            if echo == b'-1' and isHome:
                self.serialPort.sendCommand((sentCommand))
                i = i+1
                logging.debug("moveCheckAgain: sending move again, %r", echo)
            elif echo == b'-1' and sFlag:
                # check to see if empty 'Step' was received
                # in readUntilFound - means motor didn't actually
                # move despite getting the command
                # then remove isHome flag, bline moves
                # that get empty steps wont be stacking
                self.serialPort.sendCommand((sentCommand))
                i = i+1
                logging.debug("moveCheckAgain: timeout")
            else:
                logging.debug("moveCheckAgain: @ recieved %r, i = %s", echo, i)
                i = 5
        logging.debug("sentCommand %s", sentCommand)

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
            logging.debug("FindtheT status: %r", status)
            # in case statusNum ==7, S was found, but ST## wasn't
            if status != b'-1':
                findTheT = status.data().find(b'T')
                if findTheT >= 0:
                    # status 04 is correct statu, others require re-prompt
                    statusNum = status[findTheT + 3]
                    logging.debug('statusnum: %r', statusNum)
                    if statusNum == '4':
                        logging.debug('status is 4')
                        return True
                    elif statusNum == '7':
                        self.serialPort.sendCommand(
                                self.commandDict.getCommand('count'))
                        self.serialPort.sendCommand(
                                self.commandDict.getCommand('count2'))
                        logging.debug("status 7: send integrate/read to fix")
                    elif statusNum == '6':
                        # i = i + 1
                        time.sleep(sleepTime/2)
                        if i < maxLoops/2:
                            # Longer wait to prevent long homescans,
                            # malset channels (eg. ST:04\r\nS\r\nST:00)
                            time.sleep(sleepTime/2)
                            logging.debug('''moveCheckAgain, i<maxLoops/2,
                                          i = %r, mL/2 = %r''', i, maxLoops/2)
                        elif isHome:
                            # Status 6 needs the command (j0f0) sent again
                            self.moveCheckAgain(sentCommand, sleepTime, isHome)
                            logging.debug("moveCheckAgain, isHome %s", isHome)
                        else:
                            # Status 6 with Move commands needs a wait
                            # do the status check again
                            logging.debug('moveCheckAgain T found, status 6')
                    else:
                        logging.debug("moveCheckAgain:status not 4,6,7: %s",
                                statusNum)
                        return
                else:
                    logging.debug("moveCheckAgain: T not found")
            else:
                # send status again
                logging.debug("moveCheckAgain: T not found")
                # i = i + 1
        logging.debug("moveCheckAgain timeout %s ", status)

    def updateRead(self, scanOrEncode):
        i = 0
        while i < 11:
            self.serialPort.sendCommand((self.commandDict.getCommand(
                scanOrEncode)))
            echo, sFlag, foundIndex = self.readUntilFound(b':',
                                                          10, 20, isHome=False)
            # read_scan returns b'Step:\xff/0c1378147\r\n'
            # then returns b'Step:\xff/0`1378147\r\n'
            echo, sFlag, foundIndex = self.readUntilFound(b':',
                                                          10, 20, isHome=False)
            # have a does string contain bactic `
            logging.debug(echo.size())
            # 17 or 18 depending on size of value returned
            findBactic = echo.data().find(b'`')
            if findBactic > 0:
                readScan = echo.data()[findBactic + 1: echo.size() - 2]
                # readScan = echo.data()[9:15]
                # despite the first echo being formated 0c123456
                # The return echo turns the 0c into ` (proper hex translation)
                # and leaves the rest of the numbers alone
                # I'm forced to assume this and encoderCount are
                # the only case where numbers return in decimal, not hex
                # given that is the only way to get near the correct numbers
                # from previous flight data
                #
                # Also note that while the VB6 does append a ">>" to the data
                # that is only used as a deliminator, not a bit shift,
                # and only locally in the vb6 for these two cases.
                # So in intrest of sanity, and because python can manage
                # without a deliminator in this case, I'm not
                # going to re-implement that.
                if scanOrEncode == "read_scan":
                    logging.debug("readScan is: ")
                    logging.debug(readScan)
                    logging.debug(int(readScan.decode('Ascii'), 16))
                    self.scanCount = (1000000 - int(readScan.decode('Ascii')))
                    if self.scanCount >= 0:
                        self.scanCount = '+' + '%06d' % self.scanCount
                    self.packetStore.setData('scanCount', self.scanCount)
                else:
                    logging.debug("readEncode is: ")
                    logging.debug(readScan)
                    logging.debug(int(readScan.decode('Ascii')))
                    logging.debug(int(readScan.decode('Ascii'), 16))

                    self.scanCount = ((1000000 - int(readScan.decode(
                        'Ascii'))*16))
                    if self.scanCount >= 0:
                        self.scanCount = '+' + '%06d' % self.scanCount
                    self.packetStore.setData('encoderCount', self.scanCount)

                break
            i = i + 1
        logging.debug('readencoder size: %d', echo.size())

    def quickRead(self, timeout):
        logging.debug("quickRead start")
        echo = self.serialPort.canReadLine(timeout)
        logging.debug(echo)
        datum = self.serialPort.canReadLine(timeout)
        logging.debug(datum)
        logging.debug("quickRead end")
        return datum

    def integrate(self, nfreq):
        # returns string of data values translated from hex to decimal
        # recepit of the @ from the move command has to occur before
        # entry into this function

        data = ''
        isFirst = True
        for freq in nfreq:
            # tune echos received in tune function
            logging.debug("Frequency/channel:" + str(freq))
            self.tune(freq, isFirst)
            # other channels than the first need resetting ocasionally.
            # isFirst = False
            # clear echos
            # dataLine = self.quickRead(25) # avg is ~9, max is currently 15
            self.getIntegrateFromProbe()
            # clear echos
            # avg is ~9, max observed issue at 25
            # dataLine = self.quickRead(30)

            # actually request the data of interest
            echo = b'-1'
            while echo == b'-1':
                self.serialPort.sendCommand((self.commandDict.getCommand(
                    "count2")))
                echo, sFlag, foundIndex = \
                    self.readUntilFound(b'R28:', 10, 20, isHome=False)
                logging.debug("reading R echo %r", echo)

            logging.debug("Echo [foundIndex] = %r, echo[foundIndex + 4] = %r",
                          echo[foundIndex], echo[foundIndex+4])
            # above to get rid of extra find when probe loop time is issue
            findSemicolon = echo.data().find(b'8')
            # logging.debug("r value data: %s, %s, %s",echo[findSemicolon],
            # echo[findSemicolon+1], echo[findSemicolon+6])
            datum = echo[findSemicolon+2: findSemicolon+8]
            # generally 4:10, ocasionally not. up to, not include last val
            logging.debug(datum)

            # translate from hex:
            datum = '%06d' % int(datum.data().decode('ascii'), 16)

            # append to string:
            data = data + ' ' + datum
            logging.debug(data)
        logging.debug(data)
        return data

    def getIntegrateFromProbe(self):
        # Start integrator I 40 command
        self.serialPort.sendCommand((self.commandDict.getCommand("count")))
        # ensure integrator starts so then can
        i = 0
        looptimeMS = 2
        looping = True
        while i < looptimeMS:
            logging.debug("integrate loop 1, checking for odd number")
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
            logging.debug("integrate loop 2, checking for even number")
            if self.waitForStatus(b'4'):
                break
            i = i + 1
            logging.debug("integrator has finished")
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
            logging.debug("sent status request")
            echo, sFlag, foundIndex = self.readUntilFound(
                    b'S', 37, 55, isHome=False)
            logging.debug("status: %s, received Status: %s, ", status, echo)
            if echo != b'-1':
                statusFound = echo.data().find(status)
                if statusFound >= 0:
                    logging.debug("status searched: %s , found: %s",
                            int(status), int(echo[statusFound]))
                    return True
                else:
                    logging.debug("status searched for: %r , found: %r",
                            status, echo)
                i = i + 1
            else:
                logging.debug("waitForStatus' readUntilFound timeout")
                i = i + 1
        logging.warning(" waitForStatus timed out: %s", int(status))
        return False

    def tune(self, fghz, isFirst):
        # these are static and can be removed from loop
        # fghz is frequency in gigahertz
        fby4 = (1000 * fghz)/4  # MHz
        chan = fby4/0.5  # convert to SNP channel (integer) 0.5 MHz = step size
        logging.debug("tune: chan = %s", chan)

        # either 'C' or 'F' set in packetStore
        # F mode formatting #####.# instead of cmode formatting #####
        # not sure it makes a difference

        # mode = self.parent.packetStore.getData("tuneMode")

        mode = 'C'
        self.serialPort.sendCommand(
            str.encode(str(mode) + '{:.5}'.format(str(chan)) + "\r\n"))
        # \n added by encode I believe
        # logging.debug(
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
