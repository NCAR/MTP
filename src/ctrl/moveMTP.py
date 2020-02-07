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
import math
import logging
import time
from PyQt5 import QtCore

class moveMTP():
    
    
    def __init__(self, parent):
        varDict = {
            'Cycling': False,    
            'lastSky': -1, #readScan sets this to actual 
        }
        self.parent = parent
        self.vars = varDict 
    

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

    def initScan(self):
        ''' copy from view '''
        # change led to yellow
        # change text on button to "initializing"


        # set current mode to init 
        self.parent.packetStore.setData("currentMode", "init")
        self.parent.app.processEvents
        # one time sleep, run only when probe is started up or re-initialized
        time.sleep(0.2)
        self.parent.app.processEvents()
        logging.debug("initScan in mtpmove")
        # initSwitch retrieved from instance of storePacket declared in view
        if (self.parent.packetStore.getData("initSwitch")):
            self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("init2")))
            logging.debug("move cycle2")
        else:
            logging.debug("move cycle1")
            self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("init1")))

    def homeScan(self):
        # self.parent.packetStore.setData("currentMode", False)

        # Resets current clk step counter
        # if this needs to be referenced downstream homescan
        # will need a check to see if it's the first time in here
        # perhaps with a homeSwitch
        self.parent.packetStore.setData("clkStep", 0)
        
        # set current elevation angle to elAngle(0)


        # make cycle timer sleep longer?
        # cycle timer should make this irrelevant
        # time.sleep(0.4) # to add up to the 0.7 of movWait in vb6
        self.parent.app.processEvents()



        if self.parent.packetStore.getData("homeSwitch"):
            # sets current mode to desired Mode if both homeSwitch and scanSet are true
            if self.parent.packetStore.getData("scanSet"):
                #self.parent.packetStore.setData("currentMode", self.parent.packetStore.getData("desiredMode"))
                #logging.debug("setitng current mode to desired mode")
    
                if self.parent.packetStore.getData("desiredMode") is "init":
                    # Sends final home packet only in init mode
                    # and only after the rest of the home scan is done
                    self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("home3")))
                    logging.debug("sending home3 command")
            else: 
                # homeSwitch is false, so send home2
                # if recieved status of 1 since home 1 was sent (setting homeSwitch to true)
                # send home2
                self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("home2")))
                logging.debug("sending home2 command")

        else:
            # send home1
            self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("home1")))
            logging.debug(" sending home1 command")
            # try and minimize time spent blocking here, though waiting for correct home response
            # need to test to see if it works
            for i in range(0, 0.7, 0.1):
                self.parent.app.processEvents()
                time.sleep(0.01)
            #time.sleep(0.7)
            #self.parent.app.processEvents
            # one time actions
            if self.parent.packetStore.getData("currentMode") is not "home":
                # set current mode to home
                self.parent.packetStore.setData("currentMode", "home")
                # Restores original value to initSwitch, resetting it
                self.parent.packetStore.setData("initSwitch", False)
                # reads in last scan (location? value?)
                # not sure this is used for anything
                # will keep commented out unless eline or bline use it
                # if uncommented: note the homescan recieve will need to have one extra flag
                # and an extra conditional for the returned read_scan step
                #self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("read_scan")))
        logging.debug("homeScan")
        # there may be other final looping stuff that needs to happen here


    def m01(self):
        # send command M1
        logging.debug("in m01")
        self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("read_M1")))
        logging.debug("in m01")
        self.parent.app.processEvents()
        logging.debug("sending m01")

    def m02(self):
        # send command M2
        self.parent.app.processEvents()
        self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("read_M2")))
        logging.debug("sending m02")

    def pt(self):
        # send command Pt
        self.parent.app.processEvents()
        self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("read_P")))
        logging.debug("sending pt")



    def Eline(self):
        logging.debug("Eline")
        self.parent.app.processEvents()

        if self.parent.packetStore.getData("calledFrom") is "Eline":
            if self.parent.packetStore.getData("integrateSwitch") is "done":
                # Check if we continue to cycling
                if self.parent.packetStore.getData("doneCycle"):
                    #logging.debug("Eline, doneCycle true")
                    self.parent.packetStore.setData("isNoiseZero", False)

                    if self.parent.packetStore.getData("isCycling"):
                        self.parent.probeStatusLED.setPixmap(self.parent.ICON_GREEN_LED.scaled(40,40))
                        self.parent.scanStatusLED.setPixmap(self.parent.ICON_GREEN_LED.scaled(40,40))
                        self.parent.packetStore.setData("switchControl", "Aline")

                    else:
                        # stop cycling
                        self.parent.probeStatusLED.setPixmap(self.parent.ICON_GREEN_LED.scaled(40,40))
                        self.parent.scanStatusLED.setPixmap(self.parent.ICON_GREEN_LED.scaled(40,40))
                        self.parent.packetStore.setData("switchControl", "Aline")
                        #logging.debug("ending init stage - should go into save/stop cycle here")
                        # Stop 
                        self.parent.cycleTimer.stop()
                        # or if we set green light on status
                        # scan button to ready
                        # and init button to re-init
                # reset integrate
                self.parent.packetStore.setData('currentFrequency', 55.51)
                # self.parent.packetStore.setData('isNoiseZero', True)
                self.parent.packetStore.setData('integrateSwitch', 55.51)
                # next time in here we finish
                self.parent.packetStore.setData('doneCycle', True)
                self.parent.packetStore.setData("isNoiseZero", True)

            if self.parent.packetStore.getData("isNoiseZero"):
                # check that noise is 0, if not set it to that
                # note that we're checking the dictionary value, not the probe here
                # dictionary value has default of -1
                if self.parent.packetStore.getData("noise") == str.encode("ND:00\r\n"):
                    # do integrate
                    #logging.debug("do integrate on noise 0")
                    self.integrate()
                else:
                    self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("noise0")))
                    #logging.debug("sending set noise 0, second of noise commands")



            else:
                # check that noise is 1, if not set it to that
                # does this first, Then integrates on noise 0
                # First do the integrate with noise 1, then noise 0
                
                if self.parent.packetStore.getData("noise") == str.encode("ND:01\r\n"):
                    #logging.debug("do integrate on noise 1")
                    self.integrate()
                else: 
                    self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("noise1")))
                    #logging.debug("sending set noise 1, first of noise commands")
                    #logging.debug("encoding check: noise: %s, encoder: %s", self.parent.packetStore.getData("noise"), str.encode("N :01"))



        elif self.parent.packetStore.getData("calledFrom") is not "Eline":
            # one time actions

            # set current mode to home
            self.parent.packetStore.setData("calledFrom", "Eline")
            
            # on second+ full call to eline, need to reset ElineSwitch
            self.parent.packetStore.setData("isNoiseZero", False) 
            
            # Restores original values for homeScan, resetting it
            self.parent.packetStore.setData("homeSwitch", False)
            self.parent.packetStore.setData("scanSet", False)
            
            # clear data stored in packetStore.integrateData from previous call
            self.eline = QtCore.QByteArray(str.encode("E "))
            self.parent.packetStore.setData("Eline", self.eline)
            self.parent.packetStore.setData('currentFrequency', 55.51)
            self.parent.packetStore.setData("doneCycle", False)

            self.parent.packetStore.setData("integrateData", "")

            # Because we don't have a call to the serial port 
            self.parent.cycleTimer.start()

            # should do a homescan here, then return


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
                integrateSwitch = self.parent.packetStore.getData("integrateSwitch")
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






    def tune(self, fghz):
        self.parent.app.processEvents()
        # fghz is frequency in gigahertz
        fby4 = (1000 * fghz)/4 #MHz
        chan = fby4/0.5  # convert to SNP channel (integer) 0.5 MHz = step size
        #logging.debug("tune: chan = %s", chan)
        
        # either 'C' or 'F' set in packetStore
        # F mode formatting #####.# instead of cmode formatting #####
        # not sure it makes a difference

        # mode = self.parent.packetStore.getData("tuneMode")

        mode = 'C'
        self.parent.serialPort.sendCommand(str.encode(str(mode) + '{:.5}'.format(str(chan)) +"\r")) # \n added by encode I believe
        #logging.debug("Tuning: currently using mode C as that's what's called in vb6")
        # no official response, just echos
        # and echos that are indistinguishable from each other
        # eg: echo when buffer is sending to probe is same 
        # as echo from probe: both "C#####\r\n"
        self.parent.packetStore.setData("tuneSwitch", False)







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
        aline = " " + str(self.parent.packetStore.getData("pitchavg"))
        aline = aline + " " + str(self.parent.packetStore.getData("pitchrms"))
        aline = aline + " " + str(self.parent.packetStore.getData("rollavg"))
        aline = aline + " " + str(self.parent.packetStore.getData("rollrms"))
        aline = aline + " " + str(self.parent.packetStore.getData("Zpavg"))
        aline = aline + " " + str(self.parent.packetStore.getData("Zprms"))
        aline = aline + " " + str(self.parent.packetStore.getData("oatavg"))
        aline = aline + " " + str(self.parent.packetStore.getData("oatrms"))
        aline = aline + " " + str(self.parent.packetStore.getData("latavg"))
        aline = aline + " " + str(self.parent.packetStore.getData("latrms"))
        aline = aline + " " + str(self.parent.packetStore.getData("lonavg"))
        aline = aline + " " + str(self.parent.packetStore.getData("lonrms"))
        aline = aline + " " + str(self.parent.packetStore.getData("scanCount"))
        aline = aline + " " + str(self.parent.packetStore.getData("encoderCount"))
        self.parent.packetStore.setData("Aline", aline)
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

        # translate units 
        self.ft_km = 3280.8 # translate from ft to km 
        self.zp = self.zp/self.ft_km
        self.oat = self.oat + 273.15 # to kelvin
        
        
        # implement averaging:
        # from pitch to lon, avg and rms


        # save A line:
        aline = "A " + self.currentDate + self.pitch_Frame + self.roll_Frame + self.zp + self.oat + self.lat + self.lon + self.scanCount + self.encoderCount
        self.parent.packetStore.setData("Aline", aline)
        '''


        self.parent.packetStore.setData("angleI", 0) # angle index
        self.parent.app.processEvents

        self.parent.packetStore.setData("switchControl", "blIne")       
        self.parent.serialPort.sendCommand(str.encode(self.parent.commandDict.getCommand("read_scan")))
        # need to implement the better logic counters in bline
        # for scanCount and encoderCount
        self.parent.packetStore.setData("scanCount", int(self.parent.packetStore.getData("scanCount")) + 1)
        logging.debug("Aline")

    def blIne(self):
        logging.debug("in Bline")
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
            self.bline = QtCore.QByteArray(str.encode("B "))
            self.parent.packetStore.setData("Bline", self.bline)
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

    def saveData(self):
        logging.debug("saving Data to file")
        # clear udp string
        self.udpArray =  QtCore.QByteArray(str.encode(""))
        # store everything locally
        aline = self.parent.packetStore.getData('Aline')
        t = time.gmtime();
        # yyyymmdd hhmmss in udp feed for backwards compatability
        # yyyymmdd hh:mm:ss in save feed
        self.currentDateUDP =  "%02d%02d%02d %02d%02d%02d" %(t[0], t[1], t[2],t[3], t[4], t[5])
        self.currentDateSave =  "%02d%02d%02d %02d:%02d:%02d" %( t[0], t[1], t[2], t[3], t[4], t[5])
        # aline = "A " + self.currentDate
        self.udpArray.append("A " + self.currentDateUDP + " " + self.aline)
        self.iwg = self.parent.packetStore.getData('IWG')
        self.udpArray.append(self.iwg)
        self.bline = self.parent.packetStore.getData('Bline')
        self.udpArray.append(self.bline)
        m01 = self.parent.packetStore.getData('M01')
        self.udpArray.append(m01)
        m02 = self.parent.packetStore.getData('M02')
        self.udpArray.append(m02)
        pt = self.parent.packetStore.getData('Pt')
        self.udpArray.append(pt)
        self.eline = self.parent.packetStore.getData('Eline')
        self.udpArray.append(self.eline)
        if self.bline.size > 30:
            logging.info("bline size larger than expected (30): %s", self.bline.size)
        if self.eline.size > 06:
            logging.info("eline size larger than expected (06): %s", self.bline.size)
        # open file in append binary mode
        with open("MTP_data.txt", "ab") as datafile:
            # may need to .append instead of +
            datafile.write(str.encode("A " + self.currentDateSave + " " + self.aline))
            datafile.write(str.encode('\n'))
            datafile.write(self.iwg)
            datafile.write(self.bline)
            datafile.write(str.encode('\n'))
            datafile.write(m01)
            datafile.write(m02)
            datafile.write(pt)
            datafile.write(self.eline)
            datafile.write(str.encode('\n'))
            # this \n doesn't leave the ^M's
            datafile.write(str.encode('\n'))
        # the send Data should have the repress b' data ' 
        # additions that python adds
        self.sendData(self.udpArray)


    def sendData(self, udpData):
        logging.debug("sendingDataUDP")

    def getAngle(self, targetEl):
        # changed from goAngle because editor says that would be overriding something
        # though I can't find what or where that would be
        # logging.debug("moveMTP goAngle/getAngle called, targetEl: %s", targetEl)
        self.zel = self.parent.packetStore.getArray("El. Angles", 1) # current array has total number in array at zero, zenith/fiduciary (?) at 1 and actual angles after that. 
        # logging.debug("Zel to be added to targetEl: %s", self.zel)
        if self.parent.packetStore.getData("pitchCorrect"):
            logging.info("Correcting Pitch")
            # targetClkAngle = self.configMam()
        else:
            logging.info("Using instantanious MAM")
            self.targetClkAngle = self.zel + targetEl

        self.sD = self.parent.packetStore.getData("stepsDegree") 
        #logging.debug("stepDeg: %s", self.sD)
        self.targetClkStep = self.targetClkAngle * self.sD
        #logging.debug("targetClkStep: %s", self.targetClkStep)

        self.currentClkStep = self.parent.packetStore.getData("currentClkStep")
        #logging.debug("currentClkStep: %s", self.currentClkStep)
        self.parent.packetStore.setData("Nsteps", self.targetClkStep - self.parent.packetStore.getData("currentClkStep"))
        # nsteps check here
        
        self.nstep = self.parent.packetStore.getData("Nsteps")
        if self.nstep == 0:
            logging.info("nstep is zero loop")

        # drop everything after the decimal point:
        self.nstepSplit = str(self.nstep).split('.')
        self.nstep = self.nstepSplit[0]
        #logging.debug(" strip nstp of everything after (and including) the decimal point: %s", self.nstepSplit[0])
        if self.nstep[0] is '-':
            self.nstepSplit = str(self.nstep).split('-')
            self.nstep = self.nstepSplit[1].rjust(6,'0')
        else:
            self.nstepSplit = str(self.nstep).split('+') 
            # this split shouldn't actually do anything
            # other than add continuity to the nsteps
            self.nstep = self.nstepSplit[0].rjust(6,'0')
        # pad with zeros if necessary to get to 6 numerical values

        # preceeded with a + or -
        #logging.debug("unrounded: %s, rounded nstep value to 0, does this get rid of '.' ?: 6.0f", str(self.nstep)) 
        if self.nstep is 0.0:
            logging.error(" moving 0 steps, nstep calculation turned to 0")
            # suspect this occurs when pitch/roll/z are 0
            # need to have a catch case when above are nan's

        # abs( nsteps)  should be less than 20
        # move to moveScan/ check logic against that
        self.backCommand = self.nstep + self.parent.commandDict.getCommand("move_end")
        if self.nstepSplit[0] is '-':
            self.frontCommand= self.parent.commandDict.getCommand("move_bak_front")
        else:
            self.frontCommand = self.parent.commandDict.getCommand("move_fwd_front")  
        # return should have switch value of "Step:"
        self.parent.serialPort.sendCommand(str.encode(self.frontCommand + self.backCommand))
        self.parent.packetStore.setData("targetClkStep", self.targetClkStep)
        # self.parent.packetStore.setData("currentClkStep", self.targetClkStep)
        # set in serial to avoid infinite loop of zero nstep
        self.angleI = self.parent.packetStore.getData("angleI") # angle index, zenith at 1
        #moveDone flag?

    
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

        yi = self.getConfig(OffsetYi)
        pi = self.getConfig(OffsetPi)
        ri = self.getConfig(OffsetRi)
        rpd = 0.0174532925199433    # Radians per degree = arctan(1)/45


        cY = cos(yi * rpd)
        cP = cos(pi * rpd)
        cR = cos(ri * rpd)
        sy = sin(yi * rpd)
        sP = sin(pi * rpd)
        sR = sin(ri * rpd)
        
        self.setMAM(1, 1, cP * cY)
        self.setMAM(1, 2, -cP * sY)
        self.setMAM(1, 3, sP)
        self.setMAM(2, 1, sR * sP * cY + cR * sY)
        self.setMAM(2, 2, -sR * sP * sY + cR * cY)
        self.setMAM(2, 3, -sR * cP)
        self.setMAM(3, 1, -cR * sP * cY + sR * sY)
        self.setMAM(3, 2, cR * sP * sY + sR * cY)
        self.setMAM(3, 3, cR * cP)
        return

    def fSc(self):
        """ Given the commanded elevation angle (Ec) this routine should return the desired
' elevation angle (Elevation) with respect to the horizon.
' It is a check that the correct Ec value was calculated by fEc
'
' MJ Mahoney, January 10, 2002
' Enter with MTP Attitude Matrix MAM, aircraft Pitch and Roll in degrees, and
' commanded elevation angle wrt to horizon.
'
' Return with desired elevation angle

' rpd = Atn(1) / 45#      'Radians per degree

' Convert angle from degrees to radians
  """
        P = Pd * rpd
        R = Rd * rpd
        E = Ec * rpd

        cP = cos(P)
        sP = sin(P)
        cR = cos(R)
        sR = sin(R)

        alpha = -cR * sP * self.setMAM(1, 1) + sR * self.setMAM(2, 1) + cR * cP * self.setMAM(3, 1)
        beta = -1 * (-cR * sP * self.setMAM(1, 3) + sR * self.setMAM(2, 3) + cR * cP * self.setMAM(3, 3))
        fSe = -ASN(alpha * cos(E) + beta * sin(E)) / rpd

    def fEc(self):
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
        
        # Then fEc = 180#: Return
        if Elevation is 180: 
            return 180

        # rpd = Atn(1) / 45#       'Radians per degree 3.14159265358979

        P = Pd * rpd
        R = Rd * rpd
        E = Elevation * rpd

        cP = cos(P)
        sP = sin(P)
        cR = cos(R)
        sR = sin(R)
        sE = sin(E)
        alpha = -cR * sP * self.getMAM(1, 1) + sR * self.getMAM(2, 1) + cR * cP * self.getMAM(3, 1)
        beta = -1 * (-cR * sP * self.getMAM(1, 3) + sR * self.getMAM(2, 3) + cR * cP * self.getMAM(3, 3))

        A = alpha ^ 2 + beta ^ 2
        B = 2 * sE * beta
        C = sE ^ 2 - alpha ^ 2
        Arg = B ^ 2 - 4 * A * C

        if alpha is 0:
            if beta > 0: 
                Ec_at_Emax = 90
            else:
                Ec_at_Emax = -90
        else:
            Ec_at_Emax = Atn(beta / alpha) / rpd

        E_max = -ASN(alpha * cos(Ec_at_Emax * rpd) + beta * sin(Ec_at_Emax * rpd))
        Emax = E_max / rpd #Always + since it is maximum elevation angle
        #Debug.Print alpha; beta; Ec_at_Emax; alpha * cos(Ec_at_Emax) + beta * sin(Ec_at_Emax)
        Ep90 = abs(-ASN(beta) / rpd)
        Em90 = -Ep90
        E_Ec_0 = -ASN(alpha) / rpd  #Elevation at which Ec=0

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
                fEc1 = ASN((-B - sqrt(Arg)) / (2 * A)) / rpd
                fEc2 = ASN((-B + sqrt(Arg)) / (2 * A)) / rpd
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
            return fEc
'''
    def ASN(self, x):
        # Take arcsine of a number
        # Valid only for +- 90 degrees

        # note that both math and numpy libs have an arcsin()
        # and an arctan() incedentally. Going with current 
        # functions for reproducability
        
        if abs(x) > 0.99999:
            ASN = x * 3.14159 / 2 
        else:
            ASN = arctan(x / sqrt(1 - x ^ 2))
        return ASN
'''
