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
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
################################################################################

import re

class readMTP:

    def __init__(self):
        # A dictionary to hold a single raw data line. A data line from a .RAW
        # MTP file has the following properties:
        self.rawline = { 're': "", # Regular expression used to identify line
                         'found': False,   # Have we found this linetype?
                         'data': "", # The contents of the line
                         'date': "", # Scan date (for the A line) or packet date
                                     # (for IWG1 line). Not used for other lines
                       }

        # A dictionary to hold a single raw data scan. A raw scan consists of
        # a set of 7 different line types
        self.rawscan = { 'Aline': dict(self.rawline),
                         'IWG1line': dict(self.rawline), 
                         'Bline': dict(self.rawline),
                         'M01line':dict(self.rawline),
                         'M02line':dict(self.rawline),
                         'Ptline':dict(self.rawline),
                         'Eline':dict(self.rawline),
                       }

        # Regular expressions to match the various scan lines
        self.rawscan['Aline']['re'] = re.compile("^A (........) (..):(..):(..) (.*)")
        self.rawscan['IWG1line']['re'] = re.compile("^(IWG1)(,.*)")
        self.rawscan['Bline']['re'] = re.compile("(^B) (.*)")
        self.rawscan['M01line']['re'] = re.compile("(^M01): (.*)")
        self.rawscan['M02line']['re'] = re.compile("(^M02): (.*)")
        self.rawscan['Ptline']['re'] = re.compile("(^Pt): (.*)")
        self.rawscan['Eline']['re'] = re.compile("(^E) (.*)")


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
            m = re.match(self.rawscan[linetype]['re'],line)
            if (m):
                # Store data. Handle special case of date in A line
                if (linetype == 'Aline'): # Reformat date/time
                    self.rawscan[linetype]['date'] =  \
                        m.group(1)+"T"+m.group(2)+m.group(3)+m.group(4)
                    self.rawscan[linetype]['data'] = m.group(5)
                else:
                    self.rawscan[linetype]['data'] = m.group(2).rstrip('\n')
                # Mark found
                self.rawscan[linetype]['found']=True
                # Exit matching loop
                break

        # Check if we have a complete scan (all linetypes have found = True
        foundall = True # Init so can boolean & per rawscan line
        for linetype in self.rawscan:
            foundall = foundall & self.rawscan[linetype]['found']

        if (foundall):
            # Have a complete scan. Reset found to False for all and return
            for linetype in self.rawscan:
                self.rawscan[linetype]['found'] = False
            return(True) # Not at EOF

    # Return an Ascii Packet (suitable for sending around the plane) e.g.
    # MTP,20140606T062252,+03.98,00.25,+00.07,00.33,+03.18,0.01,268.08,00.11,-43.308,+0.009,+172.469,+0.000,+074146,+073392,018963,020184,019593,018971,020181,019593,018970,020170,019587,018982,020193,019589,018992,020223,019617,019001,020229,019623,018992,020208,019601,018972,020181,019572,018979,020166,019558,018977,020161,019554,2928,2321,2898,3082,1923,2921,2432,2944,2016,1394,2096,2202,2136,1508,4095,1558,2177,13823,13811,10352,13315,13327,13304,14460,021506,022917,022752,019806,021164,020697
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
        # But since the individual data 
        # strings are space separated, split string on spaces and rejoin with 
        # commas
        separator = ' '
        line = separator.join(packet) # Join the components into a string
        values = line.split()         # Split string on spaces
        separator = ','
        return separator.join(values) # Rejoin with commas

if __name__ == "__main__":
    readRaw()
