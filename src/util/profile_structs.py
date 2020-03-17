###############################################################################
# Dictionaries to hold final, processed Profile data for the Microwave
# Temperature Profiler (MTP).
###############################################################################
import numpy
import copy


# Dictionary to hold info on a single tropopause. We use an array of these
# dictionaries in the code to store all the tropopauses
TropopauseRecord = {
    'idx': numpy.nan,   # The level (in the temperature profile) of the trop
    'altc': numpy.nan,  # The altitude of the found tropopause
    'tempc': numpy.nan  # The temperature of the found tropopause
}

AtmosphericTemperatureProfile = {
    'Temperatures': [],  # Physical temperature
    'Altitudes': [],
    'RCFIndex': numpy.nan,  # Index of RCF file (template) used to create this
                            # profile
    'RCFALT1Index': numpy.nan,  # Flight level below aircraft from template
    'RCFALT2Index': numpy.nan,  # Flight level above aircraft from template
    'RCFMRIndex':  {          # Meridional Region Index: Quality of match
        'val': numpy.nan,     # between measured Brightness Temperture (TB)
        'short_name': 'MRI',  # and TB from template
        'units': '#',
        'long_name': 'retrieval quality metric (ranges 0-2, <1 is excellent)'},
    'trop': [copy.deepcopy(TropopauseRecord),
             copy.deepcopy(TropopauseRecord)],  # Array of 2 tropopauses
}
