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
from PyQt5.QtGui import QFontMetrics, QFont

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

        # When data appears on the MTP socket, call plotData()
        self.readNotifier = QSocketNotifier(
                self.client.getSocketFileDescriptor(), QSocketNotifier.Read)
        self.readNotifier.activated.connect(lambda: self.plotData())

    def initUI(self):
        """ Initialize the GUI UI """
        # Set window title
        self.setWindowTitle('MTP viewer')

        # Set the initial size of the window created. it is user resizeable.
        self.resize(800, 910)

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
        self.quitButton = QAction('Quit', self)
        self.quitButton.setShortcut('Ctrl+Q')
        self.quitButton.setToolTip('Exit application')
        self.quitButton.triggered.connect(self.close)
        menubar.addAction(self.quitButton)

    def configEngWindow(self, windowID, header):
        """
        Configure the Engineering windows - monospace font to make text
        allignment easier, and resize minimum width to fit header.
        """
        font = QFont("monospace")               # Use a monospace font
        windowID.setFont(font)
        fontMetrics = QFontMetrics(font)        # QFontMetrics based on font
        textSize = fontMetrics.size(0, header)  # Size of text in font
        textWidth = textSize.width() + 60       # constant may need tweaking
        textHeight = textSize.height()
        windowID.setMinimumSize(textWidth, textHeight)  # Finally, set size

    def initView(self):
        """ Initialize the central widget """
        # Create the grid layout for the central widget. Assign the layout to
        # the widget. The grid layout will hold multiple sub-windows and plots.
        self.layout = QGridLayout()
        self.view.setLayout(self.layout)

        # Create the Engineering 1 display window
        self.eng1 = QPlainTextEdit()
        self.eng1.setReadOnly(True)
        self.eng1.setFixedHeight(200)
        self.eng1.setDocumentTitle("Pt")
        self.layout.addWidget(self.eng1, 9, 0, 1, 1)
        self.eng1.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.header_eng1 = "Channel\tCounts  Ohms  Temp  "
        self.eng1.setPlainText(self.header_eng1)

        # Size the Eng 1 window to the width of the header text
        self.configEngWindow(self.eng1, self.header_eng1)

        # Create the Engineering 2 display window
        self.eng2 = QPlainTextEdit()
        self.eng2.setReadOnly(True)
        self.layout.addWidget(self.eng2, 9, 1, 1, 1)
        self.eng2.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.header_eng2 = "Channel  Counts  Volts"
        self.eng2.setPlainText(self.header_eng2)

        # Size the Eng 2 window to the width of the header text
        self.configEngWindow(self.eng2, self.header_eng2)

        # Create the Engineering 3 display window
        self.eng3 = QPlainTextEdit()
        self.eng3.setReadOnly(True)
        self.layout.addWidget(self.eng3, 9, 2, 1, 1)
        self.eng3.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.header_eng3 = "Channel  Counts  Value  "
        self.eng3.appendPlainText(self.header_eng3)

        # Size the Eng 3 window to the width of the header text
        self.configEngWindow(self.eng3, self.header_eng3)

        # Create a project metadata group box
        # metadata = QGroupBox("Project info")
        metadata = QPlainTextEdit("Project info")
        metadata.setFixedHeight(50)
        self.layout.addWidget(metadata, 0, 0, 1, 3)

        # Create a box to hold the list of brightness temps
        tb = QPlainTextEdit("Brightness Temps")
        tb.setFixedHeight(300)
        self.layout.addWidget(tb, 1, 0)

        # Create our scan and temperature plot and add it to the layout
        self.scantemp = ScanTemp()
        st = self.scantemp.getWindow()
        st.setFixedHeight(300)
        self.layout.addWidget(st, 1, 1)

        # Create a window to hold our timeseries plot and parameter selection
        # dropdown menu
        self.timeseries = Timeseries(self.client)
        self.layout.addLayout(self.timeseries.getWindow(), 1, 2)

        # Create a box to hold selected RCFs and controls
        tb = QPlainTextEdit("Control panel")
        tb.setFixedHeight(100)
        self.layout.addWidget(tb, 2, 0, 1, 3)

        # Create a File data display window
        filedata = QPlainTextEdit()
        filedata.setReadOnly(True)
        filedata.setFixedHeight(150)
        self.layout.addWidget(filedata, 3, 0, 5, 3)
        filedata.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        filedata.appendPlainText("MTP data block display")

        # Temporarily insert some sample data to get an idea how it will
        # look. Remove this when get data parsing coded.
        filedata.appendPlainText("A YYYYMMDD HH:MM:SS --- --- ---")
        filedata.appendPlainText("B ------ ------ ------ ------ ------ ------")
        filedata.appendPlainText("M01: ---- ---- ---- ---- ---- ---- ----")
        filedata.appendPlainText("M02: ---- ---- ---- ---- ---- ---- ----")
        filedata.appendPlainText("Pt: ---- ----- ----- ----- ----- -----")
        filedata.appendPlainText("E ------ ------ ------ ------ ------ ------")
        # End temporary display block

        # IWG record display window
        iwg = QPlainTextEdit()
        iwg.setReadOnly(True)
        iwg.setFixedHeight(50)
        self.layout.addWidget(iwg, 8, 0, 1, 3)
        iwg.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        # Temporarily insert some sample data to get an idea how it will
        # look. Remove this when get data parsing coded.
        iwg.appendPlainText("IWG1,YYYYMMDDTHHMMSS,-xx.xxxx,xxx.xxx,")
        # End temporary display block

    def close(self):
        """ Actions to take when Quit button is clicked """
        self.client.close()  # Close UDP and IWG connections
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

        # Calculate the resistance and temperatures from the Pt line
        self.client.calcPt()
        # Update the Engineering 1 box with Pt calculated values (p, t)
        self.writeEng1()

        # Process any events generated by the GUI so it stays reponsive to the
        # user.
        self.app.processEvents()

    def writeEng1(self):
        """
        Function to take the parse Pt line data and populate the Engineering 1
        display box
        """
        # Overwrite the previous values by using setPlainText to clear the box
        # and rewrite the header.
        self.eng1.setPlainText(self.header_eng1)

        # Then append all the lines of data. Need to calculate ohms and temp
        # elsewhere before can display here.
        for var in self.client.reader.getVarList('Ptline'):
            name = self.client.reader.getName('Ptline', var)
            val = "%05d" % int(self.client.reader.getVar('Ptline', var))
            R = "%06.2f" % self.client.reader.getResistance('Ptline', var)

            # For whatever reason, the Temp is not displayed in the VB code
            # for the low and hi ref channels. So block them out here.
            if var == 'TR350CNTP' or var == 'TR600CNTP':
                T = ""
            else:
                T = "%+5.2f" % self.client.reader.getTemperature('Ptline', var)

            self.eng1.appendPlainText(name + "\t" + val + "  " + R + "  " + T)
