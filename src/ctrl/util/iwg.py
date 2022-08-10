###############################################################################
# MTP-specific functions for storing and manipulating IWG packets. Uses
# util/readiwg which assumes an MTPrecord exists, so create one here specific
# to control program needs.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import re
import copy
import socket
from util.readiwg import IWG
from util.MTP import MTPrecord
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPiwg():

    def __init__(self):
        # Dictionary to hold IWG data. This is a complete MTP record dictionary
        # which is overkill at this point, but I am not sure if being able to
        # hold the entire MTP record will be useful later, so for now
        # instantiate the entire thing. To work with IWG data, a single record
        # holds a pointer to the current data as well as a history of the last
        # n IWG packets. (not sure what N is yet..)
        self.rawscan = copy.deepcopy(MTPrecord)

        # Average in-flight pitch/roll is about 2.7/0
        self.defaultPitch = 2.7
        self.defaultRoll = 0.0

    def connectIWG(self, iwgport):
        # Connect to IWG UDP data stream
        self.sockI = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Share the IWG packet port
        self.sockI.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sockI.bind(("0.0.0.0", iwgport))
        self.sockI.setblocking(False)

    def socket(self):
        return(self.sockI)

    def initIWG(self, asciiparms):
        """
        Instantiate an instance of an IWG reader. Points to an MTP dictionary
        that will store the IWG data. Requires the location of the ascii_parms
        file.
        """
        self.asciiparms = asciiparms

        # Initialize the IWG reader
        self.iwg = IWG(self.rawscan['IWG1line'])

        # Initialize the IWG section of the MTP dictionary using the variable
        # list provided in the ascii_parms file.
        self.iwg.initIWGfromAsciiParms(self.asciiparms)

        # Get the names of the variables from the asciiparms file that we
        # need for the A line
        self.pitch = self.iwg.getVar(self.asciiparms, 15)
        self.roll = self.iwg.getVar(self.asciiparms, 16)
        self.paltf = self.iwg.getVar(self.asciiparms, 5)
        self.atx = self.iwg.getVar(self.asciiparms, 19)
        self.lat = self.iwg.getVar(self.asciiparms, 1)
        self.lon = self.iwg.getVar(self.asciiparms, 2)

        # Set average in-flight pitch/roll so that if not receiving IWG,
        # we have something. Also set remaining IWG values to zero so they
        # aren't nan. But keep them non-physical so they are obvious
        self.rawscan['IWG1line']['values'][self.pitch]['val'] = \
            self.defaultPitch
        self.rawscan['IWG1line']['values'][self.roll]['val'] = self.defaultRoll
        self.rawscan['IWG1line']['values'][self.paltf]['val'] = 0
        self.rawscan['IWG1line']['values'][self.atx]['val'] = 0
        self.rawscan['IWG1line']['values'][self.lat]['val'] = 0
        self.rawscan['IWG1line']['values'][self.lon]['val'] = 0

    def readIWG(self):
        """ Tell client to read latest IWG record and save to dictionary """
        # Listen for IWG packets
        self.dataI = self.sockI.recv(2048).decode()

        # Display the latest IWG packet.
        logger.printmsg("info", self.dataI)

        self.saveIWG()

    def saveIWG(self):
        # Store IWG record to values field in data dictionary
        # This currently saves INSTANTANEOUS IWG values, which are then
        # used in the A line. Need to update to do scan averaging - JAA
        status = self.iwg.parseIwgPacket(self.dataI, self.asciiparms)
        if status is True:  # Successful parse of IWG packet
            # Store to date, data, & asciiPacket
            if 're' in self.rawscan['IWG1line']:
                m = re.match(re.compile(self.rawscan['IWG1line']['re']),
                             self.dataI)
                self.rawscan['IWG1line']['date'] = m.group(1)  # packet time
                self.rawscan['IWG1line']['data'] = m.group(2).rstrip('\r')
                self.rawscan['IWG1line']['asciiPacket'] = \
                    self.dataI.rstrip('\r')

    def getIWG(self):
        """ Return the complete IWG line as received """
        return(self.rawscan['IWG1line']['asciiPacket'])

    def getPitch(self):
        """ Return scan average aircraft pitch """
        if self.rawscan['IWG1line']['values'][self.pitch]['val'] == '':
            self.rawscan['IWG1line']['values'][self.pitch]['val'] = \
                self.defaultPitch
        return(self.rawscan['IWG1line']['values'][self.pitch]['val'])

    def getRoll(self):
        """ Return scan average aircraft roll """
        if self.rawscan['IWG1line']['values'][self.roll]['val'] == '':
            self.rawscan['IWG1line']['values'][self.roll]['val'] = \
                self.defaultRoll
        return(self.rawscan['IWG1line']['values'][self.roll]['val'])

    def getPalt(self):
        """ Return scan average pressure altitude in km """
        # Check if var name has an 'F' in it. PALTF is the standard, but
        # just in case...
        if 'F' not in self.paltf:
            logger.printmsg("warning", "Cannot confirm that IWG packet " +
                            "contains pressure altitude in feet. Units " +
                            "may be wrong in A line")
        var = self.rawscan['IWG1line']['values'][self.paltf]['val']
        return(float(var) * 0.0003048)  # Feet to km

    def getAtx(self):
        """ Return scan average air temperature """
        # Return air temperature in Kelvin (convert C to K)
        return(float(self.rawscan['IWG1line']['values'][self.atx]['val']) +
               273.15)

    def getLat(self):
        """ Return scan average aircraft latitude """
        return(self.rawscan['IWG1line']['values'][self.lat]['val'])

    def getLon(self):
        """ Return scan average aircraft longitude """
        return(self.rawscan['IWG1line']['values'][self.lon]['val'])
