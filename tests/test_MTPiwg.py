###############################################################################
# Test ctrl/util/iwg.py
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
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import os
import numpy
import unittest
from lib.rootdir import getrootdir
from ctrl.util.iwg import MTPiwg


class TESTMTPiwg(unittest.TestCase):

    def setUp(self):

        self.MTPiwg = MTPiwg()

        # Instantiate an instance of an IWG reader
        asciiparms = os.path.join(getrootdir(), 'Data', 'NGV',
                                  'DEEPWAVE', 'config', 'ascii_parms')
        self.MTPiwg.initIWG(asciiparms)

    def test_initIWG(self):
        # Test variable names accurately retrieved from IWG file
        self.assertEqual(self.MTPiwg.pitch, "PITCH")
        self.assertEqual(self.MTPiwg.roll, "ROLL")
        self.assertEqual(self.MTPiwg.paltf, "PALTF")
        self.assertEqual(self.MTPiwg.atx, "ATX")
        self.assertEqual(self.MTPiwg.lat, "GGLAT")
        self.assertEqual(self.MTPiwg.lon, "GGLON")

        # Test default values of each variable set correctly
        self.assertEqual(
            self.MTPiwg.iwgrecord['values'][self.MTPiwg.pitch]['val'],
            self.MTPiwg.defaultPitch)
        self.assertEqual(
            self.MTPiwg.iwgrecord['values'][self.MTPiwg.roll]['val'],
            self.MTPiwg.defaultRoll)
        self.assertTrue(numpy.isnan(
            self.MTPiwg.iwgrecord['values'][self.MTPiwg.paltf]['val']))
        self.assertTrue(numpy.isnan(
           self.MTPiwg.iwgrecord['values'][self.MTPiwg.atx]['val']))
        self.assertTrue(numpy.isnan(
            self.MTPiwg.iwgrecord['values'][self.MTPiwg.lat]['val']))
        self.assertTrue(numpy.isnan(
            self.MTPiwg.iwgrecord['values'][self.MTPiwg.lon]['val']))

    def test_averageIWG_nodata(self):
        # Test no data
        self.assertEqual(self.MTPiwg.averageIWG(), False)
        self.assertTrue(numpy.isnan(self.MTPiwg.sapitch))
        self.assertTrue(numpy.isnan(self.MTPiwg.srpitch))
        self.assertTrue(numpy.isnan(self.MTPiwg.saroll))
        self.assertTrue(numpy.isnan(self.MTPiwg.srroll))
        self.assertTrue(numpy.isnan(self.MTPiwg.sapalt))
        self.assertTrue(numpy.isnan(self.MTPiwg.srpalt))
        self.assertTrue(numpy.isnan(self.MTPiwg.saatx))
        self.assertTrue(numpy.isnan(self.MTPiwg.sratx))
        self.assertTrue(numpy.isnan(self.MTPiwg.salat))
        self.assertTrue(numpy.isnan(self.MTPiwg.srlat))
        self.assertTrue(numpy.isnan(self.MTPiwg.salon))
        self.assertTrue(numpy.isnan(self.MTPiwg.srlon))

        # Test default pitch/roll
        self.assertEqual(self.MTPiwg.getSAPitch(), self.MTPiwg.defaultPitch)
        self.assertEqual(self.MTPiwg.getSARoll(), self.MTPiwg.defaultRoll)

    def test_averageIWG(self):
        self.MTPiwg.scanIWGlist = \
            [{'values': {
                'GGLAT': {'val': '-43.483795', 'idx': 2},
                'GGLON': {'val': '172.53812', 'idx': 3},
                'PALTF': {'val': '8.7217455', 'idx': 6},
                'PITCH': {'val': '11.723514', 'idx': 16},
                'ROLL': {'val': '-0.7392261', 'idx': 17},
                'ATX': {'val': '9.868251', 'idx': 20}}},
             {'values': {
                'GGLAT': {'val': '-43.4832', 'idx': 2},
                'GGLON': {'val': '172.53879', 'idx': 3},
                'PALTF': {'val': '96.38735', 'idx': 6},
                'PITCH': {'val': '11.161944', 'idx': 16},
                'ROLL': {'val': '-0.8686588', 'idx': 17},
                'ATX': {'val': '9.654987', 'idx': 20}}},
             {'values': {
                'GGLAT': {'val': '-43.4826', 'idx': 2},
                'GGLON': {'val': '172.53946', 'idx': 3},
                'PALTF': {'val': '152.50584', 'idx': 6},
                'PITCH': {'val': '10.844309', 'idx': 16},
                'ROLL': {'val': '-0.7149133', 'idx': 17},
                'ATX': {'val': '9.528961', 'idx': 20}}},
             {'values': {
                'GGLAT': {'val': '-43.482', 'idx': 2},
                'GGLON': {'val': '172.54015', 'idx': 3},
                'PALTF': {'val': '208.21182', 'idx': 6},
                'PITCH': {'val': '10.892206', 'idx': 16},
                'ROLL': {'val': '-0.98706937', 'idx': 17},
                'ATX': {'val': '9.428931', 'idx': 20}}},
             {'values': {
                'GGLAT': {'val': '-43.48139', 'idx': 2},
                'GGLON': {'val': '172.54082', 'idx': 3},
                'PALTF': {'val': '263.29666', 'idx': 6},
                'PITCH': {'val': '11.091804', 'idx': 16},
                'ROLL': {'val': '-1.2203641', 'idx': 17},
                'ATX': {'val': '9.303497', 'idx': 20}}}]

        self.assertEqual(self.MTPiwg.averageIWG(), True)
        self.assertEqual("%+06.2f " % float(self.MTPiwg.sapitch), "+11.14 ")
        self.assertEqual("%05.2f " % float(self.MTPiwg.srpitch), "00.31 ")
        self.assertEqual("%+06.2f " % float(self.MTPiwg.saroll), "-00.91 ")
        self.assertEqual("%05.2f " % float(self.MTPiwg.srroll), "00.18 ")
        self.assertEqual("%+06.2f " % float(self.MTPiwg.sapalt), "+145.82 ")
        self.assertEqual("%04.2f " % float(self.MTPiwg.srpalt), "88.29 ")
        self.assertEqual("%+06.2f " % float(self.MTPiwg.saatx), "+09.56 ")
        self.assertEqual("%05.2f " % float(self.MTPiwg.sratx), "00.19 ")
        self.assertEqual("%+07.3f " % float(self.MTPiwg.salat), "-43.483 ")
        self.assertEqual("%+06.3f " % float(self.MTPiwg.srlat), "+0.001 ")
        self.assertEqual("%+07.3f " % float(self.MTPiwg.salon), "+172.539 ")
        self.assertEqual("%+06.3f " % float(self.MTPiwg.srlon), "+0.001 ")

        # Test palt in km
        # Convert after average
        self.assertEqual("%08.6f" % float(self.MTPiwg.getSAPalt()), "0.044447")
        self.assertEqual("%08.6f" % float(self.MTPiwg.getSRPalt()), "0.026912")
        # Convert before average
        for iwgrec in self.MTPiwg.scanIWGlist:
            iwgrec['values']['PALTF']['val'] = \
                float(iwgrec['values']['PALTF']['val']) * 0.0003048
        valueList = self.MTPiwg.getVals(self.MTPiwg.paltf)
        self.assertEqual("%08.6f" % self.MTPiwg.avg(valueList), "0.044447")
        self.assertEqual("%08.6f" % self.MTPiwg.rmse(valueList, 0.044447),
                         "0.026912")

        # Test atx in K
        # Convert after average
        self.assertEqual("%08.6f" % float(self.MTPiwg.getSAAtx()),
                         "282.706925")
        self.assertEqual("%08.6f" % float(self.MTPiwg.getSRAtx()), "0.193871")
        # Convert before average
        for iwgrec in self.MTPiwg.scanIWGlist:
            iwgrec['values']['ATX']['val'] = \
                float(iwgrec['values']['ATX']['val']) + 273.15
        valueList = self.MTPiwg.getVals(self.MTPiwg.atx)
        self.assertEqual("%08.6f" % self.MTPiwg.avg(valueList), "282.706925")
        self.assertEqual("%08.6f" % self.MTPiwg.rmse(valueList, 282.706925),
                         "0.193871")

    def test_averageIWG_missing(self):
        # Then add a missing rec and test that values are correct
        self.MTPiwg.scanIWGlist = \
            [{'values': {
                'GGLAT': {'val': '-43.483795', 'idx': 2},
                'GGLON': {'val': '172.53812', 'idx': 3},
                'PALTF': {'val': '8.7217455', 'idx': 6},
                'PITCH': {'val': '11.723514', 'idx': 16},
                'ROLL': {'val': '-0.7392261', 'idx': 17},
                'ATX': {'val': '9.868251', 'idx': 20}}},
             {'values': {
                'GGLAT': {'val': '-43.4832', 'idx': 2},
                'GGLON': {'val': '172.53879', 'idx': 3},
                'PALTF': {'val': '96.38735', 'idx': 6},
                'PITCH': {'val': '11.161944', 'idx': 16},
                'ROLL': {'val': '-0.8686588', 'idx': 17},
                'ATX': {'val': '9.654987', 'idx': 20}}},
             {'values': {
                'GGLAT': {'val': '-43.4826', 'idx': 2},
                'GGLON': {'val': '172.53946', 'idx': 3},
                'PALTF': {'val': '152.50584', 'idx': 6},
                'PITCH': {'val': '10.844309', 'idx': 16},
                'ROLL': {'val': '-0.7149133', 'idx': 17},
                'ATX': {'val': '9.528961', 'idx': 20}}},
             {'values': {
                'GGLAT': {'val': '-43.482', 'idx': 2},
                'GGLON': {'val': '172.54015', 'idx': 3},
                'PALTF': {'val': '208.21182', 'idx': 6},
                'PITCH': {'val': '10.892206', 'idx': 16},
                'ROLL': {'val': '-0.98706937', 'idx': 17},
                'ATX': {'val': '9.428931', 'idx': 20}}},
             {'values': {  # Missing rec
                'GGLAT': {'val': '', 'idx': 2},
                'GGLON': {'val': '', 'idx': 3},
                'PALTF': {'val': '', 'idx': 6},
                'PITCH': {'val': '', 'idx': 16},
                'ROLL': {'val': '', 'idx': 17},
                'ATX': {'val': '', 'idx': 20}}}]

        self.assertEqual(self.MTPiwg.averageIWG(), True)
        self.assertEqual("%+06.2f " % float(self.MTPiwg.sapitch), "+11.16 ")
        self.assertEqual("%05.2f " % float(self.MTPiwg.srpitch), "00.35 ")
        self.assertEqual("%+06.2f " % float(self.MTPiwg.saroll), "-00.83 ")
        self.assertEqual("%05.2f " % float(self.MTPiwg.srroll), "00.11 ")
        self.assertEqual("%+06.2f " % float(self.MTPiwg.sapalt), "+116.46 ")
        self.assertEqual("%04.2f " % float(self.MTPiwg.srpalt), "73.70 ")
        self.assertEqual("%+06.2f " % float(self.MTPiwg.saatx), "+09.62 ")
        self.assertEqual("%05.2f " % float(self.MTPiwg.sratx), "00.16 ")
        self.assertEqual("%+07.3f " % float(self.MTPiwg.salat), "-43.483 ")
        self.assertEqual("%+06.3f " % float(self.MTPiwg.srlat), "+0.001 ")
        self.assertEqual("%+07.3f " % float(self.MTPiwg.salon), "+172.539 ")
        self.assertEqual("%+06.3f " % float(self.MTPiwg.srlon), "+0.001 ")

    def test_missingPaltAtx(self):
        # Confirm return missing without unit conversion applied
        self.MTPiwg.sapalt = numpy.nan
        self.MTPiwg.srpalt = numpy.nan
        self.MTPiwg.saatx = numpy.nan
        self.assertTrue(numpy.isnan(self.MTPiwg.getSAAtx()))
        self.assertTrue(numpy.isnan(self.MTPiwg.getSRPalt()))
