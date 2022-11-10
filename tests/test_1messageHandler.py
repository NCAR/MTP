###############################################################################
# Test functionality of message handler printmsg. WARNING: This test MUST be
# run before test_gui, since test_gui instantiates a QApplication and there is
# no way to get rid of it after it exists. To ensure this, I have named this
# file with a 1. Tests are sorted in string order by filename.
#
# To run these tests:
#     python3 -m unittest discover -s ../tests -v
#
# To increase debugging info i.e. if trying to figure out test_quit issues,
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
import logging
from io import StringIO
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")
# Set environment var to indicate we are in testing mode
# Need this to logger won't try to open message boxes
logger.setDisableMessageBox(True)


class TESTprintmsg(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None  # See entire diff when asserts fail

        # For testing, we want to capture the log messages in a buffer so we
        # can compare the log output to what we expect.
        self.stream = StringIO()  # Set output stream to buffer

        # Instantiate a logger
        self.log = logger.initStream(self.stream, logging.INFO)

    def test_loggerConfig(self):
        # Test the logging level and stream are as expected for testing.
        # This has caused me lots of pain - looking for output that was at a
        # different level or stream than exepected
        self.assertEqual(logging.getLevelName(self.log.getEffectiveLevel()),
                         "DEBUG")
        for handler in self.log.handlers:
            self.assertTrue('_io.StringIO' in str(handler.stream))

    def test_noappInfo(self):
        """ Test that when an app isn't running, messages go to stderr """
        # When no QApplication is present, printmsg uses logging so output goes
        # to stderr and logging level is prepended

        # Test info message
        logger.info("test no app")
        logger.flushHandler()
        self.assertRegex(self.stream.getvalue(),
                         r'.*INFO | .*test_1messageHandler.py | test no app\n')

    def test_noappWarning(self):
        """ Test that when an app isn't running, messages go to stderr """
        # Test warning message
        logger.warning("test no app")
        logger.flushHandler()
        self.assertRegex(self.stream.getvalue(), r'.*WARNING | ' +
                         '.*test_1messageHandler.py | test no app\n')

    def test_noappError(self):
        """ Test that when an app isn't running, messages go to stderr """
        # Test error message
        logger.error("test no app")
        logger.flushHandler()
        self.assertRegex(self.stream.getvalue(), r'.*ERROR | ' +
                         '.*test_1messageHandler.py | test no app\n')

    def test_1noapp_2(self):
        """ Test when app isn't running, msgbox isn't called """
        with patch.object(logger, 'msgbox') as mock_method:
            logger.info("test no app")
            mock_method.assert_not_called()

    def test_app(self):
        """ Test that when there is an app, messages go to QMessageBox """
        self.app = QApplication([])  # Instantiates a QApplication
        logger.setDisableMessageBox(False)  # test instantiating boxes

        with patch.object(logger, 'msgbox') as mock_method:
            logger.debug("test app")
            mock_method.assert_not_called()

            logger.info("test app")
            mock_method.assert_not_called()

            logger.warning("test app")
            mock_method.assert_called()

            logger.error("test app")
            mock_method.assert_called()

        # test that call return appropriate icon for level
        # These calls generate a QMessageBox which must be clicked on for
        # tests to proceed. Have not figure out how to close them
        # programmatically.

        box = logger.msgbox(logging.INFO, "test app", None)
        self.assertEqual(box.icon(), 4)  # using question for info

        box = logger.msgbox(logging.WARNING, "test app", None)
        self.assertEqual(box.icon(), 2)  # 2 = critical

        box = logger.msgbox(logging.ERROR, "test app", None)
        self.assertEqual(box.icon(), 3)  # 3 = error

        self.app.quit()

    def tearDown(self):
        logger.delHandler()
