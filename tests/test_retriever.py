###############################################################################
# Test util/retriever.py
#
# This program is designed to test the Retriever class to assure that it is
# performing as expected.
#
# To run these tests:
#     cd src/
#     python3 -m unittest discover -s ../tests -v
#
# To increase debugging info uncomment this line:
# import faulthandler; faulthandler.enable()
# and then run these tests with the -Xfaulthandler option, e.g.
#
# python3 -Xfaulthandler -m unittest discover -s ../tests -v
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import numpy
import unittest
import os
import logging
from io import StringIO
from util.retriever import Retriever
from EOLpython.Qlogger.messageHandler import QLogger as logger

class TESTretriever(unittest.TestCase):

    def setUp(self):
        self.RCFdir = "../tests/test_data"
        # Constants the apply specifically to the CSET RCF file in the dir
        # above - NRCKA068.RCF
        # Flight levels are determined manually by looking at the levels most
        # flown at during a project
        self.flightLevelsKm = [13.0, 12.0, 9.5, 8.0, 6.0, 5.0, 3.5, 2.5, 2.0,
                               1.5, 1.0, 0.5, 0.0]
        self.numFlightLevels = len(self.flightLevelsKm)
        self.scanBTs = [238.371, 240.351, 241.809, 243.789, 246.028, 248.06,
                        249.414, 250.665, 252.123, 254.207, 240.948, 241.837,
                        242.815, 244.682, 246.238, 248.06, 248.682, 249.749,
                        250.238, 251.438, 243.099, 244.25, 245.044, 245.639,
                        246.79, 248.06, 248.893, 249.608, 250.679, 251.433]
        self.ACAltKm = 8.206

        self.maxDiff = None  # See entire diff when asserts fail

        # Set environment var to indicate we are in testing mode
        os.environ["TEST_FLAG"] = "true"

        # For testing, we want to capture the log messages in a buffer so we
        # can compare the log output to what we expect.
        self.stream = StringIO()  # Set output stream to buffer

        # Instantiate a logger
        self.log = logger.initLogger(self.stream, logging.INFO)

    def test_getRCSet(self):
        """ Test creation of a functioning retrieval_coefficient_fileset """
        Rtr = Retriever(self.RCFdir)

        # Instantiating retriever calls getRCFs which reads RCFs in from
        # RCFdir. There is only one RCF in the test_data dir, so...
        self.assertEqual(len(Rtr.rcf_set._RCFs), 1)

        # Test that BestWtdRcSet returns as expected with spot checks
        BestWtdRcSet = Rtr.getRCSet(self.scanBTs, self.ACAltKm)
        self.assertEqual(BestWtdRcSet['RCFFileName'],
                         '../tests/test_data/NRCKA068.RCF')

        self.assertEqual(BestWtdRcSet['RCFId'], 'NRCKA068')
        self.assertEqual('%8.6f' % BestWtdRcSet['SumLnProb'], '0.368112')
        self.assertEqual(BestWtdRcSet['RCFIndex'], 0)
        self.assertEqual('%6.2f' % BestWtdRcSet['FL_RCs']['sBP'], '346.27')
        self.assertEqual('%7.5f' % BestWtdRcSet['FL_RCs']['Src'][0],
                         '-1.63965')
        self.assertEqual(BestWtdRcSet['FL_RCs']['Spare'], [])
        self.assertEqual(BestWtdRcSet['FL_RCs']['RCFALT1Index'], 12)  # Topit
        self.assertEqual(BestWtdRcSet['FL_RCs']['RCFALT2Index'], 13)  # Botit

        # Test that if acaltkm is missing or negative, getRCSet returns an
        # exception
        ACAltKm = numpy.nan
        try:
            BestWtdRcSet = Rtr.getRCSet(self.scanBTs, ACAltKm)
        except Exception as err:
            self.assertEqual(str(err), "Aircraft altitude must exist and be " +
                             "greater than zero to match template to scan")

        ACAltKm = -1
        try:
            BestWtdRcSet = Rtr.getRCSet(self.scanBTs, ACAltKm)
        except Exception as err:
            self.assertEqual(str(err), "Aircraft altitude must exist and be " +
                             "greater than zero to match template to scan")

        # Should only read in the RCF dir once, so check than len still just 1
        self.assertEqual(len(Rtr.rcf_set._RCFs), 1)

    def test_retriever(self):
        """ Validate retrieved profile """
        # Put together a functioning retrieval_coefficient_fileset
        Rtr = Retriever(self.RCFdir)
        BestWtdRcSet = Rtr.getRCSet(self.scanBTs, self.ACAltKm)

        # Validate that the function for selecting an RCF (template) from the
        # set is still functioning properly.  Provide a couple of scan values
        # and verify that the correct RCF is selected.
        self.ATP = Rtr.retrieve(self.scanBTs, BestWtdRcSet)

        CSETtemperatures = [302.876, 306.119, 299.146, 287.682, 277.022,
                            269.615, 263.658, 260.455, 257.541, 255.615,
                            253.782, 251.916, 250.884, 249.876, 249.072,
                            247.950, 246.511, 245.041, 243.325, 241.652,
                            239.213, 236.930, 234.69, 231.494, 227.767,
                            222.628, 217.153, 210.764, 205.396, 207.846,
                            213.289, 218.629, 225.059]

        for i in range(len(CSETtemperatures)):
            self.assertEqual('%7.3f' % self.ATP['Temperatures'][i],
                             '%7.3f' % CSETtemperatures[i])

        CSETaltitudes = [1.16856e-05, 0.193576, 1.69316, 3.09271, 4.19232,
                         4.99206, 5.69188, 6.1916, 6.59147, 6.89149, 7.19132,
                         7.49123, 7.69109, 7.891, 8.0409, 8.19097, 8.34079,
                         8.49084, 8.69062, 8.89064, 9.1905, 9.4903, 9.79032,
                         10.1896, 10.6881, 11.3863, 12.1863, 13.3864, 15.0862,
                         17.1867, 19.5863, 22.6868, 26.1867]

        for i in range(len(CSETaltitudes)):
            self.assertEqual('%7.4f' % self.ATP['Altitudes'][i],
                             '%7.4f' % CSETaltitudes[i])

        # Should only read in the RCF dir once, so check than len still just 1
        self.assertEqual(len(Rtr.rcf_set._RCFs), 1)

    def tearDown(self):
        logger.delHandler()
        if "TEST_FLAG" in os.environ:
            del os.environ['TEST_FLAG']
