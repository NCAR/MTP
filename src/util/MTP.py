###############################################################################
#
# This python dictionary stores the content of a single raw MTP record
#
# A <date> <time> SAPITCH SRPITCH SAROLL SRROLL SAPALT SRPALT SAAT SRAT SALAT
#         SRLAT SALON SRLON SMCMD SMENC
# B SCNT[30]
# M01: VM08CNTE VVIDCNTE VP08CNTE VMTRCNTE VSYNCNTE VP15CNTE VP05CNTE VM15CNTE
# M02: ACCPCNTE TDATCNTE TMTRCNTE TAIRCNTE TSMPCNTE TPSPCNTE TNCCNTE TSYNCNTE
# Pt: TR350CNTP TTCNTRCNTP TTEDGCNTP TWINCNTP TMIXCNTP TAMPCNTP TNDCNTP
#         TR600CNTP
# E TCNT[6]
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import numpy

MTPrecord = {
    # A string to hold an Ascii packet before it is parsed
    'asciiPacket': "",

    # A dictionary to hold a single raw data scan. A raw scan consists of
    # a set of 7 different line types
    'Aline': {
        # Regular expressions to match the various scan lines
        're': "^A (........) (..):(..):(..) (.*)",
        'found': False,
        'date': "",  # YYYYMMDDTHHMMSS
        'data': [],  # A string containing the data values after date/time
        'values': {'DATE': {  # MTP Scan Date (YYYYMMDD)
                  'val': numpy.nan},
                 'timestr': {  # MTP Scan Time (HHMMSS)
                  'val': numpy.nan},
                 'TIME': {  # MTP Scan Time (HHMMSS) converted to secs
                  'val': numpy.nan},
                 'SAPITCH': {  # MTP Scan Avg Pitch (degree)
                  'val': numpy.nan, 'idx': 0,
                  'short_name': 'platform_pitch',
                  'units': 'degree',
                  'long_name': 'Aircraft pitch (deg)',
                  '_FillValue': "-99.9"},
                 'SRPITCH': {  # MTP Scan RMSE Pitch (degree)
                  'val': numpy.nan, 'idx': 1},
                 'SAROLL':  {  # MTP Scan Avg Roll (degree)
                  'val': numpy.nan, 'idx': 2,
                  'short_name': 'platform_roll',
                  'units': 'degree',
                  'long_name': 'Aircraft roll (deg)',
                  '_FillValue': "-99.9"},
                 'SRROLL':  {  # MTP Scan RMSE Roll (degree)
                  'val': numpy.nan, 'idx': 3},
                 'SAPALT':  {  # MTP Scan Avg Pressure Altitude (km)
                  'val': numpy.nan, 'idx': 4,
                  'short_name': 'barometric_altitude',
                  'units': 'km',
                  'long_name': 'Pressure altitude of GV (km)',
                  '_FillValue': "-99.999"},
                 'SRPALT':  {  # MTP Scan RMSE Pressure Alt (km)
                  'val': numpy.nan, 'idx': 5},
                 'SAAT':    {  # MTP Scan Avg Ambient Air Temp (deg_K)
                  'val': numpy.nan, 'idx': 6},
                 'SRAT':    {  # MTP Scan RMSE Ambient Air Temp(deg_K)
                  'val': numpy.nan, 'idx': 7},
                 'SALAT':   {  # MTP Scan Avg Latitude (degree_N)
                  'val': numpy.nan, 'idx': 8,
                  'short_name': 'latitude',
                  'units': 'degree_north',
                  'long_name': 'Latitude (deg)',
                  '_FillValue': "-999.99"},
                 'SRLAT':   {  # MTP Scan RMSE Latitude (degree_N)
                  'val': numpy.nan, 'idx': 9},
                 'SALON':   {  # MTP Scan Avg Longitude (degree_E)
                  'val': numpy.nan, 'idx': 10,
                  'short_name': 'longitude',
                  'units': 'degree_east',
                  'long_name': 'Longitude (deg)',
                  '_FillValue': "-9999.99"},
                 'SRLON':   {  # MTP Scan RMSE Longitude (degree_E)
                  'val': numpy.nan, 'idx': 11},
                 'SMCMD':   {  # MTP Scan Motor Commanded Position
                  'val': numpy.nan, 'idx': 12},
                 'SMENC':   {  # MTP Scan Motor Encoded Position
                  'val': numpy.nan, 'idx': 13},
                 },
    },
    'IWG1line': {
        # From project "ascii_parms" file
        're': "^IWG1,(........T......),(.*)",
        'found': False,
        'date': "",
        'asciiPacket': "",
        'data': [],
        'values': {'DATE': {  # IWG1 packet Date (YYYYMMDD)
                  'val': numpy.nan},
                 'TIME': {  # IWG1 packet Time (HHMMSS) converted to secs
                  'val': numpy.nan},
                 # Additional variables are created dynamically from list of
                 # vars read from ascii_parms
                 },
    },

    'Bline': {
        're': "(^B) (.*)",
        'found': False,
        'data': [],
        'values': {'SCNT': {  # MTP Scan Counts[Angle,Channel]
                  'val': [numpy.nan]*30,
                  'tb': [numpy.nan]*30}  # Calculated Brightness Temperatures
                 },
    },
    'M01line': {  # MTP Engineering Multiplxr
        're': "(^M01): (.*)",
        'found': False,
        'data': [],
        'values': {'VM08CNTE': {  # Vm08 Counts
                        'val': numpy.nan, 'idx': 0,
                        'fact': -2.73,  # factors from decodeM01 in VB6
                                        # used to convert counts to volts
                        'volts': numpy.nan,  # Calculated voltage
                        'name': "-8V  PS"},
                   'VVIDCNTE': {  # Vvid Counts
                        'val': numpy.nan, 'idx': 1,
                        'fact': 1,
                        'volts': numpy.nan,  # Calculated voltage
                        'name': "Video V."},
                   'VP08CNTE': {  # Vp08 Counts
                        'val': numpy.nan, 'idx': 2,
                        'fact': 2.78,
                        'volts': numpy.nan,  # Calculated voltage
                        'name': "+8V  PS"},
                   'VMTRCNTE': {  # Vmtr Count
                        'val': numpy.nan, 'idx': 3,
                        'fact': 7.79,
                        'volts': numpy.nan,  # Calculated voltage
                        'name': "+24V Step"},
                   'VSYNCNTE': {  # Vsyn Counts
                        'val': numpy.nan, 'idx': 4,
                        'fact': 7.79,
                        'volts': numpy.nan,  # Calculated voltage
                        'name': "+15V Syn"},
                   'VP15CNTE': {  # Vp15 Counts
                        'val': numpy.nan, 'idx': 5,
                        'fact': 5.1,
                        'volts': numpy.nan,  # Calculated voltage
                        'name': "+15V PS"},
                   'VP05CNTE': {  # Vp05 Counts
                        'val': numpy.nan, 'idx': 6,
                        'fact': 2,
                        'volts': numpy.nan,  # Calculated voltage
                        'name': "VCC  PS"},
                   'VM15CNTE': {  # VM15 Counts
                        'val': numpy.nan, 'idx': 7,
                        'fact': -5.1,
                        'volts': numpy.nan,  # Calculated voltage
                        'name': "-15V PS"},
                   },
    },

    'M02line': {  # MTP Engineering Multiplxr
        're': "(^M02): (.*)",
        'found': False,
        'data': [],
        'values': {'ACCPCNTE': {  # Acceler Counts
                        'val': numpy.nan, 'idx': 0,
                        'temperature': numpy.nan,  # Calculated acceleration
                        'name': "Acceler"},
                   'TDATCNTE': {  # T Data Counts
                        'val': numpy.nan, 'idx': 1,
                        'temperature': numpy.nan,  # Calculated temperature
                        'name': "T Data"},
                   'TMTRCNTE': {  # T Motor Counts
                        'val': numpy.nan, 'idx': 2,
                        'temperature': numpy.nan,  # Calculated temperature
                        'name': "T Motor"},
                   'TAIRCNTE': {  # T Pod Air Counts
                        'val': numpy.nan, 'idx': 3,
                        'temperature': numpy.nan,  # Calculated temperature
                        'name': "T Pod Air"},
                   'TSMPCNTE': {  # T Scan Counts
                        'val': numpy.nan, 'idx': 4,
                        'temperature': numpy.nan,  # Calculated temperature
                        'name': "T Scan"},
                   'TPSPCNTE': {  # T Power Supply Counts
                        'val': numpy.nan, 'idx': 5,
                        'temperature': numpy.nan,  # Calculated temperature
                        'name': "T Pwr Sup"},
                   'TNCCNTE': {  # T N/C Counts
                        'val': numpy.nan, 'idx': 6,
                        'temperature': numpy.nan,  # Calculated temperature
                        'name': "T N/C"},
                   'TSYNCNTE': {  # T Synth Counts
                        'val': numpy.nan, 'idx': 7,
                        'temperature': numpy.nan,  # Calculated temperature
                        'name': "T Synth"},
                   },
    },
    'Ptline': {  # MTP Platinum Multiplxr
        're': "(^Pt): (.*)",
        'found': False,
        'data': [],
        'values': {'TR350CNTP': {  # R350 Counts
                         'val': numpy.nan, 'idx': 0,
                         'resistance': numpy.nan,   # Calculated resistance
                         'temperature': numpy.nan,  # Calculated temperature
                         'name': "Rref 350"},       # Name displayed in GUI
                   'TTCNTRCNTP': {  # Target Center Temp Counts
                         'val': numpy.nan, 'idx': 1,
                         'resistance': numpy.nan,   # Calculated resistance
                         'temperature': numpy.nan,  # Calculated temperature
                         'name': "Target 1"},       # Name displayed in GUI
                   'TTEDGCNTP': {  # Target Edge Temp Counts
                         'val': numpy.nan, 'idx': 2,
                         'resistance': numpy.nan,   # Calculated resistance
                         'temperature': numpy.nan,  # Calculated temperature
                         'name': "Target 2"},       # Name displayed in GUI
                   'TWINCNTP': {  # Polyethelene Window Temp Counts
                         'val': numpy.nan, 'idx': 3,
                         'resistance': numpy.nan,   # Calculated resistance
                         'temperature': numpy.nan,  # Calculated temperature
                         'name': "Window"},         # Name displayed in GUI
                   'TMIXCNTP': {  # Mixer Temperature Counts
                         'val': numpy.nan, 'idx': 4,
                         'resistance': numpy.nan,   # Calculated resistance
                         'temperature': numpy.nan,  # Calculated temperature
                         'name': "Mixer"},          # Name displayed in GUI
                   'TAMPCNTP': {  # Amplifier Temp Counts
                         'val': numpy.nan, 'idx': 5,
                         'resistance': numpy.nan,   # Calculated resistance
                         'temperature': numpy.nan,  # Calculated temperature
                         'name': "Dblr Amp"},       # Name displayed in GUI
                   'TNDCNTP': {  # Noise Diode Temp Counts
                         'val': numpy.nan, 'idx': 6,
                         'resistance': numpy.nan,   # Calculated resistance
                         'temperature': numpy.nan,  # Calculated temperature
                         'name': "Noise D."},       # Name displayed in GUI
                   'TR600CNTP': {  # R600 Counts
                         'val': numpy.nan, 'idx': 7,
                         'resistance': numpy.nan,   # Calculated resistance
                         'temperature': numpy.nan,  # Calculated temperature
                         'name': "Rref 600"},       # Name displayed in GUI
                   },
    },
    'Eline': {
        're': "(^E) (.*)",
        'found': False,
        'data': [],
        # The vector of counts produced by the MTP target. This vector is of
        # length 6 - three per channel for the noise diode turned on (stored as
        # the first three values) and three for it turned off (the next 3).
        'values': {'TCNT': {  # MTP Target Counts[Target,Channel]
                    'val': [numpy.nan]*6}
                   },
    },
    'tbi': "",  # Will hold an inverted brightness temperature array
    'BestWtdRCSet': "",  # Will hold an RC_Set_4Retrieval dictionary
    'ATP': "",  # Will hold an AtmosphericTemperatureProfile dictionary
}
