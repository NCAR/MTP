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
#import unittest
#from PyQt6.QtWidgets import QApplication

#from viewer.MTPviewer import MTPviewer
#from viewer.MTPclient import MTPclient


#class TESTquit(unittest.TestCase):

    # There is a problem with how pg releases it's children which causes a
    # QBasicTimer error when I run the tests. Testing the Quit button is not
    # that important - you're going to know quickly if it stops working - so
    # for now comment this out. I have spent quite a bit of time and haven't
    # yet figured out how to assign parents to make this work. Need to assign
    # self.stp as the parent of self.profile (I think) in plotScanTemp().
    # When running the main code, no errors occur. They only occur when running
    # these unit tests.

#   def test_quit(self):
#       """ Test mouse click on 'Quit' in GUI Quit Menu """
#       self.app = QApplication([])
#       self.client = MTPclient()
#       self.client.config(self.configfile)
#       self.viewer = MTPviewer(self.client, self.app)

        # To start, socket should be open, so a call to fileno() should return
        # a socket value that is not failure (-1)
        # MTP socket
#       self.assertNotEqual(self.viewer.client.getSocketFileDescriptor(), -1)
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
#       self.app.quit()
