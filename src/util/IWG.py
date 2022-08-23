###############################################################################
#
# This python dictionary stores the content of a single IWG record, or of an
# average over a set of IWG records
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import numpy

IWGrecord = {
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
}
