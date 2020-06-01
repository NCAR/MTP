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
from util.readGVnc import readGVnc
from proc.file_struct import data_files
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget, QAction, \
                            QListWidget, QLabel
from PyQt5.QtGui import QFont
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPprocessor(QMainWindow):

    def __init__(self, client, parent=None):
        """
        Create a window to be the post-flight processing environment.
        Requires access to a raw MTP data file and a final RAF Low-Rate (LRT)
        NetCDF file.
        """

        self.client = client

        super(MTPprocessor, self).__init__(parent)
        self.filelist = []

        self.initUI()

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
        menubar = self.menuBar()

        # Mac OS treats menubars differently. To get a similar outcome, we can
        # add the following line: menubar.setNativeMenuBar(False).
        menubar.setNativeMenuBar(False)

        # Add a menu option to load a flight file to process
        self.loadFlight = QAction('LoadFlight', self)
        self.loadFlight.setToolTip('Load data for a single flight')
        self.loadFlight.triggered.connect(self.flightSelectWindow)
        menubar.addAction(self.loadFlight)

        # Add a menu option to save final data
        self.saveButton = QAction('Save ICARTT', self)
        self.saveButton.setToolTip('Save Processed Data to an ICARTT file')
        self.saveButton.triggered.connect(self.saveICARTT)
        menubar.addAction(self.saveButton)
        self.icartt = ICARTT(self.client)

    def flightSelectWindow(self):
        # Create a QListWidget to hold the possible flights
        self.textbox = QListWidget(self)
        self.textbox.show()
        self.layout.addWidget(self.textbox, 1, 0)

        # Set monospace font to align text
        font = QFont("courier")               # Use a monospace font
        self.textbox.setFont(font)

        # # Add a title above the source station list
        lbl = QLabel("Available Flights")
        lbl.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.layout.addWidget(lbl, 0, 0)

        # Display stations in textbox
        for flight in self.filelist:
            # Display basename
            self.textbox.addItem(os.path.basename(flight["rawFile"]))

        # When user selects flight, make sure both the raw and nc files
        # exist on disk. If not, warn user and ask if they want to launch a
        # file selector or select a different flight. If select flight, remind
        # them to fix the setup file for future use.
        self.textbox.clicked.connect(self.setFile)

    def setFile(self):
        # The user should only be able to select one file at a time, but out
        # of an abundance of caution, check and warn user if not true.
        if len(self.textbox.selectedItems()) != 1:
            logger.printmsg("ERROR", "Please select a single flight")
        else:
            selectedRawFile = self.textbox.selectedItems()[0].text()
            # Find data_files dict that matches the selected file
            for flight in self.filelist:
                if re.match(os.path.basename(flight["rawFile"]),
                            selectedRawFile):
                    selectedRawFile = flight["rawFile"]
                    selectedNCfile = flight["ncFile"]

            self.gvreader = readGVnc()
            self.gvreader.getNGvalues(selectedNCfile)

    def saveICARTT(self):
        """ Action to take when Save ICARTT button is clicked """
        filename = self.icartt.getICARTT()
        if filename is not None:
            self.icartt.saveHeader(filename)  # Write header to output file
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
