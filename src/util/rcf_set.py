###############################################################################
# This class encapsulates the whole set of RCFs for a project and provides
# a method for determining which of the RCFs is the best match of a given
# set of brightness temperatures (scan) taken at a particular elevation.
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
# Translation from VB6 to CPP by Tom Baltzer 2015 - most comments from this
# version (http://svn.eol.ucar.edu/websvn/listing.php?repname=raf&path=%2Ftrunk
# %2Finstruments%2Fmtp%2Fsrc%2Fmtpbin%2F&#a816c0189d88386950eb4da700bf32166)
#
# Translation from CPP to Python by Janine Aquino
#
# Written in Python 3
#
# Copyright University Corporation for Atmospheric Research 2019
# VB6 and Algorithm Copyright MJ Mahoney, NASA Jet Propulsion Laboratory
###############################################################################
import os
import math
import inspect
from util.rcf_structs import RC_Set_4Retrieval
from util.rcf import RetrievalCoefficientFile
from Qlogger.messageHandler import QLogger as logger


class RetrievalCoefficientFileSet():

    def __init__(self):
        """
        Instantiate an RCF file set

        Directory is directory name containing the RCF files to be
        pulled into the set.

        filelist is an optional list of requested RCF files. Used to limit RCF
        files available for "best match" to a subset of those available in the
        Directory.
        """
        self._RCFs = []  # Array of RCF files

    def getRCFs(self, Directory, filelist=""):
        """ Get a list of available RCF files in the Directory """
        i = 0
        # Iterate over files in a directory
        for filename in os.listdir(Directory):
            found = 0
            # Ignore directories and files that don't have .RCF extension
            if (os.path.isfile(Directory + "/" + filename) and
               filename.endswith(".RCF")):
                try:
                    rcf = RetrievalCoefficientFile(Directory + "/" + filename)
                except Exception:
                    # Error opening RCF file. Failure to make fileset
                    raise

                # If success making fileset, append to list of RCFs
                self._RCFs.append(rcf)

                #  Only include files that are in the requested filelist
                #  If filelist is empty, then get everything.
                if (len(filelist) == 0):
                    # If in debug mode, print out names of RCF files that
                    # will be loaded.
                    logger.printmsg("DEBUG", "Found RCF file:" + filename +
                                    "  with ID:" + self._RCFs[i].getId())
                    i += 1
                else:
                    for j in range(len(filelist)):
                        if (filelist[j] == self._RCFs[i].getId()):
                            # If in debug mode, print out names of RCF files
                            # that will be loaded.
                            logger.printmsg("DEBUG", "Found RCF file:" +
                                            filename + "  with ID:" +
                                            self._RCFs[i].getId())
                            found = 1
                    if found:
                        i += 1
                    else:
                        self._RCFs.pop()

        # Test if got complete fileset
        if ((len(self._RCFs) == len(filelist)) or (len(filelist) == 0)):
            return(True)  # Success
        else:
            return(False)  # Failed to make a fileset

    def getRCFVector(self):
        """ Return a list of available RCF files """
        return(self._RCFs)

    def getRCFbyId(self, RCFId):
        """ Given an RCF Id, return the RCF file with that ID """
        for rcf in self._RCFs:
            if (rcf.getId() == RCFId):
                return(rcf)

        logger.printmsg("ERROR", "In " + inspect.stack()[0][3] + ":" +
                        "  Could not find RCF with ID: " + str(RCFId))
        return(False)

    def setFlightLevelsKm(self, FlightLevels, NumFlightLevels):
        """
        Set the Flight Levels in KM

        FlightLevels is an array of floating point values indicating the km
        above sea level of each flight level in each retrieval coefficient file

        NumFlightLevels is the length of the list

        testFlightLevelsKm checks that all RCFs in the set have the same flight
        levels - historically that has been the case, but it may not have to be
        Also checks that flight levels are be ordered in decreasing altitude.
        returns true if tests pass, false if not.

        """
        if (len(self._RCFs) == 0):
            logger.printmsg("ERROR", "In " + inspect.stack()[0][3] + " call " +
                            "failed: There are currently no RCFs in the set")
            return(False)

        for rcf in self._RCFs:
            if not (rcf.testFlightLevelsKm(FlightLevels, NumFlightLevels)):
                logger.printmsg("ERROR", "In " + inspect.stack()[0][3] +
                                " call failed: ERROR: Failed test of flight " +
                                "levels for RCFID:" + rcf.getId())
                return(False)

        return(True)

    def getBestWeightedRCSet(self, ScanBrightnessTemps, PAltKm, BTBias):
        """
        Get the Retrieval Coefficient Set from the "best" template
        weighted according to the flight level of the aircraft and given
        a set of Scan Brightness Temperatures

        ScanBrightnessTemps is an array of Scan Brightness Temperatures and is
        expected to be NUM_OBSVBLSs in length.  It is also expected that
        channel 1 will be in array elements 0-9 with element 0 being the
        highest scan angle and element 9 is the lowest scan angle.  Similarly,
        channel 2 will be found in elements 10-19 and channel 3 will be in
        elements 20-29.

        PAltKm is the altitude of the aircraft in km at the time that the scan
        was taken.

        BTBias is an Brightness Temperature Bias provided by the user

        Returns the weighted average set of Model Brightness Temperatures,
        RMS values, and Retrieval Coefficients from the template that best
        matches the input Scan Brightness Temperatures as observed from
        the input flight altitude.
        """

        thisRCFIndex = 0  # Which RCF index are we looking at?

        # Step through the vector of Retrieval Coefficient files (aka
        # templates) to obtain the best match for the scan at the input
        # Altitude
        for RCFit in self._RCFs:
            SumWeightedAvg = 0  # Sum of weighted differences
            SumSquares = 0      #
            SumWeights = 0      # For RMS weighting
            NumBTsIncl = 0      # Count of BTs included in Weighting

            # Get the weighted RC set for this template
            AvgWtSet = RCFit.getRCAvgWt(PAltKm)

            # Compare the template Brightness Temperatures with the
            # measured brightness temperatures to find the quality of match
            # BTIndex is the index into Scan and Model BT arrays
            for BTIndex in range(RCFit.getNUM_BRT_TEMPS()):
                Weight = 1/AvgWtSet['sOBrms'][BTIndex]**2
                SumWeights = SumWeights + Weight

                # Measured BT - Model BT = BTBias
                Diff = ScanBrightnessTemps[BTIndex]-AvgWtSet['sOBav'][BTIndex]

                if (Weight > 0):
                    NumBTsIncl += 1
                    SumWeightedAvg = SumWeightedAvg + Weight * Diff
                    SumSquares = SumSquares + Weight * (Diff**2)

            # The weighted mean of this RCF's BTs
            RCFBTWeightedMean = SumWeightedAvg / SumWeights

            # Standard Deviation about weighted mean(?)
            Numerator = SumSquares - (SumWeights * (RCFBTWeightedMean**2))
            Denominator = (NumBTsIncl-1) * SumWeights / NumBTsIncl
            if (Numerator/Denominator >= 0):
                RCFBTStdDev = math.sqrt(Numerator / Denominator)
            else:
                RCFBTStdDev = RCFBTWeightedMean  # MJ "kludge"

            # Calculate the Sum of the ln of probabilities (quality of match)
            # for "this" RCF
            thislnP = 8 * math.sqrt(RCFBTWeightedMean**2 + RCFBTStdDev**2) / \
                RCFit.getNUM_BRT_TEMPS()

            # BestlnP is the sum of the ln of Probabilities for the BestRCIndex
            # BestRCIndex is the index of "best" template (so far)
            # What should BestlnP, BestRCIndex default to?
            if (RCFit == self._RCFs[0]):
                BestlnP = thislnP
                BestRCIndex = 0
            elif (thislnP < BestlnP):
                BestlnP = thislnP
                BestRCIndex = thisRCFIndex
            thisRCFIndex += 1

        RC4R = RC_Set_4Retrieval
        RC4R['SumLnProb'] = BestlnP
        RC4R['RCFFileName'] = self._RCFs[BestRCIndex].getFileName()
        RC4R['RCFId'] = self._RCFs[BestRCIndex].getId()
        RC4R['RCFIndex'] = BestRCIndex
        RC4R['FL_RCs'] = self._RCFs[BestRCIndex].getRCAvgWt(PAltKm)
        return(RC4R)
