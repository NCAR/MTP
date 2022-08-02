###############################################################################
# Top-level program to launch the MTPcontrol test applications.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import os
if os.name == 'nt':
    import msvcrt
import sys
import datetime
import argparse
import logging
import select
from lib.config import config
from ctrl.mtp_client import MTPClient
from ctrl.util.iwg import MTPiwg
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

    # Get current time - used in raw and log filenames
    nowTime = datetime.datetime.now(datetime.timezone.utc)

    # Configure logging
    # logfile = nowTime.strftime("log.N%Y%m%d%H%M")
    # fh = open(logfile, "a")
    # stream = fh  # send logging to logfile
    stream = sys.stdout  # send logging to terminal window
    logger.initLogger(stream, args.loglevel, args.logmod)

    # Initialize a config file (includes reading it into a dictionary)
    configfile = config(args.config)

    # Dictionary of allowed commands to send to firmware
    commandDict = MTPcommand()

    # Create the raw data filename from the current UTC time
    rawfile = nowTime.strftime("N%Y%m%d%H.%M")
    rawdir = configfile.getPath('rawdir')
    rawfilename = os.path.join(rawdir, rawfile)

    # Instantiate client which handles user commands
    try:
        client = MTPClient(rawfilename)
    except Exception as e:
        logger.printmsg("error", "Unable to open Raw file: " + e)
        print("ERROR: Unable to open Raw data output file: " + e)
        exit(1)

    # Get ports from config file to send UDP packets to MTP
    port = configfile.getInt('udp_send_port')  # port to send MTP UDP packets
    iwgport = configfile.getInt('iwg1_port')   # port to listen for IWG packets

    # connect to IWG port
    iwg = MTPiwg()
    iwg.connectIWG(iwgport)
    # Instantiate an IWG reader and configure a dictionary to store the
    # IWG data
    asciiparms = configfile.getPath('ascii_parms')
    iwg.initIWG(asciiparms)

    init = MTPProbeInit(args, port, commandDict, args.loglevel, iwg)
    move = MTPProbeMove(init, commandDict)
    data = MTPProbeCIR(init, commandDict)
    fmt = MTPDataFormat(init, data, commandDict, iwg)

    probeResponding = False

    client.printMenu()
    try:
        while True:
            if os.name == 'nt':  # Windows
                ports = [iwg.socket()]
                read_ready, _, _ = select.select(ports, [], [], 0.15)
                if msvcrt.kbhit():  # Catch if keyboard char hit
                    read_ready.append(sys.stdin)
            else:
                # Get user's menu selection. Read IWG while wait
                ports = [iwg.socket(), sys.stdin]
                read_ready, _, _ = select.select(ports, [], [], 0.15)

            if args.loglevel == "DEBUG":
                if len(read_ready) == 0:
                    print('timed out')

            if iwg.socket() in read_ready:
                iwg.readIWG()

            if sys.stdin in read_ready:
                cmdInput = sys.stdin.readline()
                cmdInput = str(cmdInput).strip('\n')

                # Check if probe is on and responding
                # Separate on and responding so can pop up waiting for
                # radiometer - JAA
                if probeResponding is False or cmdInput == '9':
                    probeResponding = init.bootCheck()
                    if cmdInput == '9':
                        # Command executed, so loop back and ask for next
                        # command
                        client.printMenu()
                        continue

                # Make sure have read everything from the buffer for the
                # previous command before continuing. If the buffer is not
                # clear, this indicates a problem, so notify user.
                init.clearBuffer()

                client.readInput(cmdInput, init, move, data, fmt)
                client.printMenu()

    except KeyboardInterrupt:
        exit(1)


if __name__ == "__main__":
    main()
