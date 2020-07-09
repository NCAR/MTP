###############################################################################
# Routines related to processing raw MTP data into final data.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2020
###############################################################################
import os
import re
import copy
from lib.config import config
from lib.icartt import ICARTT
from matplotlib.backends.backend_qt5agg import (
       NavigationToolbar2QT as NavigationToolbar)
from util.readGVnc import readGVnc
from proc.file_struct import data_files
from proc.plotTimeSeries import TimeSeries
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget, QAction, \
                            QListWidget, QLabel
from PyQt5.QtGui import QFont
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPprocessor(QMainWindow):

    def __init__(self, viewer, client, parent=None):
        """
        Create a window to be the post-flight processing environment.
        Requires access to a raw MTP data file and a final RAF Low-Rate (LRT)
        NetCDF file.
        """

        self.client = client
        self.viewer = viewer

        super().__init__(parent)
        self.filelist = []
        self.raw_data_file = None

        self.initUI()

        # Initialize window pointers - allows more generic code
        self.ts = False
        self.dropdown = False
        self.toolbar = False

    def initUI(self):
        """ Initialize the processing window """
        # Set window title
        self.setWindowTitle('MTP Post-processor')
        self.resize(500, 300)

        # Define central widget to hold everything
        self.view = QWidget()
        self.setCentralWidget(self.view)

        # Create the layout for the viewer
        self.initView()

        # Configure the menu bar
        self.createMenuBar()

    def initView(self):
        """ Initialize the layout of the central widget """
        self.layout = QGridLayout()
        self.view.setLayout(self.layout)

    def createMenuBar(self):
        """ Create the menu bar and add options and dropdowns """

        # A Menu bar will show menus at the top of the QMainWindow
        self.menubar = self.menuBar()

        # Mac OS treats menubars differently. To get a similar outcome, we can
        # add the following line: menubar.setNativeMenuBar(False).
        self.menubar.setNativeMenuBar(False)

        # Add a menu option to load a flight file to process
        self.loadFlight = QAction('LoadFlight', self)
        self.loadFlight.setToolTip('Load data for a single flight')
        self.loadFlight.triggered.connect(self.flightSelectWindow)
        self.menubar.addAction(self.loadFlight)

        # Add menu option to process loaded data  TBD**

        # Add menu option to plot timeseries
        self.plotSeries = QAction('Plot Timeseries', self)
        self.plotSeries.setToolTip('Plot time series for a variable')
        self.plotSeries.triggered.connect(self.plotTimeseries)
        self.menubar.addAction(self.plotSeries)

        # Add a menu option to save final data
        self.saveButton = QAction('Save ICARTT', self)
        self.saveButton.setToolTip('Save Processed Data to an ICARTT file')
        self.saveButton.triggered.connect(self.saveICARTT)
        self.menubar.addAction(self.saveButton)
        self.icartt = ICARTT(self.client)

    def flightSelectWindow(self):
        """ Create list of available data files and allow user to load one """
        # Close timeseries window and dropdown in case  'Plot Timeseries' was
        # previously selected.
        if self.ts:
            self.ts.close()
        if self.dropdown:
            self.dropdown.close()
        if self.toolbar:
            self.removeToolBar(self.toolbar)

        # Create a QListWidget to hold the possible flights
        self.textbox = QListWidget(self)
        self.textbox.show()
        self.layout.addWidget(self.textbox, 1, 0)

        # Set monospace font to align text
        font = QFont("courier")               # Use a monospace font
        self.textbox.setFont(font)

        # # Add a title above the source station list
        self.lbl = QLabel("Available Flights")
        self.lbl.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.layout.addWidget(self.lbl, 0, 0)

        # Display stations in textbox
        for flight in self.filelist:
            # Display basename
            self.textbox.addItem(os.path.basename(flight["rawFile"]))

        # When user selects flight, make sure both the raw and nc files
        # exist on disk. If not, warn user and ask if they want to launch a
        # file selector or select a different flight. If select flight, remind
        # them to fix the setup file for future use.
        self.textbox.clicked.connect(self.setFile)

    def plotTimeseries(self):
        """ Add a timeseries plot window """
        self.timeseries = TimeSeries(self.client)
        self.ts = self.timeseries.getWindow()
        self.layout.addWidget(self.ts, 1, 0)

        # Add toolbar that lets users zoom, pan, save, etc
        self.toolbar = NavigationToolbar(self.ts, self)
        self.addToolBar(self.toolbar)

        # Add a dropdown menu to select variable to plot
        # NEED TO ADD OTHER VALS BESIDES ELINE. What would Julie like? TBD**
        # SA values from Aline? Definitely want temperature a flight level
        # Don't hardcode Eline. Make generic. TBD**
        self.dropdown = \
            self.timeseries.varSelector(self.client.reader.getVarList('Eline'))
        self.layout.addWidget(self.dropdown, 0, 0)

    def closeRawFile(self):
        """ If raw_data_file is open, close it """
        if self.raw_data_file:
            self.raw_data_file.close()

    def setFile(self):
        # If have already read in JSON data, or another file, clear it!!!
        self.client.clearData()

        # The user should only be able to select one file at a time, but out
        # of an abundance of caution, check and warn user if not true.
        if len(self.textbox.selectedItems()) != 1:
            logger.printmsg("ERROR", "Please select a single flight")
            return()

        # Get file user selected
        selectedRawFile = self.textbox.selectedItems()[0].text()

        # Find data_files dict that matches the selected file
        for flight in self.filelist:
            if re.match(os.path.basename(flight["rawFile"]), selectedRawFile):
                selectedRawFile = flight["rawFile"]
                selectedNCfile = flight["ncFile"]

        # Read the NetCDF file into a pandas data frame
        self.gvreader = readGVnc()
        self.gvreader.getNGvalues(selectedNCfile)

        # Open the raw data file
        self.raw_data_file = open(selectedRawFile, 'r')

        # Have the flight selection box change somehow to show that the
        # user has sucessfully selected a flight
        # TBD**

        # Loop and read in all the raw data
        haveData = True
        self.viewer.viewScanIndex = 0
        while haveData:
            # If user clicks Quit in the main GUI window, we want to stop
            # looping and exit the app. To do this, the Quit click closes
            # raw_data_file. So check for that here.
            if self.raw_data_file.closed:
                exit()

            # Read raw_data_file until get a single complete rawscan
            # Returns False when reaches EOF
            # Each record is saved to the flightData array
            haveData = self.client.reader.readRawScan(self.raw_data_file)

            if haveData is True:  # Found a complete raw scan
                # Combine the separate lines from a raw scan into a UDP
                # packet
                packet = self.client.reader.getAsciiPacket()

                # Parse the packet and store values in data dictionary
                self.client.reader.parseAsciiPacket(packet)

                # Perform calcs on the raw MTP data
                self.client.processScan()

                # Skip doing retrievals and speed up reading in raw data file.
                # The idea then is to wait until after doing a tbfit to process
                # the data. May change this later. To be decided. Leave code
                # here for now so can uncomment later if change my mind. TBD**
                # try:
                #     self.client.createProfile()
                # except Exception as err:
                #     # retrieval failed
                #     # warn user profile will not be generated.
                #     self.viewer.reportFailedRetrieval(err)

                # Save this record to the flight library and
                # Append to JSON file on disk
                self.client.saveData()

                # Update the parent display
                self.viewer.viewScanIndex = self.viewer.viewScanIndex + 1
                self.viewer.writeDate()
                self.viewer.index.setPlainText(str(self.viewer.viewScanIndex))
                # For now, don't plot data because it slows down reading in
                # raw data file. This is post-processing mode, so in theory
                # Julie already saw all the scans during the flight. But
                # confirm her preference. TBD**
                # self.viewer.plotData()
                # If processScan is called with False, don't have data to
                # create a curtain plot.
                # self.viewer.updateCurtainPlot()

                self.viewer.app.processEvents()

        self.viewer.setScanIndex()
        self.closeRawFile()  # Done reading raw file, so close it

        # Now that selected file has been successfully loaded, replace the file
        # selection box with a timeseries plot widget
        self.textbox.close()
        self.lbl.close()
        self.plotTimeseries()

    def saveICARTT(self):
        """ Action to take when Save ICARTT button is clicked """
        filename = self.icartt.getICARTT()
        if filename is not None:
            if self.icartt.saveHeader(filename):  # Write header to output file
                self.icartt.saveData(filename)    # Write data to output file

                logger.printmsg("info", "File " + filename + " successfully " +
                                "written", "If file already existed, it was " +
                                "overwritten")

    def process(self):
        """ Action to take when Process button is clicked """
        self.show()

    def readSetup(self, prod_dir):
        """ Read the post-processing setup files """
        filenum = 0
        # Find all setup files in prod dir.
        for setupfile in sorted(os.listdir(prod_dir)):
            # Vet that this is a setup file, i.e. has name setup_rf##
            m = re.match("setup_[RTFrtf]f[0-9][0-9]", setupfile)
            if (m):
                # Add another entry to our list of file pairs
                self.filelist.append(copy.deepcopy(data_files))

                # Get the full path to the setup file
                filename = os.path.join(prod_dir, setupfile)

                # Read flight setup from setup file
                self.setupfile = config()
                self.setupfile.read(filename)

                # Save files needed for post-processing to post-processing dict
                # Prepend root dir to filename
                projdir = self.client.configfile.getProjDir()
                self.filelist[filenum]["rawFile"] = \
                    self.setupfile.prependDir('raw_file', projdir)

                self.filelist[filenum]["ncFile"] = \
                    self.setupfile.prependDir('nc_file', projdir)

                filenum += 1
