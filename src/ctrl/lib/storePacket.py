###############################################################################
# Class defining a dictionary to hold data returned from the  
# the MTP instrument, save it to a file, and create a UDP feed from it.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################


class StorePacket():

    def __init__(self):

        packet_list = {
            #'Aline':'A 20101002 19:47:30 -00.59 00.13 -00.26 00.13 +04.37 0.04 270.99 00.38 +39.123 +0.016 -103.967 +0.044 +072727 +071776',    
            #'IWG': 'IWG1,20101002T194729,39.1324,-103.978,4566.43,,14127.9,,180.827,190.364,293.383,0.571414,-8.02806,318.85,318.672,-0.181879,-0.417805,-0.432257,-0.0980951,2.36793,-1.66016,-35.8046,16.3486,592.062,146.734,837.903,9.55575,324.104,1.22603,45.2423,,-22.1676,',  
            #'Bline':'B 017828 019041 018564 017846 019061 018572 017874 019069 018603 017906 019095 018625 017932 019124 018637 017949 019139 018655 017968 019151 018665 017979 019164 018665 017997 019161 018691 018029 019181 018705',    
            #'M01':'M01: 2928 2457 3023 3085 1925 2923 2434 2948',    
            #'M02':'M02: 2109 1299 2860 2691 2962 1116 4095 1805',    
            #'Pt':'Pt: 2157 13804 13796 10311 13383 13327 13144 14440',    
            #'Eline': 'E 020541 021894 021874 018826 020158 019813 ',    
            'firstUDP': True, # first udp packet needs to cast these to list
            # if there is no UDP, they need to have integer values
            'pitch15':0, # Array containing  
            'roll15':0,  # last 15 seconds 
            'Zp15':0,   
            'oat15':0, 
            'lat15':0,  
            'lon15':0 ,
            'pitchavg':0, # Value containing average of 
            'rollavg':0,  # last 15 seconds array
            'Zpavg':0,    # and the root mean square error
            'oatavg':0,   # default is 1 to not zero out
            'latavg':0,   # goAngle calculation from pitch
            'lonavg':0 ,  # and roll avg's
            'pitchrms':0, # Array containing average of 
            'rollrms':0,  # last 15 seconds array
            'Zprms':0,    # and the root mean square error
            'oatrms':0,   # default is 1 to not zero out
            'latrms':0,   # goAngle calculation from pitch
            'lonrms':0 ,  # and roll avg's
            # except not really, pitchavg/pitchrms added as
            # temp vars from udp averageVal
            # but we do need this in here if there is no iwg packet
            'scanCount': '+074146',
            'encoderCount':'+073392',
            'saved': False,   
            'newFrame': False,
            'isCycling': False,
            'switchControl': 'initScan',  #matchWord, start with initConfig
            'done':False, # collect last buffer remanants before going to next switchControl
            'doneCycle':False, # second time we're done with integrate
            'currentMode': 'init', # init, home, scan
            'desiredMode': 'init', # init, home, scan
            'firstInit': True, # first time initScan is called, call resetInitScan
            'initSwitch': False, # causes init 1 and 2 to be called every other time in initScan
            # there has to enough of a delay so that there are no collisions
            'init1Received': False,
            'init2Received': False,
            'homeSwitch': False,
            'isNoiseZero': False,
            'waitSwitch': False,
            'scanSet': False,     # homeScan 2nd wait switch
            'calledFrom': 'None',  # flag for homeScan, Integrate to know (E/Bline) return
            'echoCommand': False,   # Flag to start counting st's for homeStep, integrate
            'noise':-1,
            'clickStep': 0, # current click step, updated in eline (retrieval for)
            'encodeCount': -1,
            'currentFrequency': 55.51, # currently unimplemented, grab from config
            'totalFrequencies': '', # ditto above
            'integrateData': '', # store data gathered by integrate function
            'integrateSwitch': '', # middle man between current frequency and index of frequency, check if integrateCount performs same function
            'tuneSwitch': True,  # determines if call to tune is necessary
            'tuneMode': 'C',     # determines if tune 'C' or tune 'F' is sent to probe
            'count2Flag': False, # determine when to call count2 (after I## received from interate
            'integrateCount': 0, # for indexing into nfreq
            'gearRatio': 80/20,  # 2007/11/29, assumes "j256" for fiduciary
            'stepsDegree': 80/20 * (128 * (200/360)) ,# and "j128" for normal run
            # 10 sky views + target = 11
            # -179.8 location of fiduciary 2008/03/17
            # 80.0 first sky view 20080317
            # 0.00 horizon
            # -80.0 last skyview
            # need to keep these arrays formatted the same
            # to keep things backward compatable
      
            'El. Angles':[10,-179.8, 80.00, 55.00, 42.00, 25.00, 12.00, 0.00, -12.00, -25.00, -42.00, -80.00],
            #'El. Angles':[10,-179.8, 80.00, 80.00, 80.00, 80.00, 80.00, 80.00, 80.00, 80.00, 80.00, 80.00],
            #'nFreq':[55.51, 56.65, 58.8],
            'nFreq':[56.36, 57.61, 58.36],

            'angleI': 0, # bline angle iterator
            'Nangle' : 10, # First value in El. Angles
            'bSwitch': False, # do a go angle/move switch
            'pitchCorrect': False, # correct pitch in goAngle
            'bDone': False, # flag to signal donness in Bline
            'Nsteps': 0,
            'currentClkStep':0, 
            'targetClkStep':0, 

        }

        self.packet = packet_list

    def getData(self, key):
        """ Return the data for a given user-requested key """
        return(self.packet[key])

    def getArray(self, key1, key2):
        """ Return the date for a given user-requested key """
        self.a = self.packet[key1]

        return self.a[key2]

#    def getData(self):
#        """ Return a list of all configurations """
#        return(self.packet.keys())

    def setData(self, key, data):
        """ Return true if sucessfully written """
        self.packet[key] = data

    def saveData(self, saveFile):
        """ Return if successful write to file"""
        for index in range(7):
            saveFile.write(self.packet[index])
        self.packet['saved'] = True
        return self.packet['saved']

    def averageIWG(self):
        """ Averages IWG17 packet, a running sum of 17 seconds, returns currnt value/17 """
        """ Only implement if Janine's bit will not be on the plane too. """
        return (self.packet[IWG])

    def appendData(self, key, data):
        """ Append data, used when building eline, aline, bline and other QByteArray's """
        self.packet[key] = self.packet[key].append(data)

    def makeUDP(self):
        """ Return a list of all configurations """
        return(self.packet.keys())
