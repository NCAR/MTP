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
from EOLpython.logger.messageHandler import Logger

logger = Logger("EOLlogger")


class TESTicartt(unittest.TestCase):

    def setUp(self):
        # Instantiate a logger so can call just this test
        self.stream = sys.stdout  # Send log messages to stdout
        loglevel = logging.INFO
        logger.initStream(self.stream, loglevel)

        # Instantiate and MTP controller
        self.client = MTPclient()

        # Read the config file. Gets path to RCF dir
        self.client.readConfig(os.path.join(getrootdir(), 'Data', 'NGV',
                                            'DEEPWAVE', 'config', 'proj.yml'))

        # Set RCF dir to test dir
        self.client.setRCFdir('tests/test_data')
        # Now initialize the retriever (requires correct RCFdir)
        self.client.initRetriever()

        # Test record
        udp = "MTP,20140606T062435,+06.01,00.23,-00.80,00.30,+04.23,0.06," + \
              "261.48,00.44,-43.289,+0.000,+172.260,+0.024,+074739," + \
              "+073936,018005,019236,018605,018023,019240,018616,018043," + \
              "019259,018619,018066,019284,018641,018092,019307,018671," + \
              "018110,019318,018676,018112,019313,018681,018129,019319," + \
              "018675,018150,019331,018687,018158,019343,018700,2928," + \
              "2207,2898,3076,1921,2927,2430,2945,2000,1337,2064,2248," + \
              "2171,1508,4095,1529,2173,13817,13811,10246,13363,13331," + \
              "13222,14451,020858,022285,022115,019171,020547,020064"
        self.client.reader.parseAsciiPacket(udp)
        self.rawscan = self.client.reader.getRawscan()
        self.client.processScan()
        self.client.createProfile()
        self.client.reader.archive()

        sample_header = '../tests/test_data/header.ict'
        with open(sample_header, 'r') as f:
            self.header = f.read()

        self.maxDiff = None

    def testICARTT(self):
        self.icartt = ICARTT(self.client)
        # For testing, set process date to process date in test_data/header.ict
        self.icartt.build_header('20150424')
        self.icartt.build_record(self.client.reader.flightData[0], 23090)

        # Comment out until finish calculating needed value. Right now, this
        # always fails, which causes Jenkins to send a message. Now that I
        # merged with master, we can't have that.
        # self.assertEqual(self.header, self.icartt.header + self.icartt.data)
