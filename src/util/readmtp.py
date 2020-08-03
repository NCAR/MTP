###############################################################################
#
# This python class is used to read in various formats of the raw MTP data.
#
# In real-time, the MTP creates raw data files that contain a block of lines
# for each scan separated by one or more blank lines, e.g.
#
# A 20140606 06:22:52 +03.98 00.25 +00.07 00.33 +03.18 0.01 268.08 00.11
#     -43.308 +0.009 +172.469 +0.000 +074146 +073392
# IWG1,20140606T062250,-43.3061,172.455,3281.97,,10508.5,,149.998,164.027,,
#     0.502512,3.11066,283.283,281.732,-1.55388,3.46827,0.0652588,-0.258496,
#     2.48881,-5.31801,-5.92311,7.77836,683.176,127.248,1010.48,14.6122,
#     297.157,0.303804,104.277,,-72.1708,
# B 018963 020184 019593 018971 020181 019593 018970 020170 019587 018982
#     020193 019589 018992 020223 019617 019001 020229 019623 018992 020208
#     019601 018972 020181 019572 018979 020166 019558 018977 020161 019554
# M01: 2928 2321 2898 3082 1923 2921 2432 2944
# M02: 2016 1394 2096 2202 2136 1508 4095 1558
# Pt: 2177 13823 13811 10352 13315 13327 13304 14460
# E 021506 022917 022752 019806 021164 020697
#
# The variables in each line are (they should match the project
# nidas/default.xml file:
#
# A <date> <time> SAPITCH SRPITCH SAROLL SRROLL SAPALT SRPALT SAAT SRAT SALAT
#     SRLAT SALON SRLON SMCMD SMENC
# B SCNT[30]
# M01: VM08CNTE VVIDCNTE VP08CNTE VMTRCNTE VSYNCNTE VP15CNTE VP05CNTE VM15CNTE
# M02: ACCPCNTE TDATCNTE TMTRCNTE TAIRCNTE TSMPCNTE TPSPCNTE TNCCNTE TSYNCNTE
# Pt: TR350CNTP TTCNTRCNTP TTEDGCNTP TWINCNTP TMIXCNTP TAMPCNTP TNDCNTP
#     TR600CNTP
# E TCNT[6]
#
# When combined into a Ascii packet, the lines A, B, M01, M02, P, and E are
# concatenated, in order, and changed so all values are comma-separated, e.g.:
# MTP,20140606T062252,+03.98,00.25,+00.07,00.33,+03.18,0.01,268.08,00.11,
#     -43.308,+0.009,+172.469,+0.000,+074146,+073392,018963,020184,019593,
#     018971,020181,019593,018970,020170,019587,018982,020193,019589,018992,
#     020223,019617,019001,020229,019623,018992,020208,019601,018972,020181,
#     019572,018979,020166,019558,018977,020161,019554,2928,2321,2898,3082,
#     1923,2921,2432,2944,2016,1394,2096,2202,2136,1508,4095,1558,2177,13823,
#     13811,10352,13315,13327,13304,14460,021506,022917,022752,019806,021164,
#     020697
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import os
import re
import numpy
import json
import copy
from util.MTP import MTPrecord
from EOLpython.Qlogger.messageHandler import QLogger as logger


