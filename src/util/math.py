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

    def calcTfromVal(self, val: int):
        """ Calculate temperaature from an M02 line value """

        if (val == 4095) or (val == 0):
            T = numpy.nan
        else:
            cnt = 4096 - val
            RR = (1 / (cnt / 4096)) - 1
            Rt = 34800 * RR
            T = (1 / (self.A + self.B * numpy.log(Rt) +
                      self.C * numpy.log(Rt)**3) - 273.15)

        return T
