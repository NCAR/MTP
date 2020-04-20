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

logging.basicConfig(level=logging.WARNING)
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
            self.networkDatagram = self.sock_read.receiveDatagram(2048)
            # returns networkDatagram type
            #logging.debug( "in IWG read while loop")

        #logging.debug( "after IWG read while loop")

        # returns QByteArray
        self.data = self.networkDatagram.data().data().decode('ascii')
        # nope, .data() returns string (binary)
        #logging.debug("Does iwg networkDatagram really return QByte array? %s", self.networkDatagram.data())

        #logging.debug(self.data[0])
        # Stores data 
        self.parent.iwgStore = self.data

        # Writes to iwg file
        with open("IWG.txt", 'a') as iwgFile:
            iwgFile.write(str(self.data))

        iwgFile.close()

        # changes the recieved iwg buffer of type QNetworkDatagram
        # into something more accessable:
        # do this in sortIWG
        #self.data = str(self.data).split(',')
        #logging.debug("iwg buffer:" +self.data[1])
        #self.parent.packetStore.setData("IWGSplit", self.data)

        # resets led timout timer

        self.iwgTimer.setInterval(5000)


        # if led isn't green, set it so: red led logic later
        self.parent.receivingUDPLED.setPixmap(self.parent.ICON_GREEN_LED.scaled(40,40))
        # Ensures that events will be processed at 
        # least once a second
        # doesn't because this is whole thing is an event to be queued 
        #self.parent.app.processEvents()

        self.sortIWG()

        #logging.info("Getting Iwg Data") 


    def timeoutIWG(self):
        # if IWG timer manages to timeout, then we haven't recieved 
        # an IWG packet in at least 5 s, sets IWG led to yellow
        # sets timer to timeout and check in 5s instead of 1
        self.parent.receivingUDPLED.setPixmap(self.parent.ICON_YELLOW_LED.scaled(40,40))
        #logging.debug("iwg timeout")
        #logging.info("not getting Iwg packet on port %s, subnet mask ip '%s' (red), or Iwg hasn't been recieved within past 5 seconds (yellow)", self.udp_read_port, self.udp_ip) 

        # if we never get an iwg packet, status defaults to red
        
    def sortIWG(self):
        # grabs values needed for Aline
        # calls keep15, and avgVal for each
        # logging.debug( self.parent.packetStore.getData("IWGSplit"))
        IWGSplit = self.parent.iwgStore.split(',')
        #logging.debug(IWGSplit[0])
        #logging.debug(IWGSplit[1])
        #logging.debug(IWGSplit[0:1])
        self.keep15("pitch", IWGSplit[16])
        self.keep15("roll", IWGSplit[17])
        # Zp is pressure Altitude
        # converted from IWG ft to km in keep 15
        self.keep15("Zp", IWGSplit[6])
        # oat is ambient temperature
        # converted from IWG C to K in keep 15
        self.keep15("oat", IWGSplit[20])
        self.keep15("lat", IWGSplit[2])
        self.keep15("lon", IWGSplit[3])
        '''
        self.keep15("pitch",  self.parent.packetStore.getArray("IWGSplit", 16))
        self.keep15("roll",  self.parent.packetStore.getArray("IWGSplit", 17))
        self.keep15("Zp",  self.parent.packetStore.getArray("IWGSplit", 6))
        self.keep15("oat",  self.parent.packetStore.getArray("IWGSplit", 20))
        self.keep15("lat",  self.parent.packetStore.getArray("IWGSplit", 2))
        self.keep15("lon",  self.parent.packetStore.getArray("IWGSplit", 3))
        '''
        # logging.debug("sortIWG")


    def keep15(self, name, latestValue): 
        # self.list = self.parent.packetStore.getData(name)
        # logging.debug("list: %s", self.list) # more like a qbyte array
        templist = self.getArray(name)
        # logging.debug(templist)
        nval = len(templist)
        #logging.debug("nval: %s", nval)

        # Sometimes IWG packet doesn't fill out values
        # check if roll/pitch is zero in goAngle
        if latestValue is '':
            latestValue = float(0) # try and figure out nan value instead
        elif latestValue is b'':
            latestValue = float(0) # try and figure out nan value instead
        if name == "Zp":
            latestValue = float(latestValue)/3280.8 # ft/km value from vb6
        elif name is "oat":
            latestValue = float(latestValue) + 273.15 # C to K value from vb6

        # only want to keep 16 values in each array
        if nval > 15:
            nval = 15
        
        # removes oldest value if there are more than 15
        # want to shuffle last value, 
        # then second last value
        # so that the list[0] is empty
        # but others are full
        i = 0
        while i < nval: 
            # shuffle list
            # logging.debug("nval :: i " )
            #logging.debug( nval-i )
            #logging.debug( nval-(i+1))

            templist[nval-i] = templist[nval-(i+1)]
            i = i+1
        templist[0] = latestValue
        self.setArray(name, templist)
        self.averageVal(name)

        # logging.debug("in keep15")

    def getArray(self, name):
        if name is 'pitch':
            templist = self.parent.pitch15
        elif name is 'roll':
            templist = self.parent.roll15
        elif name is 'Zp':
            templist = self.parent.Zp15
        elif name is 'oat':
            templist = self.parent.oat15
        elif name is 'lat':
            templist = self.parent.lat15
        elif name is 'lon':
            templist = self.parent.lon15
        else: 
            logging.error("Undefined arrayName in udp keep15")
            templist  = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        return templist

    def setArray(self, name, data):
        if name is 'pitch':
            self.parent.pitch15 = data 
        elif name is 'roll':
            self.parent.roll15 = data 
        elif name is 'Zp':
            self.parent.Zp15 = data 
        elif name is 'oat':
            self.parent.oat15 = data 
        elif name is 'lat':
            self.parent.lat15 = data 
        elif name is 'lon':
            self.parent.lon15 = data 
        else: 
            logging.error("Undefined arrayName in udp keep15")
        #self.parent.packetStore.setData(name, self.list)


    def averageVal(self, name):
        # logging.debug("in averageVal")
        # takes in name, grabs name+array

        #data = self.parent.packetStore.getData(name)
        data15 = self.getArray(name) 
        nval = len(data15)
        # nval is 16
        #logging.debug("averageval nval = len(data_, should be 15: %s", nval)

        avg = 0
        rms = 0
        i = 0
        # calculates average and root mean square error
        while i < nval:
            #logging.debug(data15[i])
            #datum = float(self.parent.packetStore.getArray(name,i))
            datum = float(data15[i])
            # logging.debug(i)
            # logging.debug(datum)
            # logging.debug("averageVal for loop")
            avg = avg + datum
            rms = rms + (datum * datum)
            i = i + 1 
        avg = avg/nval
        # logging.debug("avg %f", avg)
        if rms - (avg * avg) * nval >0:
            if nval > 1:
                rms = math.sqrt((rms - (avg * avg) * nval)/(nval-1))
            else:
                rms = 0.0
        else: 
            rms = 0.0
        
        # checks value of avg and rms
        # logging.debug("rms: %f   , avg: %f",  rms, avg)
        # logging.debug(name + "avg")
        # saves avg and rms in nameAvg and nameRMS
        # truncate values to third decimal place
        avg = int(avg * 1000) / 1000.0
        rms = int(rms * 1000) / 1000.0

        #keeping these in the packet store because they are single values
        # may remove if time still an issue
        logging.debug("Got IWG,name = %s",str(name) + 'avg or rms')
        self.parent.packetStore.setData(str(name) + 'avg', avg)
        self.parent.packetStore.setData(str(name) + 'rms', rms)
        

    def timeoutUDP(self):
        # sets the sending UDP light to red if haven't sent udp in 50 seconds
        # 30 would probably do, but 50 for now
        self.parent.sendingUDPLED.setPixmap(self.parent.ICON_RED_LED.scaled(40,40))
        #logging.debug("UDP feed stopped sending. Probe may no longer be cycling")

    def sendUDP(self, packet):
        """ Send a packet out the udp port """
        self.sock_write.writeDatagram(packet, udp_ip, udp_write_port)
        # or out both udp ports if we want R.I.C. involved
        # self.sock_write_ric.writeDatagram(packet, udp_ip, udp_write_ric_port)

        #logging.debug("sending udp packet %s", packet)
        self.parent.sendingUDPLED.setPixmap(self.parent.ICON_GREEN_LED.scaled(40,40))



if __name__ == "__main__":

    import doctest
    doctest.testmode()
