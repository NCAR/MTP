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
import logging
from io import StringIO
from unittest.mock import mock_open, patch
from util.readmtp import readMTP
from lib.rootdir import getrootdir
from pathlib import Path
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


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

        # For testing, we want to capture the log messages in a buffer so we
        # can compare the log output to what we expect.
        self.stream = StringIO()  # Set output stream to buffer

        # Instantiate a logger
        self.log = logger.initStream(self.stream, logging.INFO)

    def test_parseLine_Aline(self):
        """ Test correct parsing of A line """

        self.mtp.parseLine(self.Aline)
        self.assertEqual(self.mtp.rawscan['Aline']['date'], '20140606T062418')
        self.assertEqual(self.mtp.rawscan['Aline']['data'],
                         "+06.49 00.19 -00.79 00.87 +04.00 0.06 263.32 00.48" +
                         " -43.290 +0.005 +172.296 +0.051 +074684 +073904")

    def test_parseLine_Bline(self):
        """ Test correct parsing of B line """
        self.mtp.parseLine(self.Bline)
        self.assertEqual(self.mtp.rawscan['Bline']['data'],
                         "018089 019327 018696 018110 019321 018704 018113 " +
                         "019326 018702 018130 019356 018716 018159 019377 " +
                         "018744 018174 019392 018756 018178 019394 018758 " +
                         "018197 019397 018757 018211 019404 018763 018228 " +
                         "019419 018774")

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

    def test_getVarArray(self):
        """ Test getting an array of values for a variable """
        # Save some test data to the dictionary
        self.mtp.parseLine(self.Aline)  # Save Aline to rawscan 'data' var
        # Parse 'data' line into vars in Aline
        self.mtp.assignAvalues(self.mtp.rawscan['Aline']['data'].split())
        self.mtp.parseLine(self.Eline)  # Save Eline to rawscan 'data' var
        # Parse 'data' line into vars in Eline
        self.mtp.assignEvalues(self.mtp.rawscan['Eline']['data'].split())

        # Copy rawscan to flightData[0]
        self.mtp.flightData = []
        self.mtp.flightData.append(self.mtp.rawscan)

        # Get back list of vals for SAPITCH - will be one val since we only
        # loaded one record
        vals = self.mtp.getVarArray('Aline', 'SAPITCH')
        # Test getVarArray with timeseries line
        self.assertEqual(vals, ['+06.49'])

        # Try to get back using getVarArrayi - will fail
        vals = self.mtp.getVarArrayi('Aline', 'SAPITCH', 0)
        # Test getVarArray with timeseries line
        self.assertEqual(vals, None)

        # Test getVarArrayi with timeseries of lists
        # Get back list of vals for TCNT[0] - will be one val since we only
        # loaded one record
        vals = self.mtp.getVarArrayi('Eline', 'TCNT', 0)
        self.assertEqual(vals, [20890])

        # Try to get back using getVarArray - will fail
        vals = self.mtp.getVarArray('Eline', 'TCNT')
        self.assertEqual(vals, None)

    def test_getVarList(self):
        """ Test getting list of vars from an MTP line """
        vars = self.mtp.getVarList('Eline')
        self.assertEqual(vars, ['TCNT'])
        vars = self.mtp.getVarList('Aline')
        self.assertEqual(vars, ['DATE', 'timestr', 'TIME', 'SAPITCH',
                                'SRPITCH', 'SAROLL', 'SRROLL', 'SAPALT',
                                'SRPALT', 'SAAT', 'SRAT', 'SALAT', 'SRLAT',
                                'SALON', 'SRLON', 'SMCMD', 'SMENC'])

    def test_readRawScan(self):
        """
        Test reading a scan from an MTP Raw data file and storing them to a
        dictionary
        """
        # Data to test against
        Aline_date = "20140606T062252"
        Aline_data = "+03.98 00.25 +00.07 00.33 +03.18 0.01 268.08 00.11 " + \
                     "-43.308 +0.009 +172.469 +0.000 +074146 +073392"
        IWGline_date = "20140606T062250"
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

    def testClearFlightData(self):
        # Read in some data
        # selectedRawFile is the Raw file listed in the Production dir setup
        # file for the flight the user selected. Hardcode it here for testing
        selectedRawFile = os.path.join(getrootdir(), 'Data', 'NGV', 'DEEPWAVE',
                                       'Raw', 'N2014060606.22')
        self.mtp.flightData = []
        with patch('__main__.open', mock_open()):
            with open(selectedRawFile) as raw_data_file:
                status = self.mtp.readRawScan(raw_data_file)

                # Copy rawscan to flightData
                self.mtp.flightData.append(self.mtp.rawscan)

        self.assertEqual(status, True)  # Successful read of a raw data record
        self.assertNotEqual(len(self.mtp.flightData), 0)

        self.mtp.clearFlightData()
        self.assertEqual(len(self.mtp.flightData), 0)

    def testRemoveJSON(self):
        """ Test that JSON file is actually removed """
        # Create a json file to run test on
        testFile = "./test.json"
        Path(testFile).touch()

        self.mtp.removeJSON(testFile)
        self.assertFalse(os.path.exists(testFile))

    def test_testATP(self):
        """ Test checking if ATP data exists """

        # Save some test data to the dictionary
        self.mtp.parseLine(self.Aline)  # Save Aline to rawscan 'data' var
        # Parse 'data' line into vars in Aline
        self.mtp.assignAvalues(self.mtp.rawscan['Aline']['data'].split())
        self.mtp.parseLine(self.Eline)  # Save Eline to rawscan 'data' var
        # Parse 'data' line into vars in Eline
        self.mtp.assignEvalues(self.mtp.rawscan['Eline']['data'].split())

        # Copy rawscan to flightData[0]
        self.mtp.flightData = []
        self.mtp.flightData.append(self.mtp.rawscan)

        # At this point, record does not have a temperature profile, so testATP
        # should raise an exception.
        try:  # Test with index explicitely given
            ATPindex = self.mtp.testATP(0)
            self.fail("test did not raise exception when it should")
        except Exception:
            self.assertRaises(TypeError)

        # Add a second record
        self.mtp.flightData.append(copy.deepcopy(self.mtp.rawscan))

        try:  # Test where it loops through available indices (currenty only 2)
            ATPindex = self.mtp.testATP()
            self.fail("test did not raise exception when it should")
        except Exception:
            self.assertRaises(TypeError)

        # Save some ATP data to the second record
        self.ATP = {
            "Temperatures": [numpy.nan, numpy.nan, numpy.nan, numpy.nan,
                             numpy.nan, 285.991221599588, 282.1991538448363,
                             276.91784151018356, 271.93707879815145,
                             268.4843641965844, 265.79099333858017,
                             263.9570950783439, 263.93676566278367,
                             265.12858811974337, 266.7712908670056,
                             267.74539400934407, 267.3757391329155,
                             266.92210215323735, 266.52477149578095,
                             266.27152317630976, 265.27666823297903,
                             263.69450395801283, 262.07832135889896,
                             259.7527727573438, 255.9491328577825,
                             250.659604934907, 243.35775430806373,
                             232.14908495942655, 216.6290491888501,
                             212.8365762810815, 214.23430412364627,
                             212.83876584311477, 214.86413289929013],
            "Altitudes": [numpy.nan, numpy.nan, numpy.nan, numpy.nan,
                          numpy.nan, 0.2353068904202467, 0.7783906486897896,
                          1.161080854973117, 1.5608247489892135,
                          1.860750042842486, 2.160582615859046,
                          2.4604135247808356, 2.6603578130517613,
                          2.860261197429454, 3.010216730638362,
                          3.1600564313081194, 3.3100040496335597,
                          3.459984892374451, 3.6598287921095545,
                          3.8597621787929426, 4.159582654826694,
                          4.45944384947284, 4.7593441904534615,
                          5.159098030323642, 5.65873774918837,
                          6.358469372343037, 7.157905247467961,
                          8.357191105968385, 10.056147508372693,
                          12.149115325855126, 14.548906190772062,
                          17.649503602691457, 21.148526183448475],
            "RCFIndex": 52, "RCFALT1Index": 12, "RCFALT2Index": 13,
            "RCFMRIndex": {"val": 0.6341593516079854, "short_name": "MRI",
                           "units": "#", "long_name": "retrieval quality \
                           metric (ranges 0-2, <1 is excellent)",
                           "_FillValue": "-99.9"},
            "trop": {"val": [{"idx": 28, "altc": 10.056147508372693,
                              "tempc": 216.6290491888501},
                             {"idx": numpy.nan, "altc": numpy.nan,
                              "tempc": numpy.nan}],
                     "short_name": "tropopause_altitude", "units": "km",
                     "long_name": "Tropopause", "_FillValue": "-99.9"}
        }
        self.mtp.flightData[1]['ATP'] = copy.deepcopy(self.ATP)

        # Test first rec
        try:  # Test with index explicitely given
            ATPindex = self.mtp.testATP(0)
            self.fail("test did not raise exception when it should")
        except Exception:
            self.assertRaises(TypeError)

        # Test second rec
        try:  # Test with index explicitely given
            ATPindex = self.mtp.testATP(1)
            self.assertEqual(ATPindex, 1)
        except Exception:
            # Should not get here
            self.fail("test raised Exception when it shouldn't")

        # Test looping through recs
        try:
            ATPindex = self.mtp.testATP()
            self.assertEqual(ATPindex, 1)
        except Exception:
            # Should not get here
            self.fail("test raised Exception when it shouldn't")

    def tearDown(self):
        logger.delHandler()
