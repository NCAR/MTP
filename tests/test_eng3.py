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
from lib.rootdir import getrootdir

import sys
import logging
from EOLpython.logger.messageHandler import Logger as logger


class TESTeng3(unittest.TestCase):

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

        self.args = argparse.Namespace(cnts=False, postprocess=False,
                                       realtime=True)

        self.viewer = MTPviewer(self.client, self.app, self.args)

    def test_eng3_noJSON(self):
        """ Test Engineering 3 display window shows what we expect """
        # The third engineering window displays the M02 line
        # To start, window just shows the header: "Channel Counts  Value"
        # unless there is a json file with data, in which case, data from last
        # record in JSON file will be read in by MTPviewer initializer and
        # displayed.

        # Test with no JSON file
        filename = ""
        self.viewer.loadJson(filename)
        self.assertEqual(self.viewer.eng3.toPlainText(),
                         "Channel\tCounts  Value")

    def test_eng3_JSON(self):
        # Test with JSON file
        filename = "../tests/test_data/DEEPWAVErf01.mtpRealTime.json"
        self.viewer.loadJson(filename)
        self.assertEqual(self.viewer.eng3.toPlainText(),
                         "Channel\tCounts  Value\n" +
                         "Acceler\t2061  +01.10 g\n" +
                         "T Data\t1316  +39.51 C\n" +
                         "T Motor\t2188  +18.51 C\n" +
                         "T Pod Air\t2743  +06.16 C\n" +
                         "T Scan\t2697  +07.21 C\n" +
                         "T Pwr Sup\t1591  +32.27 C\n" +
                         "T N/C\t4095  N/A\n" +
                         "T Synth\t1535  +33.67 C")

        # Send an MTP packet to the parser and confirm it gets parsed
        # correctly.
        line = "M02: 2510 1277 1835 1994 1926 1497 4095 1491"
        mtp = self.client.reader
        mtp.parseLine(line)
        values = mtp.rawscan['M02line']['data'].split(' ')
        mtp.assignM02values(values)
        self.assertEqual(mtp.getVar('M02line', 'ACCPCNTE'), '2510')

        # Then check the window display values
        self.client.calcM02()
        self.viewer.writeEng3()
        self.assertEqual(self.viewer.eng3.toPlainText(),
                         "Channel\tCounts  Value\n" +
                         "Acceler\t2510  -00.03 g\n" +
                         "T Data\t1277  +40.62 C\n" +
                         "T Motor\t1835  +26.43 C\n" +
                         "T Pod Air\t1994  +22.81 C\n" +
                         "T Scan\t1926  +24.35 C\n" +
                         "T Pwr Sup\t1497  +34.65 C\n" +
                         "T N/C\t4095  N/A\n" +
                         "T Synth\t1491  +34.80 C")

    # def ():
        # Test plotting of scnt
        # scan1 = self.scnt_inv[0:10]
        # scan2 = self.scnt_inv[10:20]
        # scan3 = self.scnt_inv[20:30]

    def tearDown(self):
        self.viewer.close()
        self.app.quit()
