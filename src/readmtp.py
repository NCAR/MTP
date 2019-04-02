################################################################################
#
# This python class is used to read in various formats of the raw MTP data.
#
# In real-time, the MTP creates raw data files that contain a block of lines for
# each scan separated by one or more blank lines, e.g.
#
# A 20140606 06:22:52 +03.98 00.25 +00.07 00.33 +03.18 0.01 268.08 00.11 -43.308 +0.009 +172.469 +0.000 +074146 +073392
# IWG1,20140606T062250,-43.3061,172.455,3281.97,,10508.5,,149.998,164.027,,0.502512,3.11066,283.283,281.732,-1.55388,3.46827,0.0652588,-0.258496,2.48881,-5.31801,-5.92311,7.77836,683.176,127.248,1010.48,14.6122,297.157,0.303804,104.277,,-72.1708,
# B 018963 020184 019593 018971 020181 019593 018970 020170 019587 018982 020193 019589 018992 020223 019617 019001 020229 019623 018992 020208 019601 018972 020181 019572 018979 020166 019558 018977 020161 019554
# M01: 2928 2321 2898 3082 1923 2921 2432 2944
# M02: 2016 1394 2096 2202 2136 1508 4095 1558
# Pt: 2177 13823 13811 10352 13315 13327 13304 14460
# E 021506 022917 022752 019806 021164 020697
#
# The variables in each line are (they should match the project
# nidas/default.xml file:
#
# A <date> <time> SAPITCH SRPITCH SAROLL SRROLL SAPALT SRPALT SAAT SRAT SALAT SRLAT SALON SRLON SMCMD SMENC
# B SCNT[30]
# M01: VM08CNTE VVIDCNTE VP08CNTE VMTRCNTE VSYNCNTE VP15CNTE VP05CNTE VM15CNTE
# M02: ACCPCNTE TDATCNTE TMTRCNTE TAIRCNTE TSMPCNTE TPSPCNTE TNCCNTE TSYNCNTE
# Pt: TR350CNTP TTCNTRCNTP TTEDGCNTP TWINCNTP TMIXCNTP TAMPCNTP TNDCNTP TR600CNTP
# E TCNT[6]
#
# When combined into a Ascii packet, the lines A, B, M01, M02, P, and E are
# concatenated, in order, and changed so all values are comma-separated, e.g.:
# MTP,20140606T062252,+03.98,00.25,+00.07,00.33,+03.18,0.01,268.08,00.11,-43.308,+0.009,+172.469,+0.000,+074146,+073392,018963,020184,019593,018971,020181,019593,018970,020170,019587,018982,020193,019589,018992,020223,019617,019001,020229,019623,018992,020208,019601,018972,020181,019572,018979,020166,019558,018977,020161,019554,2928,2321,2898,3082,1923,2921,2432,2944,2016,1394,2096,2202,2136,1508,4095,1558,2177,13823,13811,10352,13315,13327,13304,14460,021506,022917,022752,019806,021164,020697
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
################################################################################

import re
import numpy
from MTP import MTPrecord

