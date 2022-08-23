###############################################################################
# MTP-specific functions for storing and manipulating IWG packets. Uses
# util/readiwg.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import re
import numpy
import copy
import socket
from util.readiwg import IWG
from util.IWG import IWGrecord
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPiwg():

    def __init__(self):
        # Dictionary to hold IWG data.
        self.iwgrecord = copy.deepcopy(IWGrecord)

        # Array to hold all the IWG records received during a single MTP scan
        self.scanIWGlist = []

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
        self.iwg = IWG(self.iwgrecord)

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

        # Set in-flight pitch/roll so that if not receiving IWG,
        # we have something. Also set remaining IWG values to zero so they
        # aren't nan. But keep them non-physical so they are obvious
        self.iwgrecord['values'][self.pitch]['val'] = self.defaultPitch
        self.iwgrecord['values'][self.roll]['val'] = self.defaultRoll
        self.iwgrecord['values'][self.paltf]['val'] = numpy.nan
        self.iwgrecord['values'][self.atx]['val'] = numpy.nan
        self.iwgrecord['values'][self.lat]['val'] = numpy.nan
        self.iwgrecord['values'][self.lon]['val'] = numpy.nan

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
            if 're' in self.iwgrecord:
                m = re.match(re.compile(self.iwgrecord['re']),
                             self.dataI)
                self.iwgrecord['date'] = m.group(1)  # packet time
                self.iwgrecord['data'] = m.group(2).rstrip('\r')
                self.iwgrecord['asciiPacket'] = \
                    self.dataI.rstrip('\r')

        self.scanIWGlist.append(copy.deepcopy(self.iwgrecord))

    def clearIWG(self):
        """ Clear the list of IWG records """
        self.scanIWGlist = []

    def averageIWG(self):
        """
        Calculate the average pitch, roll, palt, atx, lat, and lon from the
        values collected during the current scan
        """
        self.sapitch = numpy.nan
        self.srpitch = numpy.nan
        self.saroll = numpy.nan
        self.srroll = numpy.nan
        self.sapalt = numpy.nan
        self.srpalt = numpy.nan
        self.saatx = numpy.nan
        self.sratx = numpy.nan
        self.salat = numpy.nan
        self.srlat = numpy.nan
        self.salon = numpy.nan
        self.srlon = numpy.nan

        if len(self.scanIWGlist) == 0:
            return(False)  # Nothing to average so bail

        # calculate avg and rmse pitch
        valueList = self.getVals(self.pitch)
        self.sapitch = self.avg(valueList)
        self.srpitch = self.rmse(valueList, self.sapitch)

        # calculate avg and rmse roll
        valueList = self.getVals(self.roll)
        self.saroll = self.avg(valueList)
        self.srroll = self.rmse(valueList, self.saroll)

        # calculate avg and rmse pressure altitude
        valueList = self.getVals(self.paltf)
        self.sapalt = self.avg(valueList)
        self.srpalt = self.rmse(valueList, self.sapalt)

        # calculate avg and rmse air temperature
        valueList = self.getVals(self.atx)
        self.saatx = self.avg(valueList)
        self.sratx = self.rmse(valueList, self.saatx)

        # calculate avg and rmse latitude
        valueList = self.getVals(self.lat)
        self.salat = self.avg(valueList)
        self.srlat = self.rmse(valueList, self.salat)

        # calculate avg and rmse longitude
        valueList = self.getVals(self.lon)
        self.salon = self.avg(valueList)
        self.srlon = self.rmse(valueList, self.salon)

        return(True)

    def getVals(self, var):
        """
        Retrieve values from the scanIWGlist for the requested variable
        """
        valueList = []
        for iwgrec in self.scanIWGlist:
            if iwgrec['values'][var]['val'] != '':  # Skip missing values
                valueList.append(float(iwgrec['values'][var]['val']))

        return(valueList)

    def rmse(self, valueList, avg):
        """ Calculate RMSE from a list of values and their average """
        rmse = 0
        if len(valueList) == 0:
            return(numpy.nan)  # Nothing to find RMSE so return missing
        else:
            for val in valueList:
                rmse = rmse + (float(val) - avg)**2
            rmse = numpy.sqrt(rmse/len(valueList))

        return(rmse)

    def avg(self, valueList):
        """ Calculate the average of a list of values """
        if len(valueList) == 0:
            return(numpy.nan)  # Nothing to average so return missing
        else:
            return(sum(valueList)/len(valueList))

    def getIWG(self):
        """ Return the complete IWG line as received """
        return(self.iwgrecord['asciiPacket'])

    def saveAvg(self, date, aline):
        """
        Save the time and values from the last average so that if IWG drops
        out, the most recent average can be recovered
        """
        self.iwgrecord['date'] = date
        self.iwgrecord['data'] = aline

    def getLastAvgTime(self):
        """ Get the time of the last successful average """
        if self.iwgrecord['date'] != "":
            return(self.iwgrecord['date'])
        else:
            return("")  # Never had IWG

    def getAvgAline(self):
        """
        Get the IWG average portion of the A line from last successful average
        """
        return(self.iwgrecord['data'])

    def getPitch(self):
        """ Return instantaneous aircraft pitch """
        if self.iwgrecord['values'][self.pitch]['val'] == '':
            self.iwgrecord['values'][self.pitch]['val'] = self.defaultPitch
        return(self.iwgrecord['values'][self.pitch]['val'])

    def getSAPitch(self):
        """ Return scan average aircraft pitch """
        if numpy.isnan(self.sapitch):
            self.sapitch = self.defaultPitch
        return(self.sapitch)

    def getSRPitch(self):
        """ Return scan RMSE pitch """
        return(self.srpitch)

    def getRoll(self):
        """ Return instantaneous aircraft roll """
        if self.iwgrecord['values'][self.roll]['val'] == '':
            self.iwgrecord['values'][self.roll]['val'] = self.defaultRoll
        return(self.iwgrecord['values'][self.roll]['val'])

    def getSARoll(self):
        """ Return scan average aircraft roll """
        if numpy.isnan(self.saroll):
            self.saroll = self.defaultRoll
        return(self.saroll)

    def getSRRoll(self):
        """ Return scan RMSE roll """
        return(self.srroll)

    def getPalt(self):
        """ Return instantaneous pressure altitude in km """
        # Check if var name has an 'F' in it. PALTF is the standard, but
        # just in case...
        if 'F' not in self.paltf:
            logger.printmsg("warning", "Cannot confirm that IWG packet " +
                            "contains pressure altitude in feet. Units " +
                            "may be wrong in A line")
        var = self.iwgrecord['values'][self.paltf]['val']
        return(float(var) * 0.0003048)  # Feet to km

    def getSAPalt(self):
        """ Return scan average pressure altitude in km """
        return(self.sapalt * 0.0003048)  # Feet to km

    def getSRPalt(self):
        """ Return scan RMSE pressure altitude in km """
        return(self.srpalt * 0.0003048)  # Feet to km

    def getAtx(self):
        """ Return instantaneous air temperature """
        # Return air temperature in Kelvin (convert C to K)
        return(float(self.iwgrecord['values'][self.atx]['val']) + 273.15)

    def getSAAtx(self):
        """ Return scan average air temperature """
        return(self.saatx + 273.15)  # C to K

    def getSRAtx(self):
        """ Return scan RMSE air temperature """
        return(self.sratx)

    def getLat(self):
        """ Return instantaneous aircraft latitude """
        return(self.iwgrecord['values'][self.lat]['val'])

    def getSALat(self):
        """ Return scan average aircraft latitude """
        return(self.salat)

    def getSRLat(self):
        """ Return scan RMSE aircraft latitude """
        return(self.srlat)

    def getLon(self):
        """ Return instantaneous aircraft longitude """
        return(self.iwgrecord['values'][self.lon]['val'])

    def getSALon(self):
        """ Return scan average aircraft longitude """
        return(self.salon)

    def getSRLon(self):
        """ Return scan RMSE aircraft longitude """
        return(self.srlon)
