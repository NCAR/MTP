###############################################################################
# Class to hold math calculations
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import numpy


class MTPmath():

    def __init__(self):

        # Thermistor constants
        self.A = 0.0009376
        self.B = 0.0002208
        self.C = 0.0000001276

        # rref constants
        self.R0 = 350  # rref low
        self.R7 = 600  # rref high

        # Set constants for platinum wire (pt) gain equation for temperature of
        # target.  These should remain constant as long as physical target
        # doesn't change.  If target is replaced, these may change.
        self.Apt = -244.3364635
        self.Bpt = 0.462418
        self.Cpt = 0.0000588
        self.Dpt = -0.000000013

    def calcTfromVal(self, val: float):
        """ Calculate temperature in celsius from an M02 line value """

        if (val == 4095) or (val == 0):
            T = numpy.nan
        else:
            cnt = 4096 - val
            RR = (1 / (cnt / 4096)) - 1
            Rt = 34800 * RR
            T = (1 / (self.A + self.B * numpy.log(Rt) +
                      self.C * numpy.log(Rt)**3) - 273.15)

        return T  # Celsius

    def calcG(self, val: float):
        """ Calculate acceleration from counts (first value in M02 line) """

        G = -1.0 * ((val * 0.001) - 2.5) / 0.4

        return G

    def calcV(self, val: int, fact):
        """ Calculate voltage from an M01 line value """

        # Volts = constant * cnts/1000
        # Constants for each engineering value are hardcoded in MTP.py
        V = fact * (val / 1000)

        return V  # volts

    def calcPtT(self, Ct0, Ctvar, Ct7):
        """ Calculate temperatures for Ptline values """

        # Calculate slope component of resistance equation
        rslop = (Ct7 - Ct0) / (self.R7 - self.R0)

        # This line added to Visual Basic routine 2011/05/03 RFD
        if rslop == 0:
            rslop = 49.1
        # End of addition 2011/05/03

        # Resistance from counts (R)
        self.R = self.R0 + (Ctvar - Ct0) / rslop

        # Temperature of each value from counts
        T = self.Apt + self.Bpt * self.R + self.Cpt * self.R ** 2 + \
            self.Dpt * self.R ** 3

        return T

    def getR(self):
        return self.R
