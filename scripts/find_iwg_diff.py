###############################################################################
# Quick script to parse a diff of two IWG files. Assumes diff command was
# > diff NGYYYYMMDD.RAW NGYYYYMMDD.RNG > mtp_<proj>_raw_rng.diff
#
# While trying to determine what the MTP VB6 code does to transform a RAW
# file into an RNG file, it became helpful to just diff the two files and
# see what I found. Turns out I found lots of lines that were different.
# This script compares a set of matched records from the two files and reports
# while values changed, using the ascii_parms file to equate data vaules with
# variable names.
#
# Also assumes file contains RAW/RNG pairs and that unpaired lines have
# been removed (I said this was a *quick* script).
#
# Written in Python 3 - run using "python3 find_iwg_diff.py <diff file>"
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2020
##############################################################################
import re
import sys

# Diff file should be given on command line
try:
    difffile = sys.argv[1]
except IndexError:
    print("Diff file must be given as command line argument")
    print(" e.g. python3 fred.py mtp_deepwave_raw_rng.diff")
    sys.exit(1)

# Get the variable names for the values in the IWG lines
ascii_parms = open('../config/ascii_parms')
ascii_vals = ['IWG', 'DATETIME']
while True:
    line = ascii_parms.readline()
    if len(line) == 0:  # EOF
        break

    # Check for comment lines
    m = re.match(re.compile("^#"), line)
    if (m):  # Have a comment
        next
    else:
        newVar = line.rstrip('\n')
        ascii_vals.append(newVar)

# Open the diff file
df = open(difffile, 'r')
while True:  # Loop through file
    line = df.readline()  # Read line
    if len(line) == 0:  # If EOF, exit
        break
    # Find line that begins "< IWG1," and save values to rawvals array
    m = re.match(re.compile("^< IWG1,"), line)
    if m:
        raw = line.rstrip('\n')
        rawvals = raw.split(',')

    # Find line that begins "> IWG1," and save values to rngvals array
    m = re.match(re.compile("^> IWG1,"), line)
    if m:
        rng = line.rstrip('\n')
        rngvals = rng.split(',')
        # When find a '>' line, assume have both values from the pair. Print
        # differences, tagged with variable name, to stdout, e.g.
        # 20140725T003126 PALTF 5500.85 5511.16
        # First value is from RAW file. Second is from RNG file.
        for i in range(len(rngvals)):  # Loop through values on an IWG line
            if i == 0:
                next  # skip IWG1 line marker
            elif rawvals[i] != rngvals[i]:
                # If value in RNG line does not match value in RAW line, print
                # out values tagged with time and variable name.
                print(rawvals[1], ascii_vals[i], rawvals[i], rngvals[i])
