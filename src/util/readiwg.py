###############################################################################
# This python class is used to read in an IWG1 packet.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import re
import numpy
from util.readascii_parms import AsciiParms
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class IWG:

    def __init__(self, iwgrecord):
        """ This class takes as input an IWGrecord dictionary """

        self.iwg = iwgrecord
        # Flag to indicate when parseIwgPacket has thrown an error.
        self.ERROR_FLAG = False

        self.index = 2  # index of each variable in IWG1line (after dateTtime)

    def initIWGfromAsciiParms(self, asciiparms):
        """
        Initialize the IWG section of the MTP dictionary using the variable
        list provided in the ascii_parms file.
        """
        # Init an ascii parms file reader
        self.ascii_parms = AsciiParms(asciiparms)

        # Attempt to open ascii_parms file. Exit on failure.
        if self.ascii_parms.open() is False:
            exit(1)

        status = True
        while status:
            # Read var from ascii_parms file
            newVar = self.ascii_parms.readVar()

            # Save to IWG section of dictionary
            status = self.createPacket(newVar)

        self.ascii_parms.close()

    def getVar(self, asciiparms, index):
        """ Get the index'th var from ascii parms file. """

        for var in self.iwg['values']:
            if var != 'DATE' and var != 'TIME':
                if self.iwg['values'][var]['idx'] == index + 1:
                    newVar = var
                    break

        return newVar

    def createPacket(self, newVar):
        """ Create the IWG1line section of the MTP dictionary dynamically """

        self.iwg['values'][newVar] = \
            {'val': numpy.nan, 'idx': self.index}
        self.index = self.index + 1
        if self.index > 32:  # Only keep first 31 values; rest are user vals
            return False
        else:
            return True

    def getIwgPacket(self):
        """  Return the IWG packet to the caller """
        return self.iwg['asciiPacket']

    def parseIwgPacket(self, IWGpacket, ascii_parms_file):
        """
        Parse an IWG1 packet and store it's values in the data dictionary. If
        this function throw an error, don't parse any more packets that arrive.
        Ignore them when self.ERROR_FLAG = True
        """
        if self.ERROR_FLAG is True:
            return False  # Did not succeed in reading IWG packet

        separator = ','
        self.values = IWGpacket.split(separator)

        # Only keep first 31 values; rest are user vals
        del self.values[33:]

        # values[0] contains the packet identifier, in this case 'IWG1' so skip
        # values[1] contains the datetime, i.e. yyyymmddThhMMss
        m = re.match("(........)T(..)(..)(..)", self.values[1])
        if (m):
            # Save YYYYMMDD to variable DATE
            self.iwg['values']['DATE']['val'] = m.group(1)
            # Save seconds since midnight to variable TIME
            self.iwg['values']['TIME']['val'] = \
                int(m.group(2))*3600+int(m.group(3))*60+int(m.group(4))

        # If length of values read in from ascii_parms file doesn't match
        # length of IWG1 packet received, warn user. len below includes date
        # and time.
        if len(self.iwg['values']) != len(self.values):
            self.ERROR_FLAG = True
            logger.error("IWG packet being received on UDP feed has a " +
                         "different number of values (" +
                         str(len(self.values)) + ") than listed in " +
                         "ascii_parms file (" + str(len(self.iwg['values'])) +
                         ") in config dir " + ascii_parms_file +
                         ". Should be 33.")
            exit(1)

        # Parse the rest of the line and assign variables to the data
        # dictionary
        for key in self.iwg['values']:
            if (key != 'DATE' and key != 'TIME'):
                self.iwg['values'][key]['val'] = \
                    self.values[int(self.iwg['values'][key]['idx'])]

        return True  # Successful parse of IWG packet
