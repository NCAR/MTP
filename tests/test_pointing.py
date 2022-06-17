###############################################################################
# Test ctrl/pointing.py
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
from math import atan
import logging
import unittest
from io import StringIO
from ctrl.pointing import pointMTP
from EOLpython.Qlogger.messageHandler import QLogger as logger


class TESTpointing(unittest.TestCase):

    def setUp(self):

        # For testing, we want to capture the log messages in a buffer so we
        # can compare the log output to what we expect.
        self.stream = StringIO()  # Set output stream to buffer

        # Instantiate a logger
        self.log = logger.initLogger(self.stream, logging.INFO)

        self.point = pointMTP()

    def test_rpd(self):
        rpd = 0.017453292519943295
        self.assertEqual(rpd, atan(1) / 45)

    def test_MAM(self):
        # The following MTP Attitude Matrix (MAM) assumes NSF HIAPER GV pitch,
        # roll, and yaw of [-3.576, -0.123, and -1.600] for canister wrt
        # aircraft.

        self.assertEqual(self.point.getMAM(),
                         [[0.9976638166709056, 'nan', -0.06237246157452236,
                          'nan'], [-0.027787728299641167, 0.9996115503208397,
                          0.0021425734788769915, 'nan'], [0.06240794069336683,
                          -0.00040437901882164353, 0.9980506427110911, 'nan'],
                          ['nan', 'nan', 'nan', 'nan']])

    def test_fEc(self):
        # Test null case where pitch and roll are zero. The correction to
        # forward pointing scan angle (Elevation = 0) is just due to how
        # canister is mounted on aircraft.
        self.assertEqual(self.point.fEc(0, 0, 0), 3.578037064666239)

        # Test mirror pointed at target. In that case, there is no correction
        # since we are looking internal to the probe, so changing pitch and
        # roll won't change result
        self.assertEqual(self.point.fEc(0, 0, 180), 180)
        self.assertEqual(self.point.fEc(-1.2710891, -0.47074246, 180), 180)
        self.assertEqual(self.point.fEc(-1.6022255, 0.200037, 180), 180)

        # Test non-zero pitch
        self.assertEqual(self.point.fEc(-1.2710891, 0, 0), 4.8486324625155195)
        self.assertEqual(self.point.fEc(-1.6022255, 0, 0), 5.179640262097432)

        # Test non-zero roll
        self.assertEqual(self.point.fEc(0, -0.47074246, 0), 3.5911557143025035)
        self.assertEqual(self.point.fEc(0, 0.200037, 0), 3.5724625631631226)

        # Test non-zero pitch and roll
        self.assertEqual(self.point.fEc(-1.2710891, -0.47074246, 0),
                         4.86175203868336)
        self.assertEqual(self.point.fEc(-1.6022255, 0.200037, 0),
                         5.174065663274387)

        # Test all cases in abs(Elevation) / abs(Emax) if tree
        self.assertEqual(self.point.fEc(1.6022255, 0.200037, -2),
                         -0.02914251628561277)
        self.assertEqual(self.point.fEc(1.6022255, 0.200037, 89),
                         90.97963292154063)
        # abs(Elevation) <= abs(Emax) and E_Ec_0 < 0 and Elevation >= E_Ec_0
        # and Elevation >= -Emax
        # - didn't manage to figure this one out. Maybe later.
        self.assertEqual(self.point.fEc(-1.6022255, 0.200037, -0.5),
                         4.674061928775248)
        self.assertEqual(self.point.fEc(4.0022255, 0.800037,
                                        89.33482484821836), 89.55513864488115)
        self.assertEqual(self.point.fEc(4.0022255, 0.800037, 89.2),
                         89.11067167272341)
        self.assertEqual(self.point.fEc(4.0022255, 0.800037, -89.1),
                         -89.83859528142365)
        self.assertEqual(self.point.fEc(4.0022255, 0.800037, -89.2),
                         -90.00040330391016)
        self.assertEqual(self.point.fEc(4.0022255, 0.800037,
                                        -89.33482484821836),
                         -90.44486135511816)
        self.assertEqual(self.point.fEc(4.2022255, -1.000037, 89.2),
                         89.40520184381744)
        self.assertEqual(self.point.fEc(4.2022255, 1.000037, -89.2),
                         -90.65033162684094)
        self.assertEqual(self.point.fEc(3.0022255, 1.000037, 89.2),
                         90.54916249575147)
        self.assertEqual(self.point.fEc(-4.2022255, -1.000037, -89.2),
                         -82.19354160567433)
