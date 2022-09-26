###############################################################################
# Test ctrl/util/init.py
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
import logging
import unittest
from unittest.mock import Mock
from io import StringIO
from ctrl.util.init import MTPProbeInit
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class TESTinit(unittest.TestCase):

    def setUp(self):
        # For testing, we want to capture the log messages in a buffer so we
        # can compare the log output to what we expect.
        self.stream = StringIO()  # Set output stream to buffer

        # Instantiate a logger
        self.log = logger.initStream(self.stream, logging.INFO)

        # Mock an MTPProbeInit class so don't have to handle dependencies
        # in __init__ function
        Mock(MTPProbeInit)

    # getStatus() returns an integer 0-8 with the following bits:
    # - Bit 0 = Integrator busy
    # - Bit 1 = Stepper moving
    # - Bit 2 = Synthesizer out of lock
    # - Bit 3 = spare
    # Next three tests test retrieval of these status states
    def test_integratorBusy(self):
        """ Test of logic to retrieve integrator status from status message """

        # Integrator not busy (integration complete)
        for status in [0, 2, 4, 6]:
            result = MTPProbeInit.integratorBusy(self, status)
            self.assertEqual(result, False)

        # Integrator busy
        for status in [1, 3, 5, 7]:
            result = MTPProbeInit.integratorBusy(self, status)
            self.assertEqual(result, True)

    def test_stepperBusy(self):
        """ Test of logic to retrieve stepper status from status message """

        # Stepper not moving
        for status in [0, 1, 4, 5]:
            result = MTPProbeInit.stepperBusy(self, status)
            self.assertEqual(result, False)

        # Stepper moving
        for status in [2, 3, 6, 7]:
            result = MTPProbeInit.stepperBusy(self, status)
            self.assertEqual(result, True)

    def test_synthesizerBusy(self):
        """
        Test of logic to retrieve synthesizer status from status message
        """

        # Synthesizer locked (i.e. frequency stable)
        for status in [0, 1, 2, 3]:
            result = MTPProbeInit.synthesizerBusy(self, status)
            self.assertEqual(result, False)

        # Synthesizer out of lock (i.e. frequency being adjusted)
        for status in [4, 5, 6, 7]:
            result = MTPProbeInit.synthesizerBusy(self, status)
            self.assertEqual(result, True)

    def test_findStat(self):
        """
        Test logic of identifying a UART status message within the returned
        buffer
        """

        buf = b'U/1f1j256V50000R\r\nU:U/1f1j256V50000R\r\n' + \
              b'Step:\xff/0`\r\nStep:\xff/0@\r\n'
        status = MTPProbeInit.findStat(self, buf)
        self.assertEqual(status, '@')

        buf = b'U/1f1j256V50000R\r\nU:U/1f1j256V50000R\r\nStep:/0@\r\n'
        status = MTPProbeInit.findStat(self, buf)
        self.assertEqual(status, '@')
