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
import os
import unittest
import numpy
from viewer.MTPclient import MTPclient
from lib.rootdir import getrootdir


class TESTMTPclient(unittest.TestCase):

    def setUp(self):

        os.environ["TEST_FLAG"] = "true"

        # Instantiate and MTP controller
        self.client = MTPclient()

        # Read the config file. Gets path to RCF dir
        self.client.readConfig(os.path.join(getrootdir(),
                               'config', 'proj.yml'))
        self.client.checkRCF()
        self.client.initIWG()

        # Set RCF dir to test dir
        self.client.setRCFdir('tests/test_data')

        # Now initialize the retriever (requires correct RCFdir)
        self.client.initRetriever()

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

        tempc = [201.6476707, 214.7501833, 293.0145730,
                 284.0193997, 276.0955620, 270.5628039,
                 268.4503728, 270.254762, 267.6712243,
                 266.4434724, 265.4842814, 264.4319936,
                 263.5431977, 263.5475400, 263.4502605,
                 263.0932315, 262.1891623, 261.8773375,
                 262.0316615, 262.4397227, 262.2939889,
                 261.5846731, 260.1590725, 256.3178711,
                 251.1823264, 239.8883048, 221.4252402,
                 199.1552337, 186.8330454, 202.3131984,
                 212.7286313, 215.5758512, 224.8904332]

        altc = [1.14e-05, 0.1935755,
                1.6931556, 3.0927068, 4.1923211,
                4.9920624, 5.6918845, 6.1915980,
                6.5914677, 6.8914856, 7.1913239,
                7.4912305, 7.6910947, 7.8909949,
                8.0409046, 8.1909701, 8.3407861,
                8.4908350, 8.6906238, 8.8906353,
                9.1904965, 9.4903047, 9.7903212,
                10.1895876, 10.6881028, 11.3862763,
                12.1863023, 13.3864496, 15.0862016,
                17.1866789, 19.5862504, 22.6868161,
                26.1867384]

        ATPTempc = [round(val, 7) for val in ATP['Temperatures']]
        ATPAltc = [round(val, 7) for val in ATP['Altitudes']]
        self.assertEqual(ATPTempc, tempc)
        self.assertEqual(ATPAltc, altc)
        self.assertEqual(len(ATP['trop']['val']), 2)

        # Call getProfile again and make overwrites ATP['trop']['val'] so
        # length still 2 and not 4
        ATP = self.client.getProfile(tbi, BestWtdRCSet)
        self.assertEqual(len(ATP['trop']['val']), 2)

    def tearDown(self):
        if "TEST_FLAG" in os.environ:
            del os.environ['TEST_FLAG']
