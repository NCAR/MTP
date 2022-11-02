###############################################################################
# Routine to calculate Values(mostly Temparatures in degC but also Acceleration
# in units of g) from MTP Engineering Multiplxr counts in line 2
# (M01 line). The M01 line contains 8 values:
# 'ACCPCNTE'    # Accelerator Counts
# 'TDATCNTE'    # Temperature Data Counts
# 'TMTRCNTE'    # Temperature Motor Counts
# 'TAIRCNTE'    # Temperature Pod Air Counts
# 'TSMPCNTE'    # Temperature Scan Counts
# 'TPSPCNTE'    # Temperature Power Supply Counts
# 'TNCCCNTE'    # Temperature N/C Counts
# 'TSYNCNTE'    # Temperature Synth Counts
#
#  Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import numpy
from util.math import MTPmath


class decodeM02():

    def __init__(self, reader):

        self.reader = reader
        self.math = MTPmath()

    def calcVals(self):

        for var in self.reader.getVarList('M02line'):
            val = float(self.reader.rawscan['M02line']['values'][var]['val'])
            if val == '':  # Value missing from MTP UDP string
                T = numpy.nan
            else:
                if var == 'ACCPCNTE':  # MMA1250D accelerometer 2.5V +-.25V @0G
                    # Assign result to T val to make looping easier. This is
                    # really an acceleration, not a temperature.
                    T = self.math.calcG(val)
                else:
                    T = self.math.calcTfromVal(val)

            self.reader.setCalcVal('M02line', var, T, 'temperature')
