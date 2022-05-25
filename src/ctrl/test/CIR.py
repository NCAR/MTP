###############################################################################
# MTP probe control. Class contains functions that move the probe
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import sys
import datetime
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPProbeCIR():

    def __init__(self, init):
        self.serialPort = init.getSerialPort()
        self.init = init

    def changeFrequency(self, freq):
        self.serialPort.write(freq)
        # no official response, just echos
        # and echos that are indistinguishable from each other
        # eg: echo when buffer is sending to probe is same
        # as echo from probe: both "C#####\r\n"
        # Catch tune echos
        self.init.readEchos(4)

    def integrate(self):
        self.serialPort.write(b'I 40\r\n')
        self.init.readEchos(4)

        # Check that S turns to 5 (integrator starts)
        # and that S turns back to 4 (integrator finished) to move on
        self.getIntegrateFromProbe()

    def getIntegrateFromProbe(self):
        """
        Check for integrate status. Loop looptimeoutMS times waiting for
        integrate command to return. If no return by then, resend integrate
        command. Do this indefinitely until get status 5 which indicates
        integrator has started.

        Once integrator has started, loop indefinitely until get status 4
        indicating integrator has finished.
        """
        # looptimeoutMS is actually a loopcount. Make into a time - JAA
        # Is this really the logic we want?? - JAA
        # For status, Bit 0 = integrator busy, so shouldn't these check
        # for 1,3,5,7 = integrator busy and 2,4,6 = integrator finished?

        # Index to decide when to resend integrate command. If i reaches
        # looptimeout, assume integrate command did not make it to probe
        # and resend command.
        i = 0
        looptimeoutMS = 3  # Should this be in config file so user tunable?-JAA

        # Index to decide when to ask user to bail. If i reaches
        # integratetimeout, assume there is a problem with the probe and ask
        # user if they want to exit. (Should we be asking to reinit, check
        # if probe is on, or some other mitigation approach? - JAA
        j = 0
        integratetimeout = 20

        while (True):
            if self.checkIntegrateStatus("started"):
                break

            logger.printmsg("debug", 'checking for finished integrator: ' +
                            'attempt ' + str(i))

            if i == looptimeoutMS:
                logger.printmsg("warning", "integrate loop 1," +
                                " re-send Integrate")
                self.serialPort.write(b'I 40\r\n')
                self.init.readEchos(4)
            i = i + 1

            if j == integratetimeout:
                logger.printmsg("warning", "integrator not responding to " +
                                           "start command. Exit? (y/n)")
                cmdInput = sys.stdin.readline()
                cmdInput = str(cmdInput).strip('\n')
                if cmdInput == 'y':
                    exit()
                else:
                    # Restart integrate count and ask again after
                    # integratetimeout attempts
                    j = -1
            j = j + 1

        # check that integrator has finished
        i = 0
        j = 0
        while (True):
            if self.checkIntegrateStatus("finished"):
                break

            logger.printmsg("debug", 'checking for finished integrator: ' +
                            'attempt ' + str(i))

            i = i + 1

            if j == integratetimeout:
                logger.printmsg("warning", "integrator not reporting " +
                                           "finished. Exit? (y/n)")
                cmdInput = sys.stdin.readline()
                cmdInput = str(cmdInput).strip('\n')
                if cmdInput == 'y':
                    exit()
                else:
                    # Restart integrate count and ask again after
                    # integratetimeout attempts
                    j = -1
            j = j + 1

        return True

    def checkIntegrateStatus(self, stat):
        """
        Check integrate status
         - Bit 0 = integrator busy
         - Bit 1 = Stepper moving
         - Bit 2 = Synthesizer out of lock
         - Bit 3 = spare

        Input: desired status: "started" or "finished"
        Returns: True if desired status found, False if not

        Works for any status return value (0-7). If status is odd, integrator
        busy so integrator was started. If status is even, integrator finished.
        -- BUT --
        Logically the following should never occur:
        - integrator busy while the stepper is moving [3, 7]
        - synthesizer out of lock [4, 5, 6, 7]
        We always get 4, 5 indicating synthesizer is always out of lock.
        Ask Julie if this is O.K. - JAA
        """

        # Check for valid stat string
        if stat != "started" and stat != "finished":
            logger.printmsg("debug", "invalid status command" + str(stat) +
                            "*** BUG IN CODE ***")
            return False

        s = self.init.getStatus()
        logger.printmsg("debug", "integrate loop, checking for " +
                        "integrator " + str(stat) + ", got status=" + str(s))

        if stat == "started" and int(s) % 2 != 0:
            # Number is odd -> integrator busy
            logger.printmsg("debug", "integrator started")
            if s == 3:
                logger.printmsg("warning", "received status indicating" +
                                " integrator busy while stepper moving." +
                                " Should not occur. Either *** BUG IN CODE " +
                                "or MTP instrument has an issue.")
            return True
        elif stat == "finished" and int(s) % 2 == 0:
            # Number is even -> integrator finished
            logger.printmsg("debug", "integrator has finished")
            return True
        else:
            return False

    def readDatumFromProbe(self):
        self.serialPort.write(b'R\r\n')
        data = self.init.readEchos(4)

        # Find counts in string. Expected string is R28:xxxx where xxxx is
        # 4-digit hex value.
        # Need to beef up checking return value - JAA
        logger.printmsg("debug", "Return value is " + str(data))
        findColon = data.find(b':')
        hexcounts = data[findColon+1:findColon+5]

        # translate from hex and format as 6-digit integer
        datum = '%06d' % int(hexcounts.decode('ascii'), 16)
        logger.printmsg("debug", "Counts are " + str(datum))
        return datum

    def CIR(self, freq):
        """
        At each move angle, code needs to set the Channel frequency, Integrate,
        and Read (CIR)
        """
        self.changeFrequency(freq)
        self.integrate()
        return self.readDatumFromProbe()

    def CIRS(self):
        """
        Cycle through 3 probe frequencies

        Returns a string containing three count values, one for each freq
        eg "020807 022393 022128".
        """
        data = ''

        # Convert freq to integer to send to Firmware
        # Since they don't change, this conversion could be removed from
        # the loop and just done once to save time. - per Catherine
        # Update to read from Config.mtph - JAA
        fghz = [55.51, 56.65, 58.8]  # freq in gigahertz

        # either 'C' or 'F' (set in lib/storePacket.py)
        # F mode formatting #####.# instead of cmode formatting #####
        # not sure it makes a difference
        # Eventually get from  packetStore.getData("tuneMode")
        mode = 'C'
        for f in fghz:
            fby4 = (1000 * f)/4  # MHz
            # convert to SNP channel (integer) 0.5 MHz = step size
            chan = '{:.5}'.format(str(fby4/0.5))
            logger.printmsg("debug", "tune: chan = " + chan)
            cmd = str.encode(str(mode) + str(chan) + "\r\n")
            data = data + self.CIR(cmd) + " "
            logger.printmsg("debug", "-----")
        return data.strip()  # remove trailing space

    def setNoise(self, num):
        self.serialPort.write(num)
        self.init.readEchos(4)

    def readBline(self, move):
        """
        Read all data at current position for B line.

        Returns a complete B line,
        eg "B 019110 020510 019944 019133 020540 019973 019101 020507 ...
        """
        # Determine how long it takes to create the B line
        firstTime = datetime.datetime.now()

        self.b = ''
        # Eventually move angle should be calculated using MAM.
        # For now, this just tests the flow through the code. Angles will
        # be confirmed and corrected if needed later. - JAA
        for angle in [b'U/1J0D28226J3R', b'U/1J0D7110J3R', b'U/1J0D3698J3R',
                      b'U/1J0D4835J3R', b'U/1J0D3698J3R', b'U/1J0D3413J3R',
                      b'U/1J0D3414J3R', b'U/1J0D3697J3R', b'U/1J0D4836J3R',
                      b'U/1J0D10810J3R']:
            move.moveTo(angle)
            self.b += self.CIRS() + ' '  # Collect counts for three channels
        data = "B " + str(self.b)

        logger.printmsg("debug", "data from B line:" + data)

        nextTime = datetime.datetime.now()
        logger.printmsg("debug", "B line creation took " +
                        str(nextTime-firstTime))

        return data

    def getBdata(self):
        """ Return the B data only (without B at the front) """
        return(self.b)

    def readEline(self):
        """
        Read all data at current position for noise diode on and then off.
        Since this function doesn't check probe pointing, it could be at any
        position, so pointing must be checked before using this fn.

        Returns a complete E line,
        eg "E 020807 022393 022128 019105 020672 020117"
        """
        # Determine how long it takes to create the E line
        firstTime = datetime.datetime.now()

        # Create E line
        self.setNoise(b'N 1\r\n')      # Turn noise diode on
        self.e = self.CIRS()           # Collect counts for three channels
        self.e = self.e + " "          # Add space between count sets
        self.setNoise(b'N 0\r\n')      # Turn noise diode off
        self.e = self.e + self.CIRS()  # Collect counts for three channels
        data = "E " + str(self.e)

        logger.printmsg("info", "data from E line:" + data)

        nextTime = datetime.datetime.now()
        logger.printmsg("debug", "E line creation took " +
                        str(nextTime-firstTime))

        return data

    def getEdata(self):
        """ Return the E data only (without E at the front) """
        return(self.e)

    def readM1line(self):
        """
        Read Engineering Multiplxr (M01) housekeeping data

        Returns a complete M01 line,
        eg M01: 2928 2307 2898 3078 1922 2919 2432 2945
        """
        self.serialPort.write(b'M 1\r\n')
        self.m1 = self.init.readEchos(6)
        self.m1 = self.init.sanitize(self.m1)  # clean up buffer & return data
        data = "M01: " + str(self.m1)

        logger.printmsg("info", "data from M01 line - " + data)

        return(data)

    def getM1data(self):
        """ Return the M01 data only (without M01: at the front) """
        return(self.m1)

    def readM2line(self):
        """
        Read Engineering Multiplxr (M02) housekeeping data

        Returns a complete M02 line,
        eg M02: 2009 1240 1533 1668 1699 1395 4095 1309
        """
        self.serialPort.write(b'M 2\r\n')
        self.m2 = self.init.readEchos(6)
        self.m2 = self.init.sanitize(self.m2)  # clean up buffer & return data
        data = "M02: " + str(self.m2)

        logger.printmsg("info", "data from M02 line - " + data)

        return(data)

    def getM2data(self):
        """ Return the M02 data only (without M02: at the front) """
        return(self.m2)

    def readPTline(self):
        """
        Read Platinum Multiplxr (Pt) housekeeping data

        Returns a complete Pt line,
        eg Pt: 2159 13808 13799 11732 13385 13404 13296 14439
        """
        self.serialPort.write(b'P\r\n')
        self.pt = self.init.readEchos(6)
        self.pt = self.init.sanitize(self.pt)  # clean up buffer & return data
        data = "Pt: " + str(self.pt)

        logger.printmsg("info", "data from Pt line - " + data)

        return(data)

    def getPTdata(self):
        """ Return the Pt data only (without Pt: at the front) """
        return(self.pt)
