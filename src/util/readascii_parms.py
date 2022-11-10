###############################################################################
# This python class is used to read in an ascii_parms file.
#
# Because the specific variables sent via an IWG packet can change per project,
# it is necessary to read the variable names from the project ascii_parms file
# in order to correctly identify the variables in the IWG packet.
#
# The ascii_parms file can be found under $PROJ_DIR on the EOL servers.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import re
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class AsciiParms:

    def __init__(self, ascii_parms_file):
        """
        Initialize an ascii_parms reader.

        Input: Requires full path to ascii_parms file
        """

        self.ascii_parms_file = ascii_parms_file

    def open(self):
        try:
            self.ascii_parms = open(self.ascii_parms_file, 'r')
        except OSError as err:
            logger.error(str(err) + " Copy ascii_parms for " +
                         "project into config/ dir in order to parse IWG" +
                         " packet correctly then rerun code.")
            return False
        except Exception as error:
            logger.error(str(error) + " Unexpected error " +
                         "occurred while trying to open ascii_parms file")
            return False

    def readVar(self):
        """
        Read in the next variable from the ascii parms file. Skips comment
        lines indicated by a pound sign (#).
        """
        while True:
            line = self.ascii_parms.readline()
            if len(line) == 0:  # EOF
                break

            # Check for comment lines
            m = re.match(re.compile("^#"), line)
            if (m):  # Have a comment
                next
            else:
                newVar = line.rstrip('\n')
                return newVar

        return None  # Get here at EOF

    def get(self):
        return self.ascii_parms_file

    def close(self):
        self.ascii_parms.close()
