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
from lib.config import config
from ctrl.test.init import MTPProbeInit
from ctrl.test.move import MTPProbeMove
from ctrl.test.CIR import MTPProbeCIR
from ctrl.test.manualProbeQuery import MTPQuery
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
    print("5 = CIRS ND on then off")
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

    # Move readConfig out of viewer/MTPclient to lib/readConfig and
    # get port from there. Add --config to parse_args - JAA
    port = configfile.getInt('udp_send_port')

    init = MTPProbeInit(args, port)
    move = MTPProbeMove(init)
    data = MTPProbeCIR(init)

    probeResponding = False
    while (1):

        cmdInput = printMenu()

        # Check if probe is on and responding
        if probeResponding is False or cmdInput == '9':
            probeResponding = init.bootCheck()

        if cmdInput == '0':
            # Print status
            status = init.getStatus()
            # Should check status here. What are we looking for? - JAA

        elif cmdInput == '1':
            # Initialize probe
            init.init()

        elif cmdInput == '2':
            # Move Home
            move.moveHome()

        elif cmdInput == '3':
            # Step
            if (move.isMovePossibleFromHome(maxDebugAttempts=12,
                                            scanStatus='potato') == 4):
                move.initForNewLoop()

                # Move hardcoded UART commands into move.py - JAA
                echo = move.moveTo(b'U/1J0D28226J3R\r\n')
                s = init.findChar(echo, b'@')
                logger.printmsg('debug', "First angle, status = %r", s)

        elif cmdInput == '4':
            # Read data at current position for three frequencies
            countStr = data.CIRS()
            logger.printmsg("debug", "data from one position:" + str(countStr))

        elif cmdInput == '5':
            # Read data at current position for three frequencies and for
            # noise diode on then off
            data.readEline()

        elif cmdInput == 'q':
            # Go into binary command input mode
            query = MTPQuery(init.getSerialPort())
            query.query()

        elif cmdInput == 'x':
            exit(1)


if __name__ == "__main__":
    main()
