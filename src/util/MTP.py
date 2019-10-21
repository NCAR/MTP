###############################################################################
#
# This python dictionary stores the content of a single MTP record
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
import re
import numpy

MTPrecord = {
    # A string to hold an Ascii packet before it is parsed
    'asciiPacket': "",

    # A dictionary to hold a single raw data scan. A raw scan consists of
    # a set of 7 different line types
    'Aline': {
        # Regular expressions to match the various scan lines
        're': re.compile("^A (........) (..):(..):(..) (.*)"),
        'found': False,
        'date': "",
        'data': [],
        'values': {'DATE': {  # MTP Scan Date (YYYYMMDD)
                  'val': numpy.nan},
                 'TIME': {  # MTP Scan Time (HHMMSS)
                  'val': numpy.nan},
                 'SAPITCH': {  # MTP Scan Avg Pitch (degree)
                  'val': numpy.nan, 'idx': 0},
                 'SRPITCH': {  # MTP Scan RMSE Pitch (degree)
                  'val': numpy.nan, 'idx': 1},
                 'SAROLL':  {  # MTP Scan Avg Roll (degree)
                  'val': numpy.nan, 'idx': 2},
                 'SRROLL':  {  # MTP Scan RMSE Roll (degree)
                  'val': numpy.nan, 'idx': 3},
                 'SAPALT':  {  # MTP Scan Avg Pressure Altitude (km)
                  'val': numpy.nan, 'idx': 4},
                 'SRPALT':  {  # MTP Scan RMSE Pressure Alt (km)
                  'val': numpy.nan, 'idx': 5},
                 'SAAT':    {  # MTP Scan Avg Ambient Air Temp (deg_K)
                  'val': numpy.nan, 'idx': 6},
                 'SRAT':    {  # MTP Scan RMSE Ambient Air Temp(deg_K)
                  'val': numpy.nan, 'idx': 7},
                 'SALAT':   {  # MTP Scan Avg Latitude (degree_N)
                  'val': numpy.nan, 'idx': 8},
                 'SRLAT':   {  # MTP Scan RMSE Latitude (degree_N)
                  'val': numpy.nan, 'idx': 9},
                 'SALON':   {  # MTP Scan Avg Longitude (degree_E)
                  'val': numpy.nan, 'idx': 10},
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
        're': re.compile("^IWG1,(........T......),(.*)"),
        'found': False,
        'date': "",
        'asciiPacket': "",
        'data': [],
        'values': {'DATE': {  # IWG1 packet Date (YYYYMMDD)
                  'val': numpy.nan},
                 'TIME': {  # IWG1 packet Time (HHMMSS)
                  'val': numpy.nan},
                 },
    },

    'Bline': {
        're': re.compile("(^B) (.*)"),
        'found': False,
        'data': [],
        'values': {'SCNT': {  # MTP Scan Counts[Angle,Channel]
                  'val': [numpy.nan]*30}
                 },
    },
    'M01line': {  # MTP Engineering Multiplxr
        're': re.compile("(^M01): (.*)"),
        'found': False,
        'data': [],
        'values': {'VM08CNTE': {  # Vm08 Counts
                        'val': numpy.nan, 'idx': 0},
                   'VVIDCNTE': {  # Vvid Counts
                        'val': numpy.nan, 'idx': 1},
                   'VP08CNTE': {  # Vp08 Counts
                        'val': numpy.nan, 'idx': 2},
                   'VMTRCNTE': {  # Vmtr Count
                        'val': numpy.nan, 'idx': 3},
                   'VSYNCNTE': {  # Vsyn Counts
                        'val': numpy.nan, 'idx': 4},
                   'VP15CNTE': {  # Vp15 Counts
                        'val': numpy.nan, 'idx': 5},
                   'VP05CNTE': {  # Vp05 Counts
                        'val': numpy.nan, 'idx': 6},
                   'VM15CNTE': {  # VM15 Counts
                        'val': numpy.nan, 'idx': 7},
                   },
    },

    'M02line': {  # MTP Engineering Multiplxr
        're': re.compile("(^M02): (.*)"),
        'found': False,
        'data': [],
        'values': {'ACCPCNTE': {  # Acceler Counts
                        'val': numpy.nan, 'idx': 0},
                   'TDATCNTE': {  # T Data Counts
                        'val': numpy.nan, 'idx': 1},
                   'TMTRCNTE': {  # T Motor Counts
                        'val': numpy.nan, 'idx': 2},
                   'TAIRCNTE': {  # T Pod Air Counts
                        'val': numpy.nan, 'idx': 3},
                   'TSMPCNTE': {  # T Scan Counts
                        'val': numpy.nan, 'idx': 4},
                   'TPSPCNTE': {  # T Power Supply Counts
                        'val': numpy.nan, 'idx': 5},
                   'TNCCNTE': {  # T N/C Counts
                        'val': numpy.nan, 'idx': 6},
                   'TSYNCNTE': {  # T Synth Counts
                        'val': numpy.nan, 'idx': 7},
                   },
    },
    'Ptline': {  # MTP Platinum Multiplxr
        're': re.compile("(^Pt): (.*)"),
        'found': False,
        'data': [],
        'values': {'TR350CNTP': {  # R350 Counts
                         'val': numpy.nan, 'idx': 0},
                   'TTCNTRCNTP': {  # Target Center Temp Counts
                         'val': numpy.nan, 'idx': 1},
                   'TTEDGCNTP': {  # Target Edge Temp Counts
                         'val': numpy.nan, 'idx': 2},
                   'TWINCNTP': {  # Polyethelene Window Temp Counts
                         'val': numpy.nan, 'idx': 3},
                   'TMIXCNTP': {  # Mixer Temperature Counts
                         'val': numpy.nan, 'idx': 4},
                   'TAMPCNTP': {  # Amplifier Temp Counts
                         'val': numpy.nan, 'idx': 5},
                   'TNDCNTP': {  # Noise Diode Temp Counts
                         'val': numpy.nan, 'idx': 6},
                   'TR600CNTP': {  # R600 Counts
                         'val': numpy.nan, 'idx': 7},
                   },
    },
    'Eline': {
        're': re.compile("(^E) (.*)"),
        'found': False,
        'data': [],
        'values': {'TCNT': {  # MTP Target Counts[Target,Channel]
                    'val': [numpy.nan]*6}
                   },
    },
}
