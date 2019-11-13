###############################################################################
# Calculate brightness temperatures from counts
#
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import numpy


class BrightnessTemperature():

    def __init__(self, reader):
        """
        The constants GOF and GEC don't change in real-time mode. To initialize
        a new project, the user copies a flight config from a previous project.
        Until that is implemented, hardcode the constants here.
        """
        self.channels = 3  # Number of channels
        self.Geqn = [None] * self.channels

        # From DEEPWAVE RF01 post-processing (so can compare with nimbus and
        # VB6 results to confirm these calcs are OK)
        self.GOF = 40.6
        self.GEC = [[19.87, 0.1], [23.1, 0.1], [26.05, 0.1]]

        # From CSET
        # self.GOF = 42
        # self.GEC = [[19.43, 0.2], [22.44, 0.2],[25.29, 0.2]]
        # print(self.GEC[0][0])  # GEC[11 = 19.43  # Channel 1
        # print(self.GEC[1][0])  # GEC[21 = 22.44  # Channel 2
        # print(self.GEC[2][0])  # GEC[31 = 25.29  # Channel 3
        # print(self.GEC[0][1])  # GEC[12 = -0.2  # Channel 1
        # print(self.GEC[1][1])  # GEC[22 = -0.2  # Channel 2
        # print(self.GEC[2][1])  # GEC[32 = -0.3  # Channel 3

        self.LocHor = 5  # index starts at zero
        self.GeqnMin = 10
        self.GeqnMax = 40

        self.Tifa = \
            reader.rawscan['Ptline']['values']['TMIXCNTP']['temperature']
        self.OAT = \
            reader.rawscan['Aline']['values']['SAAT']['val']
        # MTP Scan Counts[Angle, Channel]
        self.scnt = reader.rawscan['Bline']['values']['SCNT']['val']

#   def calcTB(self):
#       """
#       Calculation from real-time code. Looks to me like this just calculates
#       a running average of brightness temperatures in the forward direction.
#       THIS IS PSEUDO-CODE. HOLDING ON TO IT FOR NOW SO I CAN COMPARE TO OTHER
#       CALCS I STILL NEED TO CODE.
#       """
#       # Tdefl = Window Temperature minus average of target center and edge
#       # temperatures
#       Tdefl = TPt3 - (TPt1 + TPt2) / 2

#       for i in range(0, 3):  # For each channel
#           # count deflection is the target counts with the Noise diode off
#           # minus the scan count for this angle in the forward direction
#           cdeflect = ['Eline']['values']['TCNT'][i+3] -
#               ['Bline']['values']['SCNT'][i*10 + 5]

#           # This average is over the length of the flight
#           cntNDon(i) = ['Eline']['values']['TCNT']['val'][i]
#           cntNDoffi) = ['Eline']['values']['TCNT']['val'][i+3]
#           diff = cntNDon(i)-cntNDoff(i)
#           NDsum = NDsum + diff
#           j=j+1
#           NDavg = NDsum/j
#           rgain = (NDavg)/ Tdefl

#           # Base Target Temperature is the average of the target center and
#           # edge temperatures
#           TBaseTarget = (TPt1 + TPt2)/2

#           # Brightness Temperature is temperature of the target plus
#           # difference between target counts with niose diode off divided by
#           # gain.
#           Tb(i) = TBaseTarget + (cdeflect / rgain)

    def GainCalculation(self, reader):
        """
        Calibrate the MTP scans using the gain equation constants GOF and GEC.
        When the MTP instrument completes a scan of the atmosphere the scan
        counts are converted to Brightness Temperatures using this routine.
        This routine combines the routines TBalculation(), GainCalculation()
        and GainGE() from the real-time MTPbin code.
        """
        for i in range(0, self.channels):
            self.Geqn[i] = self.GEC[i][0] + \
                           (self.Tifa - self.GOF) * self.GEC[i][1]
            # Mask out gains that are too big or too small
            if (self.Geqn[i] < self.GeqnMin) or (self.Geqn[i] > self.GeqnMax):
                self.Geqn[i] = numpy.nan

            CHor = int(self.scnt[i + self.LocHor*3])

            for j in range(0, 10):
                C = int(self.scnt[i + j*3])  # MTP Scan Counts[Angle, Channel]
                tb = float(self.OAT) + (C - CHor) / self.Geqn[i]
                reader.rawscan['Bline']['values']['SCNT']['tb'][i + j*3] = tb
