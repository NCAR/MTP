###############################################################################
# Test readmtp.py/parseAsciiPacket(UDPpacket)
#
# Takes an Ascii Packet received from the UDP feed and tests that lines are
# saved to the MTP dictionary correctly
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
import os
import unittest
from util.readmtp import readMTP
from lib.rootdir import getrootdir


class TESTparseAsciiPacket(unittest.TestCase):

    def setUp(self):
        self.ascii_parms = os.path.join(getrootdir(), 'config/ascii_parms')

        udp = "MTP,20140606T062418,+06.49,00.19,-00.79,00.87,+04.00,0.06," + \
              "263.32,00.48,-43.290,+0.005,+172.296,+0.051,+074684," + \
              "+073904,018089,019327,018696,018110,019321,018704,018113," + \
              "019326,018702,018130,019356,018716,018159,019377,018744," + \
              "018174,019392,018756,018178,019394,018758,018197,019397," + \
              "018757,018211,019404,018763,018228,019419,018774,2928," + \
              "2228,2898,3082,1930,2923,2431,2944,2002,1345,2069,2239," + \
              "2166,1506,4095,1533,2175,13808,13811,10259,13368,13416," + \
              "13310,14460,020890,022318,022138,019200,020582,020097"
        mtp = readMTP()
        self.rawscan = mtp.getRawscan()
        mtp.parseAsciiPacket(udp)

    def testAline(self):
        """ Test Aline saved to MTP dictionary correctly """
        self.assertEqual(self.rawscan['Aline']['values']['DATE']['val'],
                         '20140606')
        self.assertEqual(self.rawscan['Aline']['values']['timestr']['val'],
                         '06:24:18')
        self.assertEqual(self.rawscan['Aline']['values']['TIME']['val'],
                         23058)
        self.assertEqual(self.rawscan['Aline']['values']['SAPITCH']['val'],
                         '+06.49')
        self.assertEqual(self.rawscan['Aline']['values']['SRPITCH']['val'],
                         '00.19')
        self.assertEqual(self.rawscan['Aline']['values']['SAROLL']['val'],
                         '-00.79')
        self.assertEqual(self.rawscan['Aline']['values']['SRROLL']['val'],
                         '00.87')
        self.assertEqual(self.rawscan['Aline']['values']['SAPALT']['val'],
                         '+04.00')
        self.assertEqual(self.rawscan['Aline']['values']['SRPALT']['val'],
                         '0.06')
        self.assertEqual(self.rawscan['Aline']['values']['SAAT']['val'],
                         '263.32')
        self.assertEqual(self.rawscan['Aline']['values']['SRAT']['val'],
                         '00.48')
        self.assertEqual(self.rawscan['Aline']['values']['SALAT']['val'],
                         '-43.290')
        self.assertEqual(self.rawscan['Aline']['values']['SRLAT']['val'],
                         '+0.005')
        self.assertEqual(self.rawscan['Aline']['values']['SALON']['val'],
                         '+172.296')
        self.assertEqual(self.rawscan['Aline']['values']['SRLON']['val'],
                         '+0.051')
        self.assertEqual(self.rawscan['Aline']['values']['SMCMD']['val'],
                         '+074684')
        self.assertEqual(self.rawscan['Aline']['values']['SMENC']['val'],
                         '+073904')

    def testBline(self):
        """ Test Bline saved to MTP dictionary correctly """
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][0],
                         '018089')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][1],
                         '019327')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][2],
                         '018696')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][3],
                         '018110')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][4],
                         '019321')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][5],
                         '018704')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][6],
                         '018113')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][7],
                         '019326')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][8],
                         '018702')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][9],
                         '018130')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][10],
                         '019356')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][11],
                         '018716')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][12],
                         '018159')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][13],
                         '019377')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][14],
                         '018744')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][15],
                         '018174')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][16],
                         '019392')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][17],
                         '018756')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][18],
                         '018178')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][19],
                         '019394')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][20],
                         '018758')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][21],
                         '018197')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][22],
                         '019397')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][23],
                         '018757')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][24],
                         '018211')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][25],
                         '019404')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][26],
                         '018763')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][27],
                         '018228')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][28],
                         '019419')
        self.assertEqual(self.rawscan['Bline']['values']['SCNT']['val'][29],
                         '018774')

    def testM01line(self):
        """ Test M01line saved to MTP dictionary correctly """
        self.assertEqual(self.rawscan['M01line']['values']['VM08CNTE']['val'],
                         '2928')
        self.assertEqual(self.rawscan['M01line']['values']['VVIDCNTE']['val'],
                         '2228')
        self.assertEqual(self.rawscan['M01line']['values']['VP08CNTE']['val'],
                         '2898')
        self.assertEqual(self.rawscan['M01line']['values']['VMTRCNTE']['val'],
                         '3082')
        self.assertEqual(self.rawscan['M01line']['values']['VSYNCNTE']['val'],
                         '1930')
        self.assertEqual(self.rawscan['M01line']['values']['VP15CNTE']['val'],
                         '2923')
        self.assertEqual(self.rawscan['M01line']['values']['VP05CNTE']['val'],
                         '2431')
        self.assertEqual(self.rawscan['M01line']['values']['VM15CNTE']['val'],
                         '2944')

    def testM02line(self):
        """ Test M02line saved to MTP dictionary correctly """
        self.assertEqual(self.rawscan['M02line']['values']['ACCPCNTE']['val'],
                         '2002')
        self.assertEqual(self.rawscan['M02line']['values']['TDATCNTE']['val'],
                         '1345')
        self.assertEqual(self.rawscan['M02line']['values']['TMTRCNTE']['val'],
                         '2069')
        self.assertEqual(self.rawscan['M02line']['values']['TAIRCNTE']['val'],
                         '2239')
        self.assertEqual(self.rawscan['M02line']['values']['TSMPCNTE']['val'],
                         '2166')
        self.assertEqual(self.rawscan['M02line']['values']['TPSPCNTE']['val'],
                         '1506')
        self.assertEqual(self.rawscan['M02line']['values']['TNCCNTE']['val'],
                         '4095')
        self.assertEqual(self.rawscan['M02line']['values']['TSYNCNTE']['val'],
                         '1533')

    def testPtline(self):
        """ Test Ptline saved to MTP dictionary correctly """
        self.assertEqual(self.rawscan['Ptline']['values']['TR350CNTP']['val'],
                         '2175')
        self.assertEqual(self.rawscan['Ptline']['values']['TTCNTRCNTP']['val'],
                         '13808')
        self.assertEqual(self.rawscan['Ptline']['values']['TTEDGCNTP']['val'],
                         '13811')
        self.assertEqual(self.rawscan['Ptline']['values']['TWINCNTP']['val'],
                         '10259')
        self.assertEqual(self.rawscan['Ptline']['values']['TMIXCNTP']['val'],
                         '13368')
        self.assertEqual(self.rawscan['Ptline']['values']['TAMPCNTP']['val'],
                         '13416')
        self.assertEqual(self.rawscan['Ptline']['values']['TNDCNTP']['val'],
                         '13310')
        self.assertEqual(self.rawscan['Ptline']['values']['TR600CNTP']['val'],
                         '14460')

    def testEline(self):
        """ Test Eline saved to MTP dictionary correctly """
        self.assertEqual(self.rawscan['Eline']['values']['TCNT']['val'][0],
                         '020890')
        self.assertEqual(self.rawscan['Eline']['values']['TCNT']['val'][1],
                         '022318')
        self.assertEqual(self.rawscan['Eline']['values']['TCNT']['val'][2],
                         '022138')
        self.assertEqual(self.rawscan['Eline']['values']['TCNT']['val'][3],
                         '019200')
        self.assertEqual(self.rawscan['Eline']['values']['TCNT']['val'][4],
                         '020582')
        self.assertEqual(self.rawscan['Eline']['values']['TCNT']['val'][5],
                         '020097')
