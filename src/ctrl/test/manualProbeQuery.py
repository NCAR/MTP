import logging
from time import time
import serial
from serial import Serial

logging.basicConfig(level = logging.DEBUG)
serialPort = serial.Serial('COM6', 9600, timeout = .5)
#serialPort.setBaudrate(9600)


while 1:
    # query/wait which command to send from user
    # needs to be in binary string format eg: b'S'
    query =  input("What command shall we send to the probe?")
    print("sending: "+ str(query))
    # send command
    query = query + '\r\n'
    serialPort.write(query.encode('ascii'))
    logging.debug("sending: %r", query.encode('ascii'))
    for i in range(4):
        print(i)
        #buf = serialPort.readline()
        buf = serialPort.readline()
        logging.debug("read %r", buf)
        '''
        if i>1:    
            query = "S\r\n"
            serialPort.write(query.encode('ascii'))
        logging.debug("read %r", buf)
        '''


