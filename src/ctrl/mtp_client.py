###############################################################################
# Class to generate a text-based MTP command menu
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import datetime
from ctrl.test.manualProbeQuery import MTPQuery
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPClient():

    def printMenu(self):
        """ List user options """
        print("Please issue a command:")
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

            # isMovePossibleFromHome() returns 4 if able to move
            if (move.isMovePossibleFromHome()):  # Check this LOGIC!!

                # Move to first angle in readBline
                cmd, currentClkStep = fmt.getAngle(80, 0)
                echo = move.moveTo(cmd)
                s = init.moveComplete(echo)
                logger.printmsg('info', "First angle reached = " + str(s))
            else:
                exit(1)

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
            fmt.readEline()

        elif cmdInput == '6':
            # Make sure the buffer is clear before starting the scan.
            init.clearBuffer()

            # Create B line
            fmt.readBline(move)

        elif cmdInput == '7':
            # Create housekeeping lines
            fmt.readM1line()
            fmt.readM2line()
            fmt.readPTline()

        elif cmdInput == '8':
            # Create UDP packet
            # During scan looping, ensure send moveHome() before read house-
            # keeping and Eline so pointing at target. Then get Bline.
            # Is this order what we want? Does it matter? - JAA
            logger.printmsg("info", "sit tight - scans typically take 17s")
            udpLine = ''

            # Determine how long it takes to create the B line
            firstTime = datetime.datetime.now(datetime.timezone.utc)

            # Get all the housekeeping data
            raw = fmt.readM1line() + '\n'  # Read M1 data from the probe
            udpLine = udpLine + fmt.getM1data()
            raw = raw + fmt.readM2line() + '\n'  # Read M2 data from the probe
            udpLine = udpLine + fmt.getM2data()
            raw = raw + fmt.readPTline() + '\n'  # Read PT data from the probe
            udpLine = udpLine + fmt.getPTdata()
            raw = raw + fmt.readEline() + '\n'  # Read E data from the probe
            udpLine = udpLine + fmt.getEdata()

            # Get the Bline data
            raw = fmt.readBline(move) + '\n' + raw  # Read B data from probe
            udpLine = fmt.getBdata() + ' ' + udpLine

            # UTC timestamp of Raw record is right after B line is collected
            nowTime = datetime.datetime.now(datetime.timezone.utc)

            # Get IWG line - TBD For now just use a static line - JAA
            IWG = 'IWG1,20101002T194729,39.1324,-103.978,4566.43,,14127.9' + \
                  ',,180.827,190.364,293.383,0.571414,-8.02806,318.85,' + \
                  '318.672,-0.181879,-0.417805,-0.432257,-0.0980951,2.367' + \
                  '93,-1.66016,-35.8046,16.3486,592.062,146.734,837.903,' + \
                  '9.55575,324.104,1.22603,45.2423,,-22    .1676, '

            # Generate timestamp for Raw data record
            RAWformattedTime = "%04d%02d%02d %02d:%02d:%02d " % (
                               nowTime.year, nowTime.month, nowTime.day,
                               nowTime.hour, nowTime.minute, nowTime.second)

            # Generate A line - TBD For now just use a static line - JAA
            aline = '+03.00 00.00 +00.00 00.00 +00.00 0.00 273.15 00.16 ' + \
                    '+39.913 +0.022 -105.118 +0.000 +073727 +072576 '

            # Put it all together to create the RAW record
            raw = 'A ' + RAWformattedTime + aline + '\n' + IWG + '\n' + raw

            logger.printmsg("info", "RAW\n" + raw)

            # Generate timestamp used in UDP packet
            UDPformattedTime = "%04d%02d%02dT%02d%02d%02d " % (
                               nowTime.year, nowTime.month, nowTime.day,
                               nowTime.hour, nowTime.minute, nowTime.second)

            # Put it all together to create the UDP packet
            udpLine = "MTP " + UDPformattedTime + aline + udpLine
            udpLine = udpLine.replace(' ', ',')
            logger.printmsg("info", "UDP packet: " + udpLine)

            logger.printmsg("info", "Raw record creation took " +
                            str(nowTime-firstTime))

            # If need to test UDP send, use lib/udp.py

        elif cmdInput == 'q':
            # Go into binary command input mode
            query = MTPQuery(init.getSerialPort())
            query.query()

        elif cmdInput == 'x':
            exit(1)

        else:
            logger.printmsg("info", "Unknown command. Please try again.")
