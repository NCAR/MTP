from serial import Serial


def main():
    device = Serial()

    server = Server(device)
    # To start, just send a single command and get a response. Don't loop.
    # server.loop()
    server.handleEvents()

    server.close()
    device.close()


class Server(object):

    def __init__(self, device):
        self.device = device

    def loop(self):

        while not self.interrupted:
            try:
                self.data = None
                self.handleEvents()
            except KeyboardInterrupt:
                self.interrupted = True

    def handleEvents(self, timeout=None):
        # Get a pointer to the serial port
        self.device.getSerial()
        # Send a command to request the Firmware Version
        self.device.getVersion()
        # Get the response
        self.device.readData()
