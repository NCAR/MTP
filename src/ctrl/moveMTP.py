###############################################################################
# Class defining a dictionary to hold all the various configurations for s
# the MTP instrument.
#
# MJ Mahoney, June 17, 2002
# Note that the values of yaw, pitch and roll given below were based
# on field measurements of insturment yaw A at zero elevation angle and
# pitch-like and roll-like parameters B and T along the MTP Sensor Unit
# edges: The measured angles in degrees were:
#
# ER2:     A=20.0  B=10.3  T=25.0
# DC8:     A=15.0  B=00.0  T=08.3  
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
from math import cos, sin, atan, asin, sqrt
import logging
from PyQt5 import QtCore

class moveMTP():
    
    
    def __init__(self, parent):
        varDict = {
            'Cycling': False,    
            'lastSky': -1, #readScan sets this to actual 
        }
        self.parent = parent
        self.vars = varDict 
        self.MAM = [['nan','nan','nan', 'nan'],['nan','nan','nan', 'nan'],['nan','nan','nan','nan'],['nan','nan','nan','nan']]
        self.configMAM()
    

    def dispatch(self, argument):
        methodName = str(argument)
        # Get the method from 'self'. Default to a lambda.
        method = getattr(self, methodName, lambda: "Invalid move method")
        logging.debug("dispatch2")
        # Call the method as we return it
        return method()


    def readScan(self):
        logging.debug("moveMTP readscan")
        #getcommand read_scan

    def initConfig(self):
        # re-load config values to lib
        # check that save file is open
        # should all be done in view.py rather than here
        return 0

        '''
    def read(self, waitReadyReadTime, readLineTime):
        # catch echos
        i=0
        for i in range(3):
            echo = self.parent.serialPort.canReadLine(waitReadyReadTime)
            if echo is not b'':
                break
            logging.debug("read: for iterator: %d",i)
        #echo = self.parent.serialPort.readLine(readLineTime)
        logging.debug("read: %s", echo)
        return echo
           '''
    def resetInitScan(self):
        logging.debug("resetInitScan in mtpmove")
        # Reset initScan logic checks
        self.parent.packetStore.setData("initSwitch", False)
        self.parent.packetStore.setData("init1Received", False)
        self.parent.packetStore.setData("init2Received", False)
        # change led to yellow
        self.parent.scanStatusLED.setPixmap(self.parent.ICON_YELLOW_LED.scaled(40,40))
        # change text on button to "initializing"
        self.parent.reInitProbe.setText("Initializing")
        # set current mode to init 
        self.parent.packetStore.setData("currentMode", "init")
        # Don't call resetInitScan again, unless moved to homeScan
        self.parent.packetStore.setData("firstInit", False)

    def initScan(self):
        if self.parent.packetStore.getData("firstInit"):
            self.resetInitScan()
        # self.parent.app.processEvents()
        # one time sleep, run only when probe is started up or re-initialized
        # time.sleep(0.2)
        logging.debug("initScan in mtpmove")
        echo = self.read(20,20)
        # initSwitch retrieved from instance of storePacket declared in view
        logging.debug("initScan received values 1: %s, 2: %s",self.parent.packetStore.getData("init1Received"),self.parent.packetStore.getData("init2Received"))

        if self.parent.packetStore.getData("init1Received") and self.parent.packetStore.getData("init2Received"):
            logging.debug("Both init commands received, moving on to home")
            # move along and reset init
            self.parent.packetStore.setData("initSwitch", False)
            self.parent.packetStore.setData("switchControl", 'resetHomeScan')
        # otherwise just swap between sending the 2 init commands
        # have to have delay otherwise they collide
        # maybe add timeout?
        initSwitch = self.parent.packetStore.getData("initSwitch")
        logging.debug("initSwitch is: %s" , initSwitch)
        if not initSwitch: 
            logging.debug("init1 sent")
            self.parent.serialPort.sendCommand(self.parent.commandDict.getCommand("init1"))
            # catch echos
            # read until receive a Step
            # if that Step is b'Step:\xff/0@\r\n' set init1Received to true
            # else cycle again
            echo = self.read(100,50)
            logging.debug("init one echo1: %s", echo)
            echo = self.read(100,20)
            logging.debug("init one echo2: %s", echo)
            echo = self.read(20,20)
            logging.debug("init one echo3: %s", echo)
            echo = self.read(20,20)
            logging.debug("init one echo4: %s", echo)
            self.parent.packetStore.setData("initSwitch", False)
        elif initSwitch: 
            logging.debug("init2 sent")
            self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("init2")))
            # catch echos
            echo = self.read(20,20)
            logging.debug("init two echo?: %s", echo)
            echo = self.read(20,20)
            logging.debug("init two echo?: %s", echo)
            self.parent.packetStore.setData("initSwitch", True)
        else:
            logging.debug("initSwitch is something other than true or false: ", initSwitch)
        logging.debug("init done")

    
    def resetHomeScan(self):
        # move all one time resets from homeScan here
        # Resets current clk step counter
        # if this needs to be referenced downstream homescan
        # will need a check to see if it's the first time in here
        # perhaps with a homeSwitch
        self.parent.packetStore.setData("clkStep", 0)
        # any more calls to initScan after this function will
        # now cause initScan to be called
        self.parent.packetStore.setData("firstInit", True)
        # set current mode to home
        self.parent.packetStore.setData("currentMode", "home")
        # Restores original value to initSwitch, resetting it
        self.parent.packetStore.setData("initSwitch", False)
        
       


    def integrate(self):
        logging.debug("integrate")
        # could be timing issue
        # self.parent.app.processEvents()

        # for each current frequency in config NFreq, call tune, then send a count (I 40) command
        if self.parent.packetStore.getData("count2Flag"):
            # for each frequency, but after I has been recorded:
            self.parent.packetStore.setData("count2Flag", False)
            #logging.debug("calling count 2, integrating a second time to get past I response to R response (with actual data) (r\r\n) ")
            # Add space between counts
            # self.eline = QtCore.QByteArray(str.encode(" "))
            ########logic bug
            # shouldn't have 2 append to elines. 
            # self.parent.packetStore.appendData("Eline", self.eline)
            self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("count2")))
        elif self.parent.packetStore.getData("currentFrequency") == 55.51:
            if self.parent.packetStore.getData("tuneSwitch"):
                # logging.debug("tune first frequency")
                self.tune(55.51)
            else:
                self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("count")))
                self.parent.packetStore.setData("integrateSwitch", 56.65)
                # logging.debug("count on first frequency, integrateSwitch = %s", integrateSwitch)
            # logging.debug("frequency 55.51")


        elif self.parent.packetStore.getData("currentFrequency") == 56.65:
            # logging.debug("frequency 56.65")
            if self.parent.packetStore.getData("tuneSwitch"):
                #logging.debug("tune second frequency")
                self.tune(56.65)
            else:
                self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("count")))
                self.parent.packetStore.setData("integrateSwitch", 58.8)
                # logging.debug("count on second frequency")

        elif self.parent.packetStore.getData("currentFrequency") == 58.8:
            # logging.debug("frequency 58.8")
            if self.parent.packetStore.getData("tuneSwitch"):
                # logging.debug("tune third frequency")
                self.tune(58.8)
            else:
                self.parent.packetStore.setData("integrateSwitch", 'done')
                self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("count")))
                # logging.debug("count on second frequency")
        else: 
            #logging.error("unknown frequency in integrate function")
            #logging.error(self.parent.packetStore.getData("currentFrequency"))
            #logging.error(self.parent.packetStore.getData("count2Flag"))
            self.parent.packetStore.setData("integrateSwitch", 'done')
            


    def Aline(self):
        self.parent.app.processEvents()
        # add current iwg values to running average, 
        # send that out instead of instant values 
        # made in goAngle for packetStore.savePacket/sendUDP

        # yyyymmdd hhmmss in udp feed
        # yyyymmdd hh:mm:ss in save feed
        # self.currentDate =  "%s%s%s %s%s%s" %( str(t[0]), str(t[1]), str(t[2]), str(t[3]), str(t[4]), str(t[5]))
        # aline = "A " + self.currentDate
        # Note that if iwg is sending, but pitch and roll are
        # not defined, they will be set to NAN
        # (aka testing on the ground)
        # those will be set to 1 in goAngle
        # but not adjusted for Aline
        try:
            logging.debug("before pitch avg")
            pitchavg = self.parent.packetStore.getData("pitchavg")
            logging.debug("after pitch avg")
            pitchrms = self.parent.packetStore.getData("pitchrms")
            logging.debug("after pitch rms1")
            rollavg = self.parent.packetStore.getData("rollavg")
            logging.debug("after pitch rms2")
            rollrms = self.parent.packetStore.getData("rollrms")
            logging.debug("after pitch rms3")
            Zpavg = self.parent.packetStore.getData("Zpavg")
            logging.debug("after pitch rms4")
            Zprms = self.parent.packetStore.getData("Zprms")
            logging.debug("after pitch rms5")
            oatavg = self.parent.packetStore.getData("oatavg")
            logging.debug("after pitch rms6")
            oatrms = self.parent.packetStore.getData("oatrms")
            logging.debug("after pitch rms7")
            latavg = self.parent.packetStore.getData("latavg")
            logging.debug("after pitch rms8")
            latrms = self.parent.packetStore.getData("latrms")
            logging.debug("after pitch rms9")
            lonavg = self.parent.packetStore.getData("lonavg")
            logging.debug("after pitch rms10")
            lonrms = self.parent.packetStore.getData("lonrms")
            logging.debug("after pitch rms end")
        except Exception as e:
            logging.debug("after pitch rms, in exception")
            logging.error(repr(e))
            logging.error(e.message)
            #logging.error(sys.exe_info()[0])
            logging.error("IWG not detected, using defaults")
            pitchavg = 3 
            pitchrms = 3 
            rollavg = 3 
            rollrms = 3 
            Zpavg = 3 
            Zprms = 3 
            oatavg = 3 
            oatrms = 3 
            latavg = 3 
            latrms = 3 
            lonavg = 3 
            lonrms = 3 
            # set from config file eventually
            # other odd constant is in udp.py -
            # sets the recieved values in iwg line to 0
        else:
            logging.debug("move:else got IWG")
            logging.debug(self.parent.packetStore.iwgStore)


        aline = " " + str(pitchavg)
        aline = aline + " " + str(pitchrms)
        aline = aline + " " + str(rollavg)
        aline = aline + " " + str(rollrms)
        aline = aline + " " + str(Zpavg)
        aline = aline + " " + str(Zprms)
        aline = aline + " " + str(oatavg)
        aline = aline + " " + str(oatrms)
        aline = aline + " " + str(latavg)
        aline = aline + " " + str(latrms)
        aline = aline + " " + str(lonavg)
        aline = aline + " " + str(lonrms)
        aline = aline + " " + str(self.parent.packetStore.getData("scanCount"))
        aline = aline + " " + str(self.parent.packetStore.getData("encoderCount"))
        self.parent.alineStore = aline
        #logging.info(aline)
        '''
        self.pitch_Frame = pitchI # from getIWG 16, deg
        self.roll_Frame = rollI # from get IWG 17, deg
        self.zp = pALTftI # from getIWG[6], ft
        self.oat = OATnavI #from getIWG[20], degrees C 
        self.lat = latI # from getIWG[2],deg 
        self.lon = lonI # fron getIWG[3], deg
        self.scanCount = # from packet store
        self.encoderCount =  # from packet store

        # translate units /
        self.ft_km = 3280.8 # translate from ft to km 
        self.zp = self.zp/self.ft_km
        self.oat = self.oat + 273.15 # to kelvin
        
        
        # implement averaging:
        # from pitch to lon, avg and rms


        # save A line:
        aline = "A " + self.currentDate + self.pitch_Frame + self.roll_Frame + self.zp + self.oat + self.lat + self.lon + self.scanCount + self.encoderCount
        #self.parent.packetStore.setData("Aline", aline)
        '''


        self.parent.packetStore.setData("angleI", 0) # angle index

        self.parent.packetStore.setData("switchControl", "blIne")       
        self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("read_scan")))
        # need to implement the better logic counters in bline
        # for scanCount and encoderCount
        self.parent.packetStore.setData("scanCount", int(self.parent.packetStore.getData("scanCount")) + 1)
        logging.debug("Aline")
        '''
    def blIne(self):
        logging.debug("in Bline")
        # self.parent.app.processEvents()
        # for bli = 1 To Nangle
        # bSwitch iteration starts at 1, because array of data from config includes precurssor Nangle
        # currently should go 0 to 8
        # anglI increases on receipt of done from integratge
        # self.parent.app.processEvents
        self.i = self.parent.packetStore.getData("angleI") # angle index
        #logging.debug("bline %f" , self.i)

        if self.i == 0:
            # first time in loop
            # do housekeeping
            #logging.debug("bline housekeeping")
            self.parent.packetStore.setData("bSwitch", True)
            self.parent.packetStore.setData("bDone", False)
            self.parent.packetStore.setData("calledFrom", 'blIne')
            # reset/clear bline
            self.parent.blineStore = QtCore.QByteArray(str.encode("B "))
            # angleI ++
            self.parent.packetStore.setData("angleI",2) # angle index, zenith at 1
            # self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("read_enc")))
            # Because we don't have a call to the serial port 
            self.parent.cycleTimer.start()
        elif self.i <= self.parent.packetStore.getData("Nangle")+1:
            #logging.debug(self.parent.packetStore.getData("Nangle"))
            
            if self.parent.packetStore.getData("bSwitch"):
                # start true, set to false in goAngle so we only do that once per
                # preferred: self.getAngle(self.parent.config.getData("El. Angles", angleI))
                # MAM goAngle getAngle math switch
                # Here is where we do or do not implement the alternate
                # calculations for correcting the pointing angle
                self.i = self.parent.packetStore.getData("angleI")
                #logging.debug("calling goAngle aka getAngle with %s", self.parent.packetStore.getArray("El. Angles", self.i))
                self.getAngle(self.parent.packetStore.getArray("El. Angles", self.i))
            else:
                #logging.debug("calling b integrate")
                self.integrateSwitch = self.parent.packetStore.getData("integrateSwitch")
                if self.integrateSwitch is "done":
                    # may want to put the angleI stuff here instead of 
                    # in the recieving logic
                    # yes we do
                    # on receipt of the integrate done signal, reset integrate
                    # anglI ++
                    # removed from recieving logic: angleI value
                    if self.i < 12:
                        #logging.debug("angleI value (2-11): %s", str(self.i))
                        self.parent.packetStore.setData("angleI", self.i +1)
                        # Reset integrate in Bline
                        self.parent.packetStore.setData("currentFrequency", 55.51)
                        self.parent.packetStore.setData("integrateSwitch", 55.51)
                        #bug with integrate switch overwriting last done?
                        #logging.debug("resetting integrateSwitch, currentFrequency")
                        
                self.integrate()
        else: 
            # stop/reset logic:
            # should only happen after i = 12
            #logging.debug("setting final done, Bline")
            self.parent.packetStore.setData("bDone", True)
            # self.parent.packetStore.setData("angleI", 2)
            #logging.debug("reset logic for bline") 
        if self.parent.packetStore.getData("bDone"):
            #logging.debug("bDone is true")
            # final housekeeping
            # reset logic for blIne
            self.parent.packetStore.setData("angleI", 0)
            # do something with collected data other than display to screen
            self.saveData()
            logging.info("data Saved")
            # self.sendData()
            #logging.info("data sent UDP: port ")
            self.parent.packetStore.setData("bDone", False)
            self.parent.packetStore.setData("switchControl", "m01")
            # Because we don't have a call to the serial port 
            self.parent.cycleTimer.start()
        else:
            logging.debug("catchall case in bline")


            
        #logging.debug("blIne End")
        '''
    def saveData(self, gmtime, dataFile):
        # self.parent.app.processEvents()
        logging.debug("saving Data to file")

        #t = time.gmtime();
        t = gmtime
        # yyyymmddhhmmss in UDP send feed
        #currentDateUDP =  "%02d%02d%02d%02d%02d%02d," %(t[0], t[1], t[2],t[3], t[4], t[5])

        # yyyymmdd hh:mm:ss in save feed
        currentDateSave =  "%02d%02d%02d %02d:%02d:%02d" %( t[0], t[1], t[2], t[3], t[4], t[5])

        saveData = "A " + currentDateSave + " " + self.parent.alineStore
        saveData = saveData + '\n'
        saveData = saveData + self.parent.iwgStore + '\n'
        saveData = saveData + self.parent.blineStore + '\n'
        saveData = saveData + self.parent.m01Store + '\n'
        saveData = saveData + self.parent.m02Store + '\n'
        saveData = saveData + self.parent.ptStore + '\n'
        saveData = saveData + self.parent.elineStore + '\n'
        logging.debug("saveData %r", saveData)
        # this \n doesn't leave the ^M's
        iwg = self.parent.iwgStore
        #iwg = str(iwg.split(','))
        #iwg = iwg[-1]
        #iwg = ','.join(iwg)
        
        # open file in append not-binary mode
        #with open("MTP_data.txt", "a") as datafile:
        with open(dataFile,"a") as datafile:
            # may need to .append instead of +
            datafile.write("A " + currentDateSave + " " + self.parent.alineStore)
            datafile.write('\r\n')
            datafile.write(iwg)
            #actual iwg packet has \r\n
            #datafile.write('\r\n')
            datafile.write(self.parent.blineStore)
            datafile.write('\r\n')
            datafile.write(self.parent.m01Store)
            datafile.write('\r\n')
            datafile.write(self.parent.m02Store)
            datafile.write('\r\n')
            datafile.write(self.parent.ptStore)
            datafile.write('\r\n')
            datafile.write(self.parent.elineStore)
            datafile.write('\r\n')
            # this \n doesn't leave the ^M's
            datafile.write('\r\n')
        # the send Data should have the repress b' data ' 
        # additions that python adds

        #udpArray = self.formUdp()
        return saveData

    def formUDP(self, gmtime):
        # new udp string
        udpArray =  QtCore.QByteArray(str.encode(""))
        # get time
        #t = time.gmtime();
        t = gmtime
        # yyyymmddhhmmss in UDP send feed
        currentDateUDP =  "%02d%02d%02dT%02d%02d%02d" %(t[0], t[1], t[2],t[3], t[4], t[5])

        udpArray.append("MTP," + currentDateUDP + self.udpFormat(self.parent.alineStore, 'a'))
        udpArray.append(self.udpFormat(self.parent.blineStore, 'b'))
        udpArray.append(self.udpFormat(self.parent.m01Store, 'm'))
        udpArray.append(self.udpFormat(self.parent.m02Store, 'm'))
        udpArray.append(self.udpFormat(self.parent.ptStore, 'p'))
        udpArray.append(self.udpFormat(self.parent.elineStore, 'e'))
        logging.debug(udpArray)
        return udpArray

    def udpFormat(self, arrayToFormat, identifier):
        logging.debug("udpFormater")
        logging.debug(arrayToFormat)
        # remove spaces, add commas, remove a/b/m01:/m02:/pt:/e
        # commas always after, including end line comma
        arrayToFormat = str.replace(arrayToFormat, ' ', ',')
        logging.debug(arrayToFormat)
        end = int(len(arrayToFormat))
        logging.debug(end)
        if identifier == 'm':
            # remove "M0#:"
            arrayToFormat = arrayToFormat[4:end-1]
            return arrayToFormat
        elif identifier == 'a':
            # as is
            return arrayToFormat
        elif identifier == 'b':
            # remove b
            arrayToFormat = arrayToFormat[1:end]
            return arrayToFormat

        elif identifier == 'p':
            # remove p:
            arrayToFormat = arrayToFormat[3:end-1]
            return arrayToFormat

        elif identifier == 'e':
            # remove e
            arrayToFormat = arrayToFormat[1:end]
            return arrayToFormat

        else:
            logging.error('udpFormat, foreign identifier: %f', identifier)


    def getAngle(self, targetEl, zel):
        # changed from goAngle because editor says that would be overriding something
        # though I can't find what or where that would be
        # logging.debug("moveMTP goAngle/getAngle called, targetEl: %s", targetEl)
        logging.debug("Zel to be added to targetEl: %s", zel)
        if self.parent.packetStore.getData("pitchCorrect"):
            logging.info("Correcting Pitch")
            # targetClkAngle = self.configMam()
        else:
            logging.info("Using instantanious MAM")
            targetClkAngle = zel + targetEl

        stepDeg = self.parent.packetStore.getData("stepsDegree") 
        logging.debug("stepDeg: %s", stepDeg)
        targetClkStep = targetClkAngle * stepDeg
        logging.debug("targetClkStep: %s", targetClkStep)

        currentClkStep = self.parent.packetStore.getData("currentClkStep")
        logging.debug("currentClkStep: %s", currentClkStep)
        #self.parent.packetStore.setData("Nsteps", self.targetClkStep - self.parent.packetStore.getData("currentClkStep"))
        # nsteps check here
        nstep = targetClkStep - currentClkStep
        logging.debug("calculated nstep: %r", nstep)
        if nstep == 0:
            logging.info("nstep is zero loop")
            # suspect this occurs when pitch/roll/z are 0
            # need to have a catch case when above are nan's
            return
        # abs( nsteps)  should never be less than 20
        # move to moveScan/ check logic against that
        # save current step so difference is actual step difference 
        self.parent.packetStore.setData("currentClkStep", currentClkStep + int(nstep))
        logging.debug("currentClkStep + nstep: %s ", currentClkStep + int(nstep))

        # drop everything after the decimal point:
        nstepSplit = str(nstep).split('.')
        nstep = nstepSplit[0]
        #logging.debug(" strip nstp of everything after (and including) the decimal point: %s", self.nstepSplit[0])
        # Split '-' off
        #right justify, pad with zeros if necessary to get to 6 numerical values
        if nstep[0] == '-':
            nstepSplit = str(nstep).split('-')
            nstep = nstepSplit[1].rjust(6,'0')
        else:
            nstepSplit = str(nstep).split('+') 
            # this split shouldn't actually do anything
            # other than add continuity to the nsteps
            nstep = nstepSplit[0].rjust(6,'0')
        ''' Shouldn't need mulitple checks for this?
        # preceeded with a + or -
        #logging.debug("unrounded: %s, rounded nstep value to 0, does this get rid of '.' ?: 6.0f", str(self.nstep)) 
        if self.nstep is 0.0:
            logging.error(" moving 0 steps, nstep calculation turned to 0")
            # suspect this occurs when pitch/roll/z are 0
            # need to have a catch case when above are nan's
        '''


        backCommand = nstep + self.parent.commandDict.getCommand("move_end")
        if nstepSplit[0] == '-':
            frontCommand= self.parent.commandDict.getCommand("move_fwd_front")
        else:
            frontCommand = self.parent.commandDict.getCommand("move_bak_front")  

        #self.parent.serialPort.sendCommand(str.encode(self.frontCommand + self.backCommand))
        #self.angleI = self.parent.packetStore.getData("angleI") # angle index, zenith at 1

        return frontCommand + backCommand    

        
    
    def configMAM(self):
        """ 
         Calculates and stores values in mam from yi,pi,ri 
         Initialized MAM in Cycle
         Note: Inst Tilt is in roll axis 
               Inst Azimuth is in yaw axis
               Inst Pitch is in pitch axis, but is included in correction
        These were converted to the U P and R values below by numerically 
        solving equations given at URL: 
        http://mtp.jpl.nasa.gov/notes/pointing/pointing.html
        Note that as of 6/4/2019 this url is defunc, these 
        equations were coppied over from the vb6 pointing.bas
        (currently on github)
        """

        MAM = self.MAM
        
        #specific to NSF HAIPER GV
        # This will change if it changes planes


        yi = -1.600 
        pi = -3.576
        ri = -0.123 
        rpd = 0.0174532925199433    # Radians per degree = arctan(1)/45


        cY = cos(yi * rpd)
        cP = cos(pi * rpd)
        cR = cos(ri * rpd)
        sY = sin(yi * rpd)
        sP = sin(pi * rpd)
        sR = sin(ri * rpd)

        MAM[0][0] = cP * cY
        MAM[0][2] = -cP * sY
        MAM[0][2] = sP
        MAM[1][0] = sR * sP * cY + cR * sY
        MAM[1][1] = -sR * sP * sY + cR * cY
        MAM[1][2] = -sR * cP
        MAM[2][0] = -cR * sP * cY + sR * sY
        MAM[2][1] = cR * sP * sY + sR * cY
        MAM[2][2] = cR * cP
        self.MAM = MAM
        return


    def fEc(self, pitch, roll, Elevation, EmaxFlag):
        # Pitch and roll can be either by frame (post) or instantaneous (realtime)
        """ Needed by goAngle in cycle in move.py """
        # Calculate commanded elevation angle needed to be at a specified
        # elevation angle (Elevation) with respect to the horizon
        #
        # MJ Mahoney, November 19, 2002
        # Enter with MTP Attitude Matrix MAM, aircraft Pitch and Roll in degrees, 
        # and desired elevation angle wrt to horizon.
        #
        # Return with commanded elevation angle
        # if Elevation = 180 degrees, the returned value will be the target position
        # In this case the pitch and roll values are irrelevant
        # Excel spreadsheet shows that LHS and RHS are the only 
        # difference in solutions
        

        print("testfECprint")
        # Then fEc = 180#: Return
        if Elevation == 180: 
            return 180
        MAM = self.MAM

        rpd = atan(1) / 45#       'Radians per degree 3.14159265358979

        # convert
        P = pitch * rpd
        R = roll * rpd
        E = Elevation * rpd

        cP = cos(P)
        sP = sin(P)
        cR = cos(R)
        sR = sin(R)
        sE = sin(E)
        alpha = -cR * sP * MAM[0][0] + sR * MAM[1][0] + cR * cP * MAM[2][0]
        beta = -1 * (-cR * sP * MAM[0][2] + sR * MAM[1][2] + cR * cP * MAM[2][2])

        A = alpha * alpha + beta * beta
        B = 2 * sE * beta
        C = sE * sE - alpha * alpha
        Arg = B * B - 4 * A * C

        if alpha == 0:
            if beta > 0: 
                Ec_at_Emax = 90
            else:
                Ec_at_Emax = -90
        else:
            Ec_at_Emax = atan(beta / alpha) / rpd

        # VB6 has a less accurate, but presumably faster ASN function for arcsin
        E_max = -asin(alpha * cos(Ec_at_Emax * rpd) + beta * sin(Ec_at_Emax * rpd))
        Emax = E_max / rpd #Always + since it is maximum elevation angle
        #Debug.Print alpha; beta; Ec_at_Emax; alpha * cos(Ec_at_Emax) + beta * sin(Ec_at_Emax)
        Ep90 = abs(-asin(beta) / rpd)
        Em90 = -Ep90
        E_Ec_0 = -asin(alpha) / rpd  #Elevation at which Ec=0

        EmaxFlag = False
        
        # The WB aircraft option has a special case here in the VB6 code
        if abs(Elevation) > abs(Emax): #Go to highest or lowest elevation angle possible
            EmaxFlag = True
            if E_Ec_0 >= 0:
                if Elevation >= 0:
                    fEc = Ec_at_Emax
                else:
                    fEc = Ec_at_Emax - 180
            else:
              if Elevation >= 0:
                  fEc = 180 + Ec_at_Emax
              else:
                  fEc = Ec_at_Emax
        else:
            if Arg < 0:
                Arg = 0
                # next two lines ambiguously indented in vb6
                fEc1 = asin((-B - sqrt(Arg)) / (2 * A)) / rpd
                fEc2 = asin((-B + sqrt(Arg)) / (2 * A)) / rpd
                if E_Ec_0 < 0:
                    # logical equivalent of Vb6 that follows 
                    if Elevation >= E_Ec_0 and Elevation >= Ep90:
                        fEc = 180 - fEc2
    
                    else:
                        fEc = fEc2
                      
                    ''' VB6 
                   If Elevation < E_Ec_0 Then
                       fEc = fEc2       '180 - fEc1
                   Else
                    Select Case Elevation
                    Case Is >= Ep90
                        fEc = 180 - fEc2
                    Case Is >= -Emax
                        fEc = fEc2
                    Case Else
                        fEc = fEc2
                    End Select
                  End If
                    '''
                  
                else:
                    if Elevation >= E_Ec_0:
                        # Vb6 - man pages suggest the last 4 lines won't be executed
                        '''
                      Select Case Elevation
                      Case Is >= Emax: fEc = fEc1
                      Case Else:  fEc = fEc1
                      End Select
                      
                      Case Is >= Em90: fEc = fEc1
                      Case Is > -Emax: fEc = -180 - fEc1
                      Case Else: fEc = Ec_at_Emax - 180
                      End Select
                        '''
                        #if Elevation >= Emax:
                        fEc = fEc1
            print(fEc)            
            return fEc

    def decode(self, line):
        # decode M01, m02, Pt
        # translates from binary string into ascii
        # and loops over hex values recieved from probe 
        # changing them to decimal
        logging.debug('decode')
        data = line.data().decode()
        data = data.split(' ')
        #data = data.split(' ')
        tmp = data[0].split(':')
        for i in data:
            print('decodetest')
            if i == data[0]:
                # reset the dataArray with first equal
                stringData = str(tmp[0]) + ": " + str(int(str(tmp[1]),16)) + " "
                logging.debug("decode m01, m02, Pt")
                #dataArray.append(str(int(str(tmp[1]).decode('ascii'),16)))
                #dataArray.append(str.encode(' '))
            else:
                if i == '\r\n':
                    stringData + '\r\n'
                elif i == '':
                    stringData
                elif i == '\r':
                    stringData
                else:
                    stringData = stringData + str(int(i,16)) + ' '
            logging.debug(" data i = %s ", i)
        return stringData
