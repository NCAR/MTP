###############################################################################
# MTP-specific functions for storing and manipulating IWG packets. Uses
# util/readiwg which assumes an MTPrecord exists, so create one here specific
# to control program needs.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
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

    def readIWG(self):
        """ Tell client to read latest IWG record and save to dictionary """
        # Listen for IWG packets
        self.dataI = self.sockI.recv(2048).decode()

        # Display the latest IWG packet.
        print(self.dataI)

        self.saveIWG()

    def saveIWG(self):
        # Store IWG record to values field in data dictionary
        status = self.iwg.parseIwgPacket(self.dataI, self.asciiparms)
        if status is True:  # Successful parse of IWG packet
            # Store to date, data, & asciiPacket
            # self.iwg.parseLine(self.dataI)
            self.rawscan['IWG1line']['asciiPacket'] = self.dataI.rstrip('\n')
