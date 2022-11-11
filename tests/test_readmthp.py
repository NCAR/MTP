###############################################################################
# readMTHP-specific unit tests
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
import numpy
import unittest
import logging
from io import StringIO
from unittest.mock import mock_open, patch
from util.readmthp import readMTHP
from lib.rootdir import getrootdir
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class TESTreadmthp(unittest.TestCase):

    def setUp(self):

        self.mthp = readMTHP()

        # For testing, we want to capture the log messages in a buffer so we
        # can compare the log output to what we expect.
        self.stream = StringIO()  # Set output stream to buffer

        # Instantiate a logger
        self.log = logger.initStream(self.stream, logging.INFO)

        # selectedRawFile is the Raw file listed in the Production dir setup
        # file for the flight the user selected. Hardcode it here for testing
        selectedRawFile = os.path.join(getrootdir(), 'Data', 'NGV', 'TI3GER',
                                       'TB', 'mthp_rf8_mtp_format.csv')
        with patch('__main__.open', mock_open()):
            with open(selectedRawFile) as raw_data_file:
                self.status = self.mthp.readRawScan(raw_data_file)

    def test_readRawScan(self):
        """
        Test reading a scan from an MTHP Raw data file and storing them to a
        dictionary
        """
        self.assertEqual(self.status, True)  # Successful read raw data record

        # Test line parsing
        self.assertEqual(len(self.mthp.vals), 8)  # Line contains expected vals
        self.assertEqual(self.mthp.vals[0], '1651091379.65941')  # time
        self.assertEqual(self.mthp.vals[1], '19.2848747461705')  # latitiude
        self.assertEqual(self.mthp.vals[2], '-156.069267675836')  # longitude
        self.assertEqual(self.mthp.vals[3], '4226.08404835989')  # altitude (m)
        self.assertEqual(self.mthp.vals[4], '11')  # angle index after read
        self.assertEqual(self.mthp.vals[5], '260.152014206036')  # ch1 @ ang 11
        self.assertEqual(self.mthp.vals[6], '261.83892732092')  # ch2 @ ang 11
        self.assertEqual(self.mthp.vals[7].strip(), '262.763664928933')  # ch3

        self.assertEqual(self.mthp.rawscan['Bline']['values']['SCNT']['tb'],
                         [267.066805963801, 269.287445529263, 272.418553255765,
                         265.714228578662, 266.555201844746, 266.96932272842,
                         264.132780586534, 266.903078826458, 267.388471872363,
                         263.140593219671, 265.142902361059, 266.151720117981,
                         264.360006740239, 267.333688102535, 266.782654597477,
                         265.610870369357, 267.324901185195, 263.891134130252,
                         260.900846490533, 263.535000033651, 264.112382820101,
                         260.578599810011, 262.553308657995, 262.231835451778,
                         262.412694293766, 264.907826064686, 264.302788487846,
                         260.152014206036, 261.83892732092, 262.763664928933])

    def test_parseTime(self):
        """ Test conversion from epoch time to UTC """
        self.mthp.parseTime(self.mthp.vals[0])
        self.assertEqual(self.mthp.rawscan['Aline']['values']['DATE']['val'],
                         "20220427")
        self.assertEqual(
            self.mthp.rawscan['Aline']['values']['timestr']['val'], "20:29:39")
        self.assertEqual(
            self.mthp.rawscan['Aline']['values']['TIME']['val'], 73779)

    def test_saveLocation(self):
        """ Test saving lat, lon, alt to dictionary """
        salat = self.mthp.saveLocation('SALAT', '19.2848747461705', numpy.nan)
        self.assertEqual(salat, '19.2848747461705')
        self.assertEqual(self.mthp.rawscan['Aline']['values']['SALAT']['val'],
                         '19.2848747461705')

        salon = self.mthp.saveLocation('SALON', '-156.069267675836', numpy.nan)
        self.assertEqual(salon, '-156.069267675836')
        self.assertEqual(self.mthp.rawscan['Aline']['values']['SALON']['val'],
                         '-156.069267675836')

        saalt = self.mthp.saveLocation('SAPALT', '4226.08404835989', numpy.nan)
        self.assertEqual(saalt, '4226.08404835989')
        self.assertEqual(self.mthp.rawscan['Aline']['values']['SAPALT']['val'],
                         '4226.08404835989')

    def tearDown(self):
        logger.delHandler()
