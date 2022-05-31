###############################################################################
# Top-level program to launch the MTPcontrol test applications.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import sys
import argparse
import logging
import datetime
from lib.config import config
from ctrl.util.init import MTPProbeInit
from ctrl.util.move import MTPProbeMove
from ctrl.util.CIR import MTPProbeCIR
from ctrl.util.format import MTPDataFormat
from ctrl.test.manualProbeQuery import MTPQuery
from ctrl.lib.mtpcommand import MTPcommand
from EOLpython.Qlogger.messageHandler import QLogger as logger


def parse_args():
    """ Instantiate a command line argument parser """

    # Define command line arguments which can be provided by users
    parser = argparse.ArgumentParser(
        description="Script to initialize the MTP instrument")
    parser.add_argument(
        '--config', type=str, required=True,
        help='File containing project-specific MTP configuration info.')
    parser.add_argument(
        '--device', type=str, default='COM6',
        help="Device on which to receive messages from MTP instrument")
    parser.add_argument(
        '--debug', dest='loglevel', action='store_const',
        const=logging.DEBUG, default=logging.INFO,
        help="Show debug log messages")
    parser.add_argument(
        '--logmod', type=str, default=None, help="Limit logging to " +
        "given module")

    # Parse the command line arguments
    args = parser.parse_args()

    return(args)


def printMenu():
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

    cmdInput = sys.stdin.readline()
    cmdInput = str(cmdInput).strip('\n')

    return(cmdInput)


def main():

    # Process command line arguments.
    args = parse_args()

    # Configure logging
    stream = sys.stdout
    logger.initLogger(stream, args.loglevel, args.logmod)

    # Initialize a config file (includes reading it into a dictionary)
    configfile = config(args.config)

    # Dictionary of allowed commands to send to firmware
    commandDict = MTPcommand()

    # Move readConfig out of viewer/MTPclient to lib/readConfig and
    # get port from there. Add --config to parse_args - JAA
    port = configfile.getInt('udp_send_port')

    init = MTPProbeInit(args, port, commandDict)
    move = MTPProbeMove(init, commandDict)
    data = MTPProbeCIR(init, commandDict)
    fmt = MTPDataFormat(init, data, commandDict)

    probeResponding = False
    while (1):

        cmdInput = printMenu()

        # Check if probe is on and responding
        # Separate on and responding so can pop up waiting for radiometer
        if probeResponding is False or cmdInput == '9':
            probeResponding = init.bootCheck()
            if cmdInput == '9':
                continue  # No need to continue; already executed command

        # Make sure we have read everything from the buffer for the previous
        # command before continuing. If the buffer is not clear, this
        # indicates a problem, so notify user.
        init.clearBuffer()

        if cmdInput == '0':
            # Print status
            init.getStatus()

        elif cmdInput == '1':
            # Initialize probe
            init.init()

        elif cmdInput == '2':
            # Move Home
            move.moveHome()

        elif cmdInput == '3':
            """ Attempt a single move """
            # Determine how long it takes to read three frequencies
            firstTime = datetime.datetime.now(datetime.timezone.utc)

            # isMovePossibleFromHome() returns 4 if able to move
            if (move.isMovePossibleFromHome()):

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
            # Need to add move to point at target - JAA
            fmt.readEline()

        elif cmdInput == '6':
            # Create B line
            fmt.readBline(move)

        elif cmdInput == '7':
            # Create housekeeping lines
            fmt.readM1line()
            fmt.readM2line()
            fmt.readPTline()

        elif cmdInput == '8':
            # Create UDP packet
            # This logic gets the housekeeping, then the Bline. Is that what
            # we want? Does it matter? - JAA
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


if __name__ == "__main__":
    main()
