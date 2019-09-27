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
#   python -m serial.tools.miniterm /dev/ttyUSB6
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import logging
#import fcntl
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
        # Open serial port self.device
        # Lock it per https://stackoverflow.com/questions/19809867/how-to-check
        # -if-serial-port-is-already-open-by-another-process-in-linux-using
        try:
            self.sport = serial.Serial(self.device, 9600, timeout=0)
            #if self.sport.isOpen():
            #    try:
            #        fcntl.flock(self.sport.fileno(), fcntl.LOCK_EX |
            #                    fcntl.LOCK_NB)
            #    except IOError:
            #        logger.info("port is busy")
            #        exit(1)
        except serial.SerialException as ex:
            logger.info("Port is unavailable: " + str(ex))
            exit()
        #self.sport.nonblocking()

    def getSerial(self):
        """ Return the pointer to the serial port """
        logger.debug("Connected to serial port " + self.sport.name)
        return self.sport

    def getVersion(self):
        """ Send a command to the instrument """
        self.sport.write(b'V\r')  # To get version, MTP expect "V" + vbCr
        # vbCr : - return to line beginning
        # Represents a carriage-return character for print and display
        # functions.
        # ASCII character 13, vbCr, is a carriage return (without a line feed)
        logger.info("Sending command - V\r")

    def readData(self):
        """
        Read data from the serial port and parse it for status updates.

        How do we know if we have a complete command. End in newline?
        Set number of chars??
        """
        rdata = self.sport.read(512)
        logger.debug("read data: " + repr(rdata))

    def close(self):
        self.sport.close()


if __name__ in "__main__":
    import doctest
    doctest.testmode()
