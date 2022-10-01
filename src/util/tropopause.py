###############################################################################
# This class encapsulates calculation of tropopause heights from
# physical temperature profiles.
#
# The WMO definition of the first tropopause (i.e., the conventional
# tropopause) is defined using two components:
#   1. The lowest level at which the linear lapse rate decreases to 2 K/km
#   or less (i.e. the profile is more steep)
# and
#   2. The average lapse rate from this level to any level within the
#   next higher 2 km does not exceed 2 K/km.
# The following functions determine the location in the profile where
# these two components are met.
#
# (It appears that MJ's algorithm does NOT follow this reference, but instead
# follows the WMO defintion.)
# Reference: Roe, J. M., and W. H. Jasperson (1980), A new tropopause
# definition from simultaneous ozone‐temperature profiles, Tech.Rep.
# AFGL‐TR‐80–0289, Air Force Geophys. Lab., Hanscom Air Force Base, Mass.
# [Available from https://apps.dtic.mil/dtic/tr/fulltext/u2/a091718.pdf]
#
# The Microwave Temperature Profiler (MTP) instrument build by JPL for
# NCAR as part of the set of instruments known as HAIS (build specifically
# in support of the Haiper GV aircraft) came with processing software
# written in Visual Basic 6.0.
#
# Written in Python 3
#
# Copyright: University Corporation for Atmospheric Research, 2019
# VB6 and Algorithm Copyright MJ Mahoney, NASA Jet Propulsion Laboratory
###############################################################################
import numpy


