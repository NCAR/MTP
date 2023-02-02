##############################################################################
#
# This python class is used to read in MTHP data. It currently reads in
# brightness temperature data, e.g. (note that the actual data is comma
# separated and has many floating point digits of accuracy. I have truncated
# the data here and formatted it into columns to make it easier to read.
#
# seconds    lat (deg) lon(deg) alt(m) angle  TB(56.363) TB(57.612) TB(58.363)
# since
# unixtime
# 1651091380 19.284874 -156.069 4226.0  1     267.066806 269.287445 272.4185533
# 1651091380 19.284874 -156.069 4226.0  2     265.714228 266.555201 266.9693227
# 1651091380 19.284874 -156.069 4226.0  3     264.132780 266.903078 267.3884719
# 1651091380 19.284874 -156.069 4226.0  4     263.140593 265.142902 266.1517201
# 1651091380 19.284874 -156.069 4226.0  5     264.360006 267.333688 266.7826546
# 1651091380 19.284874 -156.069 4226.0  6     265.610870 267.324901 263.8911341
# 1651091380 19.284874 -156.069 4226.0  7     260.900846 263.535000 264.1123828
# 1651091380 19.284874 -156.069 4226.0  8     260.578599 262.553308 262.2318355
# 1651091380 19.284874 -156.069 4226.0  9     262.412694 264.907826 264.3027885
# 1651091380 19.284874 -156.069 4226.0  10    261.022599 262.765034 262.4812719
# 1651091380 19.284874 -156.069 4226.0  11    260.152014 261.838927 262.7636649
# 1651091386 19.275332 -156.062 4292.3  1     258.431222 260.982892 259.7816012
# 1651091386 19.275332 -156.062 4292.3  2     256.121395 258.486764 258.4142367
# , etc. where the angles [1-11] are [80,55,42,25,12,0,-12,-25,-42,-55,-80]

# 2023/02/02: An updated file format received 2023/01/17 replaces the angle
# column with the actual angles and omits -55. Code has been updated to handle
# both cases. Also, previous version of code inadvertently flipped the profiles
# vertically. This has been corrected.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import numpy
import time
from util.readmtp import readMTP
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class readMTHP(readMTP):

    def readRawScan(self, raw_data_file):
        """
        Read in a scan (a group of lines) from an MTHP .csv file and store them
        to a dictionary. Keep looping until have a complete scan or reach end
        of file.
        """
        # Clear current record time, lat, lon, alt
        rectime = numpy.nan
        reclat = numpy.nan
        reclon = numpy.nan
        recalt = numpy.nan
        expected_angle_index = 1  # Index 1 corresponds to +80
        self.angles = [80,55,42,25,12,0,-12,-25,-42,-80]

        while True:

            # Read in a single line
            line = raw_data_file.readline()
            if len(line) == 0:  # EOF
                return False  # At EOF

            # Parse out components of current line
            self.vals = line.split(',')

            # Convert time from seconds since UNIX time to UTC and save to
            # dictionary
            self.parseTime(self.vals[0])

            # Save time of first line in current record block
            if numpy.isnan(float(rectime)):
                rectime = self.vals[0]

            # While time doesn't change,
            if rectime == self.vals[0]:
                # Save lat, lon, alt to dictionary
                reclat = self.saveLocation('SALAT', self.vals[1], reclat)
                reclon = self.saveLocation('SALON', self.vals[2], reclon)
                alt = float(self.vals[3])/1000.0  # meters to km
                recalt = self.saveLocation('SAPALT', alt, recalt)

                # Store brightness temperature data to dictionary
                angle = int(self.vals[4])  # index (1 = 80, etc)
                ch1 = self.vals[5]  # 56.363 frequency channel
                ch2 = self.vals[6]  # 57.612 frequency channel
                ch3 = self.vals[7]  # 58.363 frequency channel

                # RF08 file received 2022/11/11 had angles 1-11 (index)
                if angle == 10:  # This is an index indicator of angle
                    continue  # Skip angle 10 (-55)
                if angle == 11:  # This is an index indicator of angle
                    angle = 10  # Reset

                # RF08 file received 2023/01/17 had angles 80 to -80
                if angle < 1 or angle > 11:
                    expected_angle = self.angles[expected_angle_index - 1]

                if angle == expected_angle_index or angle == expected_angle:
                    # Save in original order to 'tb'
                    index = (10 - expected_angle_index) * 3
                    self.rawscan['Bline']['values']['SCNT']['tb'][index] \
                        = float(ch1)
                    self.rawscan['Bline']['values']['SCNT']['tb'][index + 1] \
                        = float(ch2)
                    self.rawscan['Bline']['values']['SCNT']['tb'][index + 2] \
                        = float(ch3)

                    # Save in inverted order to 'tbi'
                    index = 10 - expected_angle_index
                    self.rawscan['tbi'][index] = float(ch1)
                    self.rawscan['tbi'][index + 10] = float(ch2)
                    self.rawscan['tbi'][index + 20] = float(ch3)
                else:
                    logger.info("Angle %s was not expected. Should be %d or %d" %
                                (angle, expected_angle_index, expected_angle))
                expected_angle_index = expected_angle_index + 1

            # Check if we have a complete scan (all angles have found = True
            if angle == 10 or angle == -80:
                return True

    def saveLocation(self, var, val, expected_val):
        # Modifies expected_val
        if numpy.isnan(float(expected_val)):
            expected_val = val
            self.rawscan['Aline']['values'][var]['val'] = val
        else:
            if expected_val != val:  # error in input data
                logger.info("%s %f varies in single scan" % (var, val))

        return expected_val

    def parseTime(self, epochtime):
        # Convert time from seconds since UNIX time to UTC
        utctime = time.gmtime(float(epochtime))
        self.rawscan['Aline']['values']['DATE']['val'] = "%04d%02d%02d" % \
            (utctime.tm_year, utctime.tm_mon, utctime.tm_mday)
        self.rawscan['Aline']['values']['timestr']['val'] = "%02d:%02d:%02d" \
            % (utctime.tm_hour, utctime.tm_min, utctime.tm_sec)
        self.rawscan['Aline']['values']['TIME']['val'] = \
            int(utctime.tm_hour * 3600 + utctime.tm_min * 60 + utctime.tm_sec)
