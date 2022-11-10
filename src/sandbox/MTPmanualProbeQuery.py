###############################################################################
# Simple wrapper script to send manual command to the probe. Useful for testing
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import sys
import logging
import serial
import socket
import argparse
from ctrl.lib.manualProbeQuery import MTPQuery
from EOLpython.Qlogger.messageHandler import QLogger as logger


def main():

    # Parse command line args
    parser = argparse.ArgumentParser(
        description="Script to send manual commands to the MTP probe")
    parser.add_argument(
        '--device', type=str, default='COM6',
        help="Device on which to receive messages from MTP instrument")
    args = parser.parse_args()

    logger.initLogger(sys.stdout, logging.DEBUG, None)

    try:
        serialPort = serial.Serial(args.device, 9600, timeout=0.15)
        udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        udpSocket.connect(('127.0.0.1', 32107))  # ip, port number
    except serial.SerialException:
        print("Device " + args.device + " does not exist on this machine." +
              " Please specify a valid device using the --device command" +
              " line option. Type '" + sys.argv[0] + " --help' for the " +
              "help menu")
        exit(1)

    query = MTPQuery(serialPort)
    query.query()


if __name__ == "__main__":
    main()
