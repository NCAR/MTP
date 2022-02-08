import logging
import datetime
import time
import serial
import socket
import sys
from serial import Serial

logging.basicConfig(level = logging.DEBUG)
# initial setup of time, logging, serialPort, Udp port
serialPort = serial.Serial('COM6', 9600, timeout = 0.15)
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
udpSocket.connect(('127.0.0.1', 32107)) # ip, port number

def readEchos(num):
    buf = b''
    for i in range(num):
        buf = buf + serialPort.readline()

    logging.debug("read %r", buf)
    return buf 




def findChar(array, binaryCharacter):
    # status = 0-6, C, B, or @
    # can also check for binary strings
    # presumably chars are faster matches?
    # otherwise error = -1
    index = array.find(binaryCharacter)
    if index>-1:
        #logging.debug("status: %r, %r", array[index], array)
        return array[index]
    else:
        logging.error("status unknown, unable to find %r: %r",  binaryCharacter, array)
        return -1

def probeResponseCheck():
        serialPort.write(b'V\r\n')
        if findChar(readEchos(3), b"MTPH_Control.c-101103>101208")>0:
            logging.info("Probe on, responding to version string prompt")
            return True
        else:
            logging.info("Probe not responding to version string prompt")
            return False

def truncateBotchedMoveCommand():
        serialPort.write(b'Ctrl-C\r\n')
        if findChar(readEchos(3),b'Ctrl-C\r\n')>0: 
            logging.info("Probe on, responding to Ctrl-C string prompt")
            return True
        else:
            logging.info("Probe not responding to Ctrl-C string prompt")
            return False


def probeOnCheck():
    if findChar(readEchos(3), b"MTPH_Control.c-101103>101208")>0:
        logging.info("Probe on, Version string detected")
        return True
    else:
        logging.debug("No version startup string from probe found, sending V prompt")
        if probeResponseCheck():
            return True
        else:
            if truncateBotchedMoveCommand():
                logging.warning("truncateBotchedMoveCommand called, ctrl-c success") 
                return True
            else:
                logging.error("probe not responding to truncateBotchedMoveCommand ctrl-c, power cycle necessary")
                return False

    logging.error("probeOnCheck all previous logic tried, something's wrong")
    return False



# on boot probe sends 
# MTPH_Control.c-101103>101208
# needs to be caught first before other init commands are sent
# also response to V
probeResponding = False
while (1):
    if probeResponding == False:
        while probeOnCheck() == False:
            time.sleep(10)
            logging.error("probe off or not responding")
        logging.info("Probe on check returns true")
        probeResponding = True
    time.sleep(1)

    readEchos(3)
    
    




