###############################################################################
# This MTP viewer program runs on the user host, accepts MTP data from the
# client and creates plots and other displays to allow the user to monitor the
# status and function of the MTP.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import numpy
import pyqtgraph as pg

from PyQt5.QtWidgets import QGridLayout, QWidget, QTabWidget, \
     QPushButton, QComboBox, QHBoxLayout
from PyQt5.QtCore import QSocketNotifier

from viewer.MTPclient import MTPclient


class MTPviewer():

    def __init__(self, app):

        self.app = app

        self.client = MTPclient()
        self.client.connect()

        self.initUI()

        self.readNotifier = QSocketNotifier(
            self.client.getSocketFileDescriptor(), QSocketNotifier.Read)
        self.readNotifier.activated.connect(lambda: self.plotData())

    def plotData(self):

        self.client.readSocket()

        self.plotDataxy()
        self.plotDatascnt()

        self.app.processEvents()

    def plotDataxy(self):

        (self.x, self.y) = self.client.getXY()
        self.xy.clear()
        self.xyplot = self.xy.plot()
        self.xyplot.setData(self.x, self.y, connect="finite")

    def plotDatascnt(self):
        scnt = self.client.getSCNT()

        # The scan counts are stored in the ads file as cnts[angle,channel],
        # i.e. {a1c1,a1c2,a1c3,a2c1,...}. Processing requires, and the final
        # data are output as {c1a1,c1a2,c1a3,c1a4,...}. Invert the array here.
        scnt_inv = [numpy.nan]*30
        NUM_SCAN_ANGLES = 10
        NUM_CHANNELS = 3
        for j in range(NUM_SCAN_ANGLES):
            for i in range(NUM_CHANNELS):
                scnt_inv[i*10+j] = int(scnt[j*3+i])

        scan1 = scnt_inv[0:10]
        scan2 = scnt_inv[10:20]
        scan3 = scnt_inv[20:30]
        angles = numpy.array(range(10))+1

        # Scan Counts[Angle, Channel]
        self.scnt.clear()
        self.scnt.invertY(True)
        plot2 = self.scnt.plot(pen=pg.mkPen('r'))
        plot2.setData(scan1, angles, connect="finite")
        plot2 = self.scnt.plot(pen=pg.mkPen('w'))
        plot2.setData(scan2, angles, connect="finite")
        plot2 = self.scnt.plot(pen=pg.mkPen('b'))
        plot2.setData(scan3, angles, connect="finite")

    def selectPlotVar(self, text):
        self.xy.clear()
        self.client.initData()
        self.xy.setLabel('left', text)
        self.client.yvar = text
        return()

    def initUI(self):

        # Define top-level widget to hold everything
        self.glayout = QHBoxLayout()
        self.MTPgui = QWidget()
        self.MTPgui.setLayout(self.glayout)
        self.MTPgui.setObjectName("MTPgui")
        self.MTPgui.setWindowTitle('MTP viewer')
        self.MTPgui.resize(1000, 600)

        # Add a tab widget to the upper left
        self.tab = QTabWidget()
        self.glayout.addWidget(self.tab, 0)

        self.initCtrl()    # Create the layout for the "ctrl" tab
        self.initView()    # Create the layout for the "view" tab
        self.initStatus()  # Init status column to the right

        self.MTPgui.show()

        # Show the window even if data are not flowing
        self.app.processEvents()

    def initView(self):
        # Create the layout for the "view" tab
        self.layout = QGridLayout()
        self.view = QWidget()
        self.tab.addTab(self.view, "view")
        self.view.setLayout(self.layout)

        # Create a window to hold our timeseries plot
        w1layout = QGridLayout()
        self.layout.addLayout(w1layout, 0, 1)

        win1 = pg.GraphicsWindow()
        win1.setWindowTitle('Timeseries')
        w1layout.addWidget(win1, 0, 0)
        # Create empty space for the plot in the window and then
        # create an empty plot
        self.xy = win1.addPlot(bottom=self.client.xvar, left=self.client.yvar)

        # Create a window to hold our profile plot
        win2 = pg.GraphicsWindow()
        win2.setWindowTitle('Histo')
        self.layout.addWidget(win2, 0, 0, 3, 1)
        # Create empty space for the plot in the window and then
        # create an empty plot
        self.scnt = win2.addPlot(bottom='Counts', left='Angle')

        # Add a dropdown to select the variable to plot
        varSelector = QComboBox()
        for item in self.client.varlist:
            varSelector.addItem(item)

        varSelector.activated[str].connect(self.selectPlotVar)
        w1layout.addWidget(varSelector, 1, 0)

    def initStatus(self):
        # Add a quit button to the right - later add a red/green indicator to
        # display status of connectivity (like GNI).
        self.window = QWidget()
        button = QPushButton('Quit')
        button.clicked.connect(lambda: self.close())
        self.glayout.addWidget(button, 1)

    def initCtrl(self):
        # Create the layout for the "ctrl" tab
        self.ctrl = QWidget()
        self.tab.addTab(self.ctrl, "ctrl")

    def close(self):
        """ Actions to take when Quit button is clicked """
        self.client.close()  # Close UDP connection
        self.app.quit()      # Close app
