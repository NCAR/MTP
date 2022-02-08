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



def moveComplete(buf):
    # returns true if '@' is found,
    # needs a timeout if comand didn't send properly
    if buf.find(b'@') >= 0:
        return True 
    return False


def sanitize(data):
    data = data[data.find(b':') + 1 : len(data) - 3]
    placeholder = data.decode('ascii')
    place = placeholder.split(' ')
    ret = ''
    for datum in place:
        ret += '%06d' % int(datum,16) + ' '

    return ret



def sendCommand(command):
    serialPort.write(command)

    readEchos(3)

    #serialPort.write(b'S\r\n')
    #readEchos(3)

# frequencies 56.363,57.612,58.383
# translated: 
#b'C28180\r\n'
#b'C28805\r\n'
#b'C229180\r\n'


while (1):

    #command = b'U/1L4000h30m100R'
    command = b'N 1\r\n'
    #command = b'I 40\r\n'
    #command = b'C229180\r\n'
    #command = b'C28180\r\n'
    readEchos(3)
    sendCommand(command)
    time.sleep(0)
    
    




