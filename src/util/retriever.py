###############################################################################
# This class encapsulates the retrieval method which performs the inverse
# calculation of the radiative transfer model to take a set of brightness
# temperatures and generate the physical temperature profile.  It does so by
# using the RetrievalCoefficientFileSet class to obtain the weighted averaged
# retrieval coefficients from the RCF that best matches our scan at our
# flight altitude.
#
# A set of Retrieval Coefficient Files (RCFs) are currently written
# by the VB program RCCalc which takes RAOB data and converts it into
# Templates that describe what that RAOB profile would look like to the MTP
# instrument if the instrument was used to measure the atmosphere described
# by the profile.
#
# When the MTP instrument completes a scan of the atmosphere the scan counts
# are converted to Brightness Temperatures, using these the "best match"
# RCF is found and it's corresponding Retrieval Coefficients are used
# to determine the atmospheric temperature profile.
#
# The Microwave Temperature Profiler (MTP) instrument build by JPL for
# NCAR as part of the set of instruments known as HAIS (build specifically
# in support of the Haiper GV aircraft) came with processing software
# written in Visual Basic 6.0.
#
# Copyright 2015-2016 University Corporation for Atmospheric Research
#  - VB6 and Algorithm Copyright MJ Mahoney, NASA Jet Propulsion Laboratory
###############################################################################
import numpy
import math
from util.rcf_set import RetrievalCoefficientFileSet
from util.profile_structs import AtmosphericTemperatureProfile


