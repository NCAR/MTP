###############################################################################
# Convert/relay commands from a client UI via UDP to an instrument
# via RS-232.
#
# Uses pyqt5 QtSerialPort
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import logging
import time
from PyQt5.QtSerialPort import *
from PyQt5.QtCore import *
from PyQt5 import QtCore

logging.basicConfig(level=logging.DEBUG)
#logging = logging.getLogger(__name__)
class SerialInit(object):

    serialPort = QSerialPort()
    def __init__(self, parent, app, device=None):
        self.app = app
        self.parent = parent
        """
        Serial connection to instrument

        Examples:
        >>> 2+3
        5

        Add:
        if __name__ in "__main__":
            import doctest
            doctest.testmode()
        then run "python3 serial.py"
        and will run code on examples in comments
        """
        self.serialPort.setPortName('COM6')
        self.serialPort.setBaudRate(9600)
        # hopefully these are unneded
        #self.serial.setDataBits()
        #self.serial.setParity(self.parity)
        #self.serial.setStopBits(self.stop_bits)
        #self.serial.setFlowControl(self.flow_control)
        """ Check that the port isn't open already """

        if self.serialPort.isOpen():
            self.serialPort.close()
            logging.info("COM6 was open: now closed")
        while self.serialPort.isOpen() == False:
            if self.serialPort.open(QIODevice.ReadWrite):
                logging.info("COM6 is open")
            else:
                # Need to add popup here
                logging.info ("COM6 failed to open; reset USB: %r", self.serialPort.close())



        """ Not sure QtSerialPort has an exception in this case?"""
        '''
        except self.serialPort.SerialException as ex:
            logging.info("Port is unavailable: " + str(ex))
            exit()
        '''
        #as yet appears to be unnecessary
        #self.app.processEvents()
        # when probe powers on it sends a string, unprompted:
        # "MTPH_Control.c-101103>101208\r\n"
        return

    def canReadLine(self, timeVal):
        # returns a signal when there is data to be read
        logging.debug("can read line waiting ready read")
        val = self.serialPort.waitForReadyRead(timeVal)
        i=0
        while i < timeVal:
            self.parent.app.processEvents()
            if self.serialPort.canReadLine():
                buf = self.serialPort.readLine()
                logging.debug('canReadLine signal received')
                return buf
                break
            else:
                #logging.debug('canReadLine waiting for canreadline signal')
                i = i + 1
        #return b''

    def canReadAllLines(self, timeVal):
        # returns a signal when there is data to be read
        logging.debug("can read line waiting ready read")
        val = self.serialPort.waitForReadyRead(timeVal)
        i=0
        while i < timeVal:
            self.parent.app.processEvents()
            if self.serialPort.canReadLine():
                buf = self.serialPort.readLine()
                logging.debug('canReadLine signal received')
                while self.serialPort.canReadLine():
                    logging.debug('while can readline')
                    buf = buf + self.serialPort.readLine()
                    #logging.debug(buf)
                return buf
                break
            else:
                #logging.debug('canReadLine waiting for canreadline signal')
                i = i + 1
        #return b''

    def readLine(self, timeVal):
        # reads until there is no more data
        # or to first newline
        # for M01, M02, pt wait for entire line to come in. 
        # doing multiple reads just allows for the lines to 
        # run together e.g. b'03 \r\nM'
        # clear buffer
        #buf = b'' 
        #logging.debug("serialqt readline")
        i = 0 
        while i <  timeVal:
            self.parent.app.processEvents()
            #logging.debug("i: %d, timeVal: %d" , i, timeVal)
            '''
            if self.serialPort.canReadLine():
                logging.debug('canreadline')
                buf = self.serialPort.readLineData().data()
                logging.debug(buf)
                break
            else:
                i = i+1
            logging.debug("look for newline char's")
            '''
            '''
            if buf.size()-1 <= 0:
                # empty readline, exit?
                logging.debug('empty readline')
            else:
                logging.debug(buf[buf.size()-1])
            i= i+1
            '''
            i= i+1
        return self.serialPort.readLine().data()
    
    def getSerial(self):
        """ Return the pointer to the serial port """
#        logging.debug("Connected to serial port " + self.serialPort.name)
        return self.serialPort

    def sendCommand(self, command):
        """ Send a command to the serial port """
        logging.debug("Qt serial port sending command %s", command)
        self.serialPort.write(command)
        self.sentCommand = str(command)
        logging.info('Serialqt:sendCommand: Sending command - ' + str(command))
        return
    def readin(self):
        """
        Read data from the serial port and parse it for status updates.
        All responses are terminated by a carrage return and a new line.
        Pretty sure I'm not actually using this: using ticSerial instead.
        """
        message = ""
        byte = ""
        while True:
            byte = self.serialPort.read()
            if byte.decode("utf-8") == "\n":
                break
            message += byte.decode("utf-8")
        logging.debug("read data: " + message.rstrip())
        return(message.rstrip())
    
    def decodeLine(self):
        # decode M01, m02, Pt
        # translates from binary string into ascii
        # and loops over hex values recieved from probe 
        # changing them to decimal
        logging.debug('decode')
        data = self.buf.data().decode()
        data = data.split(' ')
        #data = data.split(' ')
        tmp = data[0].split(':')
        for i in data:
            if i == data[0]:
                # reset the dataArray with first equal
                stringData = str(tmp[0]) + ": " + str(int(str(tmp[1]),16)) + " "
                logging.debug("decodeLine, 0 case")
                #dataArray.append(str(int(str(tmp[1]).decode('ascii'),16)))
                #dataArray.append(str.encode(' '))
            else:
                if i == '\r\n':
                    stringData + '\r\n'
                elif i == '':
                    stringData
                elif i == '\r':
                    stringData
                else:
                    stringData = stringData + str(int(i,16)) + ' '
            logging.debug(" data i = %s ", i)
        return stringData


    def close(self):
        self.serialPort.close()
        if serialPort.isOpen():
            self.serialPort.close()
        else:
            logging.debug("qtserial closed")


if __name__ == "__main__":

    import doctest
    doctest.testmode()
