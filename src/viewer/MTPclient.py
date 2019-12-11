###############################################################################
# This MTP client program runs on the user host, and receives the MTP and IWG
# data packets from the UDP feeds.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import os
import socket
import numpy
from util.readmtp import readMTP
from util.readiwg import readIWG
from util.decodePt import decodePt
from util.decodeM01 import decodeM01
from util.decodeM02 import decodeM02
from util.calcTBs import BrightnessTemperature
from util.retriever import Retriever
from util.tropopause import Tropopause
from util.profile_structs import TropopauseRecord
from lib.rootdir import getrootdir


class MTPclient():

    def __init__(self):

        self.udp_send_port = 32106  # from viewer to MTP
        self.udp_read_port = 32107  # from MTP to viewer
        self.iwg1_port = 7071       # IWG1 packets from GV

        # Location of default ascii_parms file
        self.ascii_parms = os.path.join(getrootdir(), 'config/ascii_parms')

        # FOR TESTING, set location of RCFdir to test dir
        self.RCFdir = os.path.join(getrootdir(), 'tests/test_data')

        # Check if RCFdir exists. If not, don't create Profile plot but let
        # real-time code continue
        if not os.path.isdir(self.RCFdir):
            # Launch a file selector for user to select correct RCFdir
            return(False)

        # instantiate an RCF retriever
        self.retriever = Retriever(self.RCFdir)

        # Hack-y stuff to get plot to scroll. pyqtgraph must have a better way
        # that I haven't found yet.
        # The MTP takes a scan about once every 17 seconds. Used to scroll
        # plotting

        # The width of the time window shown on the scrolling plot. Modify
        # plotWidth to change time interval. Eg:
        # 150 scans * 17s = 42.5 min
        # 106 scans * 17s = 30 min
        self.scanInterval = 17  # seconds per scan
        self.plotWidth = 106    # number of scans to plot

        self.xvals = []
        self.yvals = []
        (self.xvals, self.yvals) = self.initData()

        # When the GUI starts, the IWG plot defaults to scan average pressure
        # altitude vs time. User can then change to another var using the
        # dropdown.
        self.xvar = 'TIME'
        self.yvar = 'SAPALT'  # km

        # Instantiate an instance of an MTP reader
        self.reader = readMTP()

        # Instantiate an instance of an IWG reader. Have it point to the same
        # MTP dictionary as the MTP reader
        self.iwg = readIWG(self.ascii_parms, self.reader.getRawscan())

        # Create a public list of the variables in the Aline. Used to plot
        # timeseries of the variables.
        self.varlist = self.reader.getVarList('Aline')

    def initData(self):
        self.xvals = [0]*self.plotWidth    # Current X values being plotted
        # Necessary to get data to scroll. Before get good data, plot NANs
        self.yvals = [numpy.nan]*self.plotWidth
        return(self.xvals, self.yvals)

    def getIWGport(self):
        return(self.iwg1_port)

    def getUDPport(self):
        return(self.udp_read_port)

    def calcPt(self):
        """
        Calculate resistance and temperature
        that correspond to counts and save to MTP dictionary.
        """
        pt = decodePt(self.reader)
        pt.calcTemp()

    def calcM01(self):
        """
        Calculate voltage that correspond to counts and save to MTP dictionary.
        """
        m01 = decodeM01(self.reader)
        m01.calcVolts()

    def calcM02(self):
        """
        Calculate values from the counts to be displayed in the Engineering 3
        box. Save to the MTP dictionary.
        """
        m02 = decodeM02(self.reader)
        m02.calcVals()

    def getSCNT(self):
        """
        Return the contents of the Bline, which contains:
            MTP Scan Counts[Angle, Channel]
        """
        vals = self.reader.getVar('Bline', 'SCNT')
        return (vals)

    def getTB(self):
        """
        Return the calculated brightness temperatures from the Bline
        """
        return(self.reader.getCalcVal('Bline', 'SCNT', 'tb'))

    def calcTB(self):
        """
        Calculate the Brightness Temperature that corresponds to the scan
        counts in the B line, and save to the MTP dictionary.
        Requires TMIXCNTP temperature (which was called Tifa in the VB code),
        SAAT (called OAT - outside air temperature in the VB6 code) , and the
        MTP Scan Counts[Angle, Channel] (SCNT) array from the Bline.
        """
        rawscan = self.reader.getRawscan()
        Tifa = rawscan['Ptline']['values']['TMIXCNTP']['temperature']
        OAT = rawscan['Aline']['values']['SAAT']['val']  # Kelvin
        scnt = rawscan['Bline']['values']['SCNT']['val']

        tb = BrightnessTemperature()

        # Calculate the brightness temperatures for the latest scan counts
        # and save them back to the MTP data dictionary.
        rawscan['Bline']['values']['SCNT']['tb'] = \
            tb.TBcalculationRT(Tifa, OAT, scnt)

    def getTemplate(self, tbi):
        """
        Get the template brightness temperatures that best fit current scan

        BestWtdRCSet will be False if acaltkm is missing or negative
        """
        rawscan = self.reader.getRawscan()
        acaltkm = float(rawscan['Aline']['values']['SAPALT']['val'])  # km
        BestWtdRCSet = self.retriever.getRCSet(tbi, acaltkm)
        return(BestWtdRCSet)

    def getProfile(self, tbi, BestWtdRCSet):
        """
        Convert brightness temperatures to atmospheric temperature profiles
        by performing an inverse calculation of the radiative transfer model.
        Requires as input Retrieval Coefficient Files (RCFs). RCF files are
        templates that describe what a given RAOB profile would look like to
        the MTP instrument if the instrument were used to measure the
        atmosphere described by the profile. The weighted averaged retrieval
        coefficients from the RCF that best matches the current scan at the
        scan flight altitude are calculated.

        When the MTP instrument completes a scan of the atmosphere the scan
        counts are converted to Brightness Temperatures (in calcTBs.py). Using
        these, the "best match" RCF is found and it's corresponding Retrieval
        Coefficients are used to determine the atmospheric temperature profile.
        """

        # If have a best template (i.e. BestWtdRCSet is not False)
        if (BestWtdRCSet):
            ATP = self.retriever.retrieve(tbi, BestWtdRCSet)

            # Add dict to hold first tropopause to array of trops
            ATP['trop'].append(TropopauseRecord.copy())

            # Instantiate a tropopause class
            NUM_RETR_LVLS = self.retriever.rcf_set._RCFs[0].getNUM_RETR_LVLS()
            trop = Tropopause(ATP, NUM_RETR_LVLS)
            startTropIndex = 0

            #  Check if all the temperatures are missing. In this case, set all
            # derived params to NAN.
            if self.retriever.checkMissing(ATP):
                ATP['RCFIndex'] = numpy.nan
                ATP['RCFALT1Index'] = numpy.nan
                ATP['RCFALT2Index'] = numpy.nan
                ATP['RCFMRIndex'] = numpy.nan

                # Also set first (and only) tropopause to NAN
                ATP['trop'][0]['idx'] = numpy.nan
                ATP['trop'][0]['altc'] = numpy.nan
                ATP['trop'][0]['tempc'] = numpy.nan

            else:
                # Found a good MTP scan. RCF indices were set in the
                # retrieve function above so just need to calculate
                # tropopauses
                [ATP['trop'][0]['idx'], ATP['trop'][0]['altc'],
                 ATP['trop'][0]['tempc']] = trop.findTropopause(startTropIndex)

                # If found a tropopause, look for a second one
                if not numpy.isnan(ATP['trop'][0]['idx']):
                    # Add a dict to hold a second tropopause
                    ATP['trop'].append(TropopauseRecord.copy())

                    # findTropopause call will modify startTropIndex to be
                    # index of level to start looking for 2nd trop.
                    [ATP['trop'][1]['idx'], ATP['trop'][1]['altc'],
                     ATP['trop'][1]['tempc']] = \
                        trop.findTropopause(startTropIndex)

            return(True)

        else:
            return(False)  # Could not create a profile from this scan

    def getXY(self):
        """
        Return the latest x and y values. xvals and yvals contain the values
        for the desired plotWidth and scanInterval.
        """
        return (self.xvals, self.yvals)

    def connect(self):
        """ Connection to UDP data streams """
        # Connect to MTP data stream
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", self.udp_read_port))

        # Connect to IWG data stream
        self.sockI = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockI.bind(("0.0.0.0", self.iwg1_port))

    def getSocketFileDescriptor(self):
        """ Return the MTP socket file descriptor """
        return self.sock.fileno()

    def getSocketFileDescriptorI(self):
        """ Return the IWG socket file descriptor """
        return self.sockI.fileno()

    def readSocket(self):
        """ Read data from the UDP feed and save it to the data dictionary """
        # Listen for MTP packets
        data = self.sock.recv(1024).decode()
        # Listen for IWG packets
        dataI = self.sockI.recv(1024).decode()

        # Store data to data dictionary
        self.reader.parseAsciiPacket(data)  # Store to values
        self.reader.parseLine(data)   # Store to date and data
        self.iwg.parseIwgPacket(dataI)   # Store to values
        self.reader.parseLine(dataI)  # Store to date, data, and asciiPacket

        # Append new X value to end of list
        self.xvals.append(int(self.reader.getVar('Aline', self.xvar)))

        # First time through, populate list with fabricated X values before
        # first X value so plot will scroll
        if (self.xvals[0] == 0):
            self.xvals = list(range(self.xvals[self.plotWidth] -
                                    self.plotWidth*self.scanInterval,
                                    self.xvals[self.plotWidth],
                                    self.scanInterval))

        # Pop oldest X value off list
        if (len(self.xvals) > self.plotWidth):
            self.xvals.pop(0)

        # Append new Y value to end of list
        self.yvals.append(float(self.reader.getVar('Aline', self.yvar)))

        # Pop oldest Y value off list
        if (len(self.yvals) > self.plotWidth):
            self.yvals.pop(0)

    def close(self):
        """ Close UDP socket connections """
        # Close the connection to the MTP data stream
        if self.sock:
            self.sock.close()

        # Close the connection to the IWG data stream
        if self.sockI:
            self.sockI.close()
