###############################################################################
# Test util/rcf_set.py
#
# This program is designed to test the RetrievalCoefficientFileSet class
# to assure that it's performing as expected.
#
# This test uses CSET RCF file NRCKA068.RCF as a test input file.
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
import unittest
from util.rcf_set import RetrievalCoefficientFileSet


class TESTrcfSet(unittest.TestCase):

    def setUp(self):
        self.Directory = "../tests/test_data"
        # Constants the apply specifically to the CSET RCF file in the dir
        # above - NRCKA068.RCF
        self.flightLevelsKm = [13.0, 12.0, 9.5, 8.0, 6.0, 5.0, 3.5, 2.5, 2.0,
                               1.5, 1.0, 0.5, 0.0]
        self.numFlightLevels = len(self.flightLevelsKm)

    def testInit(self):
        """ Test initialization with a bogus directory and empty filelist """
        self.rcf = RetrievalCoefficientFileSet()

        # Test error handling for setting of flight levels on uninitialized
        # set fails
        self.rcf.setFlightLevelsKm(self.flightLevelsKm, self.numFlightLevels)

    def testgetRCFs(self):
        """ Make sure get expected RCFs """
        # Initialize with a valid RCF directory and empty filelist so get
        # everything
        self.rcf = RetrievalCoefficientFileSet()
        self.rcf.getRCFs(self.Directory)

        # Iterate over found RCF files - currently only have one RCF in test
        # dir so can put asserts inside loop (-:
        for RCFs in self.rcf.getRCFVector():
            filename = RCFs.getFileName()
            self.assertEqual(filename, self.Directory + "/NRCKA068.RCF")
            rcfid = RCFs.getId()
            self.assertEqual(rcfid, "NRCKA068")

            rcfhdr = RCFs.getRCF_HDR()
            self.assertEqual(rcfhdr['RAOBcount'], 189)
            self.assertEqual(rcfhdr['NFL'], self.numFlightLevels)
            self.assertEqual('%7.5f' % rcfhdr['SmatrixN2'][0], "-0.00124")

        # Test setting of flight levels for properly initialized RCF set
        self.assertTrue(self.rcf.setFlightLevelsKm(self.flightLevelsKm,
                                                   self.numFlightLevels))

    def testgetBestWeightedRCSet(self):
        """ Validate the function for selecting an RCF (template) from the set
        Provide scan values to getVestWeightedRCSet and verify that the
        correct RCF is selected
        """
        # Initialize with a valid RCF directory and empty filelist so get
        # everything
        self.rcf = RetrievalCoefficientFileSet()
        self.rcf.getRCFs(self.Directory)

        # Verify correct selected RCF
        ACAltKm = 8.206
        scanBTs = [238.371, 240.351, 241.809, 243.789, 246.028, 248.06,
                   249.414, 250.665, 252.123, 254.207, 240.948, 241.837,
                   242.815, 244.682, 246.238, 248.06, 248.682, 249.749,
                   250.238, 251.438, 243.099, 244.25, 245.044, 245.639,
                   246.79, 248.06, 248.893, 249.608, 250.679, 251.433]
        BestWtdRCSet = self.rcf.getBestWeightedRCSet(scanBTs, ACAltKm, 0.0)
        self.assertEqual(BestWtdRCSet['RCFFileName'],
                         self.Directory + "/NRCKA068.RCF")
        self.assertEqual(BestWtdRCSet['RCFId'], 'NRCKA068')
        self.assertEqual('%7.5f' % BestWtdRCSet['SumLnProb'], '0.36811')
        self.assertEqual('%6.2f' % BestWtdRCSet['FL_RCs']['sBP'], '346.27')
        self.assertEqual('%7.5f' % BestWtdRCSet['FL_RCs']['Src'][0],
                         '-1.63965')
        self.assertEqual(len(BestWtdRCSet['FL_RCs']['Src']), 990)
