###############################################################################
# Test util/calcTBs.py
#
# Takes counts from the Bline, SAAT from the Aline, the temperature calculated
# from TMIXCNTP in the Ptline, and calculates brightness temperature from the
# counts.
#
# To run these tests:
#     cd src/
#     python3 -m unittest discover -s ../tests -v
#
# To increase debugging info (i.e. if trying to figure out test_quit issues,
# uncomment this line:
# import faulthandler; faulthandler.enable()
# and then run these tests with the -Xfaulthandler option, e.g.
#
# python3 -Xfaulthandler -m unittest discover -s ../tests -v
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import unittest
from util.readmtp import readMTP
from util.decodePt import decodePt
from util.calcTBs import BrightnessTemperature


class TESTcalcTBs(unittest.TestCase):

    def setUp(self):
        udp = "MTP,20140606T062418,+06.49,00.19,-00.79,00.87,+04.00,0.06," + \
              "263.32,00.48,-43.290,+0.005,+172.296,+0.051,+074684," + \
              "+073904,018089,019327,018696,018110,019321,018704,018113," + \
              "019326,018702,018130,019356,018716,018159,019377,018744," + \
              "018174,019392,018756,018178,019394,018758,018197,019397," + \
              "018757,018211,019404,018763,018228,019419,018774,2928," + \
              "2228,2898,3082,1930,2923,2431,2944,2002,1345,2069,2239," + \
              "2166,1506,4095,1533,2175,13808,13811,10259,13368,13416," + \
              "13310,14460,020890,022318,022138,019200,020582,020097"
        mtp = readMTP()  # Instantiate a reader
        # Save the contents of the udp packet to the MTP dictionary
        mtp.parseAsciiPacket(udp)

        pt = decodePt(mtp)  # Instantiate a decoder for the Pt line
        pt.calcTemp()       # Calculate the temperatures for the Pt values

        # Save off the values needed for calc brightness temperature
        self.rawscan = mtp.getRawscan()
        Tifa = self.rawscan['Ptline']['values']['TMIXCNTP']['temperature']
        OAT = self.rawscan['Aline']['values']['SAAT']['val']
        scnt = self.rawscan['Bline']['values']['SCNT']['val']

        # Calculate the brightness temperatures
        tb = BrightnessTemperature()
        self.rawscan['Bline']['values']['SCNT']['tb'] = \
            tb.TBcalculationRT(Tifa, OAT, scnt)

    def testTBcalculationRT(self):
        # These numbers are taken from an early run of this script, so this
        # test is for consistency (i.e. warn me if they change). I haven't
        # been able to test if the numbers are right yet, although they are
        # very close to the confirmed numbers for the post-processing tests
        # done with nimbus.
        tb = ['259.0284', '260.4983', '261.0111', '260.0887', '260.2379',
              '261.3189', '260.2401', '260.4549', '261.2420', '261.0985',
              '261.7572', '261.7807', '262.5627', '262.6688', '262.8582',
              '263.3200', '263.3200', '263.3200', '263.5220', '263.4068',
              '263.3970', '264.4813', '263.5371', '263.3585', '265.1881',
              '263.8409', '263.5894', '266.0464', '264.4921', '264.0127']
        for i in range(30):
            self.assertEqual(
                "%8.4f" % self.rawscan['Bline']['values']['SCNT']['tb'][i],
                tb[i])
