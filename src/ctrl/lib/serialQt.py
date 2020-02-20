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
        self.serialPort.readyRead.connect(self.tickSerial) 
        """ Check that the port isn't open already """

        if self.serialPort.isOpen():
            self.serialPort.close()
            logging.info("COM6 was open: now closed")

        if self.serialPort.open(QIODevice.ReadWrite):
            logging.info("COM6 is open")
        else:
            logging.info ("COM6 failed to open")

        """ Not sure QtSerialPort has an exception in this case?"""
        '''
        except self.serialPort.SerialException as ex:
            logging.info("Port is unavailable: " + str(ex))
            exit()
        '''
        #as yet appears to be unnecessary
        #self.app.processEvents()
        self.binI = str.encode("I")
        self.binR = str.encode("R")
        self.binRnewline = str.encode("R\n")
        self.binST = str.encode('ST')
        self.binST = str.encode('ST')
        self.binVe = str.encode('Ve')
        self.binSt = str.encode('St')
        self.bin00 = str.encode('00')
        self.binTi = str.encode('Ti')
        self.binM0 = str.encode('M0')
        self.binM01 = str.encode('M01')
        self.binPt = str.encode('Pt')
        self.binND = str.encode('ND')
        self.binU = str.encode('U/') 
        return

    def waitReadyRead(self):
        # returns a signal when there is data to be read
        # times out in 7 msec
        return self.serialPort.waitForReadyRead(7)

    def readLine(self, time):
        # reads until there is no more data
        # or to first newline
        # for M01, M02, pt wait for entire line to come in. 
        # doing multiple reads just allows for the lines to 
        # run together e.g. b'03 \r\nM'
        i = 0 
        while i < time:
            time.sleep(0.001)
        return self.serialPort.readLine()
    
    def getSerial(self):
        """ Return the pointer to the serial port """
#        logging.debug("Connected to serial port " + self.serialPort.name)
        return self.serialPort

    def sendCommand(self, command):
        """ Send a command to the serial port """
        logging.debug("serial port sending command %s", command)
        self.serialPort.write(command)
        self.sentCommand = str(command)
