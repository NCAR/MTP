###############################################################################
# This python class is used to read in an IWG1 packet.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import re
import numpy
from EOLpython.Qlogger.messageHandler import QLogger as logger


class IWG:

    def __init__(self, rawscan):

        self.rawscan = rawscan
        # Flag to indicate when parseIwgPacket has thrown an error.
        self.ERROR_FLAG = False

        self.index = 2  # index of each variable in IWG1line (after dateTtime)

    def createPacket(self, newVar):
        """ Create the IWG1line section of the MTP dictionary dynamically """

        self.rawscan['IWG1line']['values'][newVar] = \
            {'val': numpy.nan, 'idx': self.index}
        self.index = self.index + 1
        if self.index > 32:  # Only keep first 31 values; rest are user vals
            return(False)
        else:
            return(True)

    def getIwgPacket(self):
        """  Return the IWG packet to the caller """
        return(self.rawscan['IWG1line']['asciiPacket'])

    def parseIwgPacket(self, IWGpacket, ascii_parms_file):
        """
        Parse an IWG1 packet and store it's values in the data dictionary. If
        this function throw an error, don't parse any more packets that arrive.
        Ignore them when self.ERROR_FLAG = True
        """
        if self.ERROR_FLAG is True:
            return(False)  # Did not succeed in reading IWG packet

        separator = ','
        values = IWGpacket.split(separator)

        # Only keep first 31 values; rest are user vals
        del(values[33:])
        print(values)

        # values[0] contains the packet identifier, in this case 'IWG1' so skip
        # values[1] contains the datetime, i.e. yyyymmddThhMMss
        m = re.match("(........)T(..)(..)(..)", values[1])
        if (m):
            # Save YYYYMMDD to variable DATE
            self.rawscan['IWG1line']['values']['DATE']['val'] = m.group(1)
            # Save seconds since midnight to variable TIME
            self.rawscan['IWG1line']['values']['TIME']['val'] = \
                int(m.group(2))*3600+int(m.group(3))*60+int(m.group(4))

        # If length of values read in from ascii_parms file doesn't match
        # length of IWG1 packet received, warn user. len below includes date
        # and time.
        if len(self.rawscan['IWG1line']['values']) != len(values):
            self.ERROR_FLAG = True
            logger.printmsg("ERROR", "IWG packet being received on UDP feed " +
                            "has a different number of values (" +
                            str(len(values)) + ") than listed in ascii_parms" +
                            " file (" +
                            str(len(self.rawscan['IWG1line']['values'])) +
                            ") in config dir " + ascii_parms_file +
                            ". Should be 33.")
            exit(1)

        # Parse the rest of the line and assign variables to the data
        # dictionary
        for key in self.rawscan['IWG1line']['values']:
            if (key != 'DATE' and key != 'TIME'):
                self.rawscan['IWG1line']['values'][key]['val'] = \
                    values[int(self.rawscan['IWG1line']['values'][key]['idx'])]

        return(True)  # Successful parse of IWG packet
