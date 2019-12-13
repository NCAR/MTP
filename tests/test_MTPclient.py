###############################################################################
# Test viewer/MTPclient.py
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
from viewer.MTPclient import MTPclient


class TESTMTPclient(unittest.TestCase):

    def setUp(self):
        self.client = MTPclient()

        self.tb = [259.0284, 260.4983, 261.0111, 260.0887, 260.2379,
                   261.3189, 260.2401, 260.4549, 261.2420, 261.0985,
                   261.7572, 261.7807, 262.5627, 262.6688, 262.8582,
                   263.3200, 263.3200, 263.3200, 263.5220, 263.4068,
                   263.3970, 264.4813, 263.5371, 263.3585, 265.1881,
                   263.8409, 263.5894, 266.0464, 264.4921, 264.0127]

    def test_invertArray(self):
        """ Test that array is inverted correctly """
        tbi = [259.0284, 260.0887, 260.2401, 261.0985, 262.5627,
               263.3200, 263.5220, 264.4813, 265.1881, 266.0464,
               260.4983, 260.2379, 260.4549, 261.7572, 262.6688,
               263.3200, 263.4068, 263.5371, 263.8409, 264.4921,
               261.0111, 261.3189, 261.2420, 261.7807, 262.8582,
               263.3200, 263.3970, 263.3585, 263.5894, 264.0127]

        tbi_returned = self.client.invertArray(self.tb)
        self.assertEqual(tbi, tbi_returned)

    def test_getProfile(self):
        """ Test accurate conversion of brightness temperature to profile """
        tbi = self.client.invertArray(self.tb)

        # If acaltkm is missing or negative, getTemplate returns False
        acaltkm = numpy.nan
        BestWtdRCSet = self.client.getTemplate(acaltkm, tbi)
        self.assertEqual(BestWtdRCSet, False)

        acaltkm = -1.0
        BestWtdRCSet = self.client.getTemplate(acaltkm, tbi)
        self.assertEqual(BestWtdRCSet, False)

        acaltkm = 8.206
        BestWtdRCSet = self.client.getTemplate(acaltkm, tbi)
        ATP = self.client.getProfile(tbi, BestWtdRCSet)

        tempc = [201.64767074683957, 214.75018328914618, 293.0145730092069,
                 284.0193997087005, 276.09556200337505, 270.5628038683806,
                 268.450372823516, 270.25476196338826, 267.67122425928693,
                 266.44347243721955, 265.48428136343483, 264.43199363020506,
                 263.54319766553857, 263.54754004313656, 263.4502604714374,
                 263.09323149784274, 262.18916229032334, 261.87733745377534,
                 262.03166145448927, 262.4397227271337, 262.29398891879805,
                 261.5846730883158, 260.1590724612972, 256.31787105447853,
                 251.1823264162005, 239.88830475437825, 221.42524018882096,
                 199.15523365499354, 186.83304535834557, 202.3131983685151,
                 212.72863126498214, 215.57585116721094, 224.89043315101887]

        altc = [1.1443098613711076e-05, 0.19357551208708249,
                1.6931555755602745, 3.0927068288847197, 4.19232107978569,
                4.992062377476394, 5.691884472160353, 6.191598028823678,
                6.591467683830099, 6.891485557157748, 7.19132392562074,
                7.491230479847108, 7.691094650631198, 7.890994910128689,
                8.040904566739066, 8.190970111754346, 8.340786135442803,
                8.490835049747648, 8.69062382804753, 8.890635302770994,
                9.19049651676631, 9.490304681767388, 9.790321201755775,
                10.189587643610805, 10.688102793310394, 11.386276295385768,
                12.186302342366394, 13.38644959165521, 15.086201553731398,
                17.186678931128654, 19.586250448133384, 22.686816117567183,
                26.18673835348871]

        self.assertEqual(ATP['Temperatures'], tempc)
        self.assertEqual(ATP['Altitudes'], altc)
