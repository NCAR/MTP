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

        # Average in-flight pitch/roll is about 2/0
        self.defaultPitch = 2.0
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
        self.iwg = IWG(self.rawscan)

        # Initialize the IWG section of the MTP dictionary using the variable
        # list provided in the ascii_parms file.
        self.iwg.initIWGfromAsciiParms(self.asciiparms)

        # Set average in-flight pitch/roll so that if not receiving IWG,
        # we have something
        self.rawscan['IWG1line']['values']['PITCH']['val'] = self.defaultPitch
        self.rawscan['IWG1line']['values']['ROLL']['val'] = self.defaultRoll

    def readIWG(self):
        """ Tell client to read latest IWG record and save to dictionary """
        # Listen for IWG packets
        self.dataI = self.sockI.recv(2048).decode()

        # Display the latest IWG packet.
        print(self.dataI)

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
                self.rawscan['IWG1line']['data'] = m.group(2).rstrip('\n')
                self.rawscan['IWG1line']['asciiPacket'] = \
                    self.dataI.rstrip('\n')

    def getIWG(self):
        """ Return the complete IWG line as received """
        return(self.rawscan['IWG1line']['asciiPacket'])

    def pitch(self):
        """ Return scan average aircraft pitch """
        # Get pitch variable name from ascii_parms file. It is the 15th
        # variable in the standard ascii packet.
        pitch = self.iwg.getVar(self.asciiparms, 15)
        if self.rawscan['IWG1line']['values'][pitch]['val'] == '':
            self.rawscan['IWG1line']['values'][pitch]['val'] = \
                self.defaultPitch
        return(self.rawscan['IWG1line']['values'][pitch]['val'])

    def roll(self):
        """ Return scan average aircraft roll """
        # Get roll variable name from ascii_parms file. It is the 16th variable
        # in the standard ascii packet.
        roll = self.iwg.getVar(self.asciiparms, 16)
        if self.rawscan['IWG1line']['values'][roll]['val'] == '':
            self.rawscan['IWG1line']['values'][roll]['val'] = self.defaultRoll
        return(self.rawscan['IWG1line']['values'][roll]['val'])

    def palt(self):
        """ Return scan average pressure altitude in km """
        # Get pressure altitude variable name from ascii_parms file. It is the
        # 5th variable in the standard ascii packet.
        paltf = self.iwg.getVar(self.asciiparms, 5)
        # Check if var name has an 'F' in it. PALTF is the standard, but
        # just in case...
        if 'F' not in paltf:
            logger.printmsg("warning", "Cannot confirm that IWG packet " +
                            "contains pressure altitude in feet. Units " +
                            "may be wrong in A line")
        var = self.rawscan['IWG1line']['values'][paltf]['val']
        return(float(var) * 0.0003048)  # Feet to km

    def atx(self):
        """ Return scan average air temperature """
        # Get air temperature variable name from ascii_parms file. It is the
        # 19th variable in the standard ascii packet.
        atx = self.iwg.getVar(self.asciiparms, 19)
        # Return air temperature in Kelvin (convert C to K)
        return(float(self.rawscan['IWG1line']['values'][atx]['val']) + 273.15)

    def lat(self):
        """ Return scan average aircraft latitude """
        # Get latitude variable name from ascii_parms file. It is the
        # 1st variable in the standard ascii packet.
        lat = self.iwg.getVar(self.asciiparms, 1)
        return(self.rawscan['IWG1line']['values'][lat]['val'])

    def lon(self):
        """ Return scan average aircraft longitude """
        # Get longitude variable name from ascii_parms file. It is the
        # 2nd variable in the standard ascii packet.
        lon = self.iwg.getVar(self.asciiparms, 2)
        return(self.rawscan['IWG1line']['values'][lon]['val'])
