###############################################################################
# readGVnc-specific unit tests
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
from random import seed
from random import randint
from util.readGVnc import readGVnc

import sys
import logging
from EOLpython.logger.messageHandler import Logger as logger


class TESTreadgvnc(unittest.TestCase):

    def setUp(self):
        """
        To convert an MTP RAW file (NG20140606.RAW) to the corresponding RNG
        file, the VB6 code replaces the field-phase values of PALT_A and ATRL
        with values from the QC'd LRT data. Due to the fact that the final LRT
        data is not available before the final MTP data is due to the archive,
        the MTP PI traditionally has to use a near-final LRT file recommended
        by the project manager. This test documents an attempt to determine
        which LRT file was used, which led to the realization that the utilized
        file was never archived.

        An unknown LRT data file was used to create an ascii file that contains
        PALT_A and ATRL (NG20140606.asc). The values in that file were then
        used to convert the RAW file into an RNG file.
        """

        # Instantiate a logger so can call just this test
        self.stream = sys.stdout  # Send log messages to stdout
        loglevel = logging.INFO
        logger.initLogger(self.stream, loglevel)

        self.mtp = {
            # sample data values taken from the DEEPWAVE RAW and RNG data files
            '2014-06-06 06:23:08': {  # date/time in cftime format
                'PALTF': {
                    'RAW': '10769.3',
                    'RNG': '10797.52'},  # This matches NG20140606.asc
                'ATX': {
                    'RAW': '-5.48383',
                    'RNG': '-5.1945'},  # This matches NG20140606.asc
            },
            '2014-06-06 06:23:25': {
                'PALTF': {
                    'RAW': '11311.1',
                    'RNG': '11336.69'},
                'ATX': {
                    'RAW': '-6.48923',
                    'RNG': '-6.3268'},
            },
            '2014-06-06 06:26:00': {
                'PALTF': {
                    'RAW': '17008.3',
                    'RNG': '17029.92'},  # asc has .91 - rounding difference
                'ATX': {
                    'RAW': '-18.0792',
                    'RNG': '-17.8590'},
            },
        }

        self.reader = readGVnc()

#    def test_deepwave_062308_V0(self):
#        """
#        Test the field-phase LRT file to see if it was used. This file is too
#        big to include in the github repo, so this test is commented out. To
#        run this test, retrieve version 0.0 of the DEEPWAVE RF01 LRT file from
#        the EOL data archive and put it in the dir indicated by the filename
#        below, or change the filename path, and then uncomment this test.
        
#        For reference, this test confirms that the values of PALT_A in this
#        file match the values in the .asc file that was used in processing,
#        but the ATRL values do NOT match, indicating that this was NOT the file
#        used, but maybe some other preliminary file was???
#        """
#        # Load preliminary (field-phase) data file
#        filename = "../tests/test_data/DEEPWAVE/LRT/V0.0_20140905/" + \
#                   "DEEPWAVErf01.nc"

#        for time in self.mtp.keys():
#            palt_a = self.reader.getValAtTime(filename, "PALT_A", time)
#            palt_a = "{:.2f}".format(palt_a * 3.2808)
#            paltf = self.mtp[time]['PALTF']['RNG']
#            self.assertEqual(palt_a, paltf)  # PALTF matches

#            atrl = self.reader.getValAtTime(filename, "ATRL", time)
#            atrl = "{:.4f}".format(atrl)
#            atx = self.mtp[time]['ATX']['RNG']
#            self.assertNotEqual(atrl, atx)   # ATX does NOT match

    def test_deepwave_062308_V1(self):
        """ Test the first production file released """
        # Load first version of final data
        filename = "../tests/test_data/DEEPWAVE/LRT/V1.0_20150324/" + \
                   "RF01.20140606.061800_133700.PNI.nc"

        for time in self.mtp.keys():
            palt_a = self.reader.getValAtTime(filename, "PALT_A", time)
            palt_a = "{:.2f}".format(palt_a * 3.2808)
            paltf = self.mtp[time]['PALTF']['RNG']
            self.assertNotEqual(palt_a, paltf)  # PALTF does NOT match

            atrl = self.reader.getValAtTime(filename, "ATRL", time)
            atrl = "{:.4f}".format(atrl)
            atx = self.mtp[time]['ATX']['RNG']
            self.assertNotEqual(atrl, atx)   # ATX does NOT match

    def test_deepwave_062308_V1_1(self):
        """ Test version 1.1 of the production file """
        # Load data file
        filename = "../tests/test_data/DEEPWAVE/LRT/V1.1_20150526/" + \
                   "RF01Z.20140606.061800_133700.PNI.nc"

        for time in self.mtp.keys():
            palt_a = self.reader.getValAtTime(filename, "PALT_A", time)
            palt_a = "{:.2f}".format(palt_a * 3.2808)
            paltf = self.mtp[time]['PALTF']['RNG']
            self.assertNotEqual(palt_a, paltf)  # PALTF does NOT match

            atrl = self.reader.getValAtTime(filename, "ATRL", time)
            atrl = "{:.4f}".format(atrl)
            atx = self.mtp[time]['ATX']['RNG']
            self.assertNotEqual(atrl, atx)   # ATX does NOT match

    def test_deepwave_062308_V1_2(self):
        """ Test the current production file released """
        # Load first version of final data
        filename = "../tests/test_data/DEEPWAVE/LRT/V1.2_20150609current/" + \
                   "DEEPWAVErf01.nc"

        for time in self.mtp.keys():
            palt_a = self.reader.getValAtTime(filename, "PALT_A", time)
            palt_a = "{:.2f}".format(palt_a * 3.2808)
            paltf = self.mtp[time]['PALTF']['RNG']
            self.assertNotEqual(palt_a, paltf)  # PALTF does NOT match

            atrl = self.reader.getValAtTime(filename, "ATRL", time)
            atrl = "{:.4f}".format(atrl)
            atx = self.mtp[time]['ATX']['RNG']
            self.assertNotEqual(atrl, atx)   # ATX does NOT match

    def test_NGseconds(self):
        """ Get times from DataFrame in seconds """
        filename = "../tests/test_data/DEEPWAVE/LRT/V1.0_20150324/" + \
                   "RF01.20140606.061800_133700.PNI.nc"
        # Read in file times as a pandas dataframe
        ncdata = self.reader.getNGvalues(filename)

        # Generate a random row to test
        seed(3)
        row = randint(0, len(ncdata)-1)

        # Convert random filetime to seconds
        date, time = ncdata.iloc[row, 0].split(' ')
        h, m, s = time.split(':')
        sec, millisec = s.split('.')
        testtime = int(h) * 3600 + int(m) * 60 + int(sec)

        # Compare to seconds from dataframe routine
        seconds = self.reader.NGseconds()
        self.assertEqual(seconds.iloc[row], testtime)

#   def test_NGseconds_rollover(self):
#        """
#        Test conversion to seconds during midnight rollover
#        The CSET LRT file used in this test is too big to include in the
#        github repo, so this test is commented out. To run this test, retrieve
#        the most recent version of the DEEPWAVE RF01 LRT file from the EOL
#        data archive and put it in the dir indicated by the filename below, or
#        change the filename path, and then uncomment this test.
#        filename = "../tests/test_data/CSET/LRT/CSETrf09.nc"
#        self.reader.getNGvalues(filename)
#        seconds = self.reader.NGseconds()
#        self.assertEqual(seconds.iloc[29100], 88200)
