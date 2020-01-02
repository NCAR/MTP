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
        QPlainTextEdit, QFrame, QAction, QLabel, QPushButton, QGroupBox, \
        QMessageBox
from PyQt5.QtCore import QSocketNotifier, Qt
from PyQt5.QtGui import QFontMetrics, QFont

from viewer.MTPclient import MTPclient
from viewer.plotScanTemp import ScanTemp
from viewer.plotProfile import Profile
# from viewer.plotTimeseries import Timeseries
import numpy


class MTPviewer(QMainWindow):

    def __init__(self, app):

        self.app = app
        self.cell = [[numpy.nan for j in range(10)] for i in range(3)]

        self.clicked = False  # Only show error msg once

        self.client = MTPclient()
        self.client.initRetriever()
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
        self.resize(800, 855)

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

    def createTBcell(self, grid, chan, ang):
        """
        Create a grid to display the brightness temperatures for the current
        scan
        """
        cell = QPlainTextEdit("Ang " + str(ang+1))
        cell.setFixedHeight(25)
        cell.setReadOnly(True)
        if (ang+1 == 6):
            cell.setStyleSheet("QPlainTextEdit {background-color: lightgreen}")
        grid.addWidget(cell, ang+2, chan-1, 1, 1)
        return(cell)

    def writeTB(self, cell):
        """ Display the brightness temperatures in the GUI """
        reader = self.client.reader
        for i in range(0, 3):
            for j in range(0, 10):
                tb = reader.rawscan['Bline']['values']['SCNT']['tb'][i + j*3]
                cell[i][j].setPlainText('%6.2f' % tb)

    def initView(self):
        """ Initialize the central widget """
        # Create the grid layout for the central widget. Assign the layout to
        # the widget. The grid layout will hold multiple sub-windows and plots.
        self.layout = QGridLayout()
        self.view.setLayout(self.layout)

        # Create the Engineering 1 display window
        eng1label = QLabel("Platinum Multiplxr (Pt)")
        self.layout.addWidget(eng1label, 9, 0, 1, 2)

        self.eng1 = QPlainTextEdit()
        self.eng1.setReadOnly(True)
        self.eng1.setFixedHeight(300)
        self.eng1.setDocumentTitle("Pt")
        self.layout.addWidget(self.eng1, 10, 0, 1, 2)
        self.eng1.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.header_eng1 = "Channel\tCounts  Ohms  Temp  "
        self.eng1.setPlainText(self.header_eng1)

        # Size the Eng 1 window to the width of the header text
        self.configEngWindow(self.eng1, self.header_eng1)

        # Create the Engineering 2 display window
        eng2label = QLabel("Engineering Multiplxr (M01)")
        self.layout.addWidget(eng2label, 9, 2, 1, 3)

        self.eng2 = QPlainTextEdit()
        self.eng2.setReadOnly(True)
        self.layout.addWidget(self.eng2, 10, 2, 1, 3)
        self.eng2.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.header_eng2 = "Channel\tCounts  Volts"
        self.eng2.setPlainText(self.header_eng2)

        # Size the Eng 2 window to the width of the header text
        self.configEngWindow(self.eng2, self.header_eng2)

        # Create the Engineering 3 display window
        eng3label = QLabel("Engineering Multiplxr (M02)")
        eng3label.setStyleSheet("""QToolTip {background-color: lightyellow}""")
        eng3label.setToolTip("If T Synth goes over 50, turn off MTP to avoid" +
                             " damage due to overheating")
        self.layout.addWidget(eng3label, 9, 5, 1, 3)

        self.eng3 = QPlainTextEdit()
        self.eng3.setReadOnly(True)
        self.layout.addWidget(self.eng3, 10, 5, 1, 3)
        self.eng3.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.header_eng3 = "Channel\tCounts  Value"
        self.eng3.appendPlainText(self.header_eng3)

        # Size the Eng 3 window to the width of the header text
        self.configEngWindow(self.eng3, self.header_eng3)

        # Create project metadata fields for first row of GUI
        self.layout.addWidget(QLabel("Project"), 0, 0, 1, 1)
        metadata = QPlainTextEdit(self.client.getProj())
        metadata.setFixedHeight(25)
        metadata.setReadOnly(True)
        self.layout.addWidget(metadata, 0, 1, 1, 1)

        self.layout.addWidget(QLabel("FltNo"), 0, 2, 1, 1)
        metadata = QPlainTextEdit(self.client.getFltno())
        metadata.setFixedHeight(25)
        metadata.setReadOnly(True)
        self.layout.addWidget(metadata, 0, 3, 1, 1)

        self.layout.addWidget(QLabel("Date"), 0, 4, 1, 1)
        self.date = QPlainTextEdit("Date")
        self.date.setFixedHeight(25)
        self.date.setReadOnly(True)
        self.layout.addWidget(self.date, 0, 5, 1, 1)

        metadata = QLabel("Connected")
        self.layout.addWidget(metadata, 0, 6, 1, 1)
        metadata = QLabel("(TBD)")
        metadata.setStyleSheet("QLabel { color: green }")
        metadata.setFixedHeight(25)
        self.layout.addWidget(metadata, 0, 7, 1, 1)

        # Create a box to hold the list of brightness temps
        box = QGroupBox()
        box.setFixedHeight(275)
        self.layout.addWidget(box, 1, 0, 1, 2)
        grid = QGridLayout()

        ch1 = QLabel("Channel 1")
        ch1.setStyleSheet("QLabel { color: red }")
        ch1.setFixedHeight(25)
        grid.addWidget(ch1, 1, 0)
        for ang in range(10):
            self.cell[0][ang] = self.createTBcell(grid, 1, ang)

        ch2 = QLabel("Channel 2")
        ch2.setStyleSheet("QLabel { color: grey }")
        ch2.setFixedHeight(25)
        grid.addWidget(ch2, 1, 1)
        for ang in range(10):
            self.cell[1][ang] = self.createTBcell(grid, 2, ang)

        ch3 = QLabel("Channel 3")
        ch3.setStyleSheet("QLabel { color: blue }")
        ch3.setFixedHeight(25)
        grid.addWidget(ch3, 1, 2)
        for ang in range(10):
            self.cell[2][ang] = self.createTBcell(grid, 3, ang)

        box.setLayout(grid)

        # Create our scan and temperature plot and add it to the layout
        self.scantemp = ScanTemp()
        st = self.scantemp.getWindow()
        st.setFixedHeight(275)
        st.setFixedWidth(280)
        self.layout.addWidget(st, 1, 2, 1, 3)

        # Create a profile plot and add it to the layout
        self.profile = Profile()
        profile = self.profile.getWindow()
        profile.setFixedHeight(275)
        profile.setFixedWidth(300)
        self.layout.addWidget(profile, 1, 5, 1, 3)

        # Create a box to hold selected RCFs and controls
        self.layout.addWidget(QLabel("IWG port"), 2, 0, 1, 1)
        iwgport = QPlainTextEdit(str(self.client.getIWGport()))
        iwgport.setFixedHeight(25)
        iwgport.setReadOnly(True)
        self.layout.addWidget(iwgport, 2, 1, 1, 1)

        self.layout.addWidget(QLabel("UDP port"), 3, 0, 1, 1)
        udpport = QPlainTextEdit(str(self.client.getUDPport()))
        udpport.setFixedHeight(25)
        udpport.setReadOnly(True)
        self.layout.addWidget(udpport, 3, 1, 1, 1)

        back = QPushButton("BACK")
        back.setFixedHeight(25)
        back.setFixedWidth(75)
        self.layout.addWidget(back, 2, 2, 1, 1)

        nav = QLabel("<- Nav ->")
        self.layout.addWidget(nav, 2, 3, 1, 1)
        nav.setAlignment(Qt.AlignCenter)

        fwd = QPushButton("FWD")
        fwd.setFixedHeight(25)
        fwd.setFixedWidth(75)
        self.layout.addWidget(fwd, 2, 4, 1, 1)

        self.layout.addWidget(QLabel("RCF1"), 2, 5, 1, 1)
        self.RCF1 = QPlainTextEdit("RCF1#")
        self.RCF1.setFixedHeight(25)
        self.RCF1.setReadOnly(True)
        self.layout.addWidget(self.RCF1, 2, 6, 1, 1)

        self.layout.addWidget(QLabel("RCF2"), 3, 5, 1, 1)
        RCF2 = QPlainTextEdit("RCF2#")
        RCF2.setFixedHeight(25)
        RCF2.setReadOnly(True)
        self.layout.addWidget(RCF2, 3, 6, 1, 1)

        bad = QPushButton("Mark Bad Scan")
        bad.setFixedHeight(25)
        self.layout.addWidget(bad, 2, 7, 1, 1)

        mrilabel = QLabel("MRI")
        mrilabel.setStyleSheet("""QToolTip {background-color: lightyellow}""")
        mrilabel.setToolTip("Meridional Region Index: Quality of match " +
                            "between measured Brightness Temperture (TB) and" +
                            "TB from template")
        self.layout.addWidget(mrilabel, 3, 2, 1, 1)
        self.MRI = QPlainTextEdit("MRI")
        self.MRI.setFixedHeight(25)
        self.MRI.setReadOnly(True)
        self.layout.addWidget(self.MRI, 3, 3, 1, 1)

        # Create a File data display window
        self.filedata = QPlainTextEdit()
        self.filedata.setReadOnly(True)
        self.filedata.setFixedHeight(140)
        self.layout.addWidget(self.filedata, 4, 0, 4, 8)
        self.filedata.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.filedata.appendPlainText("MTP data block display")

        # Temporarily insert some sample data to get an idea how it will
        # look. Remove this when get data parsing coded.
        self.filedata.appendPlainText("A YYYYMMDD HH:MM:SS --- --- ---")
        self.filedata.appendPlainText("B ------ ------ ------ ------ ------ " +
                                      "------")
        self.filedata.appendPlainText("M01: ---- ---- ---- ---- ---- ---- " +
                                      "----")
        self.filedata.appendPlainText("M02: ---- ---- ---- ---- ---- ---- " +
                                      "----")
        self.filedata.appendPlainText("Pt: ---- ----- ----- ----- ----- -----")
        self.filedata.appendPlainText("E ------ ------ ------ ------ ------ " +
                                      "------")
        # End temporary display block

        # IWG record display window
        self.iwg = QPlainTextEdit()
        self.iwg.setReadOnly(True)
        self.iwg.setFixedHeight(60)
        self.layout.addWidget(self.iwg, 8, 0, 1, 8)
        self.iwg.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        # Temporarily insert some sample data to get an idea how it will
        # look. Remove this when get data parsing coded.
        self.iwg.appendPlainText("IWG1,YYYYMMDDTHHMMSS,-xx.xxxx,xxx.xxx,")
        # End temporary display block

    def close(self):
        """ Actions to take when Quit button is clicked """
        self.client.close()  # Close UDP and IWG connections
        self.app.quit()      # Close app

    def plotData(self):
        """
        Function to tell client to read latest data and to update all plots in
        the GUI.
        """
        # Ask client to read data from the UDP feed and save it to the data
        # dictionary.
        self.client.readSocket()

        # Perform line calculations on latest scan
        tbi = self.client.doCalcs()

        try:
            BestWtdRCSet = self.client.doRetrieval(tbi)  # Perform retrieval
        except Exception as err:
            if not self.clicked:
                QMessageBox.warning(self, '',
                                    "Could not perform retrieval --" +
                                    str(err) + "\nClick OK to stop " +
                                    "seeing this message ", QMessageBox.Ok)
                # Do not get to this point until user clicks OK
                self.clicked = True  # Only show error once

        # Display date of latest record
        self.writeDate()

        # Display the latest data in the MTP data block display
        self.writeData()

        # Display the latest IWG packet
        self.writeIWG()

        # Update the Engineering 1 box with Pt calculated values
        self.writeEng1()

        # Update the Engineering 2 box with M01 calculated values
        self.writeEng2()

        # Update the Engineering 3 box with the M02 calculated values
        self.writeEng3()

        # Display the brightness temperatures in text format
        self.writeTB(self.cell)

        # ---------- Populate scan and template plot ----------
        # Do this before begin retrieval so that if retrieval fails, use can
        # still see that counts are being collected by instrument

        # Clear the scan and template plot canvas in prep for new plots
        self.scantemp.clear()

        # Plot scan brightness temperatures.
        self.scantemp.plotTB(tbi)
        self.scantemp.draw()

        # If retrieval failed, go no further
        if not (BestWtdRCSet):
            return()

        # ---------- Retrieval succeeded ----------
        # Get the physical temperature profile (and find tropopause)
        ATP = self.client.getProfile(tbi, BestWtdRCSet)

        # Does RCF file always start with NRC? I think it stands for:
        # "Ncar gv RCf file"
        self.RCF1.setPlainText(BestWtdRCSet['RCFId'].replace('NRC', ''))

        # Display MRI
        self.MRI.setPlainText('%.3f' % (ATP['RCFMRIndex']))

        # Plot the template brightness temperatures on the scan and temp plot
        self.scantemp.plotTemplate(BestWtdRCSet['FL_RCs']['sOBav'])

        # Get min and max x values, used for auto-scaling horizontal lines
        xmin = self.scantemp.minTemp(tbi, BestWtdRCSet['FL_RCs']['sOBav'])
        xmax = self.scantemp.maxTemp(tbi, BestWtdRCSet['FL_RCs']['sOBav'])

        # Plot a line for the horizontal scan (grey line) to autoscaled width
        self.scantemp.plotHorizScan(xmin, xmax)

        # Plot the aircraft altitude (black line) to autoscaled width
        self.scantemp.plotACALT(self.client.reader.getACAlt(), xmin, xmax)

        # Draw the plots
        self.scantemp.draw()

        # ---------- Populate profile plot ----------
        # Clear the canvas in prep for new plots
        self.profile.clear()
        self.profile.configure()  # Layout the profile plot

        # Plot the profile from the template
        self.profile.plotTemplate((BestWtdRCSet['FL_RCs']['sRTav']),
                                  ATP['Altitudes'])

        # Plot the physical temperature profile
        if (ATP):  # If successfully create a profile from this scan
            self.profile.plotProfile(ATP['Temperatures'], ATP['Altitudes'])

        # Plot the aircraft altitude
        self.profile.plotACALT(self.client.reader.getVar('Aline', 'SAAT'),
                               self.client.reader.getACAlt())

        # Plot the tropopause (dotted line)
        for i in range(len(ATP['trop'])):
            self.profile.plotTropopause(ATP['trop'][i])

        # Plot the adiabatic lapse rate
        # diagonal dashed line, fixed slope anchored to ambient temperature
        # point of first tropopause
        referenceLapseRate = -2  # This is also hardcoded in tropopause.py
        self.profile.plotLapseRate(ATP['trop'][0], referenceLapseRate)

        # Draw the plots
        self.profile.draw()

        # Process any events generated by the GUI so it stays reponsive to the
        # user.
        self.app.processEvents()

    def writeDate(self):
        """ Display the record date in the Date box at the top of the GUI """
        self.date.setPlainText(self.client.reader.getDate())

    def writeData(self):
        """
        Function to write the latest data record to the data display box
        Assumes we only have the values (retrieved from the UDPd ascii
        packet so have to regenerate the data strings before can create the
        data lines.
        """
        self.filedata.appendPlainText("")  # Space between records
        self.client.reader.createAdata()  # Create the A data string
        self.filedata.appendPlainText(self.client.reader.getAline())
        self.client.reader.createBdata()  # Create the B data string
        self.filedata.appendPlainText(self.client.reader.getBline())
        self.client.reader.createM01data()  # Create the M01 data string
        self.filedata.appendPlainText(self.client.reader.getM01line())
        self.client.reader.createM02data()  # Create the M02 data string
        self.filedata.appendPlainText(self.client.reader.getM02line())
        self.client.reader.createPtdata()  # Create the Pt data string
        self.filedata.appendPlainText(self.client.reader.getPtline())
        self.client.reader.createEdata()  # Create the E data string
        self.filedata.appendPlainText(self.client.reader.getEline())

    def writeIWG(self):
        """
        Function to write the IWG line to IWG display box
        """
        self.iwg.setPlainText(self.client.iwg.getIwgPacket())

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
                degstr = '  '
            elif numpy.isnan(deg):
                val = "%04d" % int(val)
                degstr = 'N/A'
            else:
                val = "%04d" % int(val)
                # If Tsynth goes over 50, warn user by changing bkgnd to red
                if (var == 'TSYNCNTE' and deg > 50.0):
                    fmt = self.eng3.currentCharFormat()
                    fmt.setBackground(Qt.red)
                    self.eng3.setCurrentCharFormat(fmt)
                if var == 'ACCPCNTE':  # Set units of Acceler to g
                    degstr = "%+06.2f g" % deg
                else:
                    degstr = "%+06.2f C" % deg

            self.eng3.appendPlainText(name + "\t" + val + "  " + degstr)
            # Only change the Tsynth line, rest should remain on white
            if (var == 'TSYNCNTE' and deg > 50.0):
                fmt = self.eng3.currentCharFormat()
                fmt.setBackground(Qt.white)
                self.eng3.setCurrentCharFormat(fmt)
