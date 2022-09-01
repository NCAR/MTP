###############################################################################
# Test viewer/MTPclient.py
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
import logging
import unittest
import argparse
from io import StringIO
from ctrl.util.init import MTPProbeInit
from ctrl.util.move import MTPProbeMove
from ctrl.util.CIR import MTPProbeCIR
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class TESTcir(unittest.TestCase):

    def setUp(self):

        # For testing, we want to capture the log messages in a buffer so we
        # can compare the log output to what we expect.
        self.stream = StringIO()  # Set output stream to buffer

        # Instantiate a logger
        self.log = logger.initStream(self.stream, logging.INFO)

        args = argparse.Namespace(device='COM6', port=32107)

        init = MTPProbeInit(args, args.port)
        data = MTPProbeCIR(init)

    def test_integrate(self):
        self.assertTrue(True)
