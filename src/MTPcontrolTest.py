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
from ctrl.mtp_client import MTPClient
from ctrl.util.init import MTPProbeInit
from ctrl.util.move import MTPProbeMove
from ctrl.util.CIR import MTPProbeCIR
from ctrl.util.format import MTPDataFormat
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

    # Menu of user commands
    client = MTPClient()

    # Get port from config file
    port = configfile.getInt('udp_send_port')

    init = MTPProbeInit(args, port, commandDict, args.loglevel)
    move = MTPProbeMove(init, commandDict)
    data = MTPProbeCIR(init, commandDict)
    fmt = MTPDataFormat(init, data, commandDict)

    probeResponding = False

    client.printMenu()
    try:
        while True:
            # Get user's menu selection
            cmdInput = sys.stdin.readline()
            cmdInput = str(cmdInput).strip('\n')

            # Check if probe is on and responding
            # Separate on and responding so can pop up waiting for radiometer
            if probeResponding is False or cmdInput == '9':
                probeResponding = init.bootCheck()
                if cmdInput == '9':
                    continue  # No need to continue; already executed command

            # Make sure have read everything from the buffer for the previous
            # command before continuing. If the buffer is not clear, this
            # indicates a problem, so notify user.
            init.clearBuffer()

            client.readInput(cmdInput, init, move, data, fmt)
            client.printMenu()

    except KeyboardInterrupt:
        exit(1)


if __name__ == "__main__":
    main()
