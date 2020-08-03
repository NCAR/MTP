###############################################################################
# Test proc/MTPprocessor.py
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
# COPYRIGHT:   University Corporation for Atmospheric Research, 2020
###############################################################################
import os
import copy
import unittest
from unittest.mock import mock_open, patch
import argparse
from viewer.MTPviewer import MTPviewer
from PyQt5.QtWidgets import QApplication
from viewer.MTPclient import MTPclient
from proc.MTPprocessor import MTPprocessor
from lib.rootdir import getrootdir
from util.MTP import MTPrecord

import sys
import logging
from EOLpython.logger.messageHandler import Logger as logger


class TESTMTPprocessor(unittest.TestCase):

    def setUp(self):
        # Location of Production dir and config file
        self.proddir = os.path.join('Data', 'NGV',
                                    'DEEPWAVE', 'config', 'Production')
        self.configfile = os.path.join(getrootdir(), 'Data', 'NGV',
                                       'DEEPWAVE', 'config', 'proj.yml')

        # Set data dict to test against - get an empty MTPrecord
        self.dict = copy.deepcopy(MTPrecord)

        # Setup logging
        self.stream = sys.stdout  # Send log messages to stdout
        loglevel = logging.INFO
        logger.initLogger(self.stream, loglevel)

        self.app = QApplication([])
        self.client = MTPclient()
        self.client.readConfig(self.configfile)
        self.args = argparse.Namespace(PRODdir=self.proddir, realtime=False)
        self.viewer = MTPviewer(self.client, self.app, self.args)
        self.processor = MTPprocessor(self.viewer, self.client)

        self.maxDiff = None

    def test_ReadSetup(self):
        """ Test accuracy of read of setup files in config/Production dir """
        self.assertEqual(self.args.PRODdir,
                         os.path.join('Data', 'NGV', 'DEEPWAVE', 'config',
                        'Production'))

        self.processor.readSetup(self.client.configfile.getPath("PRODdir"))
        self.assertEqual(self.processor.filelist[0]['rawFile'],
                         os.path.join(getrootdir(), 'Data', 'NGV', 'DEEPWAVE',
                                      'Raw', 'N2014060606.22'))
        self.assertEqual(self.processor.filelist[0]['ncFile'],
                         os.path.join(getrootdir(), 'Data', 'NGV', 'DEEPWAVE',
                                      'NG', 'DEEPWAVErf01.nc'))
        self.assertEqual(self.processor.filelist[1]['rawFile'],
                         os.path.join(getrootdir(), 'Data', 'NGV', 'DEEPWAVE',
                                      'Raw', 'N2014061107.33'))
        self.assertEqual(self.processor.filelist[1]['ncFile'],
                         os.path.join(getrootdir(), 'Data', 'NGV', 'DEEPWAVE',
                                      'NG', 'DEEPWAVErf02.nc'))

    def test_setFile(self):
        """
        Test that when load a flight, data are all correctly written to the
        dictionary flightData. Test the first and last record (edge cases) and
        one in the middle.
        """

        # Test that dictionary and JSON are successfully cleared
        # self.processor.clearDictionary()
        # self.assertDictEqual(self.client.reader.rawscan, self.dict)
        # self.assertEqual(self.client.reader.flightData, [])
        # self.processor.removeJSON()
        # self.assertEqual(os.path.exists(self.client.getMtpRealTimeFilename()),
        #                                 False)

        # selectedRawFile is the Raw file listed in the Production dir setup
        # file for the flight the user selected. Hardcode it here for testing
        selectedRawFile = os.path.join(getrootdir(), 'Data', 'NGV', 'DEEPWAVE',
                                       'Raw', 'N2014060606.22')
        self.assertEqual(os.path.exists(selectedRawFile), True)

        # Open the file
        with patch('__main__.open', mock_open()):
            with open(selectedRawFile) as raw_data_file:
                status = self.client.reader.readRawScan(raw_data_file)

        self.assertEqual(status, True)  # Successful read of a raw data record

        # Add test data to the empty MTP record
        self.dict['Aline']['date'] = '20140606T062252'
        self.dict['Aline']['data'] = \
            '+03.98 00.25 +00.07 00.33 +03.18 0.01 ' + \
            '268.08 00.11 -43.308 +0.009 +172.469 +0.000 +074146 +073392'
        self.dict['IWG1line']['date'] = '20140606T062250'
        self.dict['IWG1line']['asciiPacket'] = \
            'IWG1,20140606T062250,-43.3061,172.455,3281.97,,10508.5,,' + \
            '149.998,164.027,,0.502512,3.11066,283.283,281.732,-1.55388,' + \
            '3.46827,0.0652588,-0.258496,2.48881,-5.31801,-5.92311,' + \
            '7.77836,683.176,127.248,1010.48,14.6122,297.157,0.303804,' + \
            '104.277,,-72.1708,'
        self.dict['IWG1line']['data'] = \
            '-43.3061,172.455,3281.97,,10508.5,,149.998,164.027,,0.502512,' + \
            '3.11066,283.283,281.732,-1.55388,3.46827,0.0652588,-0.258496,' + \
            '2.48881,-5.31801,-5.92311,7.77836,683.176,127.248,1010.48,' + \
            '14.6122,297.157,0.303804,104.277,,-72.1708,'
        self.dict['Bline']['data'] = \
            '018963 020184 019593 018971 020181 019593 018970 020170 ' + \
            '019587 018982 020193 019589 018992 020223 019617 019001 ' + \
            '020229 019623 018992 020208 019601 018972 020181 019572 ' + \
            '018979 020166 019558 018977 020161 019554 '
        self.dict['M01line']['data'] = \
            '2928 2321 2898 3082 1923 2921 2432 2944'
        self.dict['M02line']['data'] = \
            '2016 1394 2096 2202 2136 1508 4095 1558'
        self.dict['Ptline']['data'] = \
            '2177 13823 13811 10352 13315 13327 13304 14460'
        self.dict['Eline']['data'] = \
            '021506 022917 022752 019806 021164 020697 '

        # Test that raw scan stored correctly to dictionary
        self.assertDictEqual(self.client.reader.rawscan, self.dict)

        # Test that ascii packet is formed correctly and stored to rawscan
        # correctly
        packet = self.client.reader.getAsciiPacket()
        self.dict['asciiPacket'] = packet
        self.assertEqual(packet, self.client.reader.rawscan['asciiPacket'])
        self.assertDictEqual(self.client.reader.rawscan, self.dict)

        # Test that the ascii packet is parsed to rawscan values correctly
        self.client.reader.parseAsciiPacket(packet)
        self.dict['Aline']['values']['DATE']['val'] = '20140606'
        self.dict['Aline']['values']['timestr']['val'] = '06:22:52'
        self.dict['Aline']['values']['TIME']['val'] = 22972
        self.dict['Aline']['values']['SAPITCH']['val'] = '+03.98'
        self.dict['Aline']['values']['SRPITCH']['val'] = '00.25'
        self.dict['Aline']['values']['SAROLL']['val'] = '+00.07'
        self.dict['Aline']['values']['SRROLL']['val'] = '00.33'
        self.dict['Aline']['values']['SAPALT']['val'] = '+03.18'
        self.dict['Aline']['values']['SRPALT']['val'] = '0.01'
        self.dict['Aline']['values']['SAAT']['val'] = '268.08'
        self.dict['Aline']['values']['SRAT']['val'] = '00.11'
        self.dict['Aline']['values']['SALAT']['val'] = '-43.308'
        self.dict['Aline']['values']['SRLAT']['val'] = '+0.009'
        self.dict['Aline']['values']['SALON']['val'] = '+172.469'
        self.dict['Aline']['values']['SRLON']['val'] = '+0.000'
        self.dict['Aline']['values']['SMCMD']['val'] = '+074146'
        self.dict['Aline']['values']['SMENC']['val'] = '+073392'
        self.dict['Bline']['values']['SCNT']['val'] =  \
            ['018963', '020184', '019593', '018971', '020181', '019593',
             '018970', '020170', '019587', '018982', '020193', '019589',
             '018992', '020223', '019617', '019001', '020229', '019623',
             '018992', '020208', '019601', '018972', '020181', '019572',
             '018979', '020166', '019558', '018977', '020161', '019554']
        self.dict['Eline']['values']['TCNT']['val'] = \
            ['021506', '022917', '022752', '019806', '021164', '020697']
        self.dict['M01line']['values']['VM08CNTE']['val'] = '2928'
        self.dict['M01line']['values']['VVIDCNTE']['val'] = '2321'
        self.dict['M01line']['values']['VP08CNTE']['val'] = '2898'
        self.dict['M01line']['values']['VMTRCNTE']['val'] = '3082'
        self.dict['M01line']['values']['VSYNCNTE']['val'] = '1923'
        self.dict['M01line']['values']['VP15CNTE']['val'] = '2921'
        self.dict['M01line']['values']['VP05CNTE']['val'] = '2432'
        self.dict['M01line']['values']['VM15CNTE']['val'] = '2944'
        self.dict['M02line']['values']['ACCPCNTE']['val'] = '2016'
        self.dict['M02line']['values']['TDATCNTE']['val'] = '1394'
        self.dict['M02line']['values']['TMTRCNTE']['val'] = '2096'
        self.dict['M02line']['values']['TAIRCNTE']['val'] = '2202'
        self.dict['M02line']['values']['TSMPCNTE']['val'] = '2136'
        self.dict['M02line']['values']['TPSPCNTE']['val'] = '1508'
        self.dict['M02line']['values']['TNCCNTE']['val'] = '4095'
        self.dict['M02line']['values']['TSYNCNTE']['val'] = '1558'
        self.dict['Ptline']['values']['TR350CNTP']['val'] = '2177'
        self.dict['Ptline']['values']['TTCNTRCNTP']['val'] = '13823'
        self.dict['Ptline']['values']['TTEDGCNTP']['val'] = '13811'
        self.dict['Ptline']['values']['TWINCNTP']['val'] = '10352'
        self.dict['Ptline']['values']['TMIXCNTP']['val'] = '13315'
        self.dict['Ptline']['values']['TAMPCNTP']['val'] = '13327'
        self.dict['Ptline']['values']['TNDCNTP']['val'] = '13304'
        self.dict['Ptline']['values']['TR600CNTP']['val'] = '14460'

        self.assertDictEqual(self.client.reader.rawscan, self.dict)

    def tearDown(self):
        self.app.quit()
        self.app = None
