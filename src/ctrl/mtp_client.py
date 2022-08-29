###############################################################################
# Class to generate a text-based MTP command menu
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import os
import sys
if os.name == 'nt':
    import msvcrt
import select
import socket
import time
import datetime
from ctrl.util.init import MTPProbeInit
from ctrl.util.move import MTPProbeMove
from ctrl.util.CIR import MTPProbeCIR
from ctrl.util.format import MTPDataFormat
from ctrl.lib.mtpcommand import MTPcommand
from ctrl.test.manualProbeQuery import MTPQuery
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPClient():

    def __init__(self, rawfilename, configfile, args, iwg):
        self.rawfilename = rawfilename
        self.gui = args.gui

        # Open output file for raw data
        try:
            self.rawfile = open(rawfilename, "a")
        except Exception:
            raise  # Unable to open file. Pass err back up to calling function

        # Configure UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_ip = "192.168.84.255"  # These should NOT be hardcoded - JAA
        self.ric_send_port = 32106  # 7 on the ground, 6 on the GV
        self.nidas_send_port = 30101

        # Get ports from config file
        port = configfile.getInt('udp_send_port')  # to send MTP UDP packets

        # Dictionary of allowed commands to send to firmware
        commandDict = MTPcommand()

        self.init = MTPProbeInit(args, port, commandDict, args.loglevel, iwg)
        self.move = MTPProbeMove(self.init, commandDict)
        self.data = MTPProbeCIR(self.init, commandDict)
        self.fmt = MTPDataFormat(self.init, self.data, commandDict, iwg)

    def bootCheck(self):
        return(self.init.bootCheck())

    def clearBuffer(self):
        self.init.clearBuffer()

    def close(self):
        # Close output file for raw data
        try:
            self.rawfile.close()
        except Exception as err:
            logger.printmsg("ERROR", err + " Unable to close file " +
                            self.rawfilename)

    def printMenu(self):
        """ List user options """
        print("=========================================")
        print("TYPE 'c' to begin cycling and 'x' to stop")
        print("=========================================")
        print("If testing, please issue a command:")
        print("0 = Status")
        print("1 = Init")
        print("2 = Move Home")
        print("3 = Step")
        print("4 = generic CIRS")
        print("5 = E line")
        print("6 = B line")
        print("7 = Housekeeping(M1/M2/Pt)")
        print("8 = create Raw data and UDP")
        print("9 = Probe On Check")
        print("q = Manual Probe Query")
        print("x = Exit")

    def initProbe(self):
        # Initialize probe
        status = self.init.init()
        return(status)  # True if success, False if init failed

    def readInput(self, cmdInput):
        if cmdInput == '0':
            # Print status
            self.init.getStatus()

        elif cmdInput == '1':
            # Initialize probe
            self.initProbe()

        elif cmdInput == '2':
            # Move Home
            self.move.moveHome()  # Returns true of moveHome successful

        elif cmdInput == '3':
            """ Attempt a single move """
            self.singleMoveTest()

        elif cmdInput == '4':
            """ Attempt to read freq for all channels - no move """
            self.readFreqTest()

        elif cmdInput == '5':
            """ Create an E line """
            self.createElineTest()

        elif cmdInput == '6':

            logger.printmsg("info", "sit tight - Bline scan typically takes " +
                            "6 seconds")

            # Make sure the buffer is clear before starting the scan.
            self.clearBuffer()

            # move home
            self.move.moveHome()  # After each B line, probe needs move home
            self.move.moveHome()  # twice to clear move stat.

            # Create B line - need to ensure in home position first
            self.fmt.readBline(self.move)

        elif cmdInput == '7':
            # Create housekeeping lines
            self.fmt.readM1line()
            self.fmt.readM2line()
            self.fmt.readPTline()

        elif cmdInput == '8':
            self.createRawRec()

        elif cmdInput == 'c':
            self.cycle()

        elif cmdInput == 'q':
            # Go into binary command input mode
            query = MTPQuery(self.init.getSerialPort())
            query.query()

        elif cmdInput == 'x':
            self.close()
            exit(1)

        else:
            logger.printmsg("info", "Unknown command. Please try again.")

    def cycle(self):
        self.cycleMode = True

        # Initialize probe. Return true if success
        success = self.initProbe()
        if not success:  # Keep trying
            logger.printmsg("info", "Init failed. Trying again")
            time.sleep(1)  # Emulate manual response time. Prob not needed
            # Move home, then init again, because this is what I do
            self.move.moveHome()
            success = self.initProbe()

        # Move home. Returns true if successful
        success = self.move.moveHome()
        if not success:  # Keep trying
            logger.printmsg("info", "Move home failed. Trying again")
            time.sleep(1)  # Emulate manual response time. Prob not needed
            success = self.move.moveHome()

        while self.cycleMode is True:  # Cycle probe until user requests exit
            # In command line mode, capture keyboard strokes
            if self.gui is False:  # In command line mode
                self.captureExit()

            self.createRawRec()

    def stopCycle(self):
        self.cycleMode = False

    def captureExit(self):
        """
        Capture user keystroke and if 'x' exit program. Ignore all other input
        """
        if os.name == 'nt':  # Windows
            read_ready = []
            # Click x to exit loop
            if msvcrt.kbhit():  # Catch if keyboard char hit
                read_ready.append(sys.stdin)
        else:
            # Get user's menu selection.
            ports = [sys.stdin]
            read_ready, _, _ = select.select(ports, [], [], 0.15)

        if sys.stdin in read_ready:
            cmdInput = sys.stdin.readline()
            cmdInput = str(cmdInput).strip('\n')
            if cmdInput == 'x':
                self.close()
                exit(1)

    def createRawRec(self):
        logger.printmsg("info", "sit tight - complete scans " +
                        "typically take 17s")
        firstTime = datetime.datetime.now(datetime.timezone.utc)

        # Create a raw record
        raw = self.fmt.createRawRecord(self.move)
        logger.printmsg("info", "RAW\n" + raw)

        # Command finished
        nowTime = datetime.datetime.now(datetime.timezone.utc)
        logger.printmsg("info", "record creation took " +
                        str(nowTime-firstTime))

        # Write raw record to output file
        self.writeRaw(raw + "\n")

        writeTime = datetime.datetime.now(datetime.timezone.utc)
        logger.printmsg("info", "record write took " +
                        str(writeTime-nowTime))

        # Create the UDP packet
        udpLine = self.fmt.createUDPpacket()
        self.sendUDP(udpLine)

        udpTime = datetime.datetime.now(datetime.timezone.utc)
        logger.printmsg("info", "udp creation took " +
                        str(udpTime-writeTime))

    def writeFileTime(self, time):
        """
        Write a line giving the file open time as the first line of the raw
        data file.
        """
        self.rawfile.write("Instrument on " + time + "\n")
        self.rawfile.flush()

    def writeRaw(self, raw):
        self.rawfile.write(raw)
        self.rawfile.flush()

    def sendUDP(self, udpLine):
        """ Send UDP packet to RIC and nidas """
        if self.sock:  # Sent to RIC
            self.sock.sendto(udpLine.encode('utf-8'),
                             (self.udp_ip, self.ric_send_port))
        if self.sock:  # Send to nidas ip needs to be 192.168.84.255
            self.sock.sendto(udpLine.encode(),
                             (self.udp_ip, self.nidas_send_port))

    def singleMoveTest(self):
        """ Test (and time) moving to first angle from home """
        # Determine how long it takes to move to first angle
        firstTime = datetime.datetime.now(datetime.timezone.utc)

        # Confirm in home position and ready to move (not integrating or
        # already moving)
        if (self.move.isMovePossibleFromHome()):

            # Move to first angle in readBline
            cmd, currentClkStep = self.fmt.getAngle(80, 0)
            s = self.move.moveTo(cmd, self.data)
            logger.printmsg('info', "First angle reached = " + str(s))

            # Command finished
            nowTime = datetime.datetime.now(datetime.timezone.utc)
            logger.printmsg("info", "single move took " +
                            str(nowTime-firstTime))

    def readFreqTest(self):
        """ Test (and time) read freq for all channels - no move """
        # Determine how long it takes to read three frequencies
        firstTime = datetime.datetime.now(datetime.timezone.utc)

        # Read data at current position for three frequencies
        countStr = self.data.CIRS()

        # Command finished
        nowTime = datetime.datetime.now(datetime.timezone.utc)

        logger.printmsg("info", "data from one position:" + str(countStr))
        logger.printmsg("info", "freq triplet creation took " +
                        str(nowTime-firstTime))

    def createElineTest(self):
        """ Create E line """
        # Read data at current position for three frequencies and for
        # noise diode on then off
        # During scan looping, ensure send moveHome() before read Eline so
        # are pointing at target
        self.move.moveHome()
        self.fmt.readEline()
