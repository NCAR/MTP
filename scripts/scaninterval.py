###############################################################################
# Quick script to find the scan intervals in a raw MTP data file
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2021
###############################################################################
import argparse
import re
from datetime import datetime


def main():

    # Process command line arguments
    parser = argparse.ArgumentParser(
            "Script to find scan intervals for a flight\n")
    parser.add_argument('--file', type=str, help='Flight raw data file',
                        required=True)
    args = parser.parse_args()

    # Check for required filename and warn user if it wasn't provided.
    if args.file is None:
        parser.print_help()
        exit()

    # Read in times from raw data file. Times are of format 20120127 21:04:29
    # Set a default basetime, just to get something to compare to.
    basetime = datetime.strptime("19000101 00:00:00", "%Y%m%d %H:%M:%S")
    # Previous time is basetime first time thru
    previoustime = basetime
    with open(args.file, 'r') as f:
        for line in f:
            # Times are in the A line - ignore all others
            if re.match(r"^A", line):
                scantime = line[2:19]
                currenttime = datetime.strptime(scantime, "%Y%m%d %H:%M:%S")
                tdelta = currenttime-previoustime

                # ignore first time thru since don't have two times to compare
                if previoustime != basetime:
                    # Look for time differences that aren't the normal
                    # 17 or 18 sec
                    if tdelta.seconds != 17 and tdelta.seconds != 18:
                        print(tdelta.seconds)

                previoustime = currenttime


if __name__ == "__main__":
    main()
