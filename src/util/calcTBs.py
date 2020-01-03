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

    def __init__(self, configfile):
        """
        The constants GOF and GEC don't change in real-time mode. To initialize
        a new project, copy the latest values from the previous project to this
        project's config file.
        """
        # Number of channels
        self.channels = configfile.getInt('NUM_CHANNELS')

        # Number of scan angles
        self.angles = configfile.getInt('NUM_SCAN_ANGLES')

        # Scan Angle Index of horizontal scan. Index starts at 0
        self.LocHor = configfile.getInt('LOC_HOR')

        # Minimum acceptable Gain
        self.GeqnMin = configfile.getInt('GeqnMin')
        # Maximum acceptable Gain
        self.GeqnMax = configfile.getInt('GeqnMax')

        self.Geqn = [None] * self.channels
        self.tb = [None] * self.channels * self.angles

        # From DEEPWAVE RF01 post-processing (so can compare with nimbus and
        # VB6 results to confirm these calcs are OK)
        self.GOF = float(configfile.getVal('GOF'))
        self.GEC = configfile.getVal('GEC')

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

    def TBcalculationRT(self, Tifa, OAT, scnt):
        """
        Real-Time Brightness Temperature Calculations

        Calibrate the MTP scans using the gain equation constants GOF and GEC.
        When the MTP instrument completes a scan of the atmosphere the scan
        counts are converted to Brightness Temperatures using this routine.
        This routine combines the routines TBcalculation(), GainCalculation()
        and GainGE() from the real-time MTPbin code:
        MTP-VB6/MTP_realtime/VB6/VBP/Main/MOAP/MTPbin.frm
        """
        for i in range(0, self.channels):
            self.Geqn[i] = float(self.GEC[i][0]) + \
                           (Tifa - self.GOF) * float(self.GEC[i][1])
            # Mask out gains that are too big or too small
            if (self.Geqn[i] < self.GeqnMin) or (self.Geqn[i] > self.GeqnMax):
                self.Geqn[i] = numpy.nan

            CHor = int(scnt[i + self.LocHor*3])

            for j in range(0, 10):
                C = int(scnt[i + j*3])  # MTP Scan Counts[Angle, Channel]
                self.tb[i + j*3] = float(OAT) + (C - CHor) / self.Geqn[i]

        return(self.tb)
