###############################################################################
# readascii_parms unit tests
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
# COPYRIGHT:   University Corporation for Atmospheric Research, 2020
##############################################################################
import os
import unittest
from util.readascii_parms import AsciiParms

import sys
import logging
from EOLpython.logger.messageHandler import Logger as logger


class TESTreadascii_parms(unittest.TestCase):

    def setUp(self):
        # Setup logging
        self.stream = sys.stdout  # Send log messages to stdout
        loglevel = logging.INFO
        logger.initLogger(self.stream, loglevel)

        # Set environment var to indicate we are in testing mode
        os.environ["TEST_FLAG"] = "true"

    def test_open(self):
        # Test that code finds ascii_parms file or exits with useful error
        self.ascii_parms = AsciiParms("nonexistentFile")
        self.assertFalse(self.ascii_parms.open())

    def tearDown(self):
        if "TEST_FLAG" in os.environ:
            del os.environ['TEST_FLAG']
