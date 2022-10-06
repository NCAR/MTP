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
from lib.config import config
from ctrl.util.iwg import MTPiwg
from ctrl.util.init import MTPProbeInit
from ctrl.util.move import MTPProbeMove
from ctrl.util.CIR import MTPProbeCIR
from ctrl.util.format import MTPDataFormat
from ctrl.lib.mtpcommand import MTPcommand
from ctrl.lib.manualProbeQuery import MTPQuery
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class MTPClient():

    def __init__(self, args, nowTime, app=None):
        self.gui = args.gui
        self.app = app

        # Initialize counters
        self.cyclesSinceLastStop = 0
        self.totalCycles = 0
        self.elapsedTime = datetime.timedelta(seconds=0)

        # Initialize a config file (includes reading it into a dictionary)
        self.configfile = self.config(args.config)

        # connect to IWG port
        self.iwg = self.connectIWG()

        # Create the raw data filename from the current UTC time
        self.openRaw(nowTime)

        # Dictionary of allowed commands to send to firmware
        commandDict = MTPcommand()

        # Initialize probe control classes
        port = self.configfile.getInt('inst_send_port')  # send MTP UDP packets
        fghz = self.configfile.getVal('Frequencies')  # scan frequencies
        self.init = MTPProbeInit(self, args, port, commandDict, args.loglevel,
                                 self.iwg, app)
        self.move = MTPProbeMove(self.init, commandDict)
        self.data = MTPProbeCIR(self.init, commandDict, fghz)
        self.fmt = MTPDataFormat(self, self.init, self.data, commandDict,
                                 self.iwg, app, self.configfile)

    def getIWG(self):
        return self.iwg

    def config(self, configfile_name):
        # Initialize a config file (includes reading it into a dictionary)
        return config(configfile_name)

    def connectIWG(self):
        # connect to IWG port
        iwgport = self.configfile.getInt('iwg1_port')  # listen for IWG packets
        iwg = MTPiwg()
        iwg.connectIWG(iwgport)
        # Instantiate an IWG reader and configure a dictionary to store the
        # IWG data
        asciiparms = self.configfile.getPath('ascii_parms')
        iwg.initIWG(asciiparms)

        return iwg

    def openRaw(self, nowTime):
        # Open output file for raw data
        self.rawfileDate = nowTime.strftime("N%Y%m%d%H.%M")
        rawdir = self.configfile.getPath('rawdir')
        rawfilename = os.path.join(rawdir, self.rawfileDate)

        try:
            self.rawfile = open(rawfilename, "a")
        except Exception:
            raise  # Unable to open file. Pass err back up to calling function

    def getLogfilePath(self):
        logdir = self.configfile.getPath('logdir')
        return os.path.join(logdir, "log." + self.rawfileDate)

    def connectGUI(self, view):
        """
        Connect the view to the client so the client can update the view
        """
        self.view = view

    def bootCheck(self):
        return self.init.bootCheck()

    def clearBuffer(self):
        self.init.clearBuffer()

    def close(self):
        # Close output file for raw data
        try:
            self.rawfile.close()
        except Exception as err:
            logger.error(err + " Unable to close file " + self.rawfilename)

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
        if self.app:
            if status is True:
                self.view.setLEDgreen(self.view.probeStatusLED)
            else:
                self.view.setLEDred(self.view.probeStatusLED)

        return status  # True if success, False if init failed

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

            logger.info("sit tight - Bline scan typically takes 6 seconds")

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
            logger.info("Unknown command. Please try again.")

    def cycle(self):
        self.cycleMode = True

        # Initialize probe. Return true if success
        success = self.initProbe()
        if not success:  # Keep trying
            logger.info("Init failed. Trying again")
            time.sleep(1)  # Emulate manual response time. Prob not needed
            # Move home, then init again, because this is what I do
            self.move.moveHome()
            success = self.initProbe()

        # Move home. Returns true if successful
        success = self.move.moveHome()
        if not success:  # Keep trying
            logger.info("Move home failed. Trying again")
            time.sleep(1)  # Emulate manual response time. Prob not needed
            success = self.move.moveHome()

        self.move.isMovePossibleFromHome(1)

        while self.cycleMode is True:  # Cycle probe until user requests exit
            # In command line mode, capture keyboard strokes
            if self.gui is False:  # In command line mode
                self.captureExit()

            self.createRawRec()

    def stopCycle(self):
        self.cyclesSinceLastStop = 0
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
        logger.info("sit tight - complete scans typically take 17s")
        firstTime = datetime.datetime.now(datetime.timezone.utc)

        # Create a raw record
        raw = self.fmt.createRawRecord(self.move)
        logger.info("RAW\n" + raw)

        # Command finished
        nowTime = datetime.datetime.now(datetime.timezone.utc)
        logger.info("record creation took " + str(nowTime-firstTime))

        # Write raw record to output file
        self.writeRaw(raw + "\n")

        writeTime = datetime.datetime.now(datetime.timezone.utc)
        logger.info("record write took " + str(writeTime-nowTime))

        # Create the UDP packet
        udpLine = self.fmt.createUDPpacket()
        self.sendUDP(udpLine)

        udpTime = datetime.datetime.now(datetime.timezone.utc)
        logger.info("udp creation took " + str(udpTime-writeTime))

        self.cyclesSinceLastStop += 1
        self.totalCycles += 1
        self.elapsedTime = udpTime-firstTime
        if self.app:
            self.view.updateGUIEndOfLoop(self.elapsedTime, self.totalCycles,
                                         self.cyclesSinceLastStop)

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

    def processIWG(self, read_ready, iwgBox):
        """
        If IWG packet available, display it and save it to the dictionary
        """
        lastIWG = datetime.datetime.now()  # Missing IWG if > 1 sec since last
        if self.iwg.socket() in read_ready:
            self.iwg.readIWG(iwgBox)  # read, save, and display
            if iwgBox:  # Update status light
                self.view.setLEDgreen(self.view.receivingIWGLED)
            lastIWG = datetime.datetime.now()
        else:
            currIWG = datetime.datetime.now()
            if iwgBox:  # Update status light
                if currIWG - lastIWG > datetime.timedelta(seconds=1):
                    self.view.setLEDred(self.view.receivingIWGLED)

    def sendUDP(self, udpLine):
        """ Send UDP packet to RIC and nidas """
        # Configure UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        if self.sock:
            self.udp_ip = self.configfile.getVal('udp_ip')
            # Sent to RIC
            self.ric_send_port = self.configfile.getInt('inst_send_port')
            self.sock.sendto(udpLine.encode('utf-8'),
                             (self.udp_ip, self.ric_send_port))
            # Send to nidas ip needs to be 192.168.84.255
            self.nidas_send_port = self.configfile.getInt('nidas_port')
            self.sock.sendto(udpLine.encode(),
                             (self.udp_ip, self.nidas_send_port))
            # Update LED
            if self.app and self.cycleMode is True:
                self.view.updateUDPStatus(True)

    def singleMoveTest(self):
        """ Test (and time) moving to first angle from home """
        # Determine how long it takes to move to first angle
        firstTime = datetime.datetime.now(datetime.timezone.utc)

        # Confirm in home position and ready to move (not integrating or
        # already moving)
        if (self.move.isMovePossibleFromHome(0.3)):

            # Move to first angle in readBline
            cmd, currentClkStep = self.fmt.getAngle(80, 0)
            s = self.move.moveTo(cmd, self.data)
            logger.info("First angle reached = " + str(s))

            # Command finished
            nowTime = datetime.datetime.now(datetime.timezone.utc)
            logger.info("single move took " + str(nowTime-firstTime))

    def readFreqTest(self):
        """ Test (and time) read freq for all channels - no move """
        # Determine how long it takes to read three frequencies
        firstTime = datetime.datetime.now(datetime.timezone.utc)

        # Read data at current position for three frequencies
        countStr = self.data.CIRS()

        # Command finished
        nowTime = datetime.datetime.now(datetime.timezone.utc)

        logger.info("data from one position:" + str(countStr))
        logger.info("freq triplet creation took " + str(nowTime-firstTime))

    def createElineTest(self):
        """ Create E line """
        # Read data at current position for three frequencies and for
        # noise diode on then off
        # During scan looping, ensure send moveHome() before read Eline so
        # are pointing at target
        self.move.moveHome()
        self.fmt.readEline()
