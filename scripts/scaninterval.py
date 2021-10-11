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

    histogram = {}

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
    try:
        with open(args.file, 'r') as f:
            for line in f:
                # Times are in the A line - ignore all others
                if re.match(r"^A", line):
                    scantime = line[2:19]
                    currenttime = datetime.strptime(scantime,
                                                    "%Y%m%d %H:%M:%S")
                    tdelta = currenttime-previoustime

                    # don't calculate difference the first time through
                    # since we don't yet have two times to compare
                    if previoustime != basetime:
                        # Look for time differences that aren't the normal
                        # 17 or 18 sec
                        #if tdelta.seconds < 17 or tdelta.seconds > 20:
                        #    print("interval time: ", tdelta.seconds, " at ",
                        #          scantime)
                        if str(tdelta.seconds) in histogram.keys():
                            histogram[str(tdelta.seconds)] += 1
                        else:
                            histogram[str(tdelta.seconds)] = 1

                    # Rotate times in prep for reading in next time
                    previoustime = currenttime
    except UnicodeDecodeError:
        pass  # Found non-text data

    for value in histogram:
        print(value, " ", histogram[value])


if __name__ == "__main__":
    main()
