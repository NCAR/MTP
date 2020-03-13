###############################################################################
# Code to create the final output data file in ICARTT 2110 format.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import os
from lib.rootdir import getrootdir
from Qlogger.messageHandler import QLogger as logger


class ICARTT():

    def __init__(self, client):
        self.client = client

        self.file_format_index = '2110'
        self.header = ""  # string to hold header

    def get_startdate(self):
        # Get date of first record in flightData array
        self.rec = self.client.reader.getRecord(0)

        date = self.rec['Aline']['values']['DATE']['val']

        return(date)

    def getICARTT(self):
        """ Build name of ICARTT file to save data to """

        date = self.get_startdate()
        return(os.path.join(getrootdir(), 'config/MP' + date + '.NGV'))

    def build_header(self, proc_date):
        """
        Build the ICARTT data header by gathering information from the MTP data
        and config dictionaries
        """

        self.header += self.client.configfile.getVal('pi') + "\n"
        self.header += self.client.configfile.getVal('organization') + "\n"
        self.header += self.client.configfile.getVal('platform') + "\n"
        self.header += self.client.getProj() + "\n"
        self.header += "1, 1\n"

        # Get data file start date
        date = self.get_startdate()
        year = date[0:4]
        month = date[4:6]
        day = date[6:8]
        self.header += year + ", " + month + ", " + day + ", "

        # Get processing date (will usually be today)
        proc_year = proc_date[0:4]
        proc_month = proc_date[4:6]
        proc_day = proc_date[6:8]
        self.header += proc_year + ", " + proc_month + ", " + proc_day + "\n"

        # When all done, count lines and prepend first line if ICARTT file
        # which is "number of lines in header, file format index"
        self.numlines = self.header.count('\n') + 1  # +1 for line about to add
        self.header = str(self.numlines) + ", " + self.file_format_index + \
            "\n" + self.header

    def save(self, filename):
        """ Save data to ICARTT file """
        self.build_header()
        with open(filename, 'w') as f:
            f.write(self.header)

        logger.printmsg("info", "File " + filename + " successfully written",
                        "If file already existed, it was overwritten")
