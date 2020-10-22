import logging
from PyQt5.QtSerialPort import *
from PyQt5.QtCore import *
from time import *


logging.basicConfig(level = logging.DEBUG)
serialPort = QSerialPort()
serialPort.setPortName('COM6')
serialPort.setBaudRate(9600)

if serialPort.isOpen():
    serialPort.close()
    print("COM6 was open, closing to reopen")

if serialPort.open(QIODevice.ReadWrite):
    print("COM6 sucessfuly opened")
else:
    print("COM6 failed to open")


while 1:

    # query/wait which command to send from user
    # needs to be in binary string format eg: b'S'
    query =  input("What command shall we send to the probe?")
    print("sending: "+ str(query))
    # send command
    query = 'V' + '\r'
    for i in range(12):
        serialPort.write(b'V\r\n')
        logging.debug("sending: %r", b'V\r\n')
        print(i)
        sleep(1)
        #if serialPort.canReadLine():
        buf = serialPort.readData(1024)
        logging.debug("read %r", buf)



