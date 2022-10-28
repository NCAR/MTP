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
# from EOLpython.Qlogger.messageHandler import QLogger as logger


class decodePt():

    def __init__(self, reader):

        self.reader = reader

    def calcTemp(self):

        # Set some defaults
        R = [numpy.nan] * 8  # Empty array to hold resistances
        R[0] = 350           # rref low
        R[7] = 600           # rref hi

        # Set constants for platinum wire gain equation for temperature of
        # target.  These should remain constant as long as physical target
        # doesn't change.  If target is replaced, these may change.
        A = -244.3364635
        B = 0.462418
        C = 0.0000588
        D = -0.000000013

        Ct = [numpy.nan] * 8  # Empty array to hold counts
        Ct[0] = int(self.reader.getVar('Ptline', 'TR350CNTP'))  # low
        Ct[7] = int(self.reader.getVar('Ptline', 'TR600CNTP'))  # hi

        # Calculate slope component of resistance equation
        # rslop = (Ct[7] - Ct[0]) / (R[7] - R[0])
        rslop = ((int(self.reader.getVar('Ptline', 'TR600CNTP')) -   # hi
                 int(self.reader.getVar('Ptline', 'TR350CNTP'))) /  # low
                 (R[7] - R[0]))

        # This line added to Visual Basic routine 2011/05/03 RFD
        if rslop == 0:
            rslop = 49.1
        # End of addition 2011/05/03

        T = [numpy.nan] * 8  # Empty array to hold temperatures
        for var in self.reader.getVarList('Ptline'):
            # Visual Basic code for decodePt has a check for counts == 16383
            # that sets calculated values to N/A in display.
            # I have no idea why. So just check for it here and warn user.
            # Commented out because it just confused users.
            # if int(self.getCount(var)) == 16383:
            #   varname = self.reader.rawscan['Ptline']['values'][var]['name']
            #   logger.warning("count for var " + varname + " =" +
            #                  " 16383. VB6 code would display this as N/A." +
            #                  " Not sure why so this code doesn't do that." +
            #                  " Dismiss this warning to display this scan.")

            # Resistance from counts (R)
            # R[i] = 350 + (Ct[i] - Ct[0]) / rslop
            R = 350 + (int(self.getCount(var)) -
                       int(self.getCount('TR350CNTP'))) / rslop
            self.reader.setCalcVal('Ptline', var, R, 'resistance')

            # Temperature of each value from counts
            # T[i] = A + B * R[i] + C * R[i] ** 2 + D * R[i] ** 3
            T = A + B * R + C * R ** 2 + D * R ** 3
            self.reader.setCalcVal('Ptline', var, T, 'temperature')

        # From Visual Basic code. Not traced yet, so not implemented.
        # If WindowCal = True Then
        # txtTsky.Text = Format$(T(3), " +00.00; -00.00")

    def getCount(self, var):
        return self.reader.rawscan['Ptline']['values'][var]['val']
