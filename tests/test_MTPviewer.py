###############################################################################
# Test viewer/MTPviewer.py
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
###############################################################################
import os
import unittest
import argparse
import logging
from io import StringIO
from PyQt5.QtWidgets import QApplication
from viewer.MTPclient import MTPclient
from viewer.MTPviewer import MTPviewer
from lib.rootdir import getrootdir
from EOLpython.Qlogger.messageHandler import QLogger as logger


class TESTMTPviewer(unittest.TestCase):

    def setUp(self):

        # Set environment var to indicate we are in testing mode
        # Need this to logger won't try to open message boxes
        os.environ["TEST_FLAG"] = "true"

        # For testing, we want to capture the log messages in a buffer so we
        # can compare the log output to what we expect.
        self.stream = StringIO()  # Set output stream to buffer

        # Instantiate a logger
        self.log = logger.initLogger(self.stream, logging.INFO)

        # Location of default config file
        self.configfile = os.path.join(getrootdir(), 'Data', 'NGV',
                                       'DEEPWAVE', 'config', 'proj.yml')

        # Instantiate an MTP controller
        self.client = MTPclient()
        self.args = argparse.Namespace(cnts=False, postprocess=False,
                                       realtime=False)
        self.app = QApplication([])
        self.client.config(self.configfile)

        self.viewer = MTPviewer(self.client, self.app, self.args)

    def test_clickBack(self):
        """ Test clicking back returns to previous scan """
        # Initializing an MTPviewer sets viewScanIndex to -1. If try to go back
        # from there, should get an error.
        self.viewer.clickBack()
        logger.flushHandler()
        self.assertRegex(self.stream.getvalue(),
                         r"ERROR:.*No scans yet. Can't go backward\n")

        # Test with JSON file
        filename = "../tests/test_data/DEEPWAVErf01.mtpRealTime.json"
        self.viewer.loadJson(filename)

        # If on first scan and try to go back, should get error
        self.viewer.viewScanIndex = 0
        self.viewer.clickBack()
        logger.flushHandler()
        self.assertRegex(self.stream.getvalue(),
                         r"ERROR:.*On first scan. Can't go backward\n")

        # If not on last scan, should decrement viewScanIndex by one
        self.viewer.viewScanIndex = 3
        self.viewer.clickBack()
        self.assertEqual(self.viewer.viewScanIndex, 2)

    def test_clickFwd(self):
        """ Test clicking fwd advances to next scan """
        # Initializing an MTPviewer sets currentScanIndex to -1. If try to go
        # fwd from there, should get an error.
        self.viewer.clickFwd()
        logger.flushHandler()
        self.assertRegex(self.stream.getvalue(),
                         r"ERROR:.*On latest scan. Can't go forward\n")

        # Test with JSON file
        filename = "../tests/test_data/DEEPWAVErf01.mtpRealTime.json"
        self.viewer.loadJson(filename)

        # If on last scan and try to go fwd, should get error
        self.viewer.viewScanIndex = 47
        self.viewer.clickFwd()
        logger.flushHandler()
        self.assertRegex(self.stream.getvalue(),
                         r"ERROR:.*On latest scan. Can't go forward\n")

        # If not on last scan, should increment viewScanIndex by one
        self.viewer.viewScanIndex = 3
        self.viewer.clickFwd()
        self.assertEqual(self.viewer.viewScanIndex, 4)

    def tearDown(self):
        self.client.clearData()
        self.viewer.close()
        self.app.quit()
        logger.delHandler()
