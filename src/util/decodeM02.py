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


class decodeM02():

    def __init__(self, reader):

        self.reader = reader

        # Thermistor constants
        self.A = 0.0009376
        self.B = 0.0002208
        self.C = 0.0000001276

    def calcVals(self):

        for var in self.reader.getVarList('M02line'):
            val = float(self.reader.rawscan['M02line']['values'][var]['val'])
            if val == '':  # Value missing from MTP UDP string
                T = numpy.nan
            else:
                if var == 'ACCPCNTE':  # MMA1250D accelerometer 2.5V +-.25V @0G
                    T = -1.0 * ((val * 0.001) - 2.5) / 0.4
                else:
                    if (val == 4095) or (val == 0):
                        T = numpy.nan
                    else:
                        cnt = 4096 - val
                        RR = (1 / (cnt / 4096)) - 1
                        Rt = 34800 * RR
                        T = (1 / (self.A + self.B * numpy.log(Rt) +
                                  self.C * numpy.log(Rt)**3) - 273.16)

            self.reader.setCalcVal('M02line', var, T, 'temperature')
