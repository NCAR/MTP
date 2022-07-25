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
from ctrl.test.manualProbeQuery import MTPQuery
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPClient():

    def __init__(self, rawfilename):
        self.rawfilename = rawfilename

        # Open output file for raw data
        try:
            self.rawfile = open(rawfilename, "a")
        except Exception:
            raise  # Unable to open file. Pass err back up to calling function

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
        # print("If testing, please issue a command:")
        # print("0 = Status")
        # print("1 = Init")
        # print("2 = Move Home")
        # print("3 = Step")
        # print("4 = generic CIRS")
        # print("5 = E line")
        # print("6 = B line")
        # print("7 = Housekeeping(M1/M2/Pt)")
        # print("8 = create Raw data and UDP")
        # print("9 = Probe On Check")
        # print("q = Manual Probe Query")
        # print("x = Exit")

    def readInput(self, cmdInput, init, move, data, fmt):
        if cmdInput == '0':
            # Print status
            init.getStatus()

        elif cmdInput == '1':
            # Initialize probe
            init.init()

        elif cmdInput == '2':
            # Move Home
            move.moveHome()  # Returns true of moveHome successful

        elif cmdInput == '3':
            """ Attempt a single move """
            # Determine how long it takes to read three frequencies
            firstTime = datetime.datetime.now(datetime.timezone.utc)

            # Confirm in home position and ready to move (not integrating or
            # already moving)
            if (move.isMovePossibleFromHome()):

                # Move to first angle in readBline
                cmd, currentClkStep = fmt.getAngle(80, 0)
                s = move.moveTo(cmd, data)
                logger.printmsg('info', "First angle reached = " + str(s))

                # Command finished
                nowTime = datetime.datetime.now(datetime.timezone.utc)
                logger.printmsg("info", "single move took " +
                                str(nowTime-firstTime))

        elif cmdInput == '4':
            # Determine how long it takes to read three frequencies
            firstTime = datetime.datetime.now(datetime.timezone.utc)

            # Read data at current position for three frequencies
            countStr = data.CIRS()

            # Command finished
            nowTime = datetime.datetime.now(datetime.timezone.utc)

            logger.printmsg("info", "data from one position:" + str(countStr))
            logger.printmsg("info", "freq triplet creation took " +
                            str(nowTime-firstTime))

        elif cmdInput == '5':
            # Create E line
            # Read data at current position for three frequencies and for
            # noise diode on then off
            # During scan looping, ensure send moveHome() before read Eline so
            # are pointing at target
            move.moveHome()
            fmt.readEline()

        elif cmdInput == '6':

            logger.printmsg("info", "sit tight - Bline scan typically takes " +
                            "6 seconds")

            # Make sure the buffer is clear before starting the scan.
            init.clearBuffer()

            # move home
            move.moveHome()  # After each B line, probe needs two move homes
            move.moveHome()  # to clear move stat.

            # Create B line - need to ensure in home position first
            fmt.readBline(move)

        elif cmdInput == '7':
            # Create housekeeping lines
            fmt.readM1line()
            fmt.readM2line()
            fmt.readPTline()

        elif cmdInput == '8':
            self.createRawRec(move, fmt)

        elif cmdInput == 'c':
            success = init.init()  # Initialize probe. Return true if success
            if not success:  # Keep trying
                logger.printmsg("info", "Init failed. Trying again")
                time.sleep(1)  # Emulate manual response time. Prob not needed
                # Move home, then init again, because this is what I do
                move.moveHome()
                success = init.init()

            success = move.moveHome()  # Move home. Returns true if successful
            if not success:  # Keep trying
                logger.printmsg("info", "Move home failed. Trying again")
                time.sleep(1)  # Emulate manual response time. Prob not needed
                success = move.moveHome()

            while True:  # Cycle probe until user types 'x'
                if os.name == 'nt':  # Windows
                    read_ready = []
                    # Click x to exit loop
                    if msvcrt.kbhit():  # Catch if keyboard char hit
                        read_ready.append(sys.stdin)
                else:
                    # Get user's menu selection. Read IWG while wait
                    ports = [sys.stdin]
                    read_ready, _, _ = select.select(ports, [], [], 0.15)

                if sys.stdin in read_ready:
                    cmdInput = sys.stdin.readline()
                    cmdInput = str(cmdInput).strip('\n')
                    if cmdInput == 'x':
                        self.close()
                        exit(1)

                self.createRawRec(move, fmt)

        elif cmdInput == 'q':
            # Go into binary command input mode
            query = MTPQuery(init.getSerialPort())
            query.query()

        elif cmdInput == 'x':
            self.close()
            exit(1)

        else:
            logger.printmsg("info", "Unknown command. Please try again.")

    def createRawRec(self, move, fmt):
        logger.printmsg("info", "sit tight - complete scans " +
                        "typically take 17s")

        # Create a raw record
        raw = fmt.createRawRecord(move)
        logger.printmsg("info", "RAW\n" + raw)

        # Write raw record to output file
        self.writeRaw(raw + "\n")

        # Create the UDP packet
        udpLine = fmt.createUDPpacket()
        self.sendUDP(udpLine)

    def writeRaw(self, raw):
        self.rawfile.write(raw)
        self.rawfile.flush()

    def sendUDP(self, udpLine):
        """ Send UDP packet to RIC and nidas """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        udp_ip = "192.168.84.255"
        ric_send_port = 32106  # 7 on the ground, 6 on the GV
        nidas_send_port = 30101
        if sock:  # Sent to RIC
            sock.sendto(udpLine.encode('utf-8'), (udp_ip, ric_send_port))
        if sock:  # Send to nidas ip needs to be 192.168.84.255
            sock.sendto(udpLine.encode(), (udp_ip, nidas_send_port))
