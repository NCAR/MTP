###############################################################################
# Functions to generate stats on MTP Raw data files
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import argparse
import re
import numpy
from datetime import datetime


def main():

    # Instantiate an MTP stats calculator
    stats = MTPstats()

    # Process command line arguments
    args = stats.parse_args()

    # Calculate statistics on scan lengths
    stats.calc_timedelta(args.file)

    # Investigate variation on counts across time
    stats.calc_countshisto(args.file, args.start, args.end)


class MTPstats():

    def parse_args(self):
        """ Instantiate a command line argument parser """

        # Define command line arguments which can be provided
        parser = argparse.ArgumentParser(
            description="Script to display and process MTP scans")
        parser.add_argument('--file', type=str,
                            help='Raw data file to calculate statistics from',
                            required=True)
        parser.add_argument('--start', type=str, default=0,
                            help='Start of time range to calc stats (hhmmss)',
                            required=False)
        parser.add_argument('--end', type=str, default=999999,
                            help='End of time range to calc stats (hhmmss)',
                            required=False)

        # Parse the command line arguments
        args = parser.parse_args()

        return(args)

    def calc_timedelta(self, Rawfile):
        """
        Calculate time difference between each scan ( = scan length)
        Also generate histogram of how many scans have each scan length

        Get times from the A line: "A date time vals..."
        """
        FMT = '%Y%m%d %H:%M:%S'  # Format of time string
        last_time = None
        timedelta_histo = {}  # Histogram of time differences
        line_type = re.compile(r'^A')

        # Open Raw file
        raw_file = open(Rawfile, 'r')

        for line in raw_file:
            if re.match(line_type, line):
                [A, date, time, rest] = line.split(' ', 3)
                this_time = date+' '+time
                if last_time is not None:
                    tdelta = datetime.strptime(this_time, FMT) - \
                             datetime.strptime(last_time, FMT)
                    # print(tdelta)
                    # Create histogram
                    timedelta_histo[tdelta] = \
                        timedelta_histo.get(tdelta, 0) + 1

                # Rotate times in prep for reading in next time
                last_time = this_time

        print("Number of times each scan length was found:")
        for i in sorted(timedelta_histo.keys()):
            print(i, timedelta_histo[i])

        return()

    def calc_countshisto(self, Rawfile, start, end):
        """
        Gather stats on how channel counts vary with time

        Counts are in the B line
        """
        Aline = re.compile(r'^A')
        line_type = re.compile(r'^B')
        counts = {  # Hash to hold counts by angle, channel
            'scan': [[] for i in range(30)],
            'mean': [numpy.nan] * 30,
            'stdev': [numpy.nan] * 30,
        }

        # Open Raw file - not efficient, but quick to code
        raw_file = open(Rawfile, 'r')
        process = True

        for line in raw_file:
            if re.match(Aline, line):
                [A, date, time, rest] = line.split(' ', 3)
                if ((int(time.replace(":", "")) < int(start)) or
                    (int(time.replace(":", "")) >
                     int(end))):
                    process = False
                else:
                    process = True

            if re.match(line_type, line) and process:
                linecounts = line.rstrip().split(' ', 31)
                # Remove B as first item in list. Include sanity check.
                if (linecounts.pop(0) != 'B'):
                    print("Not on a B line")
                    next

                # linecounts contains a 30 element array of counts from a
                # single scan. Save each element to it's own array so can
                # agglomerate counts for a single angle, channel vs time
                for i in range(len(linecounts)):
                    # print(linecounts[i])
                    counts['scan'][i].append(linecounts[i])
                    # for j in range(len(linecounts)):
                    #    print(j, " ", counts['scan'][j])

        # Let's see what we got. At the moment I am copying these into a Google
        # sheet and plotting them there. Eventually, add this logic to the
        # timeseries plotting in MTP control.
        print("\ntimeseries of counts by angle/channel")
        for i in range(len(linecounts)):
            str1 = " "
            print(str1.join(counts['scan'][i]))

        # Calculate mean and std of counts by angle/channel. Need to do this
        # for a straight and level portion of the flight for it to be
        # meaningful.
        print("\nmean and standard dev of line counts per angle/channel:")
        for i in range(len(linecounts)):
            counts['mean'][i] = \
                numpy.mean([int(item) for item in counts['scan'][i]])
            counts['stdev'][i] = \
                numpy.std([int(item) for item in counts['scan'][i]])
            print("%0.2f  %0.2f" % (counts['mean'][i], counts['stdev'][i]))

        return()


if __name__ == "__main__":
    main()
