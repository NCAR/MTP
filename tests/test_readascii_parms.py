###############################################################################
# readascii_parms unit tests
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
##############################################################################
import unittest
from util.readascii_parms import AsciiParms


class TESTreadascii_parms(unittest.TestCase):

    def test_open(self):
        # Test that code finds ascii_parms file or exits with useful error
        self.ascii_parms = AsciiParms("nonexistentFile")
        self.assertFalse(self.ascii_parms.open())
