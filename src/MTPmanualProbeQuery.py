import sys
import logging
import serial
import socket
from ctrl.test.manualProbeQuery import MTPQuery
from EOLpython.Qlogger.messageHandler import QLogger as logger

def main():

    logger.initLogger(sys.stdout, logging.DEBUG , None)

    serialPort = serial.Serial(sys.argv[1], 9600, timeout=0.15)
    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    udpSocket.connect(('127.0.0.1', 32107))  # ip, port number

    query = MTPQuery(serialPort)
    query.query()

if __name__ == "__main__":
    main()

