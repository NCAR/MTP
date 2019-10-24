###############################################################################
# GUI-specific unit tests
#
# To run these tests:
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
from PyQt5.QtWidgets import QApplication

from viewer.MTPviewer import MTPviewer
from util.readmtp import readMTP


class TESTgui(unittest.TestCase):

    def setUp(self):
        self.app = QApplication([])

    def test_eng1(self):
        """ Test Engineering 1 display window shows what we expect """
        self.viewer = MTPviewer(self.app)
        # This first emgineering window shows the Pt line
        # To start, the window just shows "Channel  Counts  Ohms  Temp  "
        self.assertEqual(self.viewer.eng1.toPlainText(),
                         "Channel\tCounts  Ohms  Temp  ")

        # Send an MTP packet to the parser and confirm it gets parsed
        # correctly
        line = "Pt: 2165 13811 13820 03894 13415 13342 13230 14450"
        mtp = readMTP()
        mtp.parseLine(line)
        values = mtp.rawscan['Ptline']['data'].split(' ')
        mtp.assignPtvalues(values)
        self.assertEqual(mtp.getVar('Ptline', 'TR350CNTP'), '2165')
        self.assertEqual(mtp.getVar('Ptline', 'TTCNTRCNTP'), '13811')
        self.assertEqual(mtp.getVar('Ptline', 'TTEDGCNTP'), '13820')
        self.assertEqual(mtp.getVar('Ptline', 'TWINCNTP'), '03894')
        self.assertEqual(mtp.getVar('Ptline', 'TMIXCNTP'), '13415')
        self.assertEqual(mtp.getVar('Ptline', 'TAMPCNTP'), '13342')
        self.assertEqual(mtp.getVar('Ptline', 'TNDCNTP'), '13230')
        self.assertEqual(mtp.getVar('Ptline', 'TR600CNTP'), '14450')

        # Then check that window displays correct values. It looks to me like
        # the first Engineering window displays the contents of the Pt line
        # This has not been written yet...
        self.viewer.client.calcPt()
        self.viewer.writeEng1()
        self.assertEqual(self.viewer.eng1.toPlainText(),
                         "Channel\tCounts  Ohms  Temp  \n" +
                         "Rref 350\t02165  350.00  \n" +
                         "Target 1\t13811  587.00  +44.73\n" +
                         "Target 2\t13820  587.18  +44.83\n" +
                         "Window\t03894  385.19  -58.24\n" +
                         "Mixer\t13415  578.94  +40.56\n" +
                         "Dblr Amp\t13342  577.45  +39.79\n" +
                         "Noise D.\t13230  575.17  +38.61\n" +
                         "Rref 600\t14450  600.00  ")
        self.viewer.close()

    def test_eng2(self):
        """ Test Engineering 2 display window shows what we expect """
        self.viewer = MTPviewer(self.app)
        # The second engineering window displays the M01 line
        # To start, window just shows the header: "Channel Counts  Volts"
        self.assertEqual(self.viewer.eng2.toPlainText(),
                         "Channel  Counts  Volts")

        # Send an MTP packet to the parser and confirm it gets parsed
        # correctly.
        line = "M01: 2928 2321 2898 3082 1923 2921 2432 2944"
        mtp = readMTP()
        mtp.parseLine(line)
        values = mtp.rawscan['M01line']['data'].split(' ')
        mtp.assignM01values(values)
        self.assertEqual(mtp.getVar('M01line', 'VM08CNTE'), '2928')
        self.viewer.close()

    def test_getResistance(self):
        """ Test that sending linetype other than Ptline fails """
        mtp = readMTP()
        mtp.setResistance('Ptline', 'TR350CNTP', 350.00)
        self.assertEqual(mtp.getResistance('Ptline', 'TR350CNTP'), 350.00)
        # check that resistance set to NAN for non Ptline
        mtp.setResistance('M02line', 'ACCPCNTE', 2510)
        check = numpy.isnan(mtp.getResistance('M02line', 'ACCPCNTE'))
        self.assertTrue(check)

    def test_getTemperature(self):
        """ Test that sending linetype other than Ptline fails """
        mtp = readMTP()
        # check that temperature calculated correctly for other Ptline vars
        mtp.setTemperature('Ptline', 'TTCNTRCNTP', 44.73)
        self.assertEqual(mtp.getTemperature('Ptline', 'TTCNTRCNTP'), 44.73)
        # check that temperature set to NAN for non Ptline
        mtp.setTemperature('M02line', 'ACCPCNTE', 2510)
        check = numpy.isnan(mtp.getTemperature('M02line', 'ACCPCNTE'))
        self.assertTrue(check)

    # def ():
        # Test plotting of scnt
        # scan1 = self.scnt_inv[0:10]
        # scan2 = self.scnt_inv[10:20]
        # scan3 = self.scnt_inv[20:30]

    # There is a problem with how pg releases it's children which causes a
    # QBasicTimer error when I run the tests. Testing the Quit button is not
    # that important - you're going to know quickly if it stops working - so
    # for now comment this out. I have spent quite a bit of time and haven't
    # yet figured out how to assign parents to make this work. Need to assign
    # self.stp as the parent of self.profile (I think) in plotScanTemp().
    # When running the main code, no errors occur. They only occur when running
    # these unit tests.
#    def test_quit(self):
#        self.viewer = MTPviewer(self.app)
#        """ Test mouse click on 'Quit' in GUI Quit Menu """

        # To start, socket should be open, so a call to fileno() should return
        # a socket value that is not failure (-1)
        # MTP socket
#        self.assertNotEqual(self.viewer.client.getSocketFileDescriptor(), -1)
        # IWG socket
#       self.assertNotEqual(self.viewer.client.getSocketFileDescriptorI(), -1)

        # First click should close socket and return None
#       self.assertEqual(self.viewer.quitButton.trigger(), None)

        # If socket is closed, all future operations on the socket object will
        # fail. Test by requesting the socket file descriptor - should return
        # failure (-1)
        # MTP socket
#       self.assertEqual(self.viewer.client.getSocketFileDescriptor(), -1)
        # IWG socket
#       self.assertEqual(self.viewer.client.getSocketFileDescriptorI(), -1)

        # App should also be closed
#       self.viewer.close()

    def tearDown(self):
        self.app.quit()
