###############################################################################
# This MTP client program runs on the user host, and receives the MTP data
# packets from the UDP feed.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import socket
import numpy
from util.readmtp import readMTP


class MTPclient():

    def __init__(self):

        self.udp_send_port = 32106  # from viewer to MTP
        self.udp_read_port = 32107  # from MTP to viewer
        self.iwg1_port = 7071       # IWG1 packets from GV

        # Hack-y stuff to get plot to scroll. pyqtgraph must have a better way
        # that I haven't found yet.
        # The MTP takes a scan about once every 17 seconds. Used to scroll
        # plotting

        # The width of the time window shown on the scrolling plot. Modify
        # plotWidth to change time interval. Eg:
        # 150 scans * 17s = 42.5 min
        # 106 scans * 17s = 30 min
        self.scanInterval = 17  # seconds per scan
        self.plotWidth = 106    # number of scans to plot

        self.xvals = []
        self.yvals = []
        (self.xvals, self.yvals) = self.initData()

        self.xvar = 'TIME'
        self.yvar = 'SAPALT'

        # Instantiate an instance of an MTP reader
        self.reader = readMTP()
        self.varlist = self.reader.getVarList('Aline')

    def initData(self):
        self.xvals = [0]*self.plotWidth    # Current X values being plotted
        # Necessary to get data to scroll. Before get good data, plot NANs
        self.yvals = [numpy.nan]*self.plotWidth
        return(self.xvals, self.yvals)

    def getSCNT(self):
        vals = self.reader.getVar('Bline', 'SCNT')
        return (vals)

    def getXY(self):
        """ Return the latest x and y values """
        return (self.xvals, self.yvals)

    def connect(self):
        """ Connection to UDP data stream """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", self.udp_read_port))

        self.sockI = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockI.bind(("0.0.0.0", self.iwg1_port))

    def getSocketFileDescriptor(self):
        """ Return the socket file descriptor """
        return self.sock.fileno()

    def readSocket(self):
        """ Read data from the UDP feed and save it to the data dictionary """
        # Listen for UDP packets
        data = self.sock.recv(1024).decode()
        dataI = self.sockI.recv(1024).decode()

        # Store data to data dictionary
        self.reader.parseAsciiPacket(data)
        self.reader.parseIwgPacket(dataI)

        # Append new X value to end of list
        self.xvals.append(int(self.reader.getVar('Aline', self.xvar)))

        # First time through, populate list with fabricated X values before
        # first X value so plot will scroll
        if (self.xvals[0] == 0):
            self.xvals = list(range(self.xvals[self.plotWidth] -
                                    self.plotWidth*self.scanInterval,
                                    self.xvals[self.plotWidth],
                                    self.scanInterval))

        # Pop oldest X value off list
        if (len(self.xvals) > self.plotWidth):
            self.xvals.pop(0)

        # Append new Y value to end of list
        self.yvals.append(float(self.reader.getVar('Aline', self.yvar)))

        # Pop oldest Y value off list
        if (len(self.yvals) > self.plotWidth):
            self.yvals.pop(0)

    def close(self):
        """ Close connection to UDP data stream """
        if self.sock:
            print("Closing socket")
            self.sock.close()
