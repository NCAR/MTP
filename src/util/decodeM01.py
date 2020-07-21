###############################################################################
# Routine to calculate Voltage(Volts) from MTP Engineering Multiplxr counts
# (M01 line). The M01 line contains 8 values:
# 'VM08CNTE'    # Vm08 Counts
# 'VVIDCNTE'    # Vvid Counts
# 'VP08CNTE'    # Vp08 Counts
# 'VMTRCNTE'    # Vmtr Counts
# 'VSYNCNTE'    # Vsyn Counts
# 'VP15CNTE'    # Vp15 Counts
# 'VP05CNTE'    # Vp05 Counts
# 'VM15CNTE'    # VM15 Counts
#
#  Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import numpy


class decodeM01():

    def __init__(self, reader):

        self.reader = reader

    def calcVolts(self):
        """ Convert engineering mulltiplxr counts to voltages """

        # Volts = constant * cnts/1000
        # Constants for each engineering value are hardcoded in MTP.py
        for var in self.reader.getVarList('M01line'):
            fact = self.reader.rawscan['M01line']['values'][var]['fact']
            val = self.reader.rawscan['M01line']['values'][var]['val']
            if val == '':  # Value missing from MTP UDP string
                V = numpy.nan
            else:
                V = fact * (int(val) / 1000)

            self.reader.setCalcVal('M01line', var, V, 'volts')
