###############################################################################
# Code to create the final output data file in ICARTT 2110 format.
#
# Format specification taken from: http:
#    //earthdata.nasa.gov/esdis/eso/standards-and-references/icartt-file-format
#    [Last accessed 3/13/2020]
#
# If you make changes to the header or data format generated by this file, the
# new file can be tested for compliance at:
#    https://www-air.larc.nasa.gov/cgi-bin/fscan
# Note that while traditionally final MTP data files have names like
# MPYYYYMMDD.NGV, in order to run the fscan checker, the filename must be of
# the format MTP_GV_YYYYMMDD_R#.ict
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import os
from datetime import datetime
from lib.rootdir import getrootdir
from EOLpython.Qlogger.messageHandler import QLogger as logger


class ICARTT():

    def __init__(self, client):
        self.client = client

        self.file_format_index = '2110, V02_2016'
        self.header = ""  # string to hold header

    def get_startdate(self):
        # Get date of first record in flightData array
        # If no data (list index out of range), code will crash. Catch. TBD
        self.client.reader.setRawscan(0)
        date = self.client.reader.getVar('Aline', 'DATE')
        self.client.reader.resetRawscan()
        return(date)

    def getICARTT(self):
        """ Build name of ICARTT file to save data to """

        date = self.get_startdate()
        if date is None:
            return(None)
        else:
            platform = self.client.configfile.getVal('platformID')
            revision = self.client.configfile.getVal('revision')
            datadir = self.client.configfile.getPath('datadir')

            # Create path to write ICARTT file - this is final data so put in
            # 'final' dir.
            filepath = os.path.join(getrootdir(), datadir)

            # Check that filepath exists
            if not os.path.exists(filepath):
                logger.printmsg('ERROR', 'Dir ' + filepath + ' does not ' +
                                'exist. Create dir and click OK to continue,' +
                                'or click Quit to exit.')

            # Create ICARTT-compliant filename
            filename = 'MP_' + platform + "_" + date + '_' + revision + '.ict'
            # -or- Create MTP traditional filename
            # filename = 'MP' + date + '.NGV'

            return(os.path.join(filepath, filename))

    def put_var(self, line, var):
        """
        Retrieve the short_name, units, and long_name from a variable
        dictionary entry and create a variable entry for the header

        Requires:
            line name
            variable name
        """
        self.header += \
            self.client.reader.get_metadata('Aline', var, 'short_name') + \
            ", " + self.client.reader.get_metadata('Aline', var, 'units') + \
            ", " + \
            self.client.reader.get_metadata('Aline', var, 'long_name') + "\n"

    def build_header(self, proc_date):
        """
        Build the ICARTT data header by gathering information from the MTP data
        and config dictionaries
        """
        # If values are missing from proj.yml, code will crash. Need to catch
        # these returned exceptions to getVal and getPath and handle them. TBD

        # PI last name, first name/initial
        self.header += self.client.configfile.getVal('pi') + "\n"

        # Organization/affiliation of PI
        self.header += self.client.configfile.getVal('organization') + "\n"

        # Data source description (e.g., instrument name, platform name,
        # model name, etc.).
        self.header += self.client.configfile.getVal('platform') + "\n"

        # Mission name (usually the mission acronym)
        self.header += self.client.getProj() + "\n"

        # File volume number, number of file volumes (these integer values are
        # used when the data require more than one file per day; for data that
        # require only one file these values are set to 1, 1) - comma delimited
        # MTP only requires one file per day, so...
        self.header += "1, 1\n"

        # Get data file start date
        date = self.get_startdate()
        year = date[0:4]
        month = date[4:6]
        day = date[6:8]

        # Get processing date (will usually be today)
        proc_year = proc_date[0:4]
        proc_month = proc_date[4:6]
        proc_day = proc_date[6:8]

        # UTC date when data begin, UTC date of data reduction or revision
        # - comma delimited (yyyy, mm, dd, yyyy, mm, dd).
        self.header += year + ", " + month + ", " + day + ", "
        self.header += proc_year + ", " + proc_month + ", " + proc_day + "\n"

        # Data interval (This value describes the time spacing (in seconds)
        # between consecutive data records. It is the (constant) interval
        # between values of the independent variable. For 1 Hz data the data
        # interval value is 1 and for 10 Hz data the value is 0.1.
        # All intervals longer than 1 second must be reported as Start and Stop
        # times, and the Data Interval value is set to 0
        #
        # From Ali Aknan, NASA Data Curator (and ICARTT expert) 3/13/2020:
        #   To ICARTT, a 17-second time-interval is considered “non-standard”,
        #    and thus the “Stop Time” will be needed.  Most PIs in a similar
        #    situation do make up the “Stop Time”; and you would explain it in
        #    the special comments section. I do recommend doing just that.
        #
        #    If you do want to report the records with 17-second intervals,
        #    then put 17 on the “data interval” line -- in this case it will be
        #    considered as a “non-standard” reporting (per the ICARTT format,
        #    this will be allowed if the Data Manager approves it).
        self.header += "0\n"

        # List the names for the 2 independent variables starting with the
        # bounded variable (e.g., GeoAltitude), then the unbounded variable
        # (e.g., UTC time).  Time always refers to the number of seconds UTC
        # from the start of the day on which measurements began. It should be
        # noted here that the independent variable UTC should monotonically
        # increase even when crossing over to a second day.).
        self.header += "altitude, m, Remote sensing altitude in meters\n"
        self.header += "start_time, s, Elapsed UT seconds from 0 hours on" + \
                       " flight date\n"  # Aline time

        # Number of dependent bounded (primary) variables
        # The MTP data format has 4 primary variables: air_temperature,
        # air_temperature_anomaly, altitude, and air_density.
        self.header += "4\n"

        # Scale factors (1 for most cases, except where grossly inconvenient)
        self.header += "1.0, " * 3 + "1.0\n"  # No comma space after last 1

        # Missing data indicators (-9999, -99999, etc)
        # NOTE: Since I haven't started writing the data out, this may change
        # so for now just put in place-holders
        self.header += "-999, -999, -999, -999\n"

        # Variable names and units (Short variable name and units are required,
        # and optional long descriptive name, in that order, and separated by
        # commas. If the variable is unitless, enter the keyword "none" for its
        # units. Each short variable name and units (and optional long name)
        # are entered on one line. The short variable name must correspond
        # exactly to the name used for that variable as a column header, i.e.,
        # the last header line prior to start of data.).
        self.header += "air_temperature, K, Retrieved air temperature K\n"
        self.header += "air_temperature_anomaly, K, Standard error of " + \
                       "retrieved air temperature\n"
        self.header += "altitude, m, Geometric altitude meters based on " + \
                       "GPS altitude (meters)\n"
        self.header += "air_density, E+21 m-3, Molecular air density " + \
                       "(number per cubic meter) [1E+21/m3]\n"

        # Number of dependent unbounded (auxiliary) variables
        self.header += "16\n"

        # Scale factors (1 for most cases, except where grossly inconvenient)
        self.header += "1.0, " * 15 + "1.0\n"  # No comma space after last 1

        # ATP metadata is not available until a temperature profile has been
        # calculated, which causes an AtmosphericTemperatureProfile dictionary
        # to be linked to the MTPrecord dictionary. So check for that here.
        try:
            # Test existence of ATP metadata. Return pointer to first
            # record that has ATP metadata, or an exception if none found
            ATPindex = self.client.reader.testATP()
        except Exception:
            logger.printmsg("ERROR", "Temperature profiles don't exist for" +
                            " this flight. Maybe data hasn't been processed " +
                            "yet?", " Can't create ICARTT file.")
            return(False)  # Failed to build header

        # Missing data indicators (-9999, -99999, etc)
        # NOTE: Since I haven't started writing the data out, this may change
        # so for now just put in place-holders
        self.header += "-99, -9999, " + \
            "%5.3f, " % \
            float(self.client.reader.get_metadata('Aline', 'SAPALT',
                                                  '_FillValue')) + \
            "%4.1f, " % \
            float(self.client.reader.get_metadata('Aline', 'SAPITCH',
                                                  '_FillValue')) + \
            "%4.1f, " % \
            float(self.client.reader.get_metadata('Aline', 'SAROLL',
                                                  '_FillValue')) + \
            "-999.9, -99.9, -99.9, -999.9, -999.9, " + \
            "%7.2f, " % \
            float(self.client.reader.get_metadata('Aline', 'SALAT',
                                                  '_FillValue')) + \
            "%8.2f, " % \
            float(self.client.reader.get_metadata('Aline', 'SALON',
                                                  '_FillValue')) + \
            "-999.9, " + \
            "%5.1f, " % \
            float(self.client.reader.getATPmetadata('RCFMRIndex', '_FillValue',
                                                    ATPindex)) + \
            "-999.99, " + \
            "-99.99\n"

        # Variable names, units, and descriptive name. See explanation above
        self.header += "NX, #, number of altitudes in subsequent data " + \
                       "records\n"
        self.header += "end_time, s, Elapsed UT seconds from 0 hours on " + \
                       "flight date\n"

        for var in ['SAPALT', 'SAPITCH', 'SAROLL']:
            self.put_var('Aline', var)

        self.header += "brightness_temperature, K, Horizon brightness " + \
                       "temperature (ie, OAT, similar to SAT); " + \
                       "avg ch1 & ch2 & ch3(K)\n"
        self.header += "tropopause_altitude_1, km, Tropopause #1 (km).\n"
        self.header += "tropopause_altitude_2, km, Tropopause #2 (km).\n"
        self.header += "tropopause_potential_temperature_1, K, Potential " + \
                       "temperature of tropopause #1 (K).\n"
        self.header += "tropopause_potential_temperature_2, K, Potential " + \
                       "temperature of tropopause #2 (K).\n"

        for var in ['SALAT', 'SALON']:
            self.put_var('Aline', var)

        self.header += "air_temperature_lapse_rate, K km-1, dT/dz (K/km) " + \
                       "for 1.0 km layer centered on aircraft flight " + \
                       "altitude.\n"
        for var in ['RCFMRIndex']:
            self.header += \
                self.client.reader.getATPmetadata(var, 'short_name',
                                                  ATPindex) + ", " + \
                self.client.reader.getATPmetadata(var, 'units',
                                                  ATPindex) + ", " + \
                self.client.reader.getATPmetadata(var, 'long_name',
                                                  ATPindex) + "\n"
        self.header += "Tcp, K, Cold point temperature Tcp (K)\n"
        self.header += "Zcl, km, Cold point altitude Zcp (km)\n"

        # Number of special comment lines
        self.header += "1\n"

        # Special comments (Notes of problems or special circumstances unique
        # to this file. An example would be comments/problems associated with
        # a particular flight.).
        self.header += "end_time has been set to second before start time" + \
                       " of next record\n"

        # Number of normal comment lines
        self.header += "18\n"

        # Normal comments (SUPPORTING information: This is the place for
        # investigators to more completely describe the data and measurement
        # parameters. The supporting information structure is a list of key
        # word: value pairs. Specifically include here information on the
        # platform used, the geo-location of data, measurement technique, and
        # data revision comments. Note the non-optional information regarding
        # uncertainty, the upper limit of detection (ULOD) and the lower limit
        # of detection (LLOD) for each measured variable. The ULOD and LLOD are
        # the values, in the same units as the measurements that correspond to
        # the flags -7777’s and -8888’s within the data, respectively. The last
        # line of this section should contain all the “short” variable names on
        # one line.
        self.header += "PI_CONTACT_INFO: 303-497-xxxx haggerty@ucar.edu\n"
        self.header += "PLATFORM: N677F - NSF/NCAR GV\n"
        self.header += "LOCATION: Lat, Lon, and Alt included in the data" + \
                       " records\n"
        # We want to say which version of the LRT netCDF was used to update
        # the IWG values (and avg and rms aircraft vals). Put that here??
        self.header += "ASSOCIATED_DATA: linked from DATA_INFO page\n"
        self.header += "INSTRUMENT_INFO: linked from DATA_INFO page\n"
        self.header += "DATA_INFO: Put DOI of EMDAC landing page here\n"
        self.header += "UNCERTAINTY: Enter uncertainty description here\n"
        self.header += "ULOD_FLAG: -7777\n"
        self.header += "ULOD_VALUE: N/A\n"
        self.header += "LLOD_FLAG: -8888\n"
        self.header += "LLOD_VALUE: N/A\n"
        self.header += "DM_CONTACT_INFO: Enter Data Manager Info here\n"
        self.header += "PROJECT_INFO: lined from DATA_INFO page\n"
        self.header += "STIPULATIONS_ON_USE: We strongly encourage anyone " + \
                       "using the MTP data to contact us regarding its use\n"
        self.header += "OTHER_COMMENTS: Here's a brief free-form tutorial " + \
                       "on how to decipher the MTP data: Data groups " + \
                       "consist of the following group of lines per " + \
                       "17-second observing cycle.  The 1-liners (for " + \
                       "each cycle) can be stripped & imported into a " + \
                       "spreadsheet for convenient plotting of trop " + \
                       "altitude, lapse rate, etc. The tropopause " + \
                       "altitudes are calculated by cubic spline " + \
                       "interpolation of the retrieved altitudes using the" + \
                       " WMO definition (that is, trop #1 is lowest " + \
                       "altitude where average lapse rate > -2 K/km from " + \
                       "initial -2 K/km point to any point within 2 km; " + \
                       "trop #2 occurs above first trop after lapse rate " + \
                       "is < -3K/km for >1 km, and then first trop " + \
                       "definition applies, possibly from within the 1 km " + \
                       "region.)\n"
        self.header += "REVISION: R0\n"
        self.header += "R0: initial release\n"

        # Now make short_name line
        self.header += "start_time, NX, end_time, "
        for var in ['SAPALT', 'SAPITCH', 'SAROLL']:
            self.header += \
                self.client.reader.get_metadata('Aline', var, 'short_name') + \
                ", "

        self.header += "brightness_temperature, tropopause_altitude_1, " + \
            "tropopause_altitude_2, tropopause_potential_temperature_1, " + \
            "tropopause_potential_temperature_2, "
        for var in ['SALAT', 'SALON']:
            self.header += \
                self.client.reader.get_metadata('Aline', var, 'short_name') + \
                ", "

        self.header += "air_temperature_lapse_rate, " + \
            self.client.reader.getATPmetadata('RCFMRIndex', 'short_name',
                                              ATPindex) + \
            ", Tcp, Zcl, altitude, air_temperature, " + \
            "air_temperature_anomaly, altitude, air_density\n"

        # When all done, count lines and prepend first line if ICARTT file
        # which is "number of lines in header, file format index"
        self.numlines = self.header.count('\n') + 1  # +1 for line about to add
        self.header = str(self.numlines) + ", " + self.file_format_index + \
            "\n" + self.header

        return(True)  # Succeeded in building ICARTT header

    def saveHeader(self, filename):
        """ Save header to ICARTT file """
        # If successfully build header, write header to output file and
        # return success
        if self.build_header(datetime.today().strftime('%Y%m%d')):
            with open(filename, 'w') as f:
                # Write the header to the ICARTT file
                f.write(self.header)
            return(True)
        else:
            return(False)

    def saveData(self, filename):
        """ Loop through flightData and save to ICARTT file """
        fd = self.client.reader.flightData

        for index in range(len(fd)):
            if index < len(fd)-1:
                endtime = fd[index+1]['Aline']['values']['TIME']['val']-1
            else:
                # Assume 17 second scan for last scan
                endtime = fd[index]['Aline']['values']['TIME']['val']+16

            # Save a record to the ICARTT file
            self.build_record(fd[index], endtime)

        # Write record to output file
        with open(filename, 'a') as f:
            f.write(self.data)

    def build_record(self, rec, endtime):
        """
        A record consists of a single dependent unbounded line followed by NX
        dependent bounded lines
        """
        # On Windows, sometimes there is an empty flightData rec at the end
        # of the array, which wreaks havoc in this routine. So check for it
        # and return.
        if rec['ATP'] == "":
            return()

        # -- dependent unbounded line for this record --
        # start_time
        self.data = "  %5d, " % rec['Aline']['values']['TIME']['val']

        # NX - I think the altitudes are the MTP alts interpolated to the RCF
        # alts, so this next line is wrong, but leave it here for now so can
        # generate a file that passes the ICARTT checker, even thought data is
        # all missing.
        NX = len(rec['ATP']['Altitudes'])
        self.data += "%2d, " % NX

        # end_time
        self.data += "%5d, " % endtime

        # barometric_altitude
        self.data += "%5.3f, " % float(rec['Aline']['values']['SAPALT']['val'])

        # platform_pitch
        self.data += \
            "%4.1f, " % float(rec['Aline']['values']['SAPITCH']['val'])

        # platform_roll
        self.data += "%4.1f, " % float(rec['Aline']['values']['SAROLL']['val'])

        self.data += "-999.9, "  # horizontal brightness temperature
        self.data += "-99.9, "   # tropopause_alt_1
        self.data += "-99.9, "   # tropopause_alt_2
        self.data += "-999.9, "  # tropopause_potential_temperature_1
        self.data += "-999.9, "  # tropopause_potential_temperature_2

        # latitude
        self.data += \
            "%7.3f, " % float(rec['Aline']['values']['SALAT']['val'])

        # longitude
        self.data += \
            "%8.3f, " % float(rec['Aline']['values']['SALON']['val'])

        self.data += "-99.9, "    # air_temperature_lapse_rate

        # MRI
        self.data += "%5.2f, " % float(rec['ATP']['RCFMRIndex']['val'])

        self.data += "-999.99, "   # cold point temperature
        self.data += "-99.99"    # cold point altitude

        self.data += "\n"  # End of line

        # -- dependent bounded lines for this record --
        for i in range(NX):
            self.data += "-999, -999, -999, -999, -999\n"
