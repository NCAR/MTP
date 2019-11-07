###############################################################################
# readMTP-specific unit tests. Note that some tests have been split off into
# other test files for clarity
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


class TESTreadmtp(unittest.TestCase):

    def setUp(self):
        self.udp = "MTP,20140606T062418,+06.49,00.19,-00.79,00.87,+04.00," + \
            "0.06,263.32,00.48,-43.290,+0.005,+172.296,+0.051,+074684," + \
            "+073904,018089,019327,018696,018110,019321,018704,018113," + \
            "019326,018702,018130,019356,018716,018159,019377,018744," + \
            "018174,019392,018756,018178,019394,018758,018197,019397," + \
            "018757,018211,019404,018763,018228,019419,018774,2928," + \
            "2228,2898,3082,1930,2923,2431,2944,2002,1345,2069,2239," + \
            "2166,1506,4095,1533,2175,13808,13811,10259,13368,13416," + \
            "13310,14460,020890,022318,022138,019200,020582,020097"
        self.Aline = "A 20140606 06:24:18 +06.49 00.19 -00.79 00.87 +04.00" + \
            " 0.06 263.32 00.48 -43.290 +0.005 +172.296 +0.051 +074684 " + \
            "+073904"
        self.Bline = "B 018089 019327 018696 018110 019321 018704 018113 " + \
            "019326 018702 018130 019356 018716 018159 019377 018744 " + \
            "018174 019392 018756 018178 019394 018758 018197 019397 " + \
            "018757 018211 019404 018763 018228 019419 018774"
        self.M01line = "M01: 2928 2228 2898 3082 1930 2923 2431 2944"
        self.M02line = "M02: 2002 1345 2069 2239 2166 1506 4095 1533"
        self.Ptline = "Pt: 2175 13808 13811 10259 13368 13416 13310 14460"
        self.Eline = "E 020890 022318 022138 019200 020582 020097"

        self.mtp = readMTP()

    def test_getAsciiPacket(self):
        """
        Test the AsciiPacket (MTP packet to be UDPd around the plane) is formed
        correctly
        """
        self.mtp.parseLine(self.Aline)
        self.mtp.parseLine(self.Bline)
        self.mtp.parseLine(self.M01line)
        self.mtp.parseLine(self.M02line)
        self.mtp.parseLine(self.Ptline)
        self.mtp.parseLine(self.Eline)
        UDPpacket = self.mtp.getAsciiPacket()
        self.assertEqual(self.udp, UDPpacket)

    def test_createAline(self):
        """ Test that Aline is rebuilt correctly """
        self.mtp.parseAsciiPacket(self.udp)
        self.mtp.createAdata()
        self.assertEqual(self.mtp.getAline(), self.Aline)

    def test_createBline(self):
        """ Test that Bline is rebuilt correctly """
        self.mtp.parseAsciiPacket(self.udp)
        self.mtp.createBdata()
        self.assertEqual(self.mtp.getBline(), self.Bline)

    def test_createM01line(self):
        """ Test that M01line is rebuilt correctly """
        self.mtp.parseAsciiPacket(self.udp)
        self.mtp.createM01data()
        self.assertEqual(self.mtp.getM01line(), self.M01line)

    def test_createM02line(self):
        """ Test that M02line is rebuilt correctly """
        self.mtp.parseAsciiPacket(self.udp)
        self.mtp.createM02data()
        self.assertEqual(self.mtp.getM02line(), self.M02line)

    def test_createPtline(self):
        """ Test that Ptline is rebuilt correctly """
        self.mtp.parseAsciiPacket(self.udp)
        self.mtp.createPtdata()
        self.assertEqual(self.mtp.getPtline(), self.Ptline)

    def test_createEline(self):
        """ Test that Eline is rebuilt correctly """
        self.mtp.parseAsciiPacket(self.udp)
        self.mtp.createEdata()
        self.assertEqual(self.mtp.getEline(), self.Eline)
