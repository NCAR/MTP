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
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget, \
        QPlainTextEdit, QFrame, QAction, QLabel, QPushButton, QGroupBox, \
        QMessageBox
from PyQt5.QtCore import QSocketNotifier, Qt
from PyQt5.QtGui import QFontMetrics, QFont
from viewer.plotScanTemp import ScanTemp
from viewer.plotProfile import Profile
from viewer.plotCurtain import Curtain
from Qlogger.messageHandler import QLogger as logger


class MTPviewer(QMainWindow):

    def __init__(self, client, app, mtpRealTimeFile):

        self.client = client
        self.app = app
        self.mtpRealTimeFile = mtpRealTimeFile
        self.cell = [[numpy.nan for j in range(10)] for i in range(3)]

        self.clicked = False  # Only show error msg once

        # In order to support stepping forward and back through scans, we need
        # to keep track of what scan is currently being displayed. When
        # back and fwd have not been clicked, these two indices will be the
        # same.
        self.viewScanIndex = -1  # The index of the scan being displayed.
        self.currentScanIndex = -1  # index of the scan just measured by MTP

        # The QMainWindow class provides a main application window
        QMainWindow.__init__(self)

        # Create the GUI
        self.initUI()

        # If there exists an mtpRealTime file with the same proj and fltno as
        # are in the config file, then assume we are restarting this code for
        # the same flight, and read in the previous data for this flight from
        # that mtpRealTime file.
        if self.client.reader.load(self.mtpRealTimeFile):
            self.setScanIndex()
            self.updateDisplay()
            self.calcCurtain()

        # When data appears on the MTP socket, call processData()
        self.readNotifier = QSocketNotifier(
                self.client.getSocketFileDescriptor(), QSocketNotifier.Read)
        self.readNotifier.activated.connect(lambda: self.processData())

        # When data appears on the IWG socket, call processIWG()
        self.readNotifierI = QSocketNotifier(
                self.client.getSocketFileDescriptorI(), QSocketNotifier.Read)
        self.readNotifierI.activated.connect(lambda: self.processIWG())

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

        # Add a menu option to display the curtain plot
        self.curtainButton = QAction('CurtainPlot', self)
        self.curtainButton.setToolTip('Open window to display curtain plot')
        self.curtainButton.triggered.connect(self.curtainWindow)
        menubar.addAction(self.curtainButton)
        self.curtain = Curtain(self)

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
        font = QFont("courier")               # Use a monospace font
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
        self.layout.addWidget(eng1label, 9, 0, 1, 3)

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
        eng2label = QLabel("Engineering Multiplxr (M01)")
        self.layout.addWidget(eng2label, 9, 3, 1, 3)

        self.eng2 = QPlainTextEdit()
        self.eng2.setReadOnly(True)
        self.layout.addWidget(self.eng2, 10, 3, 1, 3)
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
        self.layout.addWidget(eng3label, 9, 6, 1, 3)

        self.eng3 = QPlainTextEdit()
        self.eng3.setReadOnly(True)
        self.layout.addWidget(self.eng3, 10, 6, 1, 3)
        self.eng3.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.header_eng3 = "Channel\tCounts  Value"
        self.eng3.appendPlainText(self.header_eng3)

        # Size the Eng 3 window to the width of the header text
        self.configEngWindow(self.eng3, self.header_eng3)

        # Create project metadata fields for first row of GUI
        self.layout.addWidget(QLabel("Project"), 0, 0, 1, 1,
                              alignment=Qt.AlignRight)
        metadata = QPlainTextEdit(self.client.getProj())
        metadata.setFixedHeight(25)
        metadata.setReadOnly(True)
        self.layout.addWidget(metadata, 0, 1, 1, 1)

        self.layout.addWidget(QLabel("FltNo"), 0, 2, 1, 1,
                              alignment=Qt.AlignRight)
        metadata = QPlainTextEdit(self.client.getFltno())
        metadata.setFixedHeight(25)
        metadata.setReadOnly(True)
        self.layout.addWidget(metadata, 0, 3, 1, 1)

        self.layout.addWidget(QLabel("Date"), 0, 4, 1, 1,
                              alignment=Qt.AlignRight)
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
        self.layout.addWidget(box, 1, 0, 1, 3)
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
        self.layout.addWidget(st, 1, 3, 1, 3)

        # Create a profile plot and add it to the layout
        self.profile = Profile()
        profile = self.profile.getWindow()
        profile.setFixedHeight(275)
        profile.setFixedWidth(300)
        self.layout.addWidget(profile, 1, 6, 1, 3)

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

        self.layout.addWidget(QLabel("Scan Index"), 3, 2, 1, 1)
        self.index = QPlainTextEdit("")
        self.index.setFixedHeight(25)
        self.index.setReadOnly(True)
        self.layout.addWidget(self.index, 3, 3, 1, 1)

        back = QPushButton("BACK")
        back.setFixedHeight(25)
        back.setFixedWidth(75)
        self.layout.addWidget(back, 2, 3, 1, 1, alignment=Qt.AlignRight)
        back.clicked.connect(self.clickBack)

        nav = QLabel("<- Nav ->")
        self.layout.addWidget(nav, 2, 4, 1, 1, alignment=Qt.AlignHCenter)
        nav.setAlignment(Qt.AlignCenter)

        fwd = QPushButton("FWD")
        fwd.setFixedHeight(25)
        fwd.setFixedWidth(75)
        self.layout.addWidget(fwd, 2, 5, 1, 1)
        fwd.clicked.connect(self.clickFwd)

        self.layout.addWidget(QLabel("RCF1"), 2, 6, 1, 1,
                              alignment=Qt.AlignRight)
        self.RCF1 = QPlainTextEdit("RCF1#")
        self.RCF1.setFixedHeight(25)
        self.RCF1.setReadOnly(True)
        self.layout.addWidget(self.RCF1, 2, 7, 1, 1)

        self.layout.addWidget(QLabel("RCF2"), 3, 6, 1, 1,
                              alignment=Qt.AlignRight)
        RCF2 = QPlainTextEdit("RCF2#")
        RCF2.setFixedHeight(25)
        RCF2.setReadOnly(True)
        self.layout.addWidget(RCF2, 3, 7, 1, 1)

        bad = QPushButton("Mark Bad Scan")
        bad.setFixedHeight(25)
        self.layout.addWidget(bad, 2, 8, 2, 1, alignment=Qt.AlignVCenter)

        mrilabel = QLabel("MRI")
        mrilabel.setStyleSheet("""QToolTip {background-color: lightyellow}""")
        mrilabel.setToolTip("Meridional Region Index: Quality of match " +
                            "between measured Brightness Temperture (TB) and" +
                            "TB from template")
        self.layout.addWidget(mrilabel, 3, 4, 1, 1, alignment=Qt.AlignRight)
        self.MRI = QPlainTextEdit("MRI")
        self.MRI.setFixedHeight(25)
        self.MRI.setReadOnly(True)
        self.layout.addWidget(self.MRI, 3, 5, 1, 1)

        # Create a File data display window
        self.filedata = QPlainTextEdit()
        self.filedata.setReadOnly(True)
        self.filedata.setFixedHeight(140)
        self.layout.addWidget(self.filedata, 4, 0, 4, 9)
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
        self.layout.addWidget(self.iwg, 8, 0, 1, 9)
        self.iwg.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        # Temporarily insert some sample data to get an idea how it will
        # look. Remove this when get data parsing coded.
        self.iwg.appendPlainText("IWG1,YYYYMMDDTHHMMSS,-xx.xxxx,xxx.xxx,")
        # End temporary display block

    def curtainWindow(self):
        """ Action to take when CurtainPlot button is clicked """
        self.curtain.show()

    def close(self):
        """ Actions to take when Quit button is clicked """
        self.client.close()  # Close UDP connection
        self.client.closeI()  # Close IWG connection
        self.app.quit()      # Close app

    def processIWG(self):
        """ Tell client to read latest IWG record and save to dictionary """
        self.client.readSocketI()  # Only saves to current scan

        # Display the latest IWG packet
        self.writeIWG()

    def processData(self):
        """
        Tell client to read latest data and to update all plots in the GUI.
        """
        # Ask client to read MTP data from the UDP feed and save it to the data
        # dictionaries - one for current scan and one for all scans in flight
        self.client.readSocket()

        # Perform calculations on the raw MTP data
        try:
            self.client.processMTP()
        except Exception as err:
            # if retrieval failed, so warn user profile will not be generated.
            if not self.clicked:
                QMessageBox.warning(self, '',
                                    "Could not perform retrieval --" +
                                    str(err) + "\nClick OK to stop " +
                                    "seeing this message ", QMessageBox.Ok)
                # Do not get to this point until user clicks OK
                self.clicked = True  # Only show error once

        # Copy to array of dictionaries that holds entire flight
        self.client.reader.archive()

        # Append to JSON file on disk
        self.client.reader.save(self.mtpRealTimeFile)

        # Update the display
        self.setScanIndex()
        self.plotData()
        self.updateCurtainPlot()

        # Process any events generated by the GUI so it stays reponsive to the
        # user.
        self.app.processEvents()

    def setScanIndex(self):
        # What is the index of the current scan, i.e. the one just collected
        # by the MTP (scans are stored in array so index starts at zero not 1)
        self.currentScanIndex = len(self.client.reader.flightData) - 1
        self.viewScanIndex = self.currentScanIndex  # Viewing latest scan

    def plotData(self):
        """ Populate the GUI with data from the MTP dictionary """
        # Display date of latest record
        self.writeDate()

        # Display index of latest record (start with 1, so intuitive to user
        self.index.setPlainText(str(self.viewScanIndex + 1))

        # Display the latest data in the MTP data block display
        self.writeData()

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
        self.scantemp.plotTB(self.client.getTBI())
        self.scantemp.draw()

        # If retrieval failed, go no further
        self.BestWtdRCSet = self.client.getBestWtdRCSet()
        if not (self.BestWtdRCSet):
            return()

        # ---------- Retrieval succeeded ----------
        self.ATP = self.client.getATP()
        # Does RCF file always start with NRC? I think it stands for:
        # "Ncar gv RCf file"
        self.RCF1.setPlainText(self.BestWtdRCSet['RCFId'].replace('NRC', ''))

        # Display MRI
        self.MRI.setPlainText('%.3f' % (self.ATP['RCFMRIndex']))

        # Plot the template brightness temperatures on the scan and temp plot
        self.scantemp.plotTemplate(self.BestWtdRCSet['FL_RCs']['sOBav'])

        # Get min and max x values, used for auto-scaling horizontal lines
        xmin = self.scantemp.minTemp(self.client.getTBI(),
                                     self.BestWtdRCSet['FL_RCs']['sOBav'])
        xmax = self.scantemp.maxTemp(self.client.getTBI(),
                                     self.BestWtdRCSet['FL_RCs']['sOBav'])

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
        self.profile.plotTemplate((self.BestWtdRCSet['FL_RCs']['sRTav']),
                                  self.ATP['Altitudes'])

        # Plot the physical temperature profile
        if (self.ATP):  # If successfully create a profile from this scan
            self.profile.plotProfile(self.ATP['Temperatures'],
                                     self.ATP['Altitudes'])

        # Plot the aircraft altitude
        self.profile.plotACALT(self.client.reader.getVar('Aline', 'SAAT'),
                               self.client.reader.getACAlt())

        # Plot the tropopause (dotted line)
        for i in range(len(self.ATP['trop'])):
            self.profile.plotTropopause(self.ATP['trop'][i])

        # Plot the adiabatic lapse rate
        # diagonal dashed line, fixed slope anchored to ambient temperature
        # point of first tropopause
        referenceLapseRate = -2  # This is also hardcoded in tropopause.py
        self.profile.plotLapseRate(self.ATP['trop'][0], referenceLapseRate)

        # Draw the plots
        self.profile.draw()

    def calcCurtain(self):
        """
        If read old data from JSON file, repopulate curtain plot vars with
        data so can regenerate curtain plot for old data
        """

        # Loop through previous data and add data from each record to
        # 2-D arrays used by curtain plot
        for index in range(len(self.client.reader.flightData)-1):
            thisscan = self.client.reader.flightData[index]
            time = thisscan['Aline']['values']['TIME']['val']
            temperature = thisscan['ATP']['Temperatures']

            self.curtain.addAlt(thisscan['ATP']['Altitudes'])
            self.curtain.addTemp(temperature)
            self.curtain.addTime(time, temperature)
            self.curtain.addACtime(time)
            self.curtain.addACalt(thisscan['Aline']['values']['SAPALT']['val'])
            self.curtain.addTrop(thisscan['ATP']['trop'][0])
            self.curtain.addMRI(thisscan['BestWtdRCSet']['SumLnProb'])

            # addAlt and addTime have special cases for first value read into
            # data arrays, so after first time thru, have to set first to false
            self.curtain.first = False

        # First time plotting has special case, so set first to True again
        # There has to be a cleaner way to do this - I'm being lazy.
        self.curtain.first = True

        # Generate the curtain plot
        self.curtain.plotCurtain()
        self.curtain.plotACALT()       # Plot aircraft altitude
        self.curtain.plotTropopause()  # Plot first tropopause
        self.curtain.plotMRI()         # Plot data quality

    def updateCurtainPlot(self):
        # ------- Append to the curtain plot ------ #

        self.curtain.clear()

        # Add latest data to 2-D arrays used by curtain plot
        self.curtain.addAlt(self.ATP['Altitudes'])
        self.curtain.addTemp(self.ATP['Temperatures'])
        self.curtain.addTime(self.client.reader.getVar('Aline', 'TIME'),
                             self.ATP['Temperatures'])
        self.curtain.addACtime(self.client.reader.getVar('Aline', 'TIME'))
        self.curtain.addACalt(self.client.reader.getACAlt())
        self.curtain.addTrop(self.ATP['trop'][0])
        self.curtain.addMRI(self.BestWtdRCSet['SumLnProb'])

        # Generate the curtain plot
        self.curtain.plotCurtain()
        self.curtain.plotACALT()       # Plot aircraft altitude
        self.curtain.plotTropopause()  # Plot first tropopause
        self.curtain.plotMRI()         # Plot data quality

        self.curtain.draw()

    def writeDate(self):
        """ Display the record date in the Date box at the top of the GUI """
        self.date.setPlainText(self.client.reader.getDate())

    def writeData(self):
        """ Write the latest data record to the data display box """
        self.filedata.appendPlainText("")  # Space between records
        self.filedata.appendPlainText(self.client.reader.getAline())
        self.filedata.appendPlainText(self.client.reader.getBline())
        self.filedata.appendPlainText(self.client.reader.getM01line())
        self.filedata.appendPlainText(self.client.reader.getM02line())
        self.filedata.appendPlainText(self.client.reader.getPtline())
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

    def clickBack(self):
        """ Go back to previous scan and show plots and data. """
        # Do we want the code to skip to current scan when a new scan comes
        # in, or stay where we are and user has to go forward to see current
        # scan?

        logger.printmsg("DEBUG", "Go back to scan " + str(self.viewScanIndex))

        if self.viewScanIndex < 0:  # MTP has not collected a scan yet
            # disallow click, notify user via QMessage box
            logger.printmsg("ERROR", "No scans yet. Can't go backward")
        elif self.viewScanIndex == 0:  # Only one scan, can't go backward
            # disallow click, notify user via QMessage box
            logger.printmsg("ERROR", "On first scan. Can't go backward")
        else:  # Go back one scan
            self.viewScanIndex = self.viewScanIndex - 1
            self.updateDisplay()

    def updateDisplay(self):
        """ Update display to show data from desired scan """
        # Set the reader to point to the desired scan
        self.client.reader.setRawscan(self.viewScanIndex)
        self.plotData()  # Update the display to display this scan

        # WHAT HAPPENS IF NEW SCAN COMES IN WHILE plotData IS RUNNING??

        # Set the reader back to the current scan so when it updates we
        # see that data.
        self.client.reader.resetRawscan()

    def clickFwd(self):
        """
        If not at most recent scan, go forward to next scan and show plots and
        data
        """

        logger.printmsg("DEBUG", "Go fwd to scan " +
                        str(self.viewScanIndex + 2))

        if self.viewScanIndex == self.currentScanIndex:
            # On current scan, can't go forward.
            logger.printmsg("ERROR", "On latest scan. Can't go forward")
        else:
            self.viewScanIndex = self.viewScanIndex + 1
            self.updateDisplay()
