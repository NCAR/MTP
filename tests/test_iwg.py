###############################################################################
# readiwg-specific unit tests.
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
from lib.rootdir import getrootdir
from viewer.MTPclient import MTPclient

import sys
import logging
from EOLpython.logger.messageHandler import Logger as logger


class TESTreadiwg(unittest.TestCase):

    def setUp(self):
        # Set up logging
        self.stream = sys.stdout  # Send log messages to stdout
        loglevel = logging.INFO
        logger.initLogger(self.stream, loglevel)

        # Location of default ascii_parms file
        self.ascii_parms = os.path.join(getrootdir(), 'Data', 'NGV',
                                        'DEEPWAVE', 'config', 'ascii_parms')

        self.client = MTPclient()

        # Read the config file. Gets path to RCF dir
        self.client.config(os.path.join(getrootdir(), 'Data', 'NGV',
                               'DEEPWAVE', 'config', 'proj.yml'))
        self.client.readConfig(os.path.join(getrootdir(), 'Data', 'NGV',
                               'DEEPWAVE', 'config', 'proj.yml'))

        # Test that return correct IWG line
        self.iwgrec = "IWG1,20140606T062250,-43.3061,172.455,3281.97,," + \
            "10508.5,,149.998,164.027,,0.502512,3.11066,283.283,281.732," + \
            "-1.55388,3.46827,0.0652588,-0.258496,2.48881,-5.31801" + \
            ",-5.92311,7.77836,683.176,127.248,1010.48,14.6122," + \
            "297.157,0.303804,104.277,,-72.1708,"

        # Store sample iwg line to rawscan dictionary
        self.client.reader.parseLine(self.iwgrec)

        self.iwg = self.client.initIWG()

    def test_getIwgPacket(self):
        """ Test the IWG line parses as expected """

        # Get stored ascii packet back from rawscan
        iwg2 = self.iwg.getIwgPacket()

        self.assertEqual(self.iwgrec, iwg2)

    def test_parseIwgPacket(self):
        # Test that parse correctly (this tests assumes the default ascii_parms
        # file in config/ascii_parms
        self.rawscan = self.client.reader.rawscan
        self.iwg.parseIwgPacket(self.iwgrec, self.ascii_parms)
        self.assertEqual(self.rawscan['IWG1line']['date'], '20140606T062250')
        self.assertEqual(self.rawscan['IWG1line']['values']['DATE']['val'],
                         '20140606')
        self.assertEqual(self.rawscan['IWG1line']['values']['TIME']['val'],
                         6 * 3600 + 22 * 60 + 50)
        self.assertEqual(self.rawscan['IWG1line']['values']['GGLAT']['val'],
                         '-43.3061')
        self.assertEqual(self.rawscan['IWG1line']['values']['GGLON']['val'],
                         '172.455')
        self.assertEqual(self.rawscan['IWG1line']['values']['GGALT']['val'],
                         '3281.97')
        self.assertEqual(self.rawscan['IWG1line']['values']['NAVAIL']['val'],
                         '')
        self.assertEqual(self.rawscan['IWG1line']['values']['PALTF']['val'],
                         '10508.5')
        self.assertEqual(self.rawscan['IWG1line']['values']['HGM232']['val'],
                         '')
        self.assertEqual(self.rawscan['IWG1line']['values']['GSF']['val'],
                         '149.998')
        self.assertEqual(self.rawscan['IWG1line']['values']['TASX']['val'],
                         '164.027')
        self.assertEqual(self.rawscan['IWG1line']['values']['IAS']['val'],
                         '')
        self.assertEqual(self.rawscan['IWG1line']['values']['MACH_A']['val'],
                         '0.502512')
        self.assertEqual(self.rawscan['IWG1line']['values']['VSPD']['val'],
                         '3.11066')
        self.assertEqual(self.rawscan['IWG1line']['values']['THDG']['val'],
                         '283.283')
        self.assertEqual(self.rawscan['IWG1line']['values']['TKAT']['val'],
                         '281.732')
        self.assertEqual(self.rawscan['IWG1line']['values']['DRFTA']['val'],
                         '-1.55388')
        self.assertEqual(self.rawscan['IWG1line']['values']['PITCH']['val'],
                         '3.46827')
        self.assertEqual(self.rawscan['IWG1line']['values']['ROLL']['val'],
                         '0.0652588')
        self.assertEqual(self.rawscan['IWG1line']['values']['SSLIP']['val'],
                         '-0.258496')
        self.assertEqual(self.rawscan['IWG1line']['values']['ATTACK']['val'],
                         '2.48881')
        self.assertEqual(self.rawscan['IWG1line']['values']['ATX']['val'],
                         '-5.31801')
        self.assertEqual(self.rawscan['IWG1line']['values']['DPXC']['val'],
                         '-5.92311')
        self.assertEqual(self.rawscan['IWG1line']['values']['RTX']['val'],
                         '7.77836')
        self.assertEqual(self.rawscan['IWG1line']['values']['PSXC']['val'],
                         '683.176')
        self.assertEqual(self.rawscan['IWG1line']['values']['QCXC']['val'],
                         '127.248')
        self.assertEqual(self.rawscan['IWG1line']['values']['PCAB']['val'],
                         '1010.48')
        self.assertEqual(self.rawscan['IWG1line']['values']['WSC']['val'],
                         '14.6122')
        self.assertEqual(self.rawscan['IWG1line']['values']['WDC']['val'],
                         '297.157')
        self.assertEqual(self.rawscan['IWG1line']['values']['WIC']['val'],
                         '0.303804')
        self.assertEqual(self.rawscan['IWG1line']['values']['SOLZE']['val'],
                         '104.277')
        self.assertEqual(self.rawscan['IWG1line']['values']['Solar_El_AC']
                         ['val'], '')
        self.assertEqual(self.rawscan['IWG1line']['values']['SOLAZ']['val'],
                         '-72.1708')
        self.assertEqual(self.rawscan['IWG1line']['values']['Sun_Az_AC']
                         ['val'], '')
