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


class TESTeng1(unittest.TestCase):

    def setUp(self):
        # Location of default ascii_parms file
        self.ascii_parms = os.path.join(getrootdir(), 'config', 'ascii_parms')
        self.configfile = os.path.join(getrootdir(), 'config', 'proj.yml')
        self.stream = sys.stdout  # Send log messages to stdout
        loglevel = logging.INFO
        logger.initLogger(self.stream, loglevel)

        self.app = QApplication([])
        self.client = MTPclient()
        self.client.config(self.configfile)

        self.args = argparse.Namespace(cnts=False, postprocess=False)

    def test_eng1_noJSON(self):
        """ Test Engineering 1 display window shows what we expect """
        # This first emgineering window shows the Pt line
        # To start, the window just shows "Channel  Counts  Ohms  Temp  "
        # unless there is a json file with data, in which case, data from last
        # record in JSON file will be read in by MTPviewer initializer and
        # displayed.

        # Test with no JSON file
        filename = ""
        self.viewer = MTPviewer(self.client, self.app, filename, self.args)
        self.assertEqual(self.viewer.eng1.toPlainText(),
                         "Channel\tCounts  Ohms  Temp  ")

    def test_eng1_JSON(self):
        # Test with JSON file
        filename = "../tests/test_data/DEEPWAVErf01.mtpRealTime.json"
        self.viewer = MTPviewer(self.client, self.app, filename, self.args)
        self.assertEqual(self.viewer.eng1.toPlainText(),
                         "Channel\tCounts  Ohms  Temp  \n" +
                         "Rref 350\t02174  350.00  \n" +
                         "Target 1\t13808  586.81  +44.64\n" +
                         "Target 2\t13807  586.79  +44.63\n" +
                         "Window\t06689  441.90  -29.63\n" +
                         "Mixer\t13383  578.16  +40.16\n" +
                         "Dblr Amp\t13331  577.10  +39.61\n" +
                         "Noise D.\t13215  574.74  +38.39\n" +
                         "Rref 600\t14456  600.00  ")

        # Send an MTP packet to the parser and confirm it gets parsed
        # correctly
        line = "Pt: 2165 13811 13820 03894 13415 13342 13230 14450"
        mtp = readMTP()
        mtp.parseLine(line)
        values = mtp.rawscan['Ptline']['data'].split(' ')
        mtp.assignPtvalues(values)
        self.assertEqual(mtp.getVar('Ptline', 'TR350CNTP'), '2165')
        self.assertEqual(mtp.getVar('Ptline', 'TTCNTRCNTP'), '13811')
        self.assertEqual(mtp.getVar('Ptline', 'TTEDGCNTP'), '13820')
        self.assertEqual(mtp.getVar('Ptline', 'TWINCNTP'), '03894')
        self.assertEqual(mtp.getVar('Ptline', 'TMIXCNTP'), '13415')
        self.assertEqual(mtp.getVar('Ptline', 'TAMPCNTP'), '13342')
        self.assertEqual(mtp.getVar('Ptline', 'TNDCNTP'), '13230')
        self.assertEqual(mtp.getVar('Ptline', 'TR600CNTP'), '14450')

        # Then check that window displays correct values.
        self.viewer.client.calcPt()
        self.viewer.writeEng1()
        self.assertEqual(self.viewer.eng1.toPlainText(),
                         "Channel\tCounts  Ohms  Temp  \n" +
                         "Rref 350\t02165  350.00  \n" +
                         "Target 1\t13811  587.00  +44.73\n" +
                         "Target 2\t13820  587.18  +44.83\n" +
                         "Window\t03894  385.19  -58.24\n" +
                         "Mixer\t13415  578.94  +40.56\n" +
                         "Dblr Amp\t13342  577.45  +39.79\n" +
                         "Noise D.\t13230  575.17  +38.61\n" +
                         "Rref 600\t14450  600.00  ")

    def tearDown(self):
        self.viewer.close()
        self.app.quit()