class Retriever():

    def __init__(self, Directory, filelist=None):
        """
        Directory is directory name containing the RCF files to be used.
        """
        self.Directory = Directory

        self.rcf_set = RetrievalCoefficientFileSet()
        self.ATP = AtmosphericTemperatureProfile

        # Create a file set - this should only be called once at init
        try:
            self.rcf_set.getRCFs(self.Directory, filelist)
        except Exception:
            raise

    def getRCSet(self, ScanBTs, ACAltKm):
        """
        Get the best weighted RC Set that matches this scan

        ScanBTs is an array of floating point values indicating the brightness
        temperature values in Degrees Kelvin from the scan.  The first 10
        values are for channel 1 at each of the scan angles (highest angle to
        lowest angle), the second 10 are for channel 2 and the third 10 are for
        channel 3.

        ACAltKm is the floating point altitude of the aircraft in km
        """
        # If PALT is missing or negative, can't calculate altc, tempc, rcfidx,
        # rfalt1idx, etc. Return False
        if (numpy.isnan(ACAltKm) or ACAltKm < 0):
            raise Exception("Aircraft altitude must exist and be greater " +
                            "than zero to match template to scan")

        # If fileset created successfully, find the best template to match
        # the scanned brightness temperatures
        return self.rcf_set.getBestWeightedRCSet(ScanBTs, ACAltKm, 0.0)

    def retrieve(self, ScanBTs, BestWtdRCSet):
        """
        Retrieve function.  Obtain the Physical temperature profile from a scan

        ScanBTs is an array of floating point values indicating the brightness
        temperature values in Degrees Kelvin from the scan.  The first 10
        values are for channel 1 at each of the scan angles (highest angle to
        lowest angle), the second 10 are for channel 2 and the third 10 are for
        channel 3.

        """
        # Clear the Temperature/Altitude profile
        self.ATP['Temperatures'] = []
        self.PressureAlts = []
        self.ATP['Altitudes'] = []

        # Calculate the physical temperature profile
        self.NUM_RETR_LVLS = self.rcf_set._RCFs[0].getNUM_RETR_LVLS()
        for l in range(self.NUM_RETR_LVLS):
            Temperature = BestWtdRCSet['FL_RCs']['sRTav'][l]
            self.PressureAlts.append(BestWtdRCSet['FL_RCs']['sBPrl'][l])
            for j in range(self.rcf_set._RCFs[0].getNUM_BRT_TEMPS()):
                BtDiff = (ScanBTs[j] - BestWtdRCSet['FL_RCs']['sOBav'][j])
                Temperature = Temperature + \
                    (BestWtdRCSet['FL_RCs']['Src']
                                 [l * self.rcf_set._RCFs[0].getNUM_BRT_TEMPS()
                                  + j] * BtDiff)
            self.ATP['Temperatures'].append(Temperature)

        # Copy all elements from the returned vector to ATP['Altitudes']
        self.ATP['Altitudes'] = self.Pressure2Km(self.PressureAlts)

        # Index of best RCF file for this profile
        self.ATP['RCFIndex'] = BestWtdRCSet['RCFIndex']
        # Index of flight level below aircraft Altitude
        self.ATP['RCFALT1Index'] = BestWtdRCSet['FL_RCs']['RCFALT1Index']
        # Index of flight level above aircraft Altitude
        self.ATP['RCFALT2Index'] = BestWtdRCSet['FL_RCs']['RCFALT2Index']
        # Meridional Region Index: quality of match
        self.ATP['RCFMRIndex']['val'] = BestWtdRCSet['SumLnProb']

        # Any Temperature with Altitude <= 0 is not valid (nor is altitude)
        # If Temperature is NAN (regardless of Alt, set Alt to NAN. Do this
        # so code will output same number of Temperature and Altitude records.
        for l in range(self.NUM_RETR_LVLS):
            if (self.ATP['Altitudes'][l] <= 0 or numpy.isnan(
                    self.ATP['Temperatures'][l])):
                self.ATP['Altitudes'][l] = numpy.nan
                self.ATP['Temperatures'][l] = numpy.nan

        return self.ATP

    def checkMissing(self, ATP):
        """
        Check if all the temperatures are missing. If they are, then we will
        need to set all the derived parameters to missing.
        """
        nMissMTP = 0  # Initialize
        for i in range(self.NUM_RETR_LVLS):
            if (numpy.isnan(self.ATP['Temperatures'][i])):
                nMissMTP += 1

        if (nMissMTP == self.NUM_RETR_LVLS):
            # All temperatures are missing
            return True
        else:
            return False

    def Pressure2Km(self, Pressures):
        """
        MJ's rather elaborate way of converting from pressure altitude to km
        """
        Altitudes = []
        for pit in Pressures:
            if (pit > 226.3206):  # < 11km
                Altitude = 44.3307692307692 * \
                           (1.0 - pow((pit / 1013.25), 0.190263235151657))
            elif (pit > 54.7488):  # < 20km
                Altitude = 11.0 - (6.34161998393947 * math.log(pit / 226.3206))
            elif (pit > 8.680185):  # < 32km
                Altitude = 20.0 - (216.65 * (1.0 - pow((pit / 54.7488),
                                                       -0.0292712699464088)))
            elif (pit > 1.109063):  # < 47km
                Altitude = 32.0 - (81.6607142857143 *
                                   (1.0 - pow((pit / 8.680185),
                                              -0.0819595474499447)))
            elif (pit > 0.6693885):  # < 51km
                Altitude = 47.0 - (7.92226839904554 * math.log(pit / 1.109063))
            elif (pit > 0.03956419):  # <71 km
                Altitude = 51.0 + (96.6607142857143 *
                                   (1.0 - pow((pit / 0.6693885),
                                              (0.0819595474499447))))
            elif (pit > 1.45742511874549E-03):  # 90 km
                Altitude = 71.0 + (107.325 *
                                   (1.0 - pow((pit / 0.03956419),
                                              (5.85425338928176E-02))))
            elif (pit > 5.8654139565495E-04):  # <95 km
                Altitude = 84.852 - (5.47214624555127 *
                                     math.log(pit / 0.003733834))
            elif (pit > 2.40645796828482E-04):  # <100 km
                Altitude = 95.0 - (140.597 *
                                   (1.0 - pow((pit / 5.8654139565495E-04),
                                              (-3.92234986852218E-02))))
            elif (pit > 1.03251578598705E-04):  # <105 km
                Altitude = 100.0 - (71.20438 *
                                    (1.0 - pow((pit / 2.40645796828482E-04),
                                               (-8.02032717123127E-02))))
            elif (pit > 4.81695302325482E-05):  # <110 km
                Altitude = 105.0 - (33.46154 *
                                    (1.0 - pow((pit / 1.03251578598705E-04),
                                               (-0.18265269904593))))
            else:
                if (pit <= 0):
                    pit = 0.000001
                Altitude = 110.0 - (20.0 *
                                    (1.0 - pow((pit / 4.81695302325482E-05),
                                               (-0.351255203356906))))

            Altitudes.append(Altitude)

        return Altitudes


if __name__ == "__main__":
    Directory = "/Users/janine/dev/projects/CSET/MTP/RCF"
    retr = Retriever(Directory)
