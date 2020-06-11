###############################################################################
# Convert/relay commands from a client UI via UDP to an instrument
# via RS-232.
#
# Requires the pyserial package, preferably version 3.0+:
#
#   Github: https://github.com/pyserial/pyserial
#   PyPI downloads: https://pypi.python.org/pypi/pyserial
#
# On windows:
#
#   conda install pyserial
#
# On a Raspberry PI, download the tar.gz link with wget, then extract the
# tar file:
#
#   tar zxf pyserial-3.0.tar.gz
#   cd pyserial-3.0
#   python setup.py install --user
#
# That installs pyserial into the user's site-packages directory.  pyserial
# 3.0 includes a miniterm tool that can be used to test the serial
# connection directly, like so:
#
#   python -m serial.tools.miniterm COM6
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import logging
import serial

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SerialInst(object):

    def __init__(self, device=None):
        """
        Serial connection to instrument

        Examples:
        >>> 2+3
        5

        Add:
        if __name__ in "__main__":
            import doctest
            doctest.testmode()
        then run "python3 serial.py"
        and will run code on examples in comments
        """

        if not device:
            device = 'COM6'
        self.device = device
        # Open serial port self.device. To see a list of available ports, type
        # 'python -m serial.tools.list_ports'
        try:
            self.sport = serial.Serial(self.device, 9600, timeout=0)
            if self.sport.isOpen():
                logger.info("port is open")
        except serial.SerialException as ex:
            logger.info("Port is unavailable: " + str(ex))
            exit()

    def getSerial(self):
        """ Return the pointer to the serial port """
        logger.debug("Connected to serial port " + self.sport.name)
        return self.sport

    def sendCommand(self, command):
        """ Send a command to the serial port """
        self.sport.write(command)
        self.sport.flush()
        logger.info('Sending command - ' + str(command))

    def readData(self):
        """
        Read data from the serial port and parse it for status updates.

        How do we know if we have a complete command. For now, I am assuming
        all responses are terminated by a new line. Can run commands through
        the miniterm program to ensure this is true. See comments at the top
        of this file.
        """
        message = ""
        byte = ""
        while True:
            byte = self.sport.read()
            if byte.decode("utf-8") == "\n":
                break
            message += byte.decode("utf-8")
        logger.debug("read data: " + message.rstrip())
        return(message.rstrip())

    def close(self):
        self.sport.close()


if __name__ == "__main__":

    import doctest
    doctest.testmode()