class Tropopause():

    def __init__(self, ATP, NUM_RETR_LVLS):

        self.NUM_RETR_LVLS = NUM_RETR_LVLS
        self.tempc = ATP['Temperatures']
        self.altc = ATP['Altitudes']
        # The referenceLapseRate is also hardcoded in MTPviewer.py
        self.referenceLapseRate = -2  # -2K/km; beginning of a tropopause

        # Constants used in tropopause calculations
        self.referenceLayerThickness = 2  # 2km
        self.minHt = 5.6  # Lowest alt to look for tropopause (500mb = 5.6km)

    def linearLapseRate(self, startidx, i, referenceLapseRate):
        """
        Find the first linear lapse rate (between two consecutive
        measurements) that meets or crosses the reference lapse rate cutoff.
            Inputs:
                 start_index - the index into the profile to start looking at
                     (if you don't want to start at the lowest measurement in
                      the profile).
                 i - pointer to index of lowest level where lapse rate
                     decreases to the reference lapse rate or less. (i is the
                     bottom of the layer)
                 referenceLapseRate - the cutoff lapse rate that indicates a
                     tropopause has been found.
            Output:
                 lapseRate - the linear lapse rate for the layer we are
                 working with
        """
        for i in range(startidx, self.NUM_RETR_LVLS-1):
            if (self.altc[i+1] != self.altc[i]):
                lapseRate = (self.tempc[i+1] - self.tempc[i]) / \
                            (self.altc[i+1] - self.altc[i])
                if (lapseRate >= referenceLapseRate):
                    return [lapseRate, i]

        # If no tropopause found, return nan
        i = self.NUM_RETR_LVLS
        return [numpy.nan, i]

    def Tinterp(self, altInterp, startidx):
        """
        Find the temperature at a given altitude by linear interpolation
            Inputs:
                altInterp - altitude to interpolate temperature to
                startidx  - index of the starting point to find the first
                            measurement above the interpolation point.
            Outputs:
                return temperature at the interpolation altitude
        """

        # Don’t interpolate between bottom two layers (Why?)
        if (altInterp <= self.altc[1] + 0.01):
            return numpy.nan

        # starting at startidx, find first measurement above altInterp
        for i in range(startidx, self.NUM_RETR_LVLS):
            if (self.altc[i] >= altInterp):
                break

        if (self.altc[i] < altInterp):
            return numpy.nan  # Ran out of RAOB

        # Interpolate temperature
        altBot = self.altc[i - 1]  # altitude at bottom of layer to interpolate
        tempTop = self.tempc[i]    # temperature at top of layer to interpolate
        tempBot = self.tempc[i - 1]  # temp at bottom of layer to interpolate

        return tempBot + ((tempTop - tempBot) * (altInterp - altBot) /
                          (self.altc[i] - altBot))

    def averageLapseRate(self, LT, step, startidx):
        """
        Find the average lapse rate from the bottom of this layer to the
        sub-layer
            Input:
                LT       - Level to begin our search for the tropopause
                step     - width of a step through our layer
                startidx - the measurement just under 2KM above the LT
                also uses global referenceLayerThickness
            Output:
                LRavg - average lapse rate
        """
        deltaTsum = 0  # running total of temperature difference
        LRavg = numpy.nan  # average lapse rate

        # number of sub-layers to divide layer into. Use // for integer
        # division in python3
        nlayers = int(self.referenceLayerThickness // step)

        altBot = self.altc[LT]
        for i in range(nlayers):
            # Find alt at bottom and top of layer we are testing
            altTop = self.altc[LT] + step * i

            # linear interpolation to find temperature at top and bottom
            # altitudes (since we may not have a scan there)
            tempBot = self.Tinterp(altBot, startidx)
            tempTop = self.Tinterp(altTop, startidx)
            if (numpy.isnan(tempTop)):
                return numpy.nan  # Ran out of RAOB; didn't find tropopause

            # Calculate average lapse rate from the bottom of the layer to our
            # current level
            deltaTsum = deltaTsum + (tempTop - tempBot)

            altBot = altTop  # get set for next layer

        LRavg = deltaTsum / (step * nlayers)

        return LRavg  # average lapse rate

    def findGap(self, LT, step, startidx):
        """
        If have a tropopause from a previous call to this routine, need to find
        a break between tropopauses before can look for the next one. This
        break is defined as a region where the lapse rate is less than -3 K/km.
        MJ notes that he decided to search in a 2KM layer (rather than 1 km as
        defined in WMO) as 1 km is too sensitive for RAOB data causing too many
        double (and not credible) tropopauses.

        Output:
            altBot - altitude of lowest layer to loop for next tropopause
        """
        endLapseRate = -3  # -3K/km; end of a tropopause
        altBot = self.altc[LT]
        LRavg = 0  # Initialize to something greater than endLapseRate

        while (LRavg > endLapseRate):
            # Find alt at bottom and top of layer we are testing
            altTop = altBot + self.referenceLayerThickness

            # linear interpolation to find temperature at top and bottom
            # altitudes (since we may not have a scan there)
            tempBot = self.Tinterp(altBot, startidx)
            tempTop = self.Tinterp(altTop, startidx)
            if (numpy.isnan(tempTop)):
                LRavg = numpy.nan  # Ran out of RAOB; didn't find tropopause
            else:
                # Calculate average lapse rate from the bottom of the layer to
                # our current level
                LRavg = (tempTop - tempBot) / self.referenceLayerThickness
            if (numpy.isnan(LRavg)):
                return numpy.nan  # no tropopause found

            altBot = altBot + step

        return altBot

    def findStart(self, startidx, minidx):
        """
        Locate the first retrieval above the lowest altitude to look for
        tropopause
        Input:
            minidx - the lowest altitude to look for the topopause
        Output:
            startidx - the first retrieval above that minimum
        """
        for i in range(startidx+1, self.NUM_RETR_LVLS):
            if (self.altc[i] > minidx):
                startidx = i
                return startidx

        # Ran out of RAOB
        startidx = -1

        return startidx

    def findTropopause(self, startidx):
        """
        Find a tropopause
            Input:
                startidx - the lowest altitude to look for the tropopause
            Output:
                altctrop  - the altitude of the found tropopause
                tempctrop - the temperature of the found tropopause
                LT        - the index of the found tropopause
        """
        LT = 0  # Level of best tropopause found so far
        foundTrop = 0  # Boolean to indicate when tropopause has been located
        step = 0.02

        # To start with, we don't know the tropopause location, so set to
        # missing. (This simplifies returning from all cases where trop can't
        # be found.
        altctrop = numpy.nan
        tempctrop = numpy.nan

        # At this point, startidx will be the value set in the previous pass
        # through. If it is zero, we are looking for the first tropopause. If
        # it is greater than zero, we are looking for a second or greater
        # tropopause.
        if startidx != 0:
            LT = startidx
            # Locate lowest layer above gap between tropopauses.
            altBot = self.findGap(LT, step, startidx)
            if (numpy.isnan(altBot)):
                # no tropopause found
                return startidx, numpy.nan, numpy.nan, numpy.nan

            # Locate first retrieval above identified break (altBot)
            startidx = self.findStart(startidx, altBot)
            if (startidx == -1):
                # no tropopause found
                return startidx, numpy.nan, numpy.nan, numpy.nan

        else:
            # Locate first retrieval above lowest altitude to look for
            # tropopause.
            startidx = self.findStart(startidx, self.minHt)
            if (startidx == -1):
                # no tropopause found
                return startidx, numpy.nan, numpy.nan, numpy.nan

        # Find the next tropopause (could be the first)
        # referenceLapseRate is the cutoff lapse rate that indicates a
        # transition has been found.
        while not foundTrop:
            # Starting with first measurement above 500mb, find the index (LT)
            # of the lowest level at which the linear lapse rate (LRavg)
            # decreases to 2K/km or less. This is the index of our possible
            # tropopause that meets the first part of the WMO criteria.
            # LRavg is the average lapse rate over the reference layer
            [LRavg, LT] = self.linearLapseRate(startidx, LT,
                                               self.referenceLapseRate)
            if (numpy.isnan(LRavg)):  # no tropopause found
                startidx = LT
                return startidx, numpy.nan, numpy.nan, numpy.nan

            # For the second part of the WMO definition, confirm that the
            # average lapse rate from our possible tropopause (LT) to any level
            # within the nextLThigher 2 km does not exceed 2 K/km. (‘Average is
            # >=-2). If there are no measurements within the next 2km, then the
            # average lapse rate is LRavg already calculated above.

            # Next higher measurement is less than 2km from our possible
            # tropopause if next higher measurement is more than 2km, then all
            # we can calc is the linear lapse rate, which we did above.
            if (self.altc[LT+1] - self.altc[LT] <
                    self.referenceLayerThickness):
                # loop until find measurement that is 2km above possible
                # tropopause or more, and save the level just below that (so
                # level is measurement just below top of our 2km layer.
                for startidx in range(LT+1, self.NUM_RETR_LVLS):
                    if ((self.altc[startidx+1] - self.altc[LT]) >
                            self.referenceLayerThickness):
                        break

                # Interpolate to get value at exactly 2km and calc lapse rate
                # to that level
                LRavg = self.averageLapseRate(LT, self.referenceLayerThickness,
                                              startidx)
                if (numpy.isnan(LRavg)):  # no tropopause found
                    startidx = LT
                    return startidx, numpy.nan, numpy.nan, numpy.nan

                if (LRavg < self.referenceLapseRate):
                    continue

                # Now check that lapse rate is less than 2K/km from LT to *any*
                # level within the next 2KM. Do this by dividing the layer into
                # 100 sub-layers and checking from LT to each one.
                LRavg = self.averageLapseRate(LT, step, startidx)
                if (numpy.isnan(LRavg)):  # no tropopause found
                    startidx = LT
                    return startidx, numpy.nan, numpy.nan, numpy.nan

            # Check if average lapse rate over reference layer exceeds -2K/km.
            # If so, found tropopause. If not, failed WMO criteria and still
            # haven't found tropopause. Try again with lowest possible
            # tropopause ht set to current level (startidx).
            if (LRavg >= self.referenceLapseRate):
                foundTrop = 1  # exit while loop

        # if we get here, we met all the criteria. Zt1 and TT1 are the altitude
        # and temperature of the tropopause
        altctrop = self.altc[LT]
        tempctrop = self.tempc[LT]

        # Set startidx to LT in prep for looking for additional tropopauses
        startidx = LT

        # Return index to level of tropopause; zero indicated none found
        return [startidx, LT, altctrop, tempctrop]
