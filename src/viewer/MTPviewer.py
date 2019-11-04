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
        QPlainTextEdit, QFrame, QAction, QLabel
from PyQt5.QtCore import QSocketNotifier
from PyQt5.QtGui import QFontMetrics, QFont

from viewer.MTPclient import MTPclient
from viewer.plotScanTemp import ScanTemp
# from viewer.plotTimeseries import Timeseries
import numpy


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
        self.eng1label = QLabel("Platinum Multiplxr (Pt)")
        self.layout.addWidget(self.eng1label, 9, 0, 1, 3)

        self.eng1 = QPlainTextEdit()
        self.eng1.setReadOnly(True)
        self.eng1.setFixedHeight(300)
        self.eng1.setDocumentTitle("Pt")
        self.layout.addWidget(self.eng1, 10, 0, 1, 3)
        self.eng1.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.header_eng1 = "Channel\tCounts  Ohms  Temp  "
        self.eng1.setPlainText(self.header_eng1)

        # Size the Eng 1 window to the width of the header text
        self.configEngWindow(self.eng1, self.header_eng1)

        # Create the Engineering 2 display window
        self.eng1label = QLabel("Engineering Multiplxr (M01)")
        self.layout.addWidget(self.eng1label, 9, 3, 1, 3)

        self.eng2 = QPlainTextEdit()
        self.eng2.setReadOnly(True)
        self.layout.addWidget(self.eng2, 10, 3, 1, 3)
        self.eng2.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.header_eng2 = "Channel\tCounts  Volts"
        self.eng2.setPlainText(self.header_eng2)

        # Size the Eng 2 window to the width of the header text
        self.configEngWindow(self.eng2, self.header_eng2)

        # Create the Engineering 3 display window
        self.eng1label = QLabel("Engineering Multiplxr (M02)")
        self.layout.addWidget(self.eng1label, 9, 6, 1, 3)

        self.eng3 = QPlainTextEdit()
        self.eng3.setReadOnly(True)
        self.layout.addWidget(self.eng3, 10, 6, 1, 3)
        self.eng3.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.header_eng3 = "Channel\tCounts  Value"
        self.eng3.appendPlainText(self.header_eng3)

        # Size the Eng 3 window to the width of the header text
        self.configEngWindow(self.eng3, self.header_eng3)

        # Create a project metadata group box
        # metadata = QGroupBox("Project info")
        metadata = QPlainTextEdit("Project info")
        metadata.setFixedHeight(30)
        self.layout.addWidget(metadata, 0, 0, 1, 9)

        # Create a box to hold the list of brightness temps
        tb = QPlainTextEdit("Brightness Temps")
        tb.setFixedHeight(300)
        self.layout.addWidget(tb, 1, 0, 1, 2)

        # Create our scan and temperature plot and add it to the layout
        self.scantemp = ScanTemp()
        st = self.scantemp.getWindow()
        st.setFixedHeight(300)
        st.setFixedWidth(300)
        self.layout.addWidget(st, 1, 2, 1, 3)

        # Create a window to hold our timeseries plot and parameter selection
        # dropdown menu
        # self.timeseries = Timeseries(self.client)
        # self.layout.addLayout(self.timeseries.getWindow(), 1, 5, 1, 4)

        # Create a box to hold selected RCFs and controls
        tb = QPlainTextEdit("Control panel")
        tb.setFixedHeight(50)
        self.layout.addWidget(tb, 2, 0, 1, 9)

        # Create a File data display window
        filedata = QPlainTextEdit()
        filedata.setReadOnly(True)
        filedata.setFixedHeight(150)
        self.layout.addWidget(filedata, 3, 0, 5, 9)
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
        iwg.setFixedHeight(40)
        self.layout.addWidget(iwg, 8, 0, 1, 9)
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
        # (x, y) = self.client.getXY()
        # self.timeseries.plotDataXY(x, y)

        # Update Scan and Template Plot
        # (NOTE: Currently only plots scan counts. Templates are TBD.
        scnt = self.client.getSCNT()    # Get scan counts as fn(Angle, Channel)
        self.scantemp.invertSCNT(scnt)  # Invert array so if fn(Channel, Angle)
        self.scantemp.plotDataScnt()    # Update the scan count plot

        # Calculate the resistance and temperatures from the Pt line
        self.client.calcPt()
        # Update the Engineering 1 box with Pt calculated values
        self.writeEng1()

        # Calculate the voltage from the M01 line
        self.client.calcM01()
        # Update the Engineering 2 box with M01 calculated values
        self.writeEng2()

        # Calculate the values from the M02 line
        self.client.calcM02()
        # Update the Engineering 3 box with the M02 calculated values
        self.writeEng3()

        # Process any events generated by the GUI so it stays reponsive to the
        # user.
        self.app.processEvents()

    def writeEng1(self):
        """
        Function to parse the Pt line data and populate the Engineering 1
        display box
        """
        # Overwrite the previous values by using setPlainText to clear the box
        # and rewrite the header.
        self.eng1.setPlainText(self.header_eng1)

        # Then append all the lines of data,including ohms and temp
        for var in self.client.reader.getVarList('Ptline'):
            name = self.client.reader.getName('Ptline', var)
            val = "%05d" % int(self.client.reader.getVar('Ptline', var))
            R = "%06.2f" % self.client.reader.getCalcVal('Ptline', var,
                                                         'resistance')

            # For whatever reason, the Temp is not displayed in the VB code
            # for the low and hi ref channels. So block them out here.
            if var == 'TR350CNTP' or var == 'TR600CNTP':
                T = ""
            else:
                T = "%+5.2f" % self.client.reader.getCalcVal('Ptline', var,
                                                             'temperature')

            self.eng1.appendPlainText(name + "\t" + val + "  " + R + "  " + T)

    def writeEng2(self):
        """
        Function to parse the M01 line data and populate the Engineering 1
        display box
        """
        # Overwrite the previous values by using setPlainText to clear the box
        # and rewrite the header.
        self.eng2.setPlainText(self.header_eng2)

        # Then append all the lines of data,including ohms and temp
        for var in self.client.reader.getVarList('M01line'):
            name = self.client.reader.getName('M01line', var)
            val = self.client.reader.getVar('M01line', var)
            volts = self.client.reader.getCalcVal('M01line', var, 'volts')
            # Check for missing values in the MTP UDP feed, indicated by ,,
            # and read in as the string ''
            if (val == ''):
                val = "%10s" % ' '
                volts = ' '
            elif numpy.isnan(volts):
                val = "%04d" % int(val)
                volts = 'N/A'
            else:
                val = "%04d" % int(val)
                volts = "%+06.2fV" % volts

            # Write the M01 values to the Engineering window
            self.eng2.appendPlainText(name + "\t" + val + "  " + volts)

    def writeEng3(self):
        """
        Function to parse the M02 line data and populate the Engineering 1
        display box
        """
        # Overwrite the previous values by using setPlainText to clear the box
        # and rewrite the header.
        self.eng3.setPlainText(self.header_eng3)

        # Then append all the lines of data,including ohms and temp
        for var in self.client.reader.getVarList('M02line'):
            name = self.client.reader.getName('M02line', var)
            val = self.client.reader.getVar('M02line', var)
            deg = self.client.reader.getCalcVal('M02line', var, 'temperature')
            # Check for missing values in the MTP UDP feed, indicated by ,,
            # and read in as the string ''
            if (val == ''):
                val = "%10s" % ' '
                deg = '  '
            elif numpy.isnan(deg):
                val = "%04d" % int(val)
                deg = 'N/A'
            else:
                val = "%04d" % int(val)
                if var == 'ACCPCNTE':  # Set units to g
                    deg = "%+06.2f g" % deg
                else:
                    deg = "%+06.2f C" % deg

            self.eng3.appendPlainText(name + "\t" + val + "  " + deg)

            # If Tsynth is > 50, change text color to red - to be coded
