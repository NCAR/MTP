###############################################################################
# This MTP viewer program runs on the user host, accepts MTP data from the
# client and creates plots and other displays to allow the user to monitor the
# status and function of the MTP.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget, \
        QPlainTextEdit, QFrame, QAction
from PyQt5.QtCore import QSocketNotifier

from viewer.MTPclient import MTPclient
from viewer.plotScanTemp import ScanTemp
from viewer.plotTimeseries import Timeseries


class MTPviewer(QMainWindow):

    def __init__(self, app):

        self.app = app

        self.client = MTPclient()
        self.client.connect()

        # The QMainWindow class provides a main application window
        QMainWindow.__init__(self)

        # Create the GUI
        self.initUI()

        # When data appears on the socket, call plotData()
        self.readNotifier = QSocketNotifier(
                self.client.getSocketFileDescriptor(), QSocketNotifier.Read)
        self.readNotifier.activated.connect(lambda: self.plotData())

    def initUI(self):
        """ Initialize the GUI UI """
        # Set window title
        self.setWindowTitle('MTP viewer')

        # Set the initial size of the window created. it is user resizeable.
        self.resize(1200, 800)

        # Define central widget to hold everything
        self.view = QWidget()
        self.setCentralWidget(self.view)

        # Create the layout for the viewer
        self.initView()

        # Configure the menu bar
        self.createMenuBar()

    def createMenuBar(self):
        """ Create the menu bar and add options and dropdowns """
        # A Menu bar will show menus at the top of the QMainWindow
        menubar = self.menuBar()

        # Mac OS treats menubars differently. To get a similar outcome, we can
        # add the following line: menubar.setNativeMenuBar(False).
        menubar.setNativeMenuBar(False)

        # Add a menu option to quit
        quitButton = QAction('Quit', self)
        quitButton.setShortcut('Ctrl+Q')
        quitButton.setToolTip('Exit application')
        quitButton.triggered.connect(self.close)
        menubar.addAction(quitButton)

    def initView(self):
        """ Initialize the central widget """
        # Create the grid layout for the central widget. Assign the layout to
        # the widget. The grid layout will hold multiple sub-windows and plots.
        self.layout = QGridLayout()
        self.view.setLayout(self.layout)

        # Create the Engineering 1 display window
        filedata = QPlainTextEdit()
        filedata.setReadOnly(True)
        self.layout.addWidget(filedata, 0, 0, 2, 1)
        filedata.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        filedata.appendPlainText("Engineering 1 display")

        # Create the Engineering 2 display window
        filedata = QPlainTextEdit()
        filedata.setReadOnly(True)
        self.layout.addWidget(filedata, 2, 0, 2, 1)
        filedata.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        filedata.appendPlainText("Engineering 2 display")

        # Create the Engineering 3 display window
        filedata = QPlainTextEdit()
        filedata.setReadOnly(True)
        self.layout.addWidget(filedata, 4, 0, 2, 1)
        filedata.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        filedata.appendPlainText("Engineering 3 display")

        # Create a project metadata group box
        # metadata = QGroupBox("Project info")
        metadata = QPlainTextEdit("Project info")
        self.layout.addWidget(metadata, 0, 1, 1, 3)

        # Create a box to hold the list of brightness temps
        tb = QPlainTextEdit("Brightness Temps")
        self.layout.addWidget(tb, 1, 1)

        # Create our scan and temperature plot and add it to the layout
        self.scantemp = ScanTemp()
        self.layout.addWidget(self.scantemp.getWindow(), 1, 2)

        # Create a window to hold our timeseries plot and parameter selection
        # dropdown menu
        self.timeseries = Timeseries(self.client)
        self.layout.addLayout(self.timeseries.getWindow(), 1, 3)

        # Create a box to hold selected RCFs and controls
        tb = QPlainTextEdit("Control panel")
        self.layout.addWidget(tb, 2, 1, 1, 3)

        # Create a File data display window
        filedata = QPlainTextEdit()
        filedata.setReadOnly(True)
        self.layout.addWidget(filedata, 3, 1, 2, 3)
        filedata.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        filedata.appendPlainText("MTP data block display")

        # Temporarily insert some sample data to get an idea how it will
        # look. Remove this when get data parsing coded.
        filedata.appendPlainText("A 20140606 06:22:52 +03.98 00.25 +00.07 00.33 +03.18 0.01 268.08 00.11 -43.308 +0.009 +172.469 +0.000 +074146 +073392")
        filedata.appendPlainText("B 018963 020184 019593 018971 020181 019593 018970 020170 019587 018982 020193 019589 018992 020223 019617 019001 020229 019623 018992 020208 019601 018972 020181 019572 018979 020166 019558 018977 020161 019554")
        filedata.appendPlainText("M01: 2928 2321 2898 3082 1923 2921 2432 2944")
        filedata.appendPlainText("M02: 2016 1394 2096 2202 2136 1508 4095 1558")
        filedata.appendPlainText("Pt: 2177 13823 13811 10352 13315 13327 13304 14460")
        filedata.appendPlainText("E 021506 022917 022752 019806 021164 020697")
        # End temporary display block

        # IWG record display window
        iwg = QPlainTextEdit()
        iwg.setReadOnly(True)
        self.layout.addWidget(iwg, 5, 1, 1, 3)
        iwg.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        # Temporarily insert some sample data to get an idea how it will
        # look. Remove this when get data parsing coded.
        iwg.appendPlainText("IWG1,20140606T062250,-43.3061,172.455,3281.97,,10508.5,,149.998,164.027,,0.502512,3.11066,283.283,281.732,-1.55388,3.46827,0.0652588,-0.258496,2.48881,-5.31801,-5.92311,7.77836,683.176,127.248,1010.48,14.6122,297.157,0.303804,104.277,,-72.1708,")
        # End temporary display block

    def close(self):
        """ Actions to take when Quit button is clicked """
        self.client.close()  # Close UDP connection
        self.app.quit()      # Close app

    def plotData(self):
        """
        Function to tell client to read latest data and to update all plots in
        the GUI
        """

        # Ask client to read data from the UDP feed and save it to the data
        # dictionary.
        self.client.readSocket()

        # Update the XY plot (the plot of IWG params vs time)
        (x, y) = self.client.getXY()
        self.timeseries.plotDataXY(x, y)

        # Update Scan and Template Plot
        # (NOTE: Currently only plots scan counts. Templates are TBD.
        scnt = self.client.getSCNT()    # Get scan counts as fn(Angle, Channel)
        self.scantemp.invertSCNT(scnt)  # Invert array so if fn(Channel, Angle)
        self.scantemp.plotDataScnt()    # Update the scan count plot

        # Process any events generated by the GUI so it stays reponsive to the
        # user.
        self.app.processEvents()
