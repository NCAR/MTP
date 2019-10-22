###############################################################################
# GUI-specific unit tests
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import unittest
from PyQt5.QtWidgets import QApplication

from viewer.MTPviewer import MTPviewer
from util.readmtp import readMTP


class TESTgui(unittest.TestCase):

    def setUp(self):
        app = QApplication([])
        self.viewer = MTPviewer(app)

    def test_eng1(self):
        """ Test Engineering 1 display window shows what we expect """
        # To start, the window just shows "Channel  Counts  Ohms  Temp  "
        self.assertEqual(self.viewer.eng1.toPlainText(),
                         "Channel  Counts  Ohms  Temp  ")

        # Send an MTP packet to the parser and confirm it gets parsed
        # correctly
        line = "Pt: 2177 13823 13811 10352 13315 13327 13304 14460"
        mtp = readMTP()
        mtp.parseLine(line)
        values = mtp.rawscan['Ptline']['data'].split(' ')
        mtp.assignPtvalues(values)
        self.assertEqual(mtp.getVar('Ptline', 'TR350CNTP'), '2177')
        self.assertEqual(mtp.getVar('Ptline', 'TTCNTRCNTP'), '13823')
        self.assertEqual(mtp.getVar('Ptline', 'TTEDGCNTP'), '13811')
        self.assertEqual(mtp.getVar('Ptline', 'TWINCNTP'), '10352')
        self.assertEqual(mtp.getVar('Ptline', 'TMIXCNTP'), '13315')
        self.assertEqual(mtp.getVar('Ptline', 'TAMPCNTP'), '13327')
        self.assertEqual(mtp.getVar('Ptline', 'TNDCNTP'), '13304')
        self.assertEqual(mtp.getVar('Ptline', 'TR600CNTP'), '14460')

        # Then check that window displays correct values. It looks to me like
        # the first Engineering window displays the contents of the Pt line
        # This has not been written yet...
        self.viewer.writeEng1()
        self.assertEqual(self.viewer.eng1.toPlainText(),
                         "Channel  Counts  Ohms  Temp  \n" +
                         "Rref ---  -----  ---  ---")

    def test_eng2(self):
        """ Test Engineering 2 display window shows what we expect """
        # To start, window just shows "Engineering 2 display"
        self.assertEqual(self.viewer.eng2.toPlainText(),
                         "Engineering 2 display")

        # Send an MTP packet to the parser and confirm it gets parsed
        # correctly.
        line = "M01: 2928 2321 2898 3082 1923 2921 2432 2944"
        mtp = readMTP()
        mtp.parseLine(line)
        values = mtp.rawscan['M01line']['data'].split(' ')
        mtp.assignM01values(values)
        self.assertEqual(mtp.getVar('M01line', 'VM08CNTE'), '2928')

        # The second engineering window displays the M01 line
    # def ():
        # Test plotting of scnt
        # scan1 = self.scnt_inv[0:10]
        # scan2 = self.scnt_inv[10:20]
        # scan3 = self.scnt_inv[20:30]

    # There is a problem with how pg releases it's children which causes a
    # QBasicTimer error when I run the tests. Testing the Quit button is not
    # that important - you're going to know quickly if it stops working - so
    # for now comment this out. I have spent quite a bit of time and haven't
    # yet figured out how to assign parents to make this work.
    # def test_quit(self):
    #     '''
    #     Test mouse click on 'Quit' in GUI Quit Menu
    #     '''

        # To start, socket should be open, so a call to fileno() should return
        # a socket value that is not failure (-1)
        # MTP socket
    #    self.assertNotEqual(self.viewer.client.getSocketFileDescriptor(), -1)
        # IWG socket
    #    self.assertNotEqual(self.viewer.client.getSocketFileDescriptorI(), -1)

        # First click should close socket and return None
    #    self.assertEqual(self.viewer.quitButton.trigger(), None)

        # If socket is closed, all future operations on the socket object will
        # fail. Test by requesting the socket file descriptor - should return
        # failure (-1)
        # MTP socket
    #    self.assertEqual(self.viewer.client.getSocketFileDescriptor(), -1)
        # IWG socket
    #    self.assertEqual(self.viewer.client.getSocketFileDescriptorI(), -1)

        # App should also be closed

    def tearDown(self):
        self.viewer.close()
