import logging
from serialInst import SerialInst

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main():
    device = SerialInst()

    server = Server(device)
    server.sendCommand()
    server.loop()

    server.close()
    device.close()


class Server(object):

    def __init__(self, device):
        self.device = device
        self.interrupted = False

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

    def sendCommand(self):
        # Send a command to request the Firmware Version
        self.device.sendCommand(b'V\r')

    def handleEvents(self, timeout=None):
        # Get the response
        response = self.device.readData()
        # MTP returns sent command before returns response
        if (response != 'V'):
            logger.info('Received response ' + response)

    def close(self):
        self.device.close()

if __name__ == "__main__":
    main()
