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
import functools
from functools import partial

from PyQt5.QtWidgets import QApplication,QGridLayout,QWidget,QTabWidget,QPushButton,QComboBox,QHBoxLayout
from PyQt5.QtCore import QSocketNotifier

sys.path.append('.')
from readmtp import readMTP
from MTPgui import Ui_MTPgui

class MTPclient():

    def __init__(self):

        self.udp_send_port = 32106 # from viewer to MTP
        self.udp_read_port = 32107 # from MTP to viewer

        # Hack-y stuff to get plot to scroll. pyqtgraph must have a better way
        # that I haven't found yet.
        self.scanInterval = 17 # The MTP takes a scan about once every 17
                               # seconds. Used to scroll plotting
        self.plotWidth = 150   # 150 scans*17s=42.5 min = the width of the time
                               # window shown on the scrolling plot
        self.xvals = []
        self.yvals = []
        (self.xvals,self.yvals)= self.initData()

        self.xvar = 'TIME'
        self.yvar = 'SAPALT'

        # Instantiate an instance of an MTP reader
        self.reader = readMTP()
        self.varlist = self.reader.getVarList()


    def initData(self):
        self.xvals = [0]*self.plotWidth    # Current X values being plotted
        self.yvals = [numpy.nan]*self.plotWidth #Necessary to get data to scroll
                                           # Before get good data, plot NANs
        return(self.xvals,self.yvals)

    def getSCNT(self):
        vals = self.reader.getSCNTData()
        return (vals)

    def getXY(self):
        return (self.xvals, self.yvals)

    def connect(self):
        # Connection to UDP data stream
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", self.udp_read_port))

    def getSocketFileDescriptor(self):
        return self.sock.fileno()

    def readSocket(self):
        # Listen for UDP packets
        data = self.sock.recv(1024).decode()

        # Store data to data dictionary
        self.reader.parseAsciiPacket(data)

        # Append new X value to end of list
        self.xvals.append(int(self.reader.getXYData(self.xvar)))

        # First time through, populate list with fabricated X values before
        # first X value so plot will scroll
        if (self.xvals[0] == 0):
            self.xvals = list(range(self.xvals[self.plotWidth]-
                self.plotWidth*self.scanInterval,self.xvals[self.plotWidth],
                self.scanInterval))

        # Pop oldest X value off list
        if (len(self.xvals) > self.plotWidth):
            self.xvals.pop(0)

        # Append new X value to end of list
        self.yvals.append(float(self.reader.getXYData(self.yvar)))

        # Pop oldest Y value off list
        if (len(self.yvals) > self.plotWidth):
            self.yvals.pop(0)


class MTPviewer():

    def __init__(self,client,app):

        self.app = app
        client.connect()
        self.initUI(client)

        self.readNotifier = QSocketNotifier(
            client.getSocketFileDescriptor(), QSocketNotifier.Read)
        self.readNotifier.activated.connect(lambda: self.plotData(client))


    def plotData(self,client):

        client.readSocket()

        self.plotDataxy(client)
        self.plotDatascnt(client)

        self.app.processEvents()

    def plotDataxy(self,client):

        (self.x,self.y) = client.getXY()
        self.xyplot = self.xy.plot()
        self.xyplot.setData(self.x,self.y,connect="finite")

    def plotDatascnt(self,client):
        scnt = client.getSCNT()

        # The scan counts are stored in the ads file as cnts[angle,channel],i.e.
        # {a1c1,a1c2,a1c3,a2c1,...}. Processing requires, and the final data are
        # output as {c1a1,c1a2,c1a3,c1a4,...}. Invert the array here.
        scnt_inv= [numpy.nan]*30
        NUM_SCAN_ANGLES = 10
        NUM_CHANNELS = 3
        for j in range(NUM_SCAN_ANGLES) :
            for i in range(NUM_CHANNELS) :
               scnt_inv[i*10+j]=int(scnt[j*3+i]);

        scan1 = scnt_inv[0:10]
        scan2 = scnt_inv[10:20]
        scan3 = scnt_inv[20:30]
        angles = numpy.array(range(10))+1

        # Scan Counts[Angle,Channel]
        self.scnt.clear()
        self.scnt.invertY(True)
        plot2 = self.scnt.plot(pen=pg.mkPen('r'))
        plot2.setData(scan1,angles,connect="finite")
        plot2 = self.scnt.plot(pen=pg.mkPen('w'))
        plot2.setData(scan2,angles,connect="finite")
        plot2 = self.scnt.plot(pen=pg.mkPen('b'))
        plot2.setData(scan3,angles,connect="finite")

    def selectPlotVar(self,text):
        self.xy.clear()
        client.initData()
        self.xy.setLabel('left',text)
        client.yvar = text
        return()

    def initUI(self,client):

        # Define top-level widget to hold everything
        self.glayout = QHBoxLayout()
        self.MTPgui = QWidget()
        self.MTPgui.setLayout(self.glayout)
        self.MTPgui.setObjectName("MTPgui")
        self.MTPgui.setWindowTitle('MTP viewer')
        self.MTPgui.resize(1000,600)

        # Add a tab widget to the upper left
        self.tab = QTabWidget()
        self.glayout.addWidget(self.tab,0)

        self.initCtrl() # Create the layout for the "ctrl" tab
        self.initView(client) # Create the layout for the "view" tab
        self.initStatus(client) # Init status column to the right

        self.MTPgui.show()

        #Show the window even if data are not flowing
        self.app.processEvents()

    def initView(self,client):
        # Create the layout for the "view" tab
        self.layout = QGridLayout()
        self.view = QWidget()
        self.tab.addTab(self.view, "view")
        self.view.setLayout(self.layout)

        # Create a window to hold our timeseries plot
        w1layout = QGridLayout()
        self.layout.addLayout(w1layout,0,1)

        win1 = pg.GraphicsWindow()
        win1.setWindowTitle('Timeseries')
        w1layout.addWidget(win1, 0,0)
        # Create empty space for the plot in the window and then
        # create an empty plot
        self.xy = win1.addPlot(bottom=client.xvar,left=client.yvar)

        # Create a window to hold our profile plot
        win2 = pg.GraphicsWindow()
        win2.setWindowTitle('Histo')
        self.layout.addWidget(win2, 0,0,3,1)
        # Create empty space for the plot in the window and then
        # reate an empty plot
        self.scnt = win2.addPlot(bottom='Counts',left='Angle')

        # Add a dropdown to select the variable to plot
        varSelector = QComboBox()
        for item in client.varlist:
            varSelector.addItem(item)

        varSelector.activated[str].connect(self.selectPlotVar)
        w1layout.addWidget(varSelector,1,0)

    def initStatus(self,client):
        # Add a quit button to the right - later add a red/green indicator to
        # display status of connectivity (like GNI).
        self.window = QWidget()
        button = QPushButton('Quit')
        button.clicked.connect(lambda: self.close(client))
        self.glayout.addWidget(button,1)

    def initCtrl(self):
        # Create the layout for the "ctrl" tab
        self.ctrl = QWidget()
        self.tab.addTab(self.ctrl, "ctrl")

    def close(self,client):
        if client.sock:
            client.sock.close()
        self.app.quit()


client = MTPclient()
def main():

    app = QApplication(sys.argv)

    viewer = MTPviewer(client,app)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
