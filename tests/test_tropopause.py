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

    def test_findTwoTropopauses(self):
        """ If there should be two tropopauses, make sure they are found """
        self.startTropIndex = 0
        self.NUM_RETR_LVLS = 33
        self.ATP2 = {
            'Temperatures': [285.29277619837796, 284.9391046887834,
                             275.22585745721324, 265.43706394773767,
                             257.66176195833884, 251.7473227517665,
                             246.5165452580186, 242.7213200919579,
                             239.58618305753458, 237.29889123080966,
                             234.8923779551945, 232.4238951751098,
                             230.71409172681706, 228.8349977253528,
                             227.41536870290545, 226.04075831045594,
                             224.6908965963142, 223.41225306631642,
                             221.74350128537444, 220.17881304172667,
                             218.0848532735625, 216.53731637544328,
                             215.61005841135045, 215.0940185886796,
                             214.9674572152112, 214.2293127098129,
                             212.23152889749747, 207.86963787037368,
                             204.03224961220323, 205.6038047311626,
                             212.4215635869228, 219.097400384303,
                             225.2197442808954],
            'Altitudes': [0.7312923985006143, 2.2309353714408555,
                          3.7305907275278067, 5.130337267577113,
                          6.229996472409457, 7.029821097233241,
                          7.729622625671382, 8.229563049706845,
                          8.629406563365935, 8.929302079468883,
                          9.229214227593767, 9.52905954187316,
                          9.729099783515057, 9.928973039831412,
                          10.078894154233202, 10.228864009509474,
                          10.378844355015765, 10.528530574138689,
                          10.727920825445407, 10.927134496387087,
                          11.226055184777136, 11.5261116472849,
                          11.82627060550164, 12.226150649152498,
                          12.726307866182433, 13.42637109722949,
                          14.226360225495615, 15.426297917866275,
                          17.126223122005165, 19.226237119499388,
                          21.626499832391826, 24.727297231095307,
                          28.228070002725715],
            'RCFIndex': 0,
            'RCFALT1Index': 14,
            'RCFALT2Index': 15,
            'RCFMRIndex': {'val': 0.3486558391214273, 'short_name': 'MRI',
                           'units': '#', 'long_name':
                           'retrieval quality metric \
                           (ranges 0-2, <1 is excellent)',
                           '_FillValue': '-99.9'},
            'trop': {
                     'val': [{'idx': numpy.nan, 'altc': numpy.nan,
                             'tempc': numpy.nan},
                             {'idx': numpy.nan, 'altc': numpy.nan,
                             'tempc': numpy.nan}],
                     'short_name': 'tropopause_altitude',
                     'units': 'km',
                     'long_name': 'Tropopause',
                     '_FillValue': "-99.9"},
        }

        # Instantiate a tropopause class
        self.trop = Tropopause(self.ATP2, self.NUM_RETR_LVLS)
        self.startTropIndex = 0

        # Find a first tropopause
        [self.startTropIndex, self.ATP2['trop']['val'][0]['idx'],
         self.ATP2['trop']['val'][0]['altc'],
         self.ATP2['trop']['val'][0]['tempc']] = \
            self.trop.findTropopause(self.startTropIndex)
        self.assertEqual(self.startTropIndex, 22)
        self.assertEqual(self.ATP2['trop']['val'][0]['idx'], 22)
        self.assertEqual(self.ATP2['trop']['val'][0]['altc'],
                         11.82627060550164)
        self.assertEqual(self.ATP2['trop']['val'][0]['tempc'],
                         215.61005841135045)

        # Find a second tropopause
        [self.startTropIndex, self.ATP2['trop']['val'][1]['idx'],
         self.ATP2['trop']['val'][1]['altc'],
         self.ATP2['trop']['val'][1]['tempc']] = \
            self.trop.findTropopause(self.startTropIndex)
        self.assertEqual(self.startTropIndex, 28)
        self.assertEqual(self.ATP2['trop']['val'][1]['idx'], 28)
        self.assertEqual(self.ATP2['trop']['val'][1]['altc'],
                         17.126223122005165)
        self.assertEqual(self.ATP2['trop']['val'][1]['tempc'],
                         204.03224961220323)

    def tearDown(self):
        logger.delHandler()
