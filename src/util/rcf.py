###############################################################################
# This class provides for reading in an RCF, storing and providing access to
# its data.
#
# Retrieval Coefficient Files (RCFs) are currently written by the VB program
# RCCalc which takes RAOB data and converts it into Templates that describe
# what that RAOB profile would look like to the MTP instrument if the
# instrument was used to measure the atmosphere described by the profile.
#
# Since the profile would appear differently to the MTP depending upon
# the altitude at which the instrument was performing the measurement, the
# RCF files have multiple flight levels containing expected brightness
# temperatures (observables), associated rms values and the retrieval
# coefficients that would allow one to convert from the brightness
# temperatures to the profile temperatures.
#
# Translation from VB6 to CPP by Tom Baltzer 2015 - most comments from this
# version (http://svn.eol.ucar.edu/websvn/listing.php?repname=raf&path=%2Ftrunk
# %2Finstruments%2Fmtp%2Fsrc%2Fmtpbin%2F&#a816c0189d88386950eb4da700bf32166
#
# Translation from CPP to Python by Janine Aquino
#
# Written in Python 3
#
# Copyright University Corporation for Atmospheric Research 2019
# VB6 and Algorithm Copyright MJ Mahoney, NASA Jet Propulsion Laboratory
###############################################################################
import os
import copy
import struct
import inspect
from util.rcf_structs import RCF_HDR, RCF_FL
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class RetrievalCoefficientFile():

    def __init__(self, Filename):
        """ Constructor """
        self._RCFHdr = copy.deepcopy(RCF_HDR)
        self._RCFFileName = Filename

        # Extract the RCFId from the full file path.
        self._RCFId = os.path.splitext(os.path.basename(self._RCFFileName))[0]

        # Open the RCF file
        try:
            self.openRCF()  # Open the RCF file
        except Exception:
            raise  # Pass error back up to calling function

        self.getRCF()  # Read in header

        # Sanity check that header read is working
        if not self.testFlightLevelsKm():
            logger.error("Major failure reading RCF header for " +
                         "file" + Filename + ", exiting")
            exit(1)

        self.NUM_BRT_TEMPS = self._RCFHdr['Nlo'] * self._RCFHdr['Nel']
        self.NUM_RETR_LVLS = self._RCFHdr['Nret']

        # Read in each of the flight levels
        self._RCFFl = []  # Array of dictionaries to hold the flight levels
        for i in range(self._RCFHdr['NFL']):  # Number of Flight Levels
            self._RCFFl.append(copy.deepcopy(RCF_FL))
            self.get_FL(i)

        self.closeRCF()

    def openRCF(self):
        """ Open the RCF file as binary """
        try:
            self.rcf = open(self._RCFFileName, "rb")
        except Exception:
            raise  # Unable to open file. Pass err back up to calling function

    def closeRCF(self):
        """ If RCF file is open, close it """
        try:
            self.rcf.close()
        except Exception as err:
            logger.error(err + " Unable to close file " + self._RCFFileName)
            return(False)

    def getNUM_BRT_TEMPS(self):
        """ Return the number of brightness temperatures from this RCF file """
        return(self.NUM_BRT_TEMPS)

    def getNUM_RETR_LVLS(self):
        """ Return the number of retrieval levels from this RCF file """
        return(self.NUM_RETR_LVLS)

    def getRCF(self):
        """
        Unpack the binary values into the RCF_HDR dictionary
        A type of 'H' is unsigned short, 'f' is float
        """
        self._RCFHdr['RCformat'] = struct.unpack('H', self.rcf.read(2))[0]
        # Tom never figured out how to decode CreationDateTime. So read bytes
        # into struct and let them sit.
        self._RCFHdr['CreationDateTime'] = self.rcf.read(8)
        self._RCFHdr['RAOBfilename'] = self.rcf.read(80).decode()
        self._RCFHdr['RCfilename'] = self.rcf.read(80).decode()
        self._RCFHdr['RAOBcount'] = struct.unpack('H', self.rcf.read(2))[0]
        self._RCFHdr['LR1'] = struct.unpack('f', self.rcf.read(4))[0]
        self._RCFHdr['zLRb'] = struct.unpack('f', self.rcf.read(4))[0]
        self._RCFHdr['LR2'] = struct.unpack('f', self.rcf.read(4))[0]
        self._RCFHdr['RecordStep'] = struct.unpack('f', self.rcf.read(4))[0]
        self._RCFHdr['RAOBmin'] = struct.unpack('f', self.rcf.read(4))[0]
        self._RCFHdr['ExcessTamplitude'] = \
            struct.unpack('f', self.rcf.read(4))[0]
        # Number of observables
        self._RCFHdr['Nobs'] = struct.unpack('H', self.rcf.read(2))[0]
        # Number of retrieval levels (Nret)
        self._RCFHdr['Nret'] = struct.unpack('H', self.rcf.read(2))[0]
        # Array of retrieval offset levels wrt flight level
        for i in range(self._RCFHdr['Nret']):
            self._RCFHdr['dZ'].append(struct.unpack('f', self.rcf.read(4))[0])
        # Number of flight levels (NFL)
        self._RCFHdr['NFL'] = struct.unpack('H', self.rcf.read(2))[0]
        # Array of flight levels (Km)
        for i in range(20):
            self._RCFHdr['Zr'].append(struct.unpack('f', self.rcf.read(4))[0])
        # Number of LO channels
        self._RCFHdr['Nlo'] = struct.unpack('H', self.rcf.read(2))[0]
        # LO frequencies (GHz)
        for i in range(self._RCFHdr['Nlo']):
            self._RCFHdr['LO'].append(struct.unpack('f', self.rcf.read(4))[0])
        # Scan mirror elevation angles
        self._RCFHdr['Nel'] = struct.unpack('H', self.rcf.read(2))[0]
        for i in range(self._RCFHdr['Nel']):
            self._RCFHdr['El'].append(struct.unpack('f', self.rcf.read(4))[0])
        # IF frequency offsets (GHz)
        self._RCFHdr['Nif'] = struct.unpack('H', self.rcf.read(2))[0]
        for i in range(48):
            self._RCFHdr['IFoff'].append(struct.unpack('f',
                                                       self.rcf.read(4))[0])
        for i in range(48):
            self._RCFHdr['IFwt'].append(struct.unpack('f',
                                                      self.rcf.read(4))[0])
        # Spare
        self._RCFHdr['Spare'] = struct.unpack('f'*130, self.rcf.read(4*130))
        self._RCFHdr['SURC'] = self.rcf.read(4).decode()
        for i in range(3):
            self._RCFHdr['CHnLSBloss'].append(
                struct.unpack('f', self.rcf.read(4))[0])
        self._RCFHdr['RAOBbias'] = struct.unpack('f', self.rcf.read(4))[0]
        self._RCFHdr['CH1LSBloss'] = struct.unpack('f', self.rcf.read(4))[0]
        for i in range(15*3*10):
            self._RCFHdr['SmatrixN1'].append(
                struct.unpack('f', self.rcf.read(4))[0])
        for i in range(15*3*10):
            self._RCFHdr['SmatrixN2'].append(
                struct.unpack('f', self.rcf.read(4))[0])

    def get_FL(self, lvl):
        """
        lvl is the index of the flight level

        Because I am copying the dictionary from the previous flight level to
        create this level, I need to clear it before appending new data.
        """
        self._RCFFl[lvl]['sBP'] = struct.unpack('f', self.rcf.read(4))[0]

        self._RCFFl[lvl]['sOBrms'] = []
        for i in range(self.NUM_BRT_TEMPS):
            self._RCFFl[lvl]['sOBrms'].append(
                struct.unpack('f', self.rcf.read(4))[0])

        self._RCFFl[lvl]['sOBav'] = []
        for i in range(self.NUM_BRT_TEMPS):
            self._RCFFl[lvl]['sOBav'].append(
                struct.unpack('f', self.rcf.read(4))[0])

        self._RCFFl[lvl]['sBPrl'] = []
        for i in range(self.NUM_RETR_LVLS):
            self._RCFFl[lvl]['sBPrl'].append(
                struct.unpack('f', self.rcf.read(4))[0])

        self._RCFFl[lvl]['sRTav'] = []
        for i in range(self.NUM_RETR_LVLS):
            self._RCFFl[lvl]['sRTav'].append(
                struct.unpack('f', self.rcf.read(4))[0])

        self._RCFFl[lvl]['sRMSa'] = []
        for i in range(self.NUM_RETR_LVLS):
            self._RCFFl[lvl]['sRMSa'].append(
                struct.unpack('f', self.rcf.read(4))[0])

        self._RCFFl[lvl]['sRMSe'] = []
        for i in range(self.NUM_RETR_LVLS):
            self._RCFFl[lvl]['sRMSe'].append(
                struct.unpack('f', self.rcf.read(4))[0])

        self._RCFFl[lvl]['Src'] = []
        for i in range(self.NUM_BRT_TEMPS * self.NUM_RETR_LVLS):
            self._RCFFl[lvl]['Src'].append(
                struct.unpack('f', self.rcf.read(4))[0])

        self._RCFFl[lvl]['Spare'] = []
        for i in range(67):
            self._RCFFl[lvl]['Spare'].append(
                struct.unpack('f', self.rcf.read(4))[0])

        # Convert Retrieval coefficients from column major storage
        temp = self._RCFFl[lvl]['Src'].copy()
        for j in range(self.NUM_BRT_TEMPS):
            for i in range(self.NUM_RETR_LVLS):
                self._RCFFl[lvl]['Src'][i*self.NUM_BRT_TEMPS + j] = \
                    temp[j*self.NUM_RETR_LVLS + i]

    def getId(self):
        """ Return a string containing the RCF ID """
        return(self._RCFId)

    def getFileName(self):
        """ Return a string containing the name of the RCF file """
        return(self._RCFFileName)

    def getRCF_HDR(self):
        """
        When using getRCF_HDR, be advised that char arrays have no endstring!
        """
        return(self._RCFHdr)

    def getFL_RC_Vec(self):
        return(self._RCFFl)

    def getRCAvgWt(self, PAltKm):
        """
        Get the weighted average Retrieval Coefficient Set
        PAltKm  = pressure altitude in KM at which to weight the elements
        of the set: the observables and rmms vectors as well as the retrieval
        coefficient matrices from flight levels above and below PAltKm are
        averaged with a weight factor based on nearness of PAltkm to the
        pressure altitude of the flight level as described in the RCF header.
        """
        RcSetAvWt = copy.deepcopy(RCF_FL)
        # print(RcSetAvWt['Src'])  # I want this to be empty at this point

        # First check to see if PAltKm is outside the range of Flight Level
        # PAltKms
        #  - if so then the weighted average observable will be the average
        #    observable associated with the flight level whose PAltKm is
        #    closest. Assumption is that the Flight Level Retrieval Coefficient
        #    Set vector is stored in increasing Palt (decreasing aircraft
        #    altitude). Zr contains the most common aircraft flight levels

        # If aircraft level is above highest flight level
        if PAltKm >= self._RCFHdr['Zr'][0]:
            RcSetAvWt['sBP'] = self._RCFFl[0]['sBP']
            for j in range(self.NUM_RETR_LVLS):
                RcSetAvWt['sBPrl'].append(self._RCFFl[0]['sBPrl'][j])
                RcSetAvWt['sRTav'].append(self._RCFFl[0]['sRTav'][j])
                RcSetAvWt['sRMSa'].append(self._RCFFl[0]['sRMSa'][j])
                RcSetAvWt['sRMSe'].append(self._RCFFl[0]['sRMSe'][j])
            for i in range(self.NUM_BRT_TEMPS):
                RcSetAvWt['sOBav'].append(self._RCFFl[0]['sOBav'][i])
                RcSetAvWt['sOBrms'].append(self._RCFFl[0]['sOBrms'][i])
                for j in range(self.NUM_RETR_LVLS):
                    RcSetAvWt['Src'].append(
                        self._RCFFl[0]['Src'][j * self.NUM_BRT_TEMPS + i])
            return RcSetAvWt

        # If aircraft level is below lowest flight level
        if (PAltKm <= self._RCFHdr['Zr'][self._RCFHdr['NFL']-1]):
            RcSetAvWt['sBP'] = self._RCFFl[self._RCFHdr['NFL']-1]['sBP']
            for j in range(self.NUM_RETR_LVLS):
                RcSetAvWt['sBPrl'].append(
                    self._RCFFl[self._RCFHdr['NFL']-1]['sBPrl'][j])
                RcSetAvWt['sRTav'].append(
                    self._RCFFl[self._RCFHdr['NFL']-1]['sRTav'][j])
                RcSetAvWt['sRMSa'].append(
                    self._RCFFl[self._RCFHdr['NFL']-1]['sRMSa'][j])
                RcSetAvWt['sRMSe'].append(
                    self._RCFFl[self._RCFHdr['NFL']-1]['sRMSe'][j])
            for i in range(self.NUM_BRT_TEMPS):
                RcSetAvWt['sOBav'].append(
                    self._RCFFl[self._RCFHdr['NFL']-1]['sOBav'][i])
                RcSetAvWt['sOBrms'].append(
                    self._RCFFl[self._RCFHdr['NFL']-1]['sOBrms'][i])
                for j in range(self.NUM_RETR_LVLS):
                    RcSetAvWt['Src'].append(
                        self._RCFFl[self._RCFHdr['NFL']-1]['Src'][j * self.
                                                                  NUM_BRT_TEMPS
                                                                  + i])
            return RcSetAvWt

        # Find two Flight Level Sets that are above and below the PAltKm
        # provided.  Calculate the weight for averaging and identify the RC
        # sets.
        BotWt = 0.0
        i = 0
        for it in range(self._RCFHdr['NFL']):
            if (PAltKm <= self._RCFHdr['Zr'][i] and
                    PAltKm >= self._RCFHdr['Zr'][i+1]):
                BotWt = 1.0 - ((PAltKm - self._RCFHdr['Zr'][i + 1]) /
                               (self._RCFHdr['Zr'][i] -
                                self._RCFHdr['Zr'][i + 1]))
                Topit = self._RCFFl[it]
                Botit = self._RCFFl[it + 1]
            i += 1
        TopWt = 1.0 - BotWt

        # Save the indices of the flight level sets used in averages
        RcSetAvWt['RCFALT1Index'] = it  # index of Topit
        RcSetAvWt['RCFALT2Index'] = it + 1  # index of Botit

        # Calculate the Weighted averages
        RcSetAvWt['sBP'] = Botit['sBP'] * BotWt + Topit['sBP'] * TopWt
        for j in range(self.NUM_RETR_LVLS):
            RcSetAvWt['sBPrl'].append(
                Botit['sBPrl'][j] * BotWt + Topit['sBPrl'][j] * TopWt)
            RcSetAvWt['sRTav'].append(
                Botit['sRTav'][j]*BotWt + Topit['sRTav'][j] * TopWt)
            RcSetAvWt['sRMSa'].append(
                Botit['sRMSa'][j]*BotWt + Topit['sRMSa'][j] * TopWt)
            RcSetAvWt['sRMSe'].append(
                Botit['sRMSe'][j]*BotWt + Topit['sRMSe'][j] * TopWt)

        for i in range(self.NUM_BRT_TEMPS):
            RcSetAvWt['sOBrms'].append(
                Botit['sOBrms'][i] * BotWt + Topit['sOBrms'][i] * TopWt)
            RcSetAvWt['sOBav'].append(
                Botit['sOBav'][i] * BotWt + Topit['sOBav'][i] * TopWt)

        for j in range(self.NUM_RETR_LVLS):
            for i in range(self.NUM_BRT_TEMPS):
                RcSetAvWt['Src'].append(
                    Botit['Src'][j * self.NUM_BRT_TEMPS + i] * BotWt +
                    Topit['Src'][j * self.NUM_BRT_TEMPS + i] * TopWt)

        return RcSetAvWt

    def testFlightLevelsKm(self, FlightLevels=[], Len=-1):
        """
        Test that Flight Levels (KM) are as expected.

        FlightLevels is a vector of floating point values indicating the km
        above sea level of each flight level in the retrieval coefficient file.
        Flight levels should be ordered in decreasing altitude.

        Returns true if levels successfully set, false if not.
        """

        # Test that len of the flight levels list is as expected.
        if (Len != -1 and Len != self._RCFHdr['NFL']):
            logger.error("In " + inspect.stack()[0][3] + " for " +
                         "RCFID: " + self.getId() + ", number of flight " +
                         "levels input - " + str(Len) + " - is not equal " +
                         "to number in RCF - " + str(self._RCFHdr['NFL']))
            return(False)

        # Test that the flight levels are in decreasing order
        for i in range(Len):
            if ((i+1 < Len) and
                    (self._RCFHdr['Zr'][i] <= self._RCFHdr['Zr'][i+1])):
                logger.error("In " + inspect.stack()[0][3] +
                             " for RCFID: " + self.getId() + ", flight " +
                             "levels are not in decreasing altitude.")
                return(False)

        # Add test for flight levels of current rcf equal to flight levels
        # passed in to this fn. This is used by rcf_set to confirm all RCFs in
        # a set have the same flight levels.
        if len(FlightLevels) != 0:
            for i in range(Len):
                if self._RCFHdr['Zr'][i] != FlightLevels[i]:
                    logger.error("In " + inspect.stack()[0][3] +
                                 " for RCFID: " + self.getId() + ", " +
                                 "flight levels are not as expected.")
                    return(False)

        return(True)


if __name__ == "__main__":
    filename = "/Users/janine/dev/projects/CSET/MTP/RCF/NRCKA068.RCF"
    rcf = RetrievalCoefficientFile(filename)
