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
import unittest
import numpy
from util.readmtp import readMTP

import sys
import logging
from EOLpython.logger.messageHandler import Logger

logger = Logger("EOLlogger")


class TESTgui(unittest.TestCase):

    def setUp(self):
        self.stream = sys.stdout  # Send log messages to stdout
        loglevel = logging.INFO
        logger.initStream(self.stream, loglevel)

        self.mtp = readMTP()

    def test_getResistance(self):
        """ Test that sending linetype other than Ptline fails """
        self.mtp.setCalcVal('Ptline', 'TR350CNTP', 350.00, 'resistance')
        self.assertEqual(self.mtp.getCalcVal('Ptline', 'TR350CNTP',
                                             'resistance'), 350.00)
        # check that resistance set to NAN for non Ptline
        self.mtp.setCalcVal('M02line', 'ACCPCNTE', 2510, 'resistance')
        check = numpy.isnan(self.mtp.getCalcVal('M02line', 'ACCPCNTE',
                                                'resistance'))
        self.assertTrue(check)

    def test_getTemperature(self):
        """ Test that sending linetype other than Ptline/M02line fails """
        # check that temperature calculated correctly for other Ptline vars
        self.mtp.setCalcVal('Ptline', 'TTCNTRCNTP', 44.73, 'temperature')
        self.assertEqual("%5.2f" % self.mtp.getCalcVal('Ptline', 'TTCNTRCNTP',
                                                       'temperature'), '44.73')
        # check that temperature calculated correctly for M02line vars
        self.mtp.setCalcVal('M02line', 'ACCPCNTE', -0.03, 'temperature')
        self.assertEqual("%5.2f" % self.mtp.getCalcVal('M02line', 'ACCPCNTE',
                                                       'temperature'), '-0.03')
        # check that temperature set to NAN for non Ptline/M02line
        self.mtp.setCalcVal('M01line', 'VM15CNTE', -15.01, 'temperature')
        check = numpy.isnan(self.mtp.getCalcVal('M01line', 'VM15CNTE',
                                                'temperature'))
        self.assertTrue(check)

    def tearDown(self):
        pass