#        logging.info('Sending command - ' + str(command))
        return

    def tickSerial(self):
        # Sleep to make read get whole line, not partial
        # 0.07 s sleep works for smaller commands
        # need to test if it works for the big lines
        # works for pt, m02, m01
        self.buf = QByteArray(0)
        i=0
        # less than 20 here causes M line truncation
        while i < 25: #start, stop, step
            if self.serialPort.canReadLine():
                # exit for loop
                break
            if i == 25:
                logging.error("Sleep timeout on canReadLine")
            i = i + 1
            time.sleep(0.001)
        # Add do sleep while nodata to catch multiple responses if necessary
        #while self.serialPort.canReadLine():

        self.buf = self.serialPort.peek(2)
        if self.buf == self.binM0 or self.buf == self.binPt:
            time.sleep(0.003)
            self.splitSignal() #returns QByte array of data
        else:
            self.buf = self.serialPort.readLine()
            self.splitSignal() #returns QByte array of data
            
        # Not sure this is something we want here:
        self.parent.cycleTimer.start()
        # process the recieved data
        # self.parent.app.processEvents()
        return 

    def splitSignal(self):
        # sentCommand is not refreshed at echo
        # every other time this will remove the \r as well
        # self.sentCommand = self.sentCommand[:-1] + "\\n'"
        # this function contains most of the stop/move on 
        # logic for the state machine
        # it is preferred that if the same state is detected
        # the previously sent command is resent, 
        # however this does cause some race conditions. 
        # Especially around the logic for E and B line.
        # There is another bug  caused right before the entry
        # into E line, perhaps because the setup logic 
        # doesn't prompt a command.
        # Could occur in homescan, Eline, Bline
        # Aline sends a benign status request to combat this
        # If the stopping logic didn't depend heavily on 
        # which status message (first second or third) this 
        # would be easier to determine.
        # or adding process events after resetting of logic, 
        # but before writes?
        #self.parent.app.processEvents()
        st = self.buf.data() #.decode('ascii') # decode farts on init string
        # and on b'\xff/0@\r\n', will have to keep encode switching.
        logging.debug("decode st: %s", st)
        # logging.debug("decode st[1]: %s", st[0]) # this value is unpredictable
        # have to use range - also got a b'R' string once
        logging.debug("decode st[2]: %s", st[0:2])
        logging.debug("decode shortst[2]: %s", st[0:1])
        logging.debug("decode longst[2]: %s", st[0:3])

        switchSubstring = self.buf[0:2]
        logging.debug("switchSubstring = %s", str(switchSubstring))
        shortSubstring = self.buf[0:1]
        logging.debug("shortSubstring = %s", str(shortSubstring))
        longSubstring = self.buf[0:3]
        logging.debug("longSubstring = %s", str(longSubstring))

        logging.debug("buffer = %s", str(self.buf))
        '''
        once the swap on switchSubstring is done, check for i's
        could move this to top of switch if it takes too long.
        aka if race condition remains
        '''
        if shortSubstring == self.binI:
            if switchSubstring == "I ":
                # testing to see if this removes duplicates
                self.parent.cycleTimer.stop()
                logging.debug("discarding I echo")
            else:
                # logging.debug(self.buf[1:3] + self.buf[0:1])
                # use the number returned from this to match R case
                self.parent.packetStore.setData("integrateData", self.buf[1:3])
                self.parent.packetStore.setData("count2Flag", True)
        elif shortSubstring == self.binR: 
            number = self.parent.packetStore.getData("integrateData")
            if switchSubstring == self.binRnewline:
                # testing to see if this removes duplicates
                self.parent.cycleTimer.stop()
                logging.debug("discarding R echo")
            
            elif self.parent.packetStore.getData("calledFrom") is "Eline":
                #temp = PyQt5.QtCore.QByteArray(str.encode(" "))
                #temp.append(self.buf[4:9]) # add the spaces
                # dont take above out because R\r\n will be out of bounds for r[4+]
                # though the data array doesn't do anything, 
                # it does appear that we need a bit more processing time
                # for the Eline characters to correctly get a space between 
                # them. Else they will run together
                # perhaps wherever the append space functionality is
                # should be moved
                data = self.buf[4:10] 
                # data = data.data().decode()
                # convert to normal string from binary string
                # then convert the hex to decimal
                if data == '':
                    logging.debug("data is ''")
                    return
                else:
                    data = str(int(data.data().decode('ascii'), 16))
                # initial space after E added when eline is initialized
                # could reverse this, if end space causes issues
                data = data + " "
                #logging.debug(self.buf[4:10])
                #logging.debug(data)
                self.iSwitch = self.parent.packetStore.getData("integrateSwitch")
                self.parent.packetStore.setData("currentFrequency", self.iSwitch) 
                self.parent.packetStore.setData("count2Flag", False)
                self.parent.packetStore.setData("tuneSwitch", True)
                logging.debug("integrate Switch should be set to 56 here: %s", self.iSwitch)
                self.parent.elineStore = self.parent.elineStore + data
                #self.parent.packetStore.appendData("Eline",data)
                
                # race condition causes intermittent e line truncation
                # so it will only have 3 values
                # or e value repetition. Hopfully having appending after
                # logic switching will help
                logging.debug(self.parent.elineStore)

            elif self.parent.packetStore.getData("calledFrom") is "blIne":
                #temp = PyQt5.QtCore.QByteArray(str.encode(" "))
                #temp.append(self.buf[4:9]) # add the spaces
                logging.debug("bline integrate, got R")
                data = self.buf[4:10] 
                data = str(int(data.data().decode('ascii'), 16))
                data = data + " "
                #data = int(data.decode('ascii'), 16)
                #data.append(" ")
                self.parent.blineStore = self.parent.blineStore.append(data)
                # self.parent.packetStore.appendData("Bline", data)
                # logging.debug(self.parent.packetStore.getData("Bline"))
                # Reset blIne logic - no: in bline:
                '''
                self.i = self.parent.packetStore.getData("angleI")
                if self.i < 12:
                    logging.debug("recieving logic: angleI value(2-11): %s", str(self.i))
                    self.parent.packetStore.setData("angleI", self.i +1)
                else:
                    #stop logic
                    self.parent.packetStore.setData("bDone", True)
                '''
                # Reset integrate logic
                self.parent.packetStore.setData("count2Flag", False)
                logging.debug(self.parent.packetStore.getData("count2Flag"))
                self.parent.packetStore.setData("tuneSwitch", True)
                self.parent.packetStore.setData("currentFrequency", self.parent.packetStore.getData("integrateSwitch"))
            else: 
                logging.debug("received R value, unsure who is calling")
        if switchSubstring == self.binST: 
            # sends number to update status
            # logging.debug("splitSignal:ST"
            return self.buf[3:5]

        elif switchSubstring == self.binVe:
            logging.debug("splitSignal:Ve (rsion)")
            return self.buf
        elif switchSubstring == self.binSt:
            #logging.debug("received a step signal")
            #logging.debug(str(self.buf))
            # initScan cases
            self.mode = self.parent.packetStore.getData("currentMode")
            self.switchControl = self.parent.packetStore.getData("switchControl")
            # logging.debug(self.buf[5:6])
            if self.buf[5:6] is b'\xff':
                logging.debug("got a read scan or a read encode")
            elif self.parent.packetStore.getData("switchControl") is "blIne":
                logging.debug("should be in Bline, recieved a step return, switch control set properlu")
                if self.parent.packetStore.getData("calledFrom") is "blIne":
                    logging.debug("Bline, recieved a step return, called from set properly")
                    if self.buf is b'Step:\xff/0@\r\n':
                        logging.debug("should be in Bline, meaning we've gotten to the angle we want to sample")
                        # change logic to do integrate.
                        self.parent.packetStore.setData("bSwitch", False )
                        # change currentClk step
                        self.parent.packetStore.setData("currentClkStep", self.parent.packetStore.getData("targetClkStep"))

                    elif self.buf is b'Step:\xff/0C\r\n':
                        logging.debug("want to continue sending the current request")
                    else:
                        logging.debug(" this is the infinite loop case, need to set currentClk step? recieve 'Step:\r\n' ")
                        self.parent.packetStore.setData("currentClkStep", self.parent.packetStore.getData("targetClkStep"))
                        # do an integrate and move on?
                        self.parent.packetStore.setData("bSwitch",False)
            elif self.mode is "init" and self.switchControl is "initScan":
                '''
                if self.parent.packetStore.getData("homeSwitch"):
                    if self.parent.packetStore.getData("scanSet"):
                        self.parent.packetStore.setData("switchControl", "m01")
                        logging.debug("init 3rd home command received")
                    # this I believe is unnecessary here, but needed in scan mode
                    # move along check if not sending the third command
                    #elif self.parent.packetStore.getData("currentMode") is "scan":
                    #    self.parent.packetStore.setData("switchControl", "m01")
                    #    logging.debug("init: 3rd home command skipped: scan mode")
                else:
                '''
                if self.parent.packetStore.getData("initSwitch"):
                        self.parent.packetStore.setData("switchControl", "homeScan")
                else:
                    self.parent.packetStore.setData("initSwitch", True)
            elif self.parent.packetStore.getData("switchControl") is "homeScan":
                # HomeScan readScan, checks if  
                # tick case or 0b0 is actual home value to check for
                # "Step:\xff\0@\r\n" or "Step:/0`0\r\n"
                if self.parent.packetStore.getData("homeSwitch"): 
                    # because we only send the 3rd command in init mode,
                    # have to check for that in the init case
                    if self.parent.packetStore.getData("scanSet"):
                        self.parent.packetStore.setData("switchControl", "m01")
                        self.parent.packetStore.setData("echoCommand", False)
                        logging.debug("home: 3rd home command received")
                        logging.debug("setitng current mode to desired mode:")
                        logging.debug(self.parent.packetStore.getData("desiredMode"))

                    elif self.parent.packetStore.getData("calledFrom") is "Eline":
                        # move along check if not sending the third command
                        # if returning to Eline,
                        self.parent.packetStore.setData("switchControl", "Eline")
                        self.parent.packetStore.setData("echoCommand", False)
                        logging.debug("home: 3rd home command skipped: scan mode")

                    elif self.parent.packetStore.getData("calledFrom") is "Bline":
                        # resetting to take more measurements for next angle Bline
                        self.parent.packetStore.setData("bSwitch", True)
                        # if returning to Bline :
                        self.parent.packetStore.setData("switchControl", "blIne")
                        self.parent.packetStore.setData("echoCommand", False)
                        logging.debug("home: 3rd home command skipped: scan mode")
                    else:
                        self.parent.packetStore.setData("scanSet", True)
                        logging.debug("2nd home command received")
                else:
                    # first homeStep recieved: 
                    self.parent.packetStore.setData("homeSwitch", True)
                    logging.debug("1st home command received")
                    

                logging.debug("home")
            
            elif self.mode is "scan":
                if self.parent.packetStore.getData("homeSwitch"):
                    # this I believe is unnecessary here, but needed in init mode
                    if self.parent.packetStore.getData("scanSet"):
                        #    self.parent.packetStore.setData("switchControl", "m01")
                        logging.debug("scan: 3rd home command received")
                    elif self.parent.packetStore.getData("currentMode") is "scan":
                        # move along check if not sending the third command
                        self.parent.packetStore.setData("switchControl", "m01")
                        logging.debug("scan: 3rd home command skipped: scan mode")
            else:
                logging.debug("Don't care about return status here")
                logging.debug(self.parent.packetStore.getData("switchControl"))

        elif switchSubstring == self.bin00:
            # catch return of home 1, "00000J3R"
            logging.debug("zeros")

        # readscan time case
        elif switchSubstring == self.binTi:
            #set readscan to "999999"
            logging.debug('Time')

        elif switchSubstring == self.binM0: 
            # Doesn't work on Qbyte array type:
            # self.buf.decode("ascii")
            # check self.buf[1:3] actually is substring we want
            #if self.buf[1:4] == self.bin01:
            
            self.buf = self.serialPort.readLine()
            if longSubstring == self.binM01:
                data = self.decodeLine()
                #self.parent.packetStore.setData("M01", data)
                self.parent.m01Store = data
                logging.debug("received m01 does the long substring not work here? %s ", longSubstring)
                self.parent.packetStore.setData("switchControl", "m02")
            else: 
                data = self.decodeLine()
                self.parent.m02Store = data
                logging.debug("longSubstring: %s, binM01: %s", longSubstring, self.binM01.decode('ascii'))
                #self.parent.packetStore.setData("M02", data)
                logging.debug("received m02")
                logging.debug("buff[1,4]: %s    str.encode(): %s", self.buf[1:4], "01:")
                logging.debug("buff[1,3]: %s    str.encode(): %s", self.buf[1:3], "01")
                self.parent.packetStore.setData("switchControl", "pt")

                """
                # Apparently not. Will set echoCommand in homeScan itself
                or if in homescan and initSwitch is false
        elif switchSubstring == str.encode("Pt"):
            #self.parent.packetStore.setData("Pt", self.buf)
            logging.debug("received Pt")
            self.parent.packetStore.setData("switchControl", "Eline")
            # Flag so homeScan knows where to return to, 
            # Should be set in Aline, just before Bline is called
            # and in click init
            # There really has got to be a better way to do this
            self.parent.packetStore.setData("calledFrom","Eline")
            """




            # set matchWord: next
            # or initSwitch = true
        elif switchSubstring == self.binPt:
            time.sleep(0.003)
            self.buf = self.serialPort.readLine()
            data = self.decodeLine()
            self.parent.ptStore = data
            logging.debug("received Pt")
            self.parent.packetStore.setData("switchControl", "Eline")

        elif switchSubstring == self.binND:
            # note that while the echo command "N" would also be
            # easy to match on, it is irrelavant for switching purposes
            self.parent.packetStore.setData("noise", self.buf)
            logging.debug("received setNoise data")
            '''
            if self.buf[0,4] == str.encode("N02"):
                # only on receipt of first noise command can we switch this
                # above is false. Should only switch once the last I 40
                # from integrate is called. There it should also be 
                # returning switchControl to calledFrom
                self.parent.packetStore.setData("ElineSwitch", True)
            '''

        elif switchSubstring == self.binU:
            # when we do care about the echoed commands:
            if self.parent.packetStore.getData("switchControl") is "homeScan":
                logging.debug("switchSubstring, homeScan case")
                # only care about that first command echo
                # then the st case should handle it
                self.parent.packetStore.setData("echoCommand", True)



            elif self.parent.packetStore.getData("switchControl") is "integrate":
                logging.debug("switchSubstring, integrate case")
            else:
                logging.debug("switchSubstring - discard echo case")

        elif self.buf is (self.sentCommand):
            logging.debug("sent %s" , self.sentCommand)
        else:
            logging.debug("Catch all for truncations, collisions, and unwanted command echos")
            logging.debug("sentcommand: %s with buffer: ", self.sentCommand )
            logging.debug(self.buf.data() )
            # testing to see if this removes duplicates
            self.parent.cycleTimer.stop()
            #self.parent.app.processEvents()
            logging.debug("buffer: %s ", self.buf )
            #logging.debug("buffer 3 and 4: %s \r\n", self.buf[0:2])
        logging.debug("switch end")
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
