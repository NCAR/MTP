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

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
    filename="MTPControl.log", level=logging.DEBUG)
#logging.basicConfig(level=logging.WARNING)
class doUDP(object):

    def __init__(self, parent, app, iwgFile, device=None):
        # inherits parent, and app classes
        self.app = app
        self.parent = parent
        self.IWGFile = iwgFile

        # set up ports and ip address
        self.udp_write_to_nidas = 30101
        self.udp_write_port = 32106
        self.udp_write_ric_port = 32106
        self.udp_read_port = 7071 # from IWG server 
        self.udp_read_from_ric_port = 32107 #currently not used
        # plane
        self.udp_ip_nidas=QHostAddress("192.168.84.2") # subnet mask
        # 0.0.0.0 is listen on all ipv4, not a write 
        self.udp_ip_read_broadcast_IWG=QHostAddress('0.0.0.0') # read all ipv4, read broadcast
        # needs to be different than reading from single connection because network 
        # packets indicate if they are broadcast or unicast (single computer)
        # lab
        self.udp_ip_local=QHostAddress.LocalHost 
        #self.udp_ip = QHostAddress("192.168.84.2") # subnet mask

        # initialize the reader
        self.sock_read = QUdpSocket()
        # share the iwg packet port 
        self.sock_read.bind(self.udp_ip_read_broadcast_IWG, self.udp_read_port,QUdpSocket.ReuseAddressHint)
        # apparently this init is called each time anything in
        # the class is, causing it to flash between green and yellow
        #self.parent.receivingIWGLED.setPixmap(self.parent.ICON_YELLOW_LED.scaled(40,40))

        # Need separate UDP reader for anything from ric/viewer program


        # initialize the udp writers 
        # Binding is unnecessary and counterproductive to write ports
        self.sock_write_nidas = QUdpSocket()

        self.sock_write = QUdpSocket()
        self.parent.sendingUDPLED.setPixmap(self.parent.ICON_YELLOW_LED.scaled(40,40))

        # RIC socket
        self.sock_write_ric= QUdpSocket()
        
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
        return


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

        # format here is to preserve IWG format for VB6 processing
        logging.debug(str(time.gmtime()) + "length of iwg: " + str(len(self.data)))
        stringIWG = str(self.data).split(',') 
        stringIWG = stringIWG[:32]
        stringIWG = ','.join(stringIWG)
        logging.debug(stringIWG)

        #logging.debug(self.data[0])
        # Stores data 
        # Stores IWG w/o newline char
        self.parent.iwgStore = self.data


        # Writes to iwg file
        with open(self.IWGFile,'a') as iwgFile:
            # Close " here is on a new line
            iwgFile.write("\"" + stringIWG + "\r\n\"\r\n")
            logging.debug("IWG written")
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
        self.parent.receivingIWGLED.setPixmap(self.parent.ICON_GREEN_LED.scaled(40,40))
        # Ensures that events will be processed at 
        # least once a second
        # doesn't because this is whole thing is an event to be queued 
        #self.parent.app.processEvents()

        self.sortIWG()

        #logging.info("Getting Iwg Data") 


    def timeoutIWG(self):
        # if IWG timer manages to timeout, then we haven't recieved 
        # an IWG packet in at least 5 s, sets IWG led to red
        # on receipt of IWG packet, will turn green
        self.parent.receivingIWGLED.setPixmap(
                self.parent.ICON_RED_LED.scaled(40,40))
        
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
        
        if self.parent.packetStore.getData("firstUDP"):
            templist = [0]
            if name == 'lon':
                self.parent.packetStore.setData("firstUDP", False)
            self.setArray(name, [0])

        else:
            templist = self.getArray(name)
           
            # logging.debug(templist)
            nval = len(templist)
            #logging.debug("nval: %s", nval)
    
            # Sometimes IWG packet doesn't fill out values
            # check if roll/pitch is zero in goAngle
            if latestValue == '':
                latestValue = float(0) # try and figure out nan value instead
            elif latestValue == b'':
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
                # so that the list[0] is 'empty'
                # but others are full
                i = 0
                while i < nval: 
                    # shuffle list
                    # logging.debug("nval :: i " )
                    #logging.debug( nval-i )
                    #logging.debug( nval-(i+1))

                    templist[nval-i] = templist[nval-(i+1)]
                    i = i+1
            else:
                # if there are less than or equal to 15 values, havent received enough
                # IWG packets to necessitate shuffling
                templist.append(templist[0])
            templist[0] = latestValue
            if name == 'pitch':
                self.parent.packetStore.setData(name+ 'Instant', latestValue)
            elif name == 'roll':
                self.parent.packetStore.setData(name+ 'Instant', latestValue)
            self.setArray(name, templist)
            self.averageVal(name)

            # logging.debug("in keep15")

    def getArray(self, name):
        logging.debug( name)
        if name =='pitch':
            templist = self.parent.packetStore.getData('pitch15')
        elif name == 'roll':
            templist = self.parent.packetStore.getData('roll15')
        elif name == 'Zp':
            templist = self.parent.packetStore.getData('Zp15')
        elif name == 'oat':
            templist = self.parent.packetStore.getData('oat15')
        elif name == 'lat':
            templist = self.parent.packetStore.getData('lat15')
        elif name == 'lon':
            templist = self.parent.packetStore.getData('lon15')
        else: 
            logging.error("Undefined arrayName in udp keep15")
            templist  = []
        return templist

    def setArray(self, name, data):
        if name == 'pitch':
            self.parent.packetStore.setData('pitch15', data)
        elif name == 'roll':
            self.parent.packetStore.setData('roll15', data) 
        elif name == 'Zp':
            self.parent.packetStore.setData('Zp15', data)
        elif name == 'oat':
            self.parent.packetStore.setData('oat15', data)
        elif name == 'lat':
            self.parent.packetStore.setData('lat15', data)
        elif name == 'lon':
            self.parent.packetStore.setData('lon15', data)
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
        avg = avg/len(data15)
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

    def sendUDP(self, packet, savePacket):
        """ Send a packet out the udp port """
        # Write to nidas
        self.sock_write_nidas.writeDatagram(
                bytes(savePacket, 'utf-8'), 
                self.udp_ip_nidas, self.udp_write_to_nidas)
        logging.debug("sent ric UDP")
        # real time viewing software - writes to localhost
        self.sock_write.writeDatagram(packet, self.udp_ip_local, self.udp_write_port)
        logging.debug("sent UDP")
        # Writes to R.I.C. 
        self.sock_write_ric.writeDatagram(packet, self.udp_ip_nidas, self.udp_write_ric_port)
        logging.debug("sent ric UDP")
        #nidas
        self.sock_write_nidas.writeDatagram(packet, self.udp_ip_nidas, self.udp_write_to_nidas)
        logging.debug("sent ric UDP")


        #logging.debug("sending udp packet %s", packet)
        self.parent.sendingUDPLED.setPixmap(self.parent.ICON_GREEN_LED.scaled(40,40))
        # restart timer for gui
        self.udpTimer.start(50000) # in milliseconds




if __name__ == "__main__":

    import doctest
    doctest.testmode()
