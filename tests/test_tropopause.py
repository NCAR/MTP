###############################################################################
# Test util/tropopause.py
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
import unittest
import numpy
import os
import logging
from io import StringIO
from util.tropopause import Tropopause
from EOLpython.Qlogger.messageHandler import QLogger as logger


class TESTtropopause(unittest.TestCase):

    def setUp(self):
        self.startTropIndex = 0
        self.NUM_RETR_LVLS = 33
        self.ATP = {
            'Temperatures': [201.64767074683957, 214.75018328914618,
                             293.0145730092069, 284.0193997087005,
                             276.09556200337505, 270.5628038683806,
                             268.450372823516, 270.25476196338826,
                             267.67122425928693, 266.44347243721955,
                             265.48428136343483, 264.43199363020506,
                             263.54319766553857, 263.54754004313656,
                             263.4502604714374, 263.09323149784274,
                             262.18916229032334, 261.87733745377534,
                             262.03166145448927, 262.4397227271337,
                             262.29398891879805, 261.5846730883158,
                             260.1590724612972, 256.31787105447853,
                             251.1823264162005, 239.88830475437825,
                             221.42524018882096, 199.15523365499354,
                             186.83304535834557, 202.3131983685151,
                             212.72863126498214, 215.57585116721094,
                             224.89043315101887],
            'Altitudes': [1.1443098613711076e-05, 0.19357551208708249,
                          1.6931555755602745, 3.0927068288847197,
                          4.19232107978569, 4.992062377476394,
                          5.691884472160353, 6.191598028823678,
                          6.591467683830099, 6.891485557157748,
                          7.19132392562074, 7.491230479847108,
                          7.691094650631198, 7.890994910128689,
                          8.040904566739066, 8.190970111754346,
                          8.340786135442803, 8.490835049747648,
                          8.69062382804753, 8.890635302770994,
                          9.19049651676631, 9.490304681767388,
                          9.790321201755775, 10.189587643610805,
                          10.688102793310394, 11.386276295385768,
                          12.186302342366394, 13.38644959165521,
                          15.086201553731398, 17.186678931128654,
                          19.586250448133384, 22.686816117567183,
                          26.18673835348871],
            'RCFIndex': 0,
            'RCFALT1Index': 12,
            'RCFALT2Index': 13,
            'RCFMRIndex': {'val': 4.539470399431716},
            'trop': [{'idx': numpy.nan, 'altc': numpy.nan, 'tempc': numpy.nan}]
        }

        # Instantiate a tropopause class
        self.trop = Tropopause(self.ATP, self.NUM_RETR_LVLS)

        # For testing, we want to capture the log messages in a buffer so we
        # can compare the log output to what we expect.
        self.stream = StringIO()  # Set output stream to buffer

        # Instantiate a logger
        self.log = logger.initLogger(self.stream, logging.INFO)

    def test_findStart(self):
        """ Find index of first retrieval above starting altitude """
        startidx = self.trop.findStart(0, 5.6)

        self.assertEqual(startidx, 6)

    def test_linearLapseRate(self):
        """ Find the first linear lapse rate """
        [lapseRate, i] = self.trop.linearLapseRate(6, 0, -2)
        self.assertEqual(lapseRate, 3.610846885804961)
        self.assertEqual(i, 6)

    def test_averageLapseRate(self):
        """ Find the average lapse rate from this layer to sublayer"""
        LRavg = self.trop.averageLapseRate(6, 2, 12)
        self.assertEqual(LRavg, 0)
        LRavg = self.trop.averageLapseRate(6, 0.02, 12)
        self.assertEqual(LRavg, -4.402080794161457)
        LRavg = self.trop.averageLapseRate(12, 2, 21)
        self.assertEqual(LRavg, 0)
        LRavg = self.trop.averageLapseRate(12, 0.02, 21)
        self.assertEqual(LRavg, -2.5357481642209976)

    def test_findTropopause(self):
        """ Find tropopause """
        [startidx, trop, altctrop, tempctrop] = \
            self.trop.findTropopause(self.startTropIndex)
        self.assertEqual(startidx, 28)
        self.assertEqual(trop, 28)
        self.assertEqual(altctrop, 15.086201553731398)
        self.assertEqual(tempctrop, 186.83304535834557)

        # Test that don't find a second tropopause
        [startidx, trop, altctrop, tempctrop] = \
            self.trop.findTropopause(startidx)
        self.assertEqual(startidx, 28)
        self.assertTrue(numpy.isnan(trop))
        self.assertTrue(numpy.isnan(altctrop))
        self.assertTrue(numpy.isnan(tempctrop))

    def tearDown(self):
        logger.delHandler()
