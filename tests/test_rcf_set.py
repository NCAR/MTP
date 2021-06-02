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
import os
import unittest
from util.rcf_set import RetrievalCoefficientFileSet

import logging
from io import StringIO
from EOLpython.logger.messageHandler import Logger as logger


class TESTrcfSet(unittest.TestCase):

    def setUp(self):

        # Set environment var to indicate we are in testing mode
        # Need this to logger won't try to open message boxes
        os.environ["TEST_FLAG"] = "true"

        # Set up logging
        self.stream = StringIO()  # Set output stream to buffer
        loglevel = logging.INFO
        logger.initLogger(self.stream, loglevel)

        self.Directory = "../tests/test_data"
        # Constants the apply specifically to the CSET RCF file in the dir
        # above - NRCKA068.RCF
        self.flightLevelsKm = [[] for i in range(4)]
        self.flightLevelsKm[0] = [14.0, 13.5, 13.0, 12.5, 12.0, 11.0, 9.0,
                                  7.0, 5.0, 3.5, 2.0, 1.0, 0.0, 0.0, 0.0,
                                  0.0, 0.0, 0.0, 0.0, 0.0]
        self.flightLevelsKm[1] = [13.0, 12.0, 9.5, 8.0, 6.0, 5.0, 3.5, 2.5,
                                  2.0, 1.5, 1.0, 0.5, 0.0]
        self.flightLevelsKm[2] = [13.0, 12.0, 9.5, 8.0, 6.0, 5.0, 3.5, 2.5,
                                  2.0, 1.5, 1.0, 0.5, 0.0]
        self.flightLevelsKm[3] = [13.0, 12.0, 9.5, 8.0, 6.0, 5.0, 3.5, 2.5,
                                  2.0, 1.5, 1.0, 0.5, 0.0]
        self.numFlightLevels = len(self.flightLevelsKm[3])

    def testInit(self):
        """ Test initialization with a bogus directory and empty filelist """
        self.rcf = RetrievalCoefficientFileSet()

        # Test error handling for setting of flight levels on uninitialized
        # set fails
        status = self.rcf.setFlightLevelsKm(self.flightLevelsKm,
                                            self.numFlightLevels)
        self.assertFalse(status)

    def testgetRCFs(self):
        """ Make sure get expected RCFs """
        # Initialize with a valid RCF directory and empty filelist so get
        # everything
        self.rcf = RetrievalCoefficientFileSet()
        self.rcf.getRCFs(self.Directory)

        # Iterate over found RCF files - currently using
        # more than one file, so first make an array containing
        # the expected values
        filenameList = [self.Directory + "/NRCDE067.RCF",
                        self.Directory + "/NRCDF067.RCF",
                        self.Directory + "/NRCDG067.RCF",
                        self.Directory + "/NRCKA068.RCF"]

        rcfidList = ["NRCDE067",
                     "NRCDF067",
                     "NRCDG067",
                     "NRCKA068"]

        RAOBcountList = [185, 206, 223, 189]

        SmatrixN2List = ["-0.00166", "-0.00155", "-0.00166", "-0.00124"]

        i = 0
        for RCFs in self.rcf.getRCFVector():
            filename = RCFs.getFileName()
            self.assertEqual(filename, filenameList[i])
            rcfid = RCFs.getId()
            self.assertEqual(rcfid, rcfidList[i])

            rcfhdr = RCFs.getRCF_HDR()
            self.assertEqual(rcfhdr['RAOBcount'], RAOBcountList[i])
            self.assertEqual(rcfhdr['NFL'], self.numFlightLevels)
            self.assertEqual('%7.5f' % rcfhdr['SmatrixN2'][0],
                             SmatrixN2List[i])

            print(i)
            # Test setting of flight levels for properly initialized RCF set
            self.assertTrue(self.rcf.setFlightLevelsKm(self.flightLevelsKm[i],
                                                       self.numFlightLevels))

            i += 1
        ''' Comment out this section since there aren't any files in
        the /RC directory now
        # Initialize with a valid RCF directory and empty filelist so get
        # everything
        self.rcf = RetrievalCoefficientFileSet()
        self.rcf.getRCFs(self.Directory+"/RC")

        # Iterate over found RCF files.
        files = []
        for RCFs in self.rcf.getRCFVector():
            files.append(RCFs.getFileName())

        # Expect to find:
        testfiles = ["../tests/test_data/RC/NRCKA068.RCF"]
        self.assertEqual(sorted(files), sorted(testfiles))

        # Now just ask for two of three files
        self.rcf = RetrievalCoefficientFileSet()
        self.rcf.getRCFs(self.Directory+"/RC", ["NRCDE067", "NRCDF067"])

        # Iterate over found RCF files.
        files = []
        for RCFs in self.rcf.getRCFVector():
            files.append(RCFs.getFileName())

        # Expect to find:
        testfiles = ["../tests/test_data/RC/NRCDE067.RCF",
                     "../tests/test_data/RC/NRCDF067.RCF"]
        self.assertEqual(sorted(files), sorted(testfiles))
        '''

    def testgetRCFsERR(self):
        """ Test that correct error msgs are triggered """
        # Simulate a typo in one filename.
        self.rcfset = RetrievalCoefficientFileSet()
        try:
            self.rcfset.getRCFs(self.Directory, ["NRCDE067", "NRCDA067"])
        except Exception:
            # Iterate over found RCF files.
            files = []
            for RCFs in self.rcfset.getRCFVector():
                files.append(RCFs.getFileName())
            # Should find one of the two files
            self.assertEqual(len(files), 1)

            # Expect to find:
            testfiles = ["../tests/test_data/NRCDE067.RCF"]
            self.assertEqual(sorted(files), sorted(testfiles))

            # Test that user was shown appropriate error message
            logger.flushHandler()
            self.assertRegex(self.stream.getvalue(),
                             "ERROR:.*Failed to make fileset. Requested " +
                             "RCF file NRCDA067 does not exist in RCFdir" +
                             " ../tests/test_data")

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

    def testgetWeightedRCSet(self):
        """ Validate the function for getting data for a new RCF given
        an RC4R. To demonstrate that it is working correctly, it should
        show that the input RC4R is not changed and that the correct RC4R
        is output.
        """
        # First, get a valid RC4R via the getBestWeightedRCSet function
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

        # Now that a valid RC4R has been gathered, get a new one
        secondBestWtdRCSet = self.rcf.getWeightedRCSet(BestWtdRCSet,
                                                       2, ACAltKm)
        print(secondBestWtdRCSet['RCFArray'])
        # Show that the RCFArray is the same (not making the first the second,
        # for example)
        self.assertEqual(BestWtdRCSet['RCFArray'],
                         secondBestWtdRCSet['RCFArray'])
        # And show that the first and second are different (actually made a new
        # dictionary instead of just copying a reference)
        self.assertNotEqual(BestWtdRCSet['RCFId'],
                            secondBestWtdRCSet['RCFId'])

        # Show that the elements of the RCFArray are correctly sorted
        # (Should maybe be in the previous test)
        prevElem = secondBestWtdRCSet['RCFArray'][0][1]
        for i in range(len(secondBestWtdRCSet['RCFArray'])):
            self.assertGreaterEqual(secondBestWtdRCSet['RCFArray'][i][1],
                                    prevElem)
            prevElem = secondBestWtdRCSet['RCFArray'][i][1]

    def tearDown(self):
        logger.delHandler()
        if "TEST_FLAG" in os.environ:
            del os.environ['TEST_FLAG']