class readMTP:

    def __init__(self):
        self.rawscan = MTPrecord


    def readRawScan(self,raw_data_file):
    # Read in a scan (a group of lines) from an MTP .RAW file and store them to a 
    # dictionary
      while True:

        # Read in a single line
        line = raw_data_file.readline()
        if len(line) == 0: # EOF
            return(False) # At EOF

        # Loop through possible line types, match the line, and store it in 
        # the dictionary
        for linetype in self.rawscan:
            if 're' in self.rawscan[linetype]:
                m = re.match(self.rawscan[linetype]['re'],line)
                if (m):
                    # Store data. Handle special case of date in A line
                    if (linetype == 'Aline'): # Reformat date/time
                        self.rawscan[linetype]['date'] =  \
                            m.group(1)+"T"+m.group(2)+m.group(3)+m.group(4)
                        self.rawscan[linetype]['data'] = m.group(5)
                    elif (linetype == 'IWG1line'): # Reformat date/time
                        self.rawscan[linetype]['asciiPacket'] =line.rstrip('\n')
                        self.rawscan[linetype]['date'] = m.group(0)
                        self.rawscan[linetype]['data'] = m.group(1).rstrip('\n')
                    else:
                        self.rawscan[linetype]['data'] = m.group(2).rstrip('\n')
                    # Mark found
                    self.rawscan[linetype]['found']=True
                    # Exit matching loop
                    break

        # Check if we have a complete scan (all linetypes have found = True
        foundall = True # Init so can boolean & per rawscan line
        for linetype in self.rawscan:
            if 'found' in self.rawscan[linetype]:
                foundall = foundall & self.rawscan[linetype]['found']

        if (foundall):
            # Have a complete scan. Reset found to False for all and return
            for linetype in self.rawscan:
                if 'found' in self.rawscan[linetype]:
                    self.rawscan[linetype]['found'] = False
            return(True) # Not at EOF

    def getIwgPacket(self):
        return(self.rawscan['IWG1line']['asciiPacket'])

    # Combine the separate lines from a raw scan into an Ascii packet
    # (suitable for sending around the plane).
    # Stores the Ascii packet in the dictionary.
    # Also, returns the Ascii packet to the caller.
    def getAsciiPacket(self):
        packet = [] 
        packet.append("MTP")
        packet.append(self.rawscan['Aline']['date']) # Date and Time
        packet.append(self.rawscan['Aline']['data']) # Rest of A line
        packet.append(self.rawscan['Bline']['data'])
        packet.append(self.rawscan['M01line']['data'])
        packet.append(self.rawscan['M02line']['data'])
        packet.append(self.rawscan['Ptline']['data'])
        packet.append(self.rawscan['Eline']['data'])

        # Turn our packet into a comma separated string, and return it
        # But since the individual data strings are space separated, split 
        # string on spaces and rejoin with commas
        separator = ' '
        line = separator.join(packet) # Join the components into a string
        values = line.split(separator)         # Split string on spaces
        separator = ','
        UDPpacket = separator.join(values)

        # Store the new packet in our dictionary
        self.rawscan['asciiPacket'] = UDPpacket

        # Return the newly created packet
        return (UDPpacket)

    # Parse an Ascii packet and store it's values in the data dictionary
    def parseAsciiPacket(self,UDPpacket):
        # Split string on commas
        separator = ','
        values = UDPpacket.split(separator)

        # values[0] contains the packet identifier, in this case 'MTP' so skip
        # values[1] contains the datetime, i.e. yyyymmddThhMMss
        m = re.match("(........)T(..)(..)(..)",values[1])
        if (m):
            # Save YYYYMMDD to variable DATE
            self.rawscan['Aline']['data']['DATE']['val'] = m.group(1)
            # Save seconds since midnight to variable TIME
            self.rawscan['Aline']['data']['TIME']['val'] = \
                int(m.group(2))*3600+int(m.group(3))*60+int(m.group(4))

        self.assignAvalues(values[2:16])
        self.assignBvalues(values[16:46])
        # self.assignM01values(values[46:54])
        # self.assignM02values(values[54:62])
        # self.assignPtvalues(values[62:70])
        # self.assignEvalues(values[70:76])

    # Parse the A line and assign to variables in the data dictionary
    # Expects an array of values that are just the data from the Aline, i.e.
    # does not contain the "A yyyymmdd hh:mm:ss"
    def assignAvalues(self,values):
        for key in self.rawscan['Aline']['data'].keys():
            if (key != 'DATE' and key != 'TIME'):
                self.rawscan['Aline']['data'][key]['val'] = \
                    values[int(self.rawscan['Aline']['data'][key]['idx'])]

    # Parse the B line and assign to variables in the data dictionary
    def assignBvalues(self,values):
        for key in self.rawscan['Bline']['data'].keys():
            self.rawscan['Bline']['data'][key]['val'] = values

    # Get the value of a variable from the data dictionary
    def getSCNTData(self):
        return(self.rawscan['Bline']['data']['SCNT']['val'])

    # Get the value of a variable from the data dictionary
    def getXYData(self,varname):
        return(self.rawscan['Aline']['data'][varname]['val'])

    # Get the list of variable names that are in the dictionary
    def getVarList(self):
        return(list(self.rawscan['Aline']['data'].keys()))

if __name__ == "__main__":
    readRaw()
