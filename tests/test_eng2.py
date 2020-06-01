###############################################################################
# GUI-specific unit tests
#
# To run these tests:
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
import argparse
from PyQt5.QtWidgets import QApplication

from viewer.MTPviewer import MTPviewer
from viewer.MTPclient import MTPclient
from util.readmtp import readMTP
from lib.rootdir import getrootdir

import sys
import logging
from EOLpython.logger.messageHandler import Logger as logger


class TESTeng2(unittest.TestCase):

    def setUp(self):
        # Location of default ascii_parms file
        self.ascii_parms = os.path.join(getrootdir(), 'Data', 'NGV',
                                        'DEEPWAVE', 'config', 'ascii_parms')
        self.configfile = os.path.join(getrootdir(), 'Data', 'NGV',
                                       'DEEPWAVE', 'config', 'proj.yml')
        self.stream = sys.stdout  # Send log messages to stdout
        loglevel = logging.INFO
        logger.initLogger(self.stream, loglevel)

        self.app = QApplication([])
        self.client = MTPclient()
        self.client.config(self.configfile)
        self.client.connect_udp()

        self.args = argparse.Namespace(cnts=False, postprocess=False,
                                       realtime=True)

    def test_eng2_noJSON(self):
        """ Test Engineering 2 display window shows what we expect """
        # The second engineering window displays the M01 line
        # To start, window just shows the header: "Channel Counts  Volts"
        # unless there is a json file with data, in which case, data from last
        # record in JSON file will be read in by MTPviewer initializer and
        # displayed.

        # Test with no JSON file
        filename = ""
        self.viewer = MTPviewer(self.client, None, self.app, filename,
                                self.args)
        self.assertEqual(self.viewer.eng2.toPlainText(),
                         "Channel\tCounts  Volts")

    def test_eng2_JSON(self):
        # Test with JSON file
        filename = "../tests/test_data/DEEPWAVErf01.mtpRealTime.json"
        self.viewer = MTPviewer(self.client, None, self.app, filename,
                                self.args)
        self.assertEqual(self.viewer.eng2.toPlainText(),
                         "Channel\tCounts  Volts\n" +
                         "-8V  PS\t2928  -07.99V\n" +
                         "Video V.\t2061  +02.06V\n" +
                         "+8V  PS\t2899  +08.06V\n" +
                         "+24V Step\t3082  +24.01V\n" +
                         "+15V Syn\t1923  +14.98V\n" +
                         "+15V PS\t2922  +14.90V\n" +
                         "VCC  PS\t2430  +04.86V\n" +
                         "-15V PS\t2944  -15.01V")

        # Send an MTP packet to the parser and confirm it gets parsed
        # correctly.
        line = "M01: 2929 2273 2899 3083 1929 2921 2433 2944"
        mtp = readMTP()
        mtp.parseLine(line)
        values = mtp.rawscan['M01line']['data'].split(' ')
        mtp.assignM01values(values)
        self.assertEqual(mtp.getVar('M01line', 'VM08CNTE'), '2929')

        # Then check the window display values
        self.viewer.client.calcM01()
        self.viewer.writeEng2()
        self.maxDiff = None
        self.assertEqual(self.viewer.eng2.toPlainText(),
                         "Channel\tCounts  Volts\n" +
                         "-8V  PS\t2929  -08.00V\n" +
                         "Video V.\t2273  +02.27V\n" +
                         "+8V  PS\t2899  +08.06V\n" +
                         "+24V Step\t3083  +24.02V\n" +
                         "+15V Syn\t1929  +15.03V\n" +
                         "+15V PS\t2921  +14.90V\n" +
                         "VCC  PS\t2433  +04.87V\n" +
                         "-15V PS\t2944  -15.01V")
        self.viewer.close()
        self.app.quit()
