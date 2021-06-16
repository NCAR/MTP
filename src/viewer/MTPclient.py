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
import logging
import argparse
from util.readmtp import readMTP
from util.readiwg import IWG
from util.readascii_parms import AsciiParms
from util.decodePt import decodePt
from util.decodeM01 import decodeM01
from util.decodeM02 import decodeM02
from util.calcTBs import BrightnessTemperature
from util.retriever import Retriever
from util.tropopause import Tropopause
from lib.rootdir import getrootdir
from lib.config import config
from EOLpython.util.fileselector import FileSelector
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPclient():

    def __init__(self):

        # Instantiate an instance of an MTP reader
        self.reader = readMTP()

    def config(self, configfile_name):
        """ Read in config file and set up a bunch of stuff """
        self.configfile_name = configfile_name
        # Read the config file. Gets path to RCF dir
        self.readConfig(configfile_name)

        self.checkRCF()  # Check that RCF file exists

        # Instantiate an IWG reader. Needs path to ascii_parms file.
        self.initIWG()

        # Instantiate an RCF retriever
        # If this fails, code will crash, so exit gracefully
        try:
            self.initRetriever()
        except Exception:
            exit(1)

    def connect_udp(self):
        # Connect to the MTP and IWG UDP feeds
        self.connectMTP()
        self.connectIWG()

    def parse_args(self):
        """ Instantiate a command line argument parser """

        # Define command line arguments which can be provided
        parser = argparse.ArgumentParser(
            description="Script to display and process MTP scans")
        parser.add_argument(
            '--config', type=str,
            required=True,
            help='File containing project-specific MTP configuration info. ' +
            'Defaults to config/proj.yml in code checkout for testing')
        parser.add_argument(
            '--debug', dest='loglevel', action='store_const',
            const=logging.DEBUG, default=logging.INFO,
            help="Show debug log messages")
        parser.add_argument(
            '--logmod', type=str, default=None, help="Limit logging to " +
            "given module")
        parser.add_argument(
            '--cnts', dest='cnts', action='store_const', const=True,
            help='Plot counts instead of scan/template. Useful for testing')
        parser.add_argument(
            '--rt', dest='realtime', action='store_const', const=True,
            default=False, help='Run in real-time monitoring mode.')

        # Parse the command line arguments
        args = parser.parse_args()

        return(args)

    def initIWG(self):
        """
        Instantiate an instance of an IWG reader. Have it point to the same MTP
        dictionary as the MTP reader. Requires the location of the ascii_parms
        file.
        """
        # Initialize the IWG reader
        self.iwg = IWG(self.reader.getRawscan())

        # Init and open ascii parms file
        status = True
        self.ascii_parms = AsciiParms(self.getAsciiParms())
        # Attempt to open ascii_parms file. Exit on failure.
        if self.ascii_parms.open() is False:
            exit(1)

        while status:
            # Read var from ascii_parms file
            newVar = self.ascii_parms.readVar()

            # Save to IWG section of dictionary
            status = self.iwg.createPacket(newVar)

        self.ascii_parms.close()

        return(self.iwg)

    def readConfig(self, filename):
        # Read config from config file
        self.configfile = config()
        self.configfile.read(filename)

        # udp_send_port is port from viewer to MTP
        self.udp_send_port = self.configfile.getInt('udp_send_port')
        # udp_read_port is from MTP to viewer
        self.udp_read_port = self.configfile.getInt('udp_read_port')
        # port to receive IWG1 packets from GV
        self.iwg1_port = self.configfile.getInt('iwg1_port')

        # Config for current MTP setup
        # Number of scan angles being read
        self.NUM_SCAN_ANGLES = self.configfile.getInt('NUM_SCAN_ANGLES')
        # Number of channels being read
        self.NUM_CHANNELS = self.configfile.getInt('NUM_CHANNELS')

        # Location of RCF dir
        self.RCFdir = self.configfile.getPath('RCFdir')

        # List of RCF files, if defined
        self.filelist = self.configfile.getVal('filelist')

    def checkRCF(self):
        """
        Check if RCFdir exists. If not, prompt user to select correct RCFdir
        """
        if not os.path.isdir(self.RCFdir):
            logger.printmsg("ERROR", "RCF dir " + self.RCFdir + " doesn't " +
                            "exist.", "Click OK to select correct dir. Don't" +
                            " forget to update config file with correct dir " +
                            "path")
            # Launch a file selector for user to select correct RCFdir
            # This should really be done in MTPviewer, with a non-GUI option
            # for command-line mode.
            self.loader = FileSelector()
            self.loader.set_filename("loadRCFdir", getrootdir())
            self.RCFdir = os.path.join(getrootdir(), self.loader.get_file())

    def getAsciiParms(self):
        """ Return path to ascii_parms file """
        try:
            return(self.configfile.getPath('ascii_parms'))
        except Exception:
            exit(1)

    def getProj(self):
        """ Return the project name of the current project from config file """
        try:
            return(self.configfile.getVal('project'))
        except Exception:
            exit(1)

    def getFltno(self):
        """ Return the flight number of the current flight from config file """
        try:
            return(self.configfile.getVal('fltno'))
        except Exception:
            exit(1)

    def initRetriever(self):
        """ instantiate an RCF retriever """
        try:
            self.retriever = Retriever(self.RCFdir, self.filelist)
        except Exception:
            raise

    def setRCFdir(self, Dir):
        """ Only used during testing """
        self.RCFdir = os.path.join(getrootdir(), Dir)

    def getIWGport(self):
        return(self.iwg1_port)

    def getUDPport(self):
        return(self.udp_read_port)

    def getTBI(self):
        """ Return the inverted brightness temperature array """
        return(self.reader.getTBI())

    def clearData(self):
        """ Clear the flight dictionary and JSON file on disk """
        # Remove everything from flightData
        self.reader.clearFlightData()

        # Delete the JSON file on disk
        self.reader.removeJSON(self.getMtpRealTimeFilename())

    def saveData(self):
        """
        Save current record to flight dictionaries and to JSON file on disk
        """
        # Append to array of dictionaries that holds entire flight
        self.reader.archive()

        # Append to JSON file on disk
        self.reader.save(self.getMtpRealTimeFilename())

    def getMtpRealTimeFilename(self):
        """
        Automatically generate JSON filename that includes the project and
        flight number.
        """

        # Get project dir from config. If dir not set, default to test dir
        projdir = self.configfile.getProjDir()

        return(self.reader.getJson(projdir, self.getProj(), self.getFltno()))

    def processScan(self):
        """
        Perform calculations on latest scan to convert counts to brightness
        temperature. Slice and dice the raw scan to save it and TB values to
        dictionary for current scan.
        """
        self.calcPt()  # Calculate resistance and temperatures from the Pt line
        self.calcM01()  # Calculate the voltage from the M01 line
        self.calcM02()  # Calculate the values from the M02 line

        # Calculate the brightness temperature from the Bline.
        # Uses the temperature from the Pt line so must be called after
        # callling calcPt()
        self.calcTB()

        # Invert the brightness temperature to column major storage
        tb = self.getTB()
        self.tbi = self.invertArray(tb)  # inverted brightness temperature
        self.reader.saveTBI(self.tbi)

    def createProfile(self):
        """ Perform retrieval and derive the physical temperature profile """
        # Perform retrieval for a single scan
        try:
            self.BestWtdRCSet = self.getTemplate(self.getTBI())
        except Exception:
            raise  # Pass error back up to calling function

        # If retrieval succeeded, get the physical temperature profile (and
        # find the tropopause). Save everything to current rawscan dictionary
        self.reader.saveBestWtdRCSet(self.BestWtdRCSet)

        self.ATP = self.getProfile(self.getTBI(), self.BestWtdRCSet)
        self.reader.saveATP(self.ATP)

    def getBestWtdRCSet(self):
        """ Return the best weighted RC set """
        return(self.reader.getBestWtdRCSet())

    def getATP(self):
        """ Return the ATP profile and metadata """
        return(self.reader.getATP())

    def createRecord(self):
        """ Generate the data strings for each data line and save to dict """
        self.reader.createAdata()  # Create the A data string
        self.reader.createBdata()  # Create the B data string
        self.reader.createM01data()  # Create the M01 data string
        self.reader.createM02data()  # Create the M02 data string
        self.reader.createPtdata()  # Create the Pt data string
        self.reader.createEdata()  # Create the E data string

    def getTemplate(self, tbi):
        """
        Get the template brightness temperatures that best correspond to scan
        brightness temperatures.
        BestWtdRCSet will be False if acaltkm is missing or negative
        """
        rawscan = self.reader.getRawscan()
        acaltkm = float(rawscan['Aline']['values']['SAPALT']['val'])  # km
        try:
            BestWtdRCSet = self.retriever.getRCSet(tbi, acaltkm)
            return(BestWtdRCSet)
        except Exception:
            raise

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

        # Check if self.configfile exists. If not, call readConfig.
        try:
            self.configfile
        except NameError:
            self.readConfig(self.configfile_name)

        tb = BrightnessTemperature(self.configfile)

        # Calculate the brightness temperatures for the latest scan counts
        # and save them back to the MTP data dictionary.
        rawscan['Bline']['values']['SCNT']['tb'] = \
            tb.TBcalculationRT(Tifa, OAT, self.getSCNT())

    def invertArray(self, array):
        """
        SCNT values are stored in MTP raw data file (in the Bline) as
        cnts[angle, channel], i.e. {a1c1,a1c2,a1c3,a2c1,...}. SCNT values and
        calculated brightness temperatures are stored in the MTPrecord
        dictionaryi Bline as fn[angle, channel]. Some processing steps require,
        and the final data are output as {c1a1,c1a2,c1a3,c1a4,...}.
        This function inverts the array[angle, channel] passed to it.
        """
        array_inv = [numpy.nan]*(self.NUM_SCAN_ANGLES * self.NUM_CHANNELS)
        for j in range(self.NUM_SCAN_ANGLES):
            for i in range(self.NUM_CHANNELS):
                # The scan counts are passed in as a string, so convert them
                # to integers. The scan brightness temperatures come in as
                # float so leave them.
                if (isinstance(array[j*self.NUM_CHANNELS+i], str)):
                    array_inv[i*self.NUM_SCAN_ANGLES+j] = \
                        int(array[j*self.NUM_CHANNELS+i])
                else:
                    array_inv[i*self.NUM_SCAN_ANGLES+j] = \
                        array[j*self.NUM_CHANNELS+i]
        return(array_inv)

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
                ATP['RCFMRIndex']['val'] = numpy.nan

                # Also set first (and only) tropopause to NAN
                ATP['trop']['val'][0]['idx'] = numpy.nan
                ATP['trop']['val'][0]['altc'] = numpy.nan
                ATP['trop']['val'][0]['tempc'] = numpy.nan

            else:
                # Found a good MTP scan. RCF indices were set in the
                # retrieve function above so just need to calculate
                # tropopauses
                [startTropIndex, ATP['trop']['val'][0]['idx'],
                 ATP['trop']['val'][0]['altc'],
                 ATP['trop']['val'][0]['tempc']] = \
                 trop.findTropopause(startTropIndex)

                # If found a tropopause, look for a second one
                if not numpy.isnan(ATP['trop']['val'][0]['idx']):
                    # Start at previous index
                    [startTropIndex, ATP['trop']['val'][1]['idx'],
                     ATP['trop']['val'][1]['altc'],
                     ATP['trop']['val'][1]['tempc']] = \
                        trop.findTropopause(startTropIndex)

            return(ATP)

        else:
            return(False)  # Could not create a profile from this scan

    def connectMTP(self):
        """ Connection to UDP data streams """
        # Connect to MTP data stream
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", self.udp_read_port))

    def connectIWG(self):
        # Connect to IWG data stream
        self.sockI = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockI.bind(("0.0.0.0", self.iwg1_port))

    def getSocketFileDescriptor(self):
        """ Return the MTP socket file descriptor """
        return self.sock.fileno()

    def getSocketFileDescriptorI(self):
        """ Return the IWG socket file descriptor """
        return self.sockI.fileno()

    def readSocketI(self):
        # Listen for IWG packets
        dataI = self.sockI.recv(1024).decode()

        # Store IWG record to values field in data dictionary
        status = self.iwg.parseIwgPacket(dataI, self.getAsciiParms())
        if status is True:  # Successful parse if IWG packet
            self.reader.parseLine(dataI)  # Store to date, data, & asciiPacket

    def readSocket(self):
        """ Read data from the UDP feed and save it to the data dictionary """
        # Listen for MTP packets
        data = self.sock.recv(1024).decode()

        # Store data to data dictionary
        self.reader.parseAsciiPacket(data)  # Store to values

    def close(self):
        """ Close UDP socket connections """
        # Close the connection to the MTP data stream
        if self.sock:
            self.sock.close()

    def closeI(self):
        # Close the connection to the IWG data stream
        if self.sockI:
            self.sockI.close()
