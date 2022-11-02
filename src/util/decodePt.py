###############################################################################
# Routine to calculate resistance(ohms) and temperature(deg) from MTP Platinum
# Multiplxr counts (Pt line). The Pt line contains 8 values:
# 'TR350CNTP'   # R350 Counts
# 'TTCNTRCNTP'  # Target Center Temp Counts
# 'TTEDGCNTP'   # Target Edge Temp Counts
# 'TWINCNTP'    # Polyethelene Window Temp Counts
# 'TMIXCNTP'    # Mixer Temperature Counts
# 'TAMPCNTP'    # Amplifier Temp Counts
# 'TNDCNTP'     # Noise Diode Temp Counts
# 'TR600CNTP'   # R600 Counts
#
#  Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import numpy
from util.math import MTPmath
# from EOLpython.Qlogger.messageHandler import QLogger as logger


class decodePt():

    def __init__(self, reader):

        self.reader = reader
        self.math = MTPmath()

    def calcTemp(self):

        # Set some defaults
        R = [numpy.nan] * 8  # Empty array to hold resistances
        R[0] = 350           # rref low
        R[7] = 600           # rref high

        Ct = [numpy.nan] * 8  # Empty array to hold counts
        Ct[0] = int(self.reader.getVar('Ptline', 'TR350CNTP'))  # low
        Ct[7] = int(self.reader.getVar('Ptline', 'TR600CNTP'))  # hi

        T = [numpy.nan] * 8  # Empty array to hold temperatures

        for var in self.reader.getVarList('Ptline'):
            # Visual Basic code for decodePt has a check for counts == 16383
            # that sets calculated values to N/A in display.
            # I have no idea why. So just check for it here and warn user.
            # Commented out because it just confused users.
            # if int(self.reader.getVar('Ptline', var) == 16383:
            #   varname = self.reader.rawscan['Ptline']['values'][var]['name']
            #   logger.warning("count for var " + varname + " =" +
            #                  " 16383. VB6 code would display this as N/A." +
            #                  " Not sure why so this code doesn't do that." +
            #                  " Dismiss this warning to display this scan.")

            Ctvar = int(self.reader.getVar('Ptline', var))
            T = self.math.calcPtT(Ct[0], Ctvar, Ct[7])

            self.reader.setCalcVal('Ptline', var, T, 'temperature')
            self.reader.setCalcVal('Ptline', var, self.math.getR(),
                                   'resistance')

        # From Visual Basic code. Not traced yet, so not implemented.
        # If WindowCal = True Then
        # txtTsky.Text = Format$(T(3), " +00.00; -00.00")
