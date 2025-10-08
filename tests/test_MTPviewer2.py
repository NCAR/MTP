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
from unittest.mock import patch
import argparse
import logging
from io import StringIO
from viewer.MTPclient import MTPclient
from viewer.MTPviewer import MTPviewer
from PyQt6.QtWidgets import QApplication
from lib.rootdir import getrootdir
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")
# Set environment var to indicate we are in testing mode
# Need this to logger won't try to open message boxes
logger.setDisableMessageBox(True)


class TESTMTPviewer(unittest.TestCase):

    def setUp(self):

        # For testing, we want to capture the log messages in a buffer so we
        # can compare the log output to what we expect.
        self.stream = StringIO()  # Set output stream to buffer

        # Instantiate a logger
        self.log = logger.initStream(self.stream, logging.INFO)

        # Location of default config file
        self.configfile = os.path.join(getrootdir(), 'Data', 'NGV',
                                       'DEEPWAVE', 'config', 'proj.yml')

        # Instantiate an MTP controller
        self.client = MTPclient()
        self.args = argparse.Namespace(cnts=False, postprocess=False,
                                       realtime=False)
        self.app = QApplication([])
        self.client.config(self.configfile)

        with patch.object(MTPviewer, 'setFltno'):
            self.viewer = MTPviewer(self.client, self.app, self.args)

    def test_clickGo(self):
        """ Test that clicking go goes to index selected by user """
        # Test with JSON file
        filename = "../tests/test_data/DEEPWAVErf01.mtpRealTime.json"
        self.viewer.loadJson(filename)

        # If test field is empty return without doing anything
        status = self.viewer.clickGo()
        self.assertEqual(status, None)

        # If user entered a zero, assume they meant 1
        self.viewer.index.setText(str(0))
        self.viewer.clickGo()
        self.assertEqual(self.viewer.index.text(), str(1))

        # Set index > than last scan
        self.viewer.index.setText(str(49))
        self.viewer.clickGo()
        logger.flushHandler()
        self.assertRegex(self.stream.getvalue(),
                         r".*ERROR | .*Select scan in range 1 - " +
                         str(self.viewer.currentScanIndex+1))

    def tearDown(self):
        self.client.clearData()
        self.viewer.close()
        self.app.quit()
        logger.delHandler()
