###############################################################################
#
# This python class is used to read in an IWG1 packet.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import re
import numpy


class readIWG:

    def __init__(self, ascii_parms_file, rawscan):

        self.rawscan = rawscan
        # Because the specific variables sent via the IWG packet can change per
        # project, read the variable names from the project ascii_parms file,
        # which has been copied to the config/ subdir. This will allow all
        # displays to have the correct variable names for this project. If the
        # project-specific ascii_parms file has not been set to overwrite the
        # default, the data plotted will be good, but the variable name labels
        # may not be right.
        status = self.readAsciiParms(ascii_parms_file)

        # If did not successfully read ascii_parms file, exit.
        if status is False:
            exit(1)

    def readAsciiParms(self, ascii_parms_file):
        """ Read in an IWG1 packet and store it to the MTP dictionary """
        try:
            ascii_parms = open(ascii_parms_file, 'r')
        except OSError as err:
            print(err)
            print("Copy ascii_parms for project into config/ dir in order to" +
                  " parse IWG packet correctly then rerun code.")
            return(False)
        except Exception:
            print("Unexpected error occurred while trying to open " +
                  "ascii_parms file")
            return(False)

        i = 2  # index of each variable in IWG1 line (after dateTtime)
        while True:
            line = ascii_parms.readline()
            if len(line) == 0:  # EOF
                break
            m = re.match(re.compile("^#"), line)
            if (m):  # Have a comment
                next
            else:
                newVar = line.rstrip('\n')
                self.rawscan['IWG1line']['values'][newVar] = \
                    {'val': numpy.nan, 'idx': i}
                i = i + 1
            if i > 32:  # Only keep the first 31 values; the rest are user vals
                break

        ascii_parms.close()
        return(True)

    def getIwgPacket(self):
        """  Return the IWG packet to the caller """
        return(self.rawscan['IWG1line']['asciiPacket'])

    def parseIwgPacket(self, IWGpacket):
        """
        Parse an IWG1 packet and store it's values in the data dictionary
        """
        separator = ','
        values = IWGpacket.split(separator)

        # values[0] contains the packet identifier, in this case 'IWG1' so skip
        # values[1] contains the datetime, i.e. yyyymmddThhMMss
        m = re.match("(........)T(..)(..)(..)", values[1])
        if (m):
            # Save YYYYMMDD to variable DATE
            self.rawscan['IWG1line']['values']['DATE']['val'] = m.group(1)
            # Save seconds since midnight to variable TIME
            self.rawscan['IWG1line']['values']['TIME']['val'] = \
                int(m.group(2))*3600+int(m.group(3))*60+int(m.group(4))

        # Parse the rest of the line and assign variables to the data
        # dictionary
        for key in self.rawscan['IWG1line']['values']:
            if (key != 'DATE' and key != 'TIME'):
                self.rawscan['IWG1line']['values'][key]['val'] = \
                    values[int(self.rawscan['IWG1line']['values'][key]['idx'])]
