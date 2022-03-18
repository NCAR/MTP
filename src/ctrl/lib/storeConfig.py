###############################################################################
# Class defining a dictionary to hold data loaded from the default.mtph config 
# file, changes made from the GUI, and lab values for default tests
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import logging
from os import path


class StoreConfig():

    def __init__(self, app):

        config_list = {
	    # Example packet
            #'Aline':'A 20101002 19:47:30 -00.59 00.13 -00.26 00.13 +04.37 0.04 270.99 00.38 +39.123 +0.016 -103.967 +0.044 +072727 +071776',    
            #'IWG': 'IWG1,20101002T194729,39.1324,-103.978,4566.43,,14127.9,,180.827,190.364,293.383,0.571414,-8.02806,318.85,318.672,-0.181879,-0.417805,-0.432257,-0.0980951,2.36793,-1.66016,-35.8046,16.3486,592.062,146.734,837.903,9.55575,324.104,1.22603,45.2423,,-22.1676,',  
            #'Bline':'B 017828 019041 018564 017846 019061 018572 017874 019069 018603 017906 019095 018625 017932 019124 018637 017949 019139 018655 017968 019151 018665 017979 019164 018665 017997 019161 018691 018029 019181 018705',    
            #'M01':'M01: 2928 2457 3023 3085 1925 2923 2434 2948',    
            #'M02':'M02: 2109 1299 2860 2691 2962 1116 4095 1805',    
            #'Pt':'Pt: 2157 13804 13796 10311 13383 13327 13144 14440',    
            #'Eline': 'E 020541 021894 021874 018826 020158 019813 ',    

            # From config.mtph
            'Program': 'MTPcontroller.py',
	    'Aircraft': 'NGV',
            'NominalPitch': 3,
            'Offsets':[1,2,3],
	    'OffsetYi':0,
	    'OffsetPi':0,
	    'OffsetRi':0,
	    'Frequencies':[3, 55.51,56.65,58.8],
	    'Integ.Time': 200.0, #mS note that this can't currently be changed
            'El. Angles':[10,-179.8, 80.00, 55.00, 42.00, 25.00, 12.00, 0.00, -12.00, -25.00, -42.00, -80.00],
            # From config.yml
            # Program uses these in flight, GUIRefresh displays
	    'Project': 'Default', 
	    'Flight #': 00,
	    'PI':'Default',
            'SaveFileLocation':'',
            #Everything below should be on Config Tab
            'LogFileLocation':'',
	    'ErrorLogging': False,
            'AcserverIP': '192.168.84.2',
            'USBPort': 'COM6', #COM6 windows, /dev/ttyUSB# otherwise
            # These shouldn't change unless the math behind one of them does
            'PitchCorrect': True,
            'MAM#': 1,
            # Grouped radio buttons, changing one changes all 4 to False
            # Then sets one to true.
            'Lab': False,
            'LabNoProbe':False,
            'Flight':True, 
            'FixedAngleFlight': False,

        }
        self.config = config_list 

        config_lab_list = {
            # Lab Use Only
            'El. Angles':[10,-179.8, 80.00, 55.00, 42.00, 25.00, 12.00, 0.00, -12.00, -25.00, -42.00, -80.00],
            'AngleStareLab':[10,-179.8, 80.00, 80.00, 80.00, 80.00, 80.00, 80.00, 80.00, 80.00, 80.00, 80.00],
            'Frequencies':[3, 56.36, 57.61, 58.36],
            'IWGLab': [],
            'IWGSameLab':[] , 
        }
        self.config_lab = config_lab_list

    def getData(self, key, lab):
        """ Return the data for a given user-requested key """
        if lab:
            return self.config_lab[key]
        else:
            return(self.config[key])

    def getArray(self, key, index, lab):
        """ Return the date for an index given user-requested key """
        if lab:
            a = self.config_lab[key]
            return a[index]
        else:
            a = self.config[key]
            return a[index]

    def setArray(self, key, index, value, lab):
        """ Sets individual element of an array in configStore """
        logging.debug("setArray")
        if lab: 
            logging.debug("setArray: lab")
            a = self.config_lab[key]
            a[index] = int(value)
        else:
            logging.debug("setArray: notlab, key %r", key)
            a = self.config[key]
            logging.debug("setArray: notlab, a %r, value %r, index %r", a, value, index)
            a[index] = int(value)
            logging.debug("setArray: notlab, done a %r", a)
            logging.debug("setArray: notlab, done self.config{key] %r", self.config[key])

    def setData(self, key, data, lab):
        """ Return true if sucessfully written """
        if lab:
            self.config_lab[key] = data
        else:
            self.config[key] = data

    def loadConfigMTPH(self):
        # Loads Data from Config.mtph
        # Throws error if not found

        logging.debug("loadConfigMTP")
        path = 'C:\\Users\\lroot\\MTP\\src\\ctrl\\'
        
        with open(path + "Config.mtph", 'r') as configFile:
            lines = configFile.readlines()
            for line in lines:
                if line[0] == '[':
                    key = line[1:len(line)-2]
                    array = []
                    index = 0
                else:
                    if line == '\n':
                        break;
                    elif key == 'Program' or key == 'Aircraft' or key == 'NominalPitch':
                        self.setData(key, line, lab = False)
                        logging.debug("program/aircraft/nominalPitch case")
                    elif key == 'Offsets' or key == 'Frequencies' or key == 'El.Angles':
                        line = line.split('\'')
                        line = line[0]
                        line = line.split(' ')
                        line = line[0]
                        logging.debug("load config, split: %r", line)
                        logging.debug("load config, index %r", index)
                        self.setArray(key, index, line, lab = False)
                        index = index + 1
                    elif key == 'Integ. Time':
                        blah
                    elif key == 'End':
                        logging.info("Config.mtph end of file reached")
                    else:
                        logging.error("Config.mtph unknown key %r", key)

                    # They come in with newlines, hence -1
            logging.debug("Reading config.mtph: %r", lines)


    def saveData(self, saveFile):
        """ Saves a new default.mtph, currently blind overwrite"""
        for index in range([0,8]):
            saveFile.write(index + '\n')
	    # Format for array
            if index == 'Frequencies' or index == 'El. Angles':
                for key in range(self.config[index]):
                    saveFile.write(self.config[index] + '\n')
            else:
                saveFile.write(self.config[index])
        #saves config.yaml changes?
        for index in range([8,len(self.config)]):
            logging.debug("range 8-end")

    def appendData(self, key, data):
        """ Append data, used when building eline, aline, bline and other QByteArray's """
        self.config[key] = self.config[key].append(data)

    def labFlightChange(self, changeName):
        setData(data = False, lab = False)
        setData(data = False, lab = False)
        setData(data = False, lab = False)
        setData(data = False, lab = False)
        if changeName[0:2] == 'Lab':
            logging.debug("Setting to lab mode")
            logging.debug("Setting to lab mode")
            setData(changeName, data = True, lab = True)
        else:
            setData(changeName, data = True, lab = False)