class readMTP:

    def __init__(self):
        # Instantiate dictionary to hold the MTP data.
        self.curscan = copy.deepcopy(MTPrecord)

        # An array of MTP data dictionaries - used to display a single variable
        # across time.
        self.flightData = []

        # Set the scan we are working with to be the current scan
        self.rawscan = self.curscan

    def getJson(self, projdir, proj, fltno):
        """ Build name of json file to save flight data to """
        # This is used if the code is restarted mid-flight to provide access
        # to previous data.
        return(os.path.join(projdir, proj+fltno.lower()+'.mtpRealTime.json'))

    def setRawscan(self, index):
        """ Set the MTP data dictionary we want to read a scan from """
        # The current scan is in self.rawscan and in the last scan in
        # self.flightData. Sometimes we might want this class to read from
        # a scan other than the current scan. Set that scan here.
        # Returns True or False to indicate if scan was sucessfully set to
        # index or not.
        try:
            self.rawscan = self.flightData[index]
        except Exception as err:
            logger.printmsg("ERROR", "No data available: " + str(err),
                            "Try loading some raw data")
            self.rawscan = None
            raise

        return(True)

    def resetRawscan(self):
        """ Set the data dictionary back to the current scan """
        self.rawscan = self.curscan

    def getRawscan(self):
        """ Return a pointer to the MTP data dictionary of the current scan """
        return(self.rawscan)

    def getRecord(self, index):
        """ Return a pointer to the MTP data dictionary for a specific scan """
        return(self.flightData[index])

    def getNumRecs(self):
        """ Return the number of records in the array of scans """
        return(len(self.flightData))

    def readRawScan(self, raw_data_file):
        """
        Read in a scan (a group of lines) from an MTP .RAW file and store them
        to a dictionary
        """
        while True:

            # Read in a single line
            line = raw_data_file.readline()
            if len(line) == 0:  # EOF
                return(False)  # At EOF

            # Store line to dictionary
            self.parseLine(line)

            # Check if we have a complete scan (all linetypes have found = True
            foundall = True  # Init so can boolean '&' each rawscan line
            for linetype in self.rawscan:
                if 'found' in self.rawscan[linetype]:
                    foundall = foundall & self.rawscan[linetype]['found']

            if (foundall):
                # Reset found to False for all and return
                for linetype in self.rawscan:
                    if 'found' in self.rawscan[linetype]:
                        self.rawscan[linetype]['found'] = False
                return(True)  # Not at EOF

    def reportScanStatus(self, selectedRawFile):
        """
        If read an entire file and never get foundall = True, report to user
        status of all found fields as a hint to what went wrong.
        """
        status = "Line types found:\n"
        for linetype in self.rawscan:
            if 'found' in self.rawscan[linetype]:
                status += linetype + ": " + \
                          str(self.rawscan[linetype]['found']) + "\n"

        logger.printmsg('ERROR', "No complete scans found in" +
                        selectedRawFile, status)

    def clearFlightData(self):
        """ clear the flightData list of dictionaries """
        self.flightData.clear()

    def archive(self):
        """ Append the current record to the flight library (flightData[]) """
        self.flightData.append(copy.deepcopy(self.rawscan))

    def removeJSON(self, filename):
        """ Delete the JSON file on disk """
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            logger.printmsg('ERROR', "Failed to remove JSON file " + e)

    def save(self, filename):
        """ Append the current record to a JSON file on disk """
        with open(filename, 'a') as f:
            json.dump(self.rawscan, f)
            f.write('\n')

    def load(self, filename):
        """
        Read records from JSON file on disk and prepend to flightData array
        """
        # Check if file exists. If not, nothing to load, so return failed
        if not os.path.isfile(filename):
            return(False)

        with open(filename, 'r') as f:
            previous_data = [json.loads(line) for line in f]

        # There does not appear to be a list.prepend() python function so
        # extend the previous_data array with any data written to flightData
        # since restart, and then replace flightData with the previous_data.
        # This could potentially cause us to loose a *display* record if
        # flightData is written to between the two commands below. No actual
        # data is lost - everything collected is in the JSON file.
        previous_data.extend(self.flightData)
        self.flightData = previous_data

        return(True)

    def parseLine(self, line):
        """
        Loop through possible line types, match the line, and store it in
        the dictionary
        """
        for linetype in self.rawscan:
            if 're' in self.rawscan[linetype]:
                m = re.match(re.compile(self.rawscan[linetype]['re']), line)
                if (m):
                    # Store data. Handle special case of date in A line
                    if (linetype == 'Aline'):  # Reformat date/time
                        self.rawscan[linetype]['date'] =  \
                            m.group(1)+"T"+m.group(2)+m.group(3)+m.group(4)
                        self.rawscan[linetype]['data'] = m.group(5)
                    elif (linetype == 'IWG1line'):  # Reformat date/time
                        self.rawscan[linetype]['asciiPacket'] = \
                            line.rstrip('\n')
                        self.rawscan[linetype]['date'] = m.group(1)
                        self.rawscan[linetype]['data'] = \
                            m.group(2).rstrip('\n')
                    else:
                        self.rawscan[linetype]['data'] = \
                            m.group(2).rstrip('\n')
                    # Mark found
                    self.rawscan[linetype]['found'] = True
                    # Exit matching loop
                    return(True)

    def getACAlt(self):
        """ Return the aircraft alititude (km) from the Aline """
        return(self.rawscan['Aline']['values']['SAPALT']['val'])

    def getDate(self):
        """ Return the date of the current A line record """
        return(self.rawscan['Aline']['values']['DATE']['val'])

    def getAline(self):
        """ Return the A line to the caller """
        # Create the Aline
        Aline = "A " + self.rawscan['Aline']['values']['DATE']['val'] + " " + \
                self.rawscan['Aline']['values']['timestr']['val'] + " " + \
                self.rawscan['Aline']['data']
        return(Aline)

    def getBline(self):
        """ Return the B line to the caller """
        # Create the Bline
        Bline = "B " + self.rawscan['Bline']['data']
        return(Bline)

    def getM01line(self):
        """ Return the M01 line to the caller """
        # Create the M01line
        M01line = "M01: " + self.rawscan['M01line']['data']
        return(M01line)

    def getM02line(self):
        """ Return the M02 line to the caller """
        # Create the M02line
        M02line = "M02: " + self.rawscan['M02line']['data']
        return(M02line)

    def getPtline(self):
        """ Return the Pt line to the caller """
        # Create the Ptline
        Ptline = "Pt: " + self.rawscan['Ptline']['data']
        return(Ptline)

    def getEline(self):
        """ Return the E line to the caller """
        # Create the Eline
        Eline = "E " + self.rawscan['Eline']['data']
        return(Eline)

    def getAsciiPacket(self):
        """
        Combine the separate lines from a raw scan into an Ascii packet
        (suitable for UDP-ing around the plane). Stores the Ascii packet in the
        dictionary. Also, returns the Ascii packet to the caller.
        """
        packet = []
        packet.append("MTP")
        packet.append(self.rawscan['Aline']['date'])  # Date & Time
        packet.append(self.rawscan['Aline']['data'])  # A line rest
        packet.append(self.rawscan['Bline']['data'])
        packet.append(self.rawscan['M01line']['data'])
        packet.append(self.rawscan['M02line']['data'])
        packet.append(self.rawscan['Ptline']['data'])
        packet.append(self.rawscan['Eline']['data'])

        UDPpacket = self.joinPacket(packet)

        # Store the new packet in our dictionary.
        self.writeFlightData(UDPpacket)

        # Return the newly created packet
        return (UDPpacket)

    def joinPacket(self, packet):
        # Turn our packet into a comma separated string, and return it
        # But since the individual data strings are space separated, split
        # string on spaces and rejoin with commas
        separator = ' '
        line = separator.join(packet)  # Join the components into a string
        values = line.split()          # Split string on one or more spaces
        separator = ','
        UDPpacket = separator.join(values)

        return(UDPpacket)

    def createAdata(self):
        """
        Create an A data line from the values in the dictionary. This is useful
        when all we have access to is the UDP'd Ascii packet and we want to
        recreate the records as stored by the VB code for past projects.
        """
        # According to documentation for the Python standard library
        # [https://docs.python.org/3/library/stdtypes.html#typesmapping
        # accessed Nov 6, 2019], as of version 3.7, "Dictionary order is
        # guaranteed to be insertion order. This behavior was an implementation
        # detail of CPython from 3.6.". This function takes advantage of this
        # guarantee and just loops over the Aline values in the dictionary to
        # regenrate the Aline. If the values are returned in other than
        # insertion order, then the vars in the Aline won't be in the order
        # sent out by the MTP and the A line will be incorrect.
        packet = []
        for key in self.rawscan['Aline']['values']:
            if (key != 'DATE' and key != 'TIME' and key != 'timestr'):
                packet.append(self.rawscan['Aline']['values'][key]['val'])
        separator = ' '
        Adata = separator.join(packet)  # Join the components into a string

        # Save the generated A line to the dictionary
        self.rawscan['Aline']['data'] = Adata

    def createBdata(self):
        """
        Create a B data line from the values in the dictionary and store
        it to the dictionary
        """
        separator = ' '
        self.rawscan['Bline']['data'] = \
            separator.join(self.rawscan['Bline']['values']['SCNT']['val'])

    def createM01data(self):
        """
        Create a M01 data line from the values in the dictionary and store
        it to the dictionary
        """
        packet = []
        for key in self.rawscan['M01line']['values']:
            packet.append(self.rawscan['M01line']['values'][key]['val'])
        separator = ' '
        M01data = separator.join(packet)
        self.rawscan['M01line']['data'] = M01data

    def createM02data(self):
        """
        Create a M02 data line from the values in the dictionary and store
        it to the dictionary
        """
        packet = []
        for key in self.rawscan['M02line']['values']:
            packet.append(self.rawscan['M02line']['values'][key]['val'])
        separator = ' '
        M02data = separator.join(packet)
        self.rawscan['M02line']['data'] = M02data

    def createPtdata(self):
        """
        Create a Pt data line from the values in the dictionary and store
        it to the dictionary
        """
        packet = []
        for key in self.rawscan['Ptline']['values']:
            packet.append(self.rawscan['Ptline']['values'][key]['val'])
        separator = ' '
        Ptdata = separator.join(packet)
        self.rawscan['Ptline']['data'] = Ptdata

    def createEdata(self):
        """
        Create a E data line from the values in the dictionary and store
        it to the dictionary
        """
        separator = ' '
        self.rawscan['Eline']['data'] = \
            separator.join(self.rawscan['Eline']['values']['TCNT']['val'])

    def writeFlightData(self, UDPpacket):
        """ Save a UDP packet to the flightData array """
        self.rawscan['asciiPacket'] = UDPpacket

    def parseAsciiPacket(self, UDPpacket):
        """
        Parse an Ascii packet and store it's values in the data dictionary
        """
        # Save the entire UDP packet to the dictionary. Useful for figuring out
        # what happened if something goes wrong downstream during processing.
        self.rawscan['asciiPacket'] = UDPpacket

        # Split string on commas
        separator = ','
        values = UDPpacket.split(separator)

        # values[0] contains the packet identifier, in this case 'MTP' so skip
        # values[1] contains the datetime, i.e. yyyymmddThhMMss
        m = re.match("(........)T(..)(..)(..)", values[1])
        if (m):
            # Save YYYYMMDD to variable DATE
            self.rawscan['Aline']['values']['DATE']['val'] = m.group(1)
            # Save HHMMSS to variable TIME
            self.rawscan['Aline']['values']['timestr']['val'] = \
                m.group(2)+":"+m.group(3)+":"+m.group(4)
            # Save seconds since midnight to variable TIME
            self.rawscan['Aline']['values']['TIME']['val'] = \
                int(m.group(2))*3600+int(m.group(3))*60+int(m.group(4))

        self.assignAvalues(values[2:16])
        self.assignBvalues(values[16:46])
        self.assignM01values(values[46:54])
        self.assignM02values(values[54:62])
        self.assignPtvalues(values[62:70])
        self.assignEvalues(values[70:76])

    def assignAvalues(self, values):
        """
        Parse the A line and assign to variables in the data dictionary.
        Expects an array of values that are just the data from the Aline, i.e.
        does not contain the "A yyyymmdd hh:mm:ss"
        """
        for key in self.rawscan['Aline']['values']:
            if (key != 'DATE' and key != 'TIME' and key != 'timestr'):
                self.rawscan['Aline']['values'][key]['val'] = \
                    values[int(self.rawscan['Aline']['values'][key]['idx'])]

    def assignBvalues(self, values):
        """ Parse the B line and assign to variables in the data dictionary """
        for key in self.rawscan['Bline']['values']:
            self.rawscan['Bline']['values'][key]['val'] = values

    def assignM01values(self, values):
        """
        Parse the M01 line and assign to variables in the data dictionary
        """
        for key in self.rawscan['M01line']['values']:
            self.rawscan['M01line']['values'][key]['val'] = \
                    values[int(self.rawscan['M01line']['values'][key]['idx'])]

    def assignM02values(self, values):
        """
        Parse the M02 line and assign to variables in the data dictionary
        """
        for key in self.rawscan['M02line']['values']:
            self.rawscan['M02line']['values'][key]['val'] = \
                    values[int(self.rawscan['M02line']['values'][key]['idx'])]

    def assignPtvalues(self, values):
        """
        Parse the Pt line and assign to variables in the data dictionary
        """
        for key in self.rawscan['Ptline']['values']:
            self.rawscan['Ptline']['values'][key]['val'] = \
                    values[int(self.rawscan['Ptline']['values'][key]['idx'])]

    def assignEvalues(self, values):
        """ Parse the E line and assign to variables in the data dictionary """
        for key in self.rawscan['Eline']['values']:
            self.rawscan['Eline']['values'][key]['val'] = values

    def getVar(self, linetype, var):
        """ Get the value of a variable from the data dictionary """
        if self.rawscan is not None:
            return(self.rawscan[linetype]['values'][var]['val'])
        else:
            return(None)

    def getVarList(self, linetype):
        """ Get the list of variable names that are in the dictionary """
        if self.rawscan is not None:
            return(list(self.rawscan[linetype]['values']))
        else:
            return(None)

    def getVarArray(self, linetype, var):
        """ Get an array containing all measured values of a variable """
        # This works for the A, IWG1, M01, M02, and Pt lines, which contain one
        # value per time
        self.varArray = []
        if self.rawscan is not None:
            if type(self.flightData[0][linetype]['values'][var]
                    ['val']) is list:
                return(None)
            for i in range(len(self.flightData)):
                self.varArray.append(self.flightData[i][linetype]
                                     ['values'][var]['val'])
        return(self.varArray)

    def getVarArrayi(self, linetype, var, index):
        """ Get an array containing all measured values of a variable """
        # This works for the B and E lines, which contain an array of values
        # for each time. Pass in the index of the value you want
        # For the E line, there are 6 values: Ch1NDon, Ch2NDon, Ch3NDon,
        # Ch1NDoff, Ch2NDoff, and Ch3NDoff
        self.varArray = []
        if self.rawscan is not None:
            if type(self.flightData[0][linetype]['values'][var]
                    ['val']) is not list:
                return(None)
            for i in range(len(self.flightData)):
                self.varArray.append(float(self.flightData[i][linetype]
                                           ['values'][var]['val'][index]))
        return(self.varArray)

    def get_metadata(self, linetype, var, key):
        """ Get the metadata with keyword key for the variable """
        return(self.flightData[0][linetype]['values'][var][key])

    def getATPmetadata(self, var, key, index=0):
        """ Get the metadata with keyword key for variable in ATP dict """
        try:
            metadata = self.flightData[index]['ATP'][var][key]
        except Exception:
            raise

        return(metadata)

    def testATP(self, index=None):
        """
        ATP metadata is not available until a temperature profile has been
        calculated, which causes an AtmosphericTemperatureProfile dictionary
        to be linked to the MTPrecord dictionary. So check for that here.
        """

        # If index provided, test that index
        if index is not None:
            try:
                self.getATPmetadata('RCFMRIndex', '_FillValue', index)
                return(index)
            except Exception:
                raise
        else:
            for index in range(len(self.flightData)):  # Loop through scans
                try:
                    self.getATPmetadata('RCFMRIndex', '_FillValue', index)
                    return(index)
                except Exception:
                    # found exception for this scan, but might not for the
                    # next. Just looking for one good scan, so keep going.
                    pass

            # If get here, went through entire file without finding ATP data
            # so raise exception
            raise

    def setCalcVal(self, linetype, var, value, calctype):
        """
        Set the calculated value of type calctype for a given var to value.
        """
        # Only Pt lines have a calculated resistance
        # Only Pt lines have a calculated temperature
        # Only M01 lines have a calculated voltage
        if ((calctype == 'resistance' and linetype == 'Ptline') or
           (calctype == 'temperature' and linetype == 'Ptline') or
           (calctype == 'temperature' and linetype == 'M02line') or
           (calctype == 'volts' and linetype == 'M01line')):
            self.rawscan[linetype]['values'][var][calctype] = value
        else:
            logger.printmsg("WARNING", " linetype " + linetype + " doesn't " +
                            "have a " + calctype + " entry in the MTP " +
                            "dictionary. Ignored.")

    def getCalcVal(self, linetype, var, calctype):
        """
        Get the calculated value of type calctype for a given var to value.
        """
        # Only Pt lines have a calculated resistance.
        # Only Pt lines have a calculated temperature
        # Only M01 lines have a calculated voltage
        if ((calctype == 'tb' and linetype == 'Bline') or
           (calctype == 'resistance' and linetype == 'Ptline') or
           (calctype == 'temperature' and linetype == 'Ptline') or
           (calctype == 'temperature' and linetype == 'M02line') or
           (calctype == 'volts' and linetype == 'M01line')):
            return(self.rawscan[linetype]['values'][var][calctype])
        else:
            return(numpy.nan)

    def getName(self, linetype, var):
        return(self.rawscan[linetype]['values'][var]['name'])

    def saveTBI(self, tbi):
        """ Save the inverted brightness temperature to the scan """
        self.rawscan['tbi'] = tbi

    def getTBI(self):
        """ Retrieve the brightness temperatures for the current scan """
        return(self.rawscan['tbi'])

    def saveATP(self, ATP):
        self.rawscan['ATP'] = copy.deepcopy(ATP)

    def getATP(self):
        return(self.rawscan['ATP'])

    def saveBestWtdRCSet(self, BestWtdRCSet):
        self.rawscan['BestWtdRCSet'] = copy.deepcopy(BestWtdRCSet)

    def getBestWtdRCSet(self):
        return(self.rawscan['BestWtdRCSet'])
