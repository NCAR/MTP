###############################################################################
# This python class is used to read variables from an RAF LRT NetCDF file
# See VB6 routine GetNGvalues in BAS/MTPio.Bas, as well as functions
# fTstringToSec() in multiple files in the BAS/ and VBP/Misc dirs, and
# functions fZtoP and fPtoZ in the BAS/ dir.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2020
###############################################################################
import netCDF4
import pandas as pd
from EOLpython.Qlogger.messageHandler import QLogger as logger


class readGVnc:

    def __init__(self):
        """
        The MTP Aline includes scan average and rms values of aircraft pitch,
        roll, pressure altitude, ambient air temperature, latitude, and
        longitude. During post-processing, replace the real-time values in the
        raw data with scan average and rms values calculated from the final,
        QC'd RAF Low Rate (LRT) netCDF files.
        """

        # Suggest a default varlist, but then confirm against values that are
        # available in the netCDF file, and allow users to correct vars if
        # needed.
        # This list should be in the processing config file. (Do I want to
        # split real-time config and processing config into two files?)
        varlist = ["GGLAT", "GGLON", "GGALT", "PITCH", "ROLL", "PALTF", "ATX"]
        self.varlist = varlist

    def getNGvalues(self, ncfile, varlist=None):
        """
        Read in NetCDF file. Save record to pandas DataFrame where columns are
        time and then variables in varlist

        Stolen from nc2iwg1.p written by Taylor Thomas
        """
        nc = netCDF4.Dataset(ncfile, mode='r')

        # Extract the time variable from the netCDF file. TIME contains a
        # netCDF "chunk" with the dimensions, attributed, and values of the
        # variable "Time". dtime is an array of cftime date/time objects
        # Store the cftime array as a pandas object and cast the data in it to
        # type string
        TIME = nc.variables["Time"]
        dtime = netCDF4.num2date(TIME[:], TIME.units)
        dtime = pd.Series(dtime).astype(str)

        self.ncdata = dtime.to_frame()  # Assign time to DataFrame

        # If user requested a list via the optional varlist in the call
        # to this fn, overwrite varlist with it.
        self.varlist = varlist
        logger.printmsg("DEBUG", "reading " + str(varlist))

        # Now loop through varlist and add variable data to DataFrame
        if varlist is not None:
            for var in self.varlist:
                if var in list(nc.variables.keys()):  # Var exists in nc file
                    # Extract list of values from the netCDF "chunk"
                    output = nc.variables[var][:]
                    # Convert output to DataFrame and append to ncdata
                    self.ncdata = \
                        pd.concat([self.ncdata, pd.DataFrame(output)],
                                  axis=1, ignore_index=True)
                else:
                    # print(nc.variables.keys())
                    logger.printmsg("ERROR", "Error extracting variable " +
                                    var + " from " + ncfile + ". Variable " +
                                    "not found. Click OK to continue or " +
                                    "Quit to exit.")

        return(self.ncdata)

    def NGseconds(self):
        """
        Get times from DataFrame in seconds. When date rollover occurs report
        seconds greater than 86400
        """
        # Extract date and time from dataframe into datetime object
        datetime = self.ncdata.iloc[:, 0]  # [all rows, column 0]

        # Convert time from HHMMSS to sec.
        dtime = datetime.str.split().str[1]  # Get just time from datetime
        dtime = pd.to_timedelta(dtime).dt.total_seconds().astype(int)  # to sec

        # Handle midnight rollover
        date = datetime.str.split().str[0]  # Get just date from datetime
        date = pd.to_datetime(date)  # Convert to datetime object
        start_date = date.iloc[0]  # Date of first record in file
        # Now calculate difference between record date, and first date, in secs
        diff = date.sub(start_date).dt.total_seconds().astype(int)
        # Add diff to dtime to get secs since midnight of start date of flight.
        dtime = dtime + diff

        return(dtime)

    # def CtoK(self):
        # Does conversions from C to K (+273.15), Z to P fZtoP(), fPtoZ(),
        # Alt M to Km (/1000) as necessary
        # VB code saves the variables to new vars named:
        # UT, ACINS, pALT, T, mZg, mLatitude, mLongitude, GroundSpeed, GSF_A,
        # Mach, P, mPitch, Pstatic, Ptotal, QC_A, mRoll, TAS, Heading, TOATn1,
        # TOATn2, TOATn3, TOATn4, TOATn0, Vzac, mT, mT2, mT3, mT4, AttackAngle,
        # mZp, PSFC, SideSlipAngle, TAS, Wdir, Wspd, Mach2 or Mach2=mMach2

    # def calcP(self):
        # If PSFC or PALT_A is missing, use other one to calc missing one. Be
        # sure to do unit conversions (M to Km) and ZtoP or PtoZ
#
#      Pdynamic = Ptotal - Pstatic
#      Vzac = VSPD + cTo    'VSPD makes no sense
#      If mMach2 = -32767 And mZp > 0 And mZp < 25 Then
#        mMach2 = 0.02089 + 0.06555 * mZp - 0.00122 * mZp ^ 2
#      End If
#    param(1) = P 'hPa  = fZtoP(mZp)
#    param(2) = T                   'K
#    param(3) = mPitch = PITCH
#    param(4) = mRoll  = ROLL
#    param(5) = mLatitude  = GGLAT
#    param(6) = mLongitude = GGLON
#
#    param(8) = mZg        = GGALT
#    param(9) = mZp = PALT_A/1000
#
#    param(15) = fTheta(T, P)
#    param(16) = T
#    param(17) = mT
#    param(18) = mT2
#    param(19) = mT3
#    param(20) = mT4
#    If Mach2 > 0 Then param(22) = Sqr(mMach2)
#    param(23) = mMach2
#
#    """

    def getValAtTime(self, filename, var, timestr):
        """
        filename is the NetCDF file from which to retrieve data
        var      is a valid variable name from the NetCDF file
        timestr  is a string of the format "yyyy-mm-dd hh:mm:ss" indicating the
                 time of the value you want to retrieve

        returns a single value, no longer in a dataframe
        """
        # vals is a dataframe with time in first column and the requested
        # variable values in second column.
        vals = self.getNGvalues(filename, [var])
        # Find row where time=timestr and get var from second column (index 1)
        # Returns a one-item list
        chunk = vals.loc[(vals[0] == timestr), 1]
        return(chunk.values[0])  # Return value of var as float
