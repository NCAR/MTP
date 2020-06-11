###############################################################################
# Program to control the MTP instrument operation.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import logging
from serialInst import SerialInst
from mtpcommand import MTPcommand

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    device = SerialInst()

    server = MTPctrl(device)
    # server.sendCommand("version")
    server.sendCommand("status")
    server.loop()

    server.close()
    device.close()


class MTPctrl(object):

    def __init__(self, device):
        self.device = device
        self.interrupted = False
        self.command = MTPcommand()

    def loop(self):

        while not self.interrupted:
            try:
                self.data = None
                self.handleEvents()
            except KeyboardInterrupt:  # Exit if user hits Ctrl-C
                self.interrupted = True

    def getSerial(self):
        # Get a pointer to the serial port
        self.device.getSerial()

    def sendCommand(self, command):
        """ Send a command to request the Firmware Version """
        self.device.sendCommand(
            self.command.getCommand(command).encode('UTF-8'))

    def handleEvents(self, timeout=None):
        # Get the response
        response = self.device.readData()
        # MTP returns sent command before returns response
        logger.info('Received response ' + response)

    def homeScan(self):
        """
        Adapted from
        https://github.com/NCAR/MTP-VB6/MTPH_ctrl/MTPH_Control.frm
        Sub homeScan()
        """
        # readScan()
        # VB6 code clears the input buffer here
        # TBD what home1 does
        self.device.sendCommand(self.command.getCommand("home1"))

        while True:
            response = self.device.readData()
            if response.find("Step:") >= 0:  # Found "Step:" in response
                break
        # MovWait()

        # TBD what home2 does
        self.device.sendCommand(self.command.getCommand("home2"))
        while True:
            response = self.device.readData()
            # VB6 code doesn't have colon in this response like first. Not
            # sure if this difference is meaningful.
            if response.find("Step") >= 0:  # Found "Step" in response
                break
        # MovWait()

        if scanSet is not True:
            # TBD what home3 does
            self.device.sendCommand(self.command.getCommand("home3"))
            while True:
                response = self.device.readData()
                # VB6 code doesn't have colon in this response like first.
                # Not sure if this difference is meaningful.
                if response.find("Step") >= 0:  # Found "Step" in response
                    break
            # MovWait()

        scanSet = True
        # MovWait()
        # CurrentElAngle = ElAngle(0)
        # txtCurPos = "Target"
        # CurrentClkStep = 0

    def test(self):
        """
        This has not been run yet. Wait until have more info on how instrument
        responds to commands. This is just a first attempt at porting a VB6
        function to Python.
        """
        self.homeScan()

    def close(self):
        self.device.close()


if __name__ == "__main__":

    main()
