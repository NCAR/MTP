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
import math
from PyQt5.QtNetwork import QUdpSocket, QHostAddress
from PyQt5.QtCore import QTimer
#import socket

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
class doUDP(object):

    def __init__(self, parent, app, device=None):
        # inherits parent, and app classes
        self.app = app
        self.parent = parent

        # set up ports and ip address
        self.udp_write_port = 32107
        self.udp_write_ric_port = 32106
        self.udp_read_port = 7071 # from IWG server 
        self.udp_ip="192.168.84.255" # subnet mask
        self.udp_ip=QHostAddress('0.0.0.0') # subnet mask

        # initialize the reader
        self.sock_read = QUdpSocket()
        # share the iwg packet port 
        self.sock_read.bind(self.udp_ip, self.udp_read_port,QUdpSocket.ReuseAddressHint)
        # apparently this init is called each time anything in
        # the class is, causing it to flash between green and yellow
        #self.parent.receivingUDPLED.setPixmap(self.parent.ICON_YELLOW_LED.scaled(40,40))

        # initialize the udp writer 
        self.sock_write = QUdpSocket()
        self.sock_write.bind(self.udp_ip, self.udp_write_port)
        self.parent.sendingUDPLED.setPixmap(self.parent.ICON_YELLOW_LED.scaled(40,40))

        # RIC socket
        self.sock_write_ric= QUdpSocket()
        self.sock_write_ric.bind(self.udp_ip, self.udp_write_ric_port)
        
        # Set up timer to call timeoutIWG ~5 seconds
        self.iwgTimer = QTimer()
        self.iwgTimer.timeout.connect(self.timeoutIWG)
        self.iwgTimer.start(5000) # in milliseconds

        # Set up timer to call timeoutUDP ~50 seconds
        self.udpTimer = QTimer()
        self.udpTimer.timeout.connect(self.timeoutUDP)
        self.udpTimer.start(50000) # in milliseconds

        # Connect getIwg to socket
        self.sock_read.readyRead.connect(self.getIWG)


    def getIWG(self):
        """ Gets udp feed with iwg packet """

        # while there is stuff to read, read
        # IWG may not be deliminated by newlines
        while self.sock_read.hasPendingDatagrams():
            self.networkDatagram = self.sock_read.receiveDatagram(2046)
            #logger.debug( "in IWG read while loop")

        #logger.debug( "after IWG read while loop")

        # returns QByteArray
        self.data = self.networkDatagram.data()

        # Stores data in packetStore
        self.parent.packetStore.setData("IWG", self.data)

        # changes the recieved iwg buffer of type QNetworkDatagram
        # into something more accessable:
        self.data = str(self.data).split(',')
        #logging.debug("iwg buffer:" +self.data[1])
        self.parent.packetStore.setData("IWGSplit", self.data)

        # resets led timout timer

        self.iwgTimer.setInterval(5000)


        # if led isn't green, set it so: red led logic later
        self.parent.receivingUDPLED.setPixmap(self.parent.ICON_GREEN_LED.scaled(40,40))
        # Ensures that events will be processed at 
        # least once a second
        self.parent.app.processEvents()

        self.sortIWG()

        #logger.info("Getting Iwg Data") 


    def timeoutIWG(self):
        # if IWG timer manages to timeout, then we haven't recieved 
        # an IWG packet in at least 5 s, sets IWG led to yellow
        # sets timer to timeout and check in 5s instead of 1
        self.parent.receivingUDPLED.setPixmap(self.parent.ICON_YELLOW_LED.scaled(40,40))
        logging.debug("iwg timeout")
        #logger.info("not getting Iwg packet on port %s, subnet mask ip '%s' (red), or Iwg hasn't been recieved within past 5 seconds (yellow)", self.udp_read_port, self.udp_ip) 

        # if we never get an iwg packet, status defaults to red
        
    def sortIWG(self):
        # grabs values needed for Aline
        # calls keep15, and avgVal for each
        # this could be another enum
        # logging.debug( self.parent.packetStore.getData("IWGSplit"))
        self.keep15("pitch", self.parent.packetStore.getArray("IWGSplit", 16))
        self.keep15("roll",  self.parent.packetStore.getArray("IWGSplit", 17))
        # Zp is pressure Altitude
        # converted from IWG ft to km in keep 15
        self.keep15("Zp",  self.parent.packetStore.getArray("IWGSplit", 6))
        # oat is ambient temperature
        # converted from IWG C to K in keep 15
        self.keep15("oat",  self.parent.packetStore.getArray("IWGSplit", 20))
        self.keep15("lat",  self.parent.packetStore.getArray("IWGSplit", 2))
        self.keep15("lon",  self.parent.packetStore.getArray("IWGSplit", 3))
        # logging.debug("sortIWG")


    def keep15(self, name, latestValue): 
        # removes oldest value if there are more than 15
        self.list = self.parent.packetStore.getData(name)
        # logging.debug("list: %s", self.list) # more like a qbyte array
        self.nval = len(self.list)
        # logging.debug("nval: %s", self.nval)
        # Sometimes IWG packet doesn't fill out values
        # check if roll/pitch is zero in goAngle
        if latestValue is '':
            latestValue = float(0) # try and figure out nan value instead
        if name == "Zp":
            latestValue = float(latestValue)/3280.8 # ft/km value from vb6
        elif name is "oat":
            latestValue = float(latestValue) + 273.15 # C to K value from vb6

        # only want to keep 16 values in each array
        if self.nval > 15:
            self.nval = 15
        
        # want to shuffle last value, 
        # then second last value
        # so that the list[0] is empty
        # but others are full
        i = 0
        while i < self.nval: 
            # adds latest value 
            #logging.debug("nval :: i " )
            #logging.debug( self.nval-self.i )
            #logging.debug( self.nval-(self.i+1))

            self.list[self.nval-i] = self.list[self.nval-(i+1)]
            i = i+1
        self.list[0] = latestValue
        self.parent.packetStore.setData(name, self.list)
        self.averageVal(name)

        # logging.debug("in keep15")

    def averageVal(self, name):
        # logging.debug("in averageVal")
        # takes in name, grabs name+array
        data = self.parent.packetStore.getData(name)

        avg = 0
        rms = 0
        i = 0
        # calculates average and root mean square error
        while i < self.nval:
            datum = float(self.parent.packetStore.getArray(name,i))
            # logging.debug(i)
            # logging.debug(datum)
            # logging.debug("averageVal for loop")
            avg = avg + datum
            rms = rms + datum * datum
            i = i + 1 
        avg = avg/self.nval
        # logging.debug("avg %f", avg)
        if rms - avg * avg * self.nval >0:
            if self.nval > 1:
                rms = math.sqrt((rms - avg * avg * self.nval)/(self.nval-1))
            else:
                rms = 0.0
        else: 
            rms = 0.0
        
        # checks value of avg and rms
        # logging.debug("rms: %f   , avg: %f",  rms, avg)
        # logging.debug(name + "avg")
        # saves avg and rms in nameAvg and nameRMS
        # truncate values to third decimal place
        avg = int(avg*1000)/1000.0
        rms = int(avg * 1000)/1000.0
        self.parent.packetStore.setData(str(name) +'avg', avg)
        self.parent.packetStore.setData(str(name) +'rms', rms)
        

    def timeoutUDP(self):
        # sets the sending UDP light to red if haven't sent udp in 50 seconds
        # 30 would probably do, but 50 for now
        self.parent.sendingUDPLED.setPixmap(self.parent.ICON_RED_LED.scaled(40,40))
        #logger.debug("UDP feed stopped sending. Probe may no longer be cycling")

    def sendUDP(self, packet):
        """ Send a packet out the udp port """
        self.sock_write.writeDatagram(packet, udp_ip, udp_write_port)
        # or out both udp ports if we want R.I.C. involved
        # self.sock_write_ric.writeDatagram(packet, udp_ip, udp_write_ric_port)

        #logger.debug("sending udp packet %s", packet)
        self.parent.sendingUDPLED.setPixmap(self.parent.ICON_GREEN_LED.scaled(40,40))



if __name__ == "__main__":

    import doctest
    doctest.testmode()
