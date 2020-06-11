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
import os
import copy
import numpy
import unittest
from unittest.mock import mock_open, patch
from util.readmtp import readMTP
from lib.rootdir import getrootdir


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

    def test_parseLine_Aline(self):
        """ Test correct parsing of A line """

        self.mtp.parseLine(self.Aline)
        self.assertEqual(self.mtp.rawscan['Aline']['date'],'20140606T062418')
        self.assertEqual(self.mtp.rawscan['Aline']['data'],
            "+06.49 00.19 -00.79 00.87 +04.00 0.06 263.32 00.48 -43.290 " + \
            "+0.005 +172.296 +0.051 +074684 +073904")

    def test_parseLine_Bline(self):
        """ Test correct parsing of B line """
        self.mtp.parseLine(self.Bline)
        self.assertEqual(self.mtp.rawscan['Bline']['data'],
            "018089 019327 018696 018110 019321 018704 018113 " + \
            "019326 018702 018130 019356 018716 018159 019377 018744 " + \
            "018174 019392 018756 018178 019394 018758 018197 019397 " + \
            "018757 018211 019404 018763 018228 019419 018774")

    def test_parseLine_M01line(self):
        """ Test correct parsing of M01 line """
        self.mtp.parseLine(self.M01line)
        self.assertEqual(self.mtp.rawscan['M01line']['data'],
            "2928 2228 2898 3082 1930 2923 2431 2944")

    def test_parseLine_M02line(self):
        """ Test correct parsing of M02 line """
        self.mtp.parseLine(self.M02line)
        self.assertEqual(self.mtp.rawscan['M02line']['data'],
            "2002 1345 2069 2239 2166 1506 4095 1533")

    def test_parseLine_Ptline(self):
        """ Test correct parsing of Pt line """
        self.mtp.parseLine(self.Ptline)
        self.assertEqual(self.mtp.rawscan['Ptline']['data'],
            "2175 13808 13811 10259 13368 13416 13310 14460")

    def test_parseLine_Eline(self):
        """ Test correct parsing of E line """
        self.mtp.parseLine(self.Eline)
        self.assertEqual(self.mtp.rawscan['Eline']['data'],
            "020890 022318 022138 019200 020582 020097")

    def test_getAsciiPacket(self):
        """ Test the AsciiPacket (MTP packet to be UDPd around the plane)
        is formed correctly
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

    def test_readRawScan(self):
        """
        Test reading a scan from an MTP Raw data file and storing them to a
        dictionary
        """
        # Data to test against
        Aline_date = "20140606T062252"
        Aline_data = "+03.98 00.25 +00.07 00.33 +03.18 0.01 268.08 00.11 " + \
                     "-43.308 +0.009 +172.469 +0.000 +074146 +073392"
        IWGline_date  = "20140606T062250"
        IWGline_data = \
            '-43.3061,172.455,3281.97,,10508.5,,149.998,164.027,,0.502512,' + \
            '3.11066,283.283,281.732,-1.55388,3.46827,0.0652588,-0.258496,' + \
            '2.48881,-5.31801,-5.92311,7.77836,683.176,127.248,1010.48,' + \
            '14.6122,297.157,0.303804,104.277,,-72.1708,'
        IWGline_asciiPacket = \
            'IWG1,20140606T062250,-43.3061,172.455,3281.97,,10508.5,,' + \
            '149.998,164.027,,0.502512,3.11066,283.283,281.732,-1.55388,' + \
            '3.46827,0.0652588,-0.258496,2.48881,-5.31801,-5.92311,' + \
            '7.77836,683.176,127.248,1010.48,14.6122,297.157,0.303804,' + \
            '104.277,,-72.1708,'
        Bline_data = \
            '018963 020184 019593 018971 020181 019593 018970 020170 ' + \
            '019587 018982 020193 019589 018992 020223 019617 019001 ' + \
            '020229 019623 018992 020208 019601 018972 020181 019572 ' + \
            '018979 020166 019558 018977 020161 019554 '
        M01line_data = '2928 2321 2898 3082 1923 2921 2432 2944'
        M02line_data = '2016 1394 2096 2202 2136 1508 4095 1558'
        Ptline_data = '2177 13823 13811 10352 13315 13327 13304 14460'
        Eline_data = '021506 022917 022752 019806 021164 020697 '


        # selectedRawFile is the Raw file listed in the Production dir setup
        # file for the flight the user selected. Hardcode it here for testing
        selectedRawFile = os.path.join(getrootdir(), 'Data', 'NGV', 'DEEPWAVE',
                                       'Raw', 'N2014060606.22')
        with patch('__main__.open', mock_open()):
            with open(selectedRawFile) as raw_data_file:
                status = self.mtp.readRawScan(raw_data_file)

        self.assertEqual(status, True)  # Successful read of a raw data record

        # Until call getAsciiPacket, rawscan['asciiPacket'] should remain empty
        self.assertEqual(self.mtp.rawscan['asciiPacket'], '')

        # Check A line
        # Found status was reset to false by readRawScan on successful read
        self.assertEqual(self.mtp.rawscan['Aline']['found'], False)
        self.assertEqual(self.mtp.rawscan['Aline']['date'], Aline_date)
        self.assertEqual(self.mtp.rawscan['Aline']['data'], Aline_data)
        # All Aline ['values'] should still be missing
        for key in self.mtp.rawscan['Aline']['values']:
            self.assertTrue(numpy.isnan(self.mtp.rawscan['Aline']['values']
                                                           [key]['val']))

        # Check IWG1 line
        self.assertEqual(self.mtp.rawscan['IWG1line']['found'], False)
        self.assertEqual(self.mtp.rawscan['IWG1line']['date'], IWGline_date)
        self.assertEqual(self.mtp.rawscan['IWG1line']['data'], IWGline_data)
        self.assertEqual(self.mtp.rawscan['IWG1line']['asciiPacket'],
             IWGline_asciiPacket)
        # All IWG1line ['values'] should still be missing
        for key in self.mtp.rawscan['IWG1line']['values']:
            self.assertTrue(numpy.isnan(self.mtp.rawscan['IWG1line']
                ['values'][key]['val']))

        # Check B line
        self.assertEqual(self.mtp.rawscan['Bline']['found'], False)
        self.assertEqual(self.mtp.rawscan['Bline']['data'], Bline_data)
        # All Bline ['values'] should still be missing
        for key in self.mtp.rawscan['Bline']['values']:
            for i in range(30):
                self.assertTrue(numpy.isnan(self.mtp.rawscan['Bline']
                    ['values'][key]['val'][i]))
                self.assertTrue(numpy.isnan(self.mtp.rawscan['Bline']
                    ['values'][key]['tb'][i]))

        # Check M01 line
        self.assertEqual(self.mtp.rawscan['M01line']['found'], False)
        self.assertEqual(self.mtp.rawscan['M01line']['data'], M01line_data)
        # All M01line ['values'] should still be missing
        for key in self.mtp.rawscan['M01line']['values']:
            self.assertTrue(numpy.isnan(self.mtp.rawscan['M01line']
                ['values'][key]['val']))
            self.assertTrue(numpy.isnan(self.mtp.rawscan['M01line']
                ['values'][key]['volts']))

        # Check M02 line
        self.assertEqual(self.mtp.rawscan['M02line']['found'], False)
        self.assertEqual(self.mtp.rawscan['M02line']['data'], M02line_data)
        # All M02line ['values'] should still be missing
        for key in self.mtp.rawscan['M02line']['values']:
            self.assertTrue(numpy.isnan(self.mtp.rawscan['M02line']
                ['values'][key]['val']))
            self.assertTrue(numpy.isnan(self.mtp.rawscan['M02line']
                ['values'][key]['temperature']))

        # Check Pt line
        self.assertEqual(self.mtp.rawscan['Ptline']['found'], False)
        self.assertEqual(self.mtp.rawscan['Ptline']['data'], Ptline_data)
        # All Ptline ['values'] should still be missing
        for key in self.mtp.rawscan['Ptline']['values']:
            self.assertTrue(numpy.isnan(self.mtp.rawscan['Ptline']
                ['values'][key]['val']))
            self.assertTrue(numpy.isnan(self.mtp.rawscan['Ptline']
                ['values'][key]['resistance']))
            self.assertTrue(numpy.isnan(self.mtp.rawscan['Ptline']
                ['values'][key]['temperature']))

        # Check E line
        self.assertEqual(self.mtp.rawscan['Eline']['found'], False)
        self.assertEqual(self.mtp.rawscan['Eline']['data'], Eline_data)
        # All Eline ['values'] should still be missing
        for key in self.mtp.rawscan['Eline']['values']:
            for i in range(6):
                self.assertTrue(numpy.isnan(self.mtp.rawscan['Eline']
                    ['values'][key]['val'][i]))
