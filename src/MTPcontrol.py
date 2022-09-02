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
from ctrl.util.iwg import MTPiwg
from ctrl.mtp_client import MTPClient
from ctrl.view import MTPControlView
from EOLpython.Qlogger.messageHandler import QLogger
from PyQt5.QtWidgets import QApplication

logger = QLogger("EOLlogger")


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
        const=logging.DEBUG, default=logging.WARNING,
        help="Show debug log messages. If --v also set, the level that" +
        "appears later in the command will prevail, eg --debug --v displays" +
        "info level messages and higher")
    parser.add_argument(
        '--v', dest='loglevel', action='store_const',
        const=logging.INFO, default=logging.WARNING,
        help="Verbose mode - show informational log messages. If --debug " +
        "also set, the level that appears later in the command will prevail," +
        " eg --v --debug displays debug level messages and higher")
    parser.add_argument(
        '--logmod', type=str, default=None, help="Limit logging to " +
        "given module")
    parser.add_argument(
        '--gui', action='store_true', help="Run in GUI mode")

    # Parse the command line arguments
    args = parser.parse_args()

    return(args)


def main():

    # Process command line arguments.
    args = parse_args()

    # Get current time - used in raw and log filenames
    nowTime = datetime.datetime.now(datetime.timezone.utc)

    # Configure logging
    stream = sys.stdout  # send WARNING|ERROR to terminal window
    logger.initStream(stream, args.loglevel, args.logmod)

    # Initialize a config file (includes reading it into a dictionary)
    configfile = config(args.config)

    # Create the raw data filename from the current UTC time
    rawfile = nowTime.strftime("N%Y%m%d%H.%M")
    rawdir = configfile.getPath('rawdir')
    rawfilename = os.path.join(rawdir, rawfile)

    # In addition, send all messages to logfile
    logdir = configfile.getPath('logdir')
    log_filepath = os.path.join(logdir, "log." + rawfile)
    logger.initLogfile(log_filepath, logging.DEBUG)

    # connect to IWG port
    iwgport = configfile.getInt('iwg1_port')   # to listen for IWG packets
    iwg = MTPiwg()
    iwg.connectIWG(iwgport)
    # Instantiate an IWG reader and configure a dictionary to store the
    # IWG data
    asciiparms = configfile.getPath('ascii_parms')
    iwg.initIWG(asciiparms)

    # Instantiate client which handles user commands
    try:
        client = MTPClient(rawfilename, configfile, args, iwg)
        client.writeFileTime(nowTime.strftime("%H:%M:%S %m-%d-%Y"))
    except Exception as e:
        logger.error("Unable to open Raw file: " + e)
        print("ERROR: Unable to open Raw data output file: " + e)
        exit(1)

    probeResponding = False

    if args.gui is True:  # Run in GUI mode

        app = QApplication([])

        # Instantiate the GUI
        ctrlview = MTPControlView(app, client, iwg)

        # Run the application until the user closes it.
        sys.exit(app.exec_())

    else:
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
                        probeResponding = client.bootCheck()
                        if cmdInput == '9':
                            # Command executed, so loop back and ask for next
                            # command
                            client.printMenu()
                            continue

                    # Make sure have read everything from the buffer for the
                    # previous command before continuing. If the buffer is not
                    # clear, this indicates a problem, so notify user.
                    client.clearBuffer()

                    client.readInput(cmdInput)
                    client.printMenu()

        except KeyboardInterrupt:
            exit(1)


if __name__ == "__main__":
    main()
