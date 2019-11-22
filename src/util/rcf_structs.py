###############################################################################
# Dictionaries to hold  Retrieval Coefficient File (RCF) data for the Microwave
# Temperature Profiler (MTP).
###############################################################################

RCF_HDR = {
    # Dictionary to hold the header record. Note:  For some reason the Header
    # structure itself is not matching up with this (despite the VB6 code
    # indicating that it "should").  For this reason another Union to get
    # second half of the RCF header record is defined below.  WARNING:
    # Because VB does not have an end char, these char arrays don't have an
    # end char!!
    'RCformat': 0,            # bytes -> short
    'CreationDateTime': "",   # bytes -> string
    'RAOBfilename': "",       # bytes -> string
    'RCfilename': "",         # bytes
    'RAOBcount': 0,           # bytes
    'LR1': 0.0,               # LR above top of RAOB
    'zLRb': 0.0,              # LR break altitude
    'LR2': 0.0,               # LR above break altitude
    'RecordStep': 0.0,        # Record Step through available RAOBs
    'RAOBmin': 0.0,           # Minimum acceptable RAOB altitude
    'ExcessTamplitude': 0.0,  # Random Excess Noise Level on Ground
    'Nobs': 0,                # Number of observables
    'Nret': 0,                # Number of retrieval levels
    'dZ': [],                 # Retrieval offset levels wrt flt level
    'NFL': 0,                 # Number of flight levels
    'Zr': [],                 # Flight levels (km)
    'Nlo': 0,                 # Number of LO channels
    'LO': [],                 # LO frequencies (GHz)
    'Nel': 0,                 # Number of elevation angles
    'El': [],                 # Scan mirror elevation angles
    'Nif': 0,                 # Number of IF frequencies
    'IFoff': [],              # IF frequency offsets (GHz)
    'IFwt': [],               # Weights assigned to each IF frequency
    'Spare': [],              #
    'SURC': [],               # SU IFB used to calc RCs -added 20050128
    'CHnLSBloss': [],         # CHn LSB RF loss
    'RAOBbias': 0.0,          # Bias added to RAOB before calc'ing RCs
    'CH1LSBloss': 0.0,        # CH1 LSB linear RF loss gradient
    # Sensitivity matrix: iRC, NFL, Nlo, Nel
    'SmatrixN1': [],          # Linear term [15][3][10]
    # Sensitivity matrix: iRC, NFL, Nlo, Nel
    'SmatrixN2': [],          # Quadratic term [15][3][10]
    }

RCF_FL = {
    # Dictionary to hold each flight level
    # Note: sOBav and sOBrms expect that channel 1 will be in array elements
    # 0-9 with element 0 being the highest scan angle and element 9 the lowest
    # scan angle.  Similarly, channel 2 will be found in elements 10-19 and
    # channel 3 will be in elements 20-29.
    'sBP': 0.0,    # Flight level pressure altitude (hPa)
    'sOBrms': [],  # 1-sigma apriori observable errors
    'sOBav': [],   # Archive Average observables
    'sBPrl': [],   # Pressure at retrieval levels
    'sRTav': [],   # Average T at retrieval levels
    'sRMSa': [],   # Variance in T at retrieval levels
    'sRMSe': [],   # Formal error in T at retrieval levels
    'Src': [],     # 33 retrieval levels, 30 observables
    'Spare': [],
    }
