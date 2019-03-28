################################################################################
# 
# This MTP client program runs on the user host, receives the MTP data packet
# and creates plots and other displays to allow the user to monitor the status
# and function of the MTP.
# 
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
################################################################################

import select
import socket
import sys
import PyQt5
import numpy
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

from PyQt5.QtWidgets import QApplication,QGridLayout,QWidget,QPushButton
from PyQt5.QtCore import QSocketNotifier

sys.path.append('.')
from readmtp import readMTP

app = QtGui.QApplication(sys.argv)

class MTPclient():

    def __init__(self):
        # Hack-y stuff to get plot to scroll. pyqtgraph must have a better way
        # that I haven't found yet.
        self.scanInterval = 17 # The MTP takes a scan about once every 17
                               # seconds. Used to scroll plotting
        self.plotWidth = 150   # 150 scans*17s=42.5 min = the width of the time
                               # window shown on the scrolling plot
        self.xvar = [0]*self.plotWidth    # Current X values being plotted
        self.yvar = [numpy.nan]*self.plotWidth # Necessary to get data to scroll
                                               # Before get good data, plot NANs

        self.udp_send_port = 32106 # from viewer to MTP
        self.udp_read_port = 32107 # from MTP to viewer


    def connect(self):
        # Connection to UDP data stream
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", self.udp_read_port))

    def getSocketFileDescriptor(self):
        return self.sock.fileno()

    def readSocket(self,xvar,yvar):
        # Instantiate an instance of an MTP reader
        reader = readMTP()

        # Listen for UDP packets
        data = self.sock.recv(1024).decode()

        # Store data to data dictionary
        reader.parseAsciiPacket(data)

        # Append new X value to end of list
        self.xvar.append(int(reader.getData(xvar)))

        # First time through, populate list with fabricated X values before
        # first X value so plot will scroll
        if (self.xvar[0] == 0):
            self.xvar = list(range(self.xvar[self.plotWidth]-
                self.plotWidth*self.scanInterval,self.xvar[self.plotWidth],
                self.scanInterval))

        # Pop oldest X value off list
        if (len(self.xvar) > self.plotWidth):
            self.xvar.pop(0)

        # Append new X value to end of list
        self.yvar.append(float(reader.getData(yvar)))
        # Pop oldest Y value off list
        if (len(self.yvar) > self.plotWidth):
            self.yvar.pop(0)

        return(self.xvar,self.yvar)


class MTPviewer():

    def __init__(self,client):

        self.x=[]
        self.y=[]
        client.connect()
        self.initUI(client)

        self.readNotifier = QSocketNotifier(
            client.getSocketFileDescriptor(), QSocketNotifier.Read)
        self.readNotifier.activated.connect(lambda: self.plotData(client))

    def plotData(self,client):
        (self.x,self.y) = client.readSocket('TIME','SAPITCH')

        self.saplot.setData(self.x,self.y,connect="finite")

        QtGui.QApplication.processEvents()


    def initUI(self,client):

        # Define top-level widget to hold everything
        self.w = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()
        self.w.setLayout(self.layout)

        # Create a window to hold our timeseries plot
        win = pg.GraphicsWindow()
        win.setWindowTitle('MTP Viewer')

        # Create empty space for the plot in the win
        p1 = win.addPlot(title="SAPITCH")
        # Create an empty plot
        self.saplot = p1.plot(client.xvar,client.yvar)
        # Choose plot location
        self.layout.addWidget(win, 0, 1)

        # Add a quit button
        button = QPushButton('Quit')
        button.clicked.connect(lambda: self.close(client))
        self.layout.addWidget(button,0,0)

        self.w.show()

        #Show the window even if data are not flowing
        QtGui.QApplication.processEvents()

    def close(self,client):
        if client.sock:
            client.sock.close()
        app.quit()


def main():

    client = MTPclient()
    viewer = MTPviewer(client)

    sys.exit( pg.QtGui.QApplication.exec_())


if __name__ == "__main__":
    main()
