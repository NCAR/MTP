###############################################################################
# Test lib/icartt.py
#
# Takes a sample header from the test_data dir and confirms that code generates
# the same header
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
from lib.icartt import ICARTT
from lib.rootdir import getrootdir
from viewer.MTPclient import MTPclient

import sys
import logging
from logger.messageHandler import Logger as logger


class TESTicartt(unittest.TestCase):

    def setUp(self):
        # Instantiate a logger so can call just this test
        self.stream = sys.stdout  # Send log messages to stdout
        loglevel = logging.INFO
        logger.initLogger(self.stream, loglevel)

        # Instantiate and MTP controller
        self.client = MTPclient()

        # Read the config file. Gets path to RCF dir
        self.client.readConfig(os.path.join(getrootdir(),
                               'config', 'proj.yml'))

        # Set RCF dir to test dir
        self.client.setRCFdir('tests/test_data')
        # Now initialize the retriever (requires correct RCFdir)
        self.client.initRetriever()

        # Test record
        udp = "MTP,20140606T062418,+06.49,00.19,-00.79,00.87,+04.00,0.06," + \
              "263.32,00.48,-43.290,+0.005,+172.296,+0.051,+074684," + \
              "+073904,018089,019327,018696,018110,019321,018704,018113," + \
              "019326,018702,018130,019356,018716,018159,019377,018744," + \
              "018174,019392,018756,018178,019394,018758,018197,019397," + \
              "018757,018211,019404,018763,018228,019419,018774,2928," + \
              "2228,2898,3082,1930,2923,2431,2944,2002,1345,2069,2239," + \
              "2166,1506,4095,1533,2175,13808,13811,10259,13368,13416," + \
              "13310,14460,020890,022318,022138,019200,020582,020097"
        self.client.reader.parseAsciiPacket(udp)
        self.rawscan = self.client.reader.getRawscan()
        self.client.processMTP()
        self.client.reader.archive()

        sample_header = '../tests/test_data/header.ict'
        with open(sample_header, 'r') as f:
            self.header = f.read()

        self.maxDiff = None

    def testICARTT(self):
        self.icartt = ICARTT(self.client)
        # For testing, set process date to process date in test_data/header.ict
        self.icartt.build_header('20150424')

        self.assertEqual(self.header, self.icartt.header)
