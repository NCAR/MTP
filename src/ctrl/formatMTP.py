###############################################################################
# Class for all the formatting to change the probe responses into counts
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
from math import pow, log
from PyQt5 import QtCore
from EOLpython.Qlogger.messageHandler import QLogger as logger

class formatMTP():
    
    
    def __init__(self, parent):
        varDict = {
            'Cycling': False,    
            'lastSky': -1, #readScan sets this to actual 
        }
        self.vars = varDict 
        self.parent = parent

    def Aline(self):
        # Aline shouldn't have the savefile stuff. 

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
        '''
        try:
            logger.printmsg("debug", "before pitch avg")
            pitchavg = self.parent.packetStore.getData("pitchavg")
            logger.printmsg("debug", "after pitch avg")
            pitchrms = self.parent.packetStore.getData("pitchrms")
            logger.printmsg("debug", "after pitch rms1")
            rollavg = self.parent.packetStore.getData("rollavg")
            logger.printmsg("debug", "after pitch rms2")
            rollrms = self.parent.packetStore.getData("rollrms")
            logger.printmsg("debug", "after pitch rms3")
            Zpavg = self.parent.packetStore.getData("Zpavg")
            logger.printmsg("debug", "after pitch rms4")
            Zprms = self.parent.packetStore.getData("Zprms")
            logger.printmsg("debug", "after pitch rms5")
            oatavg = self.parent.packetStore.getData("oatavg")
            logger.printmsg("debug", "after pitch rms6")
            oatrms = self.parent.packetStore.getData("oatrms")
            logger.printmsg("debug", "after pitch rms7")
            latavg = self.parent.packetStore.getData("latavg")
            logger.printmsg("debug", "after pitch rms8")
            latrms = self.parent.packetStore.getData("latrms")
            logger.printmsg("debug", "after pitch rms9")
            lonavg = self.parent.packetStore.getData("lonavg")
            logger.printmsg("debug", "after pitch rms10")
            lonrms = self.parent.packetStore.getData("lonrms")
            logger.printmsg("debug", "after pitch rms end")
        except Exception as e:
            logger.printmsg("debug", "after pitch rms, in exception")
            # should be error or warning (next 4)
            logger.printmsg("debug", repr(e))
            #logger.printmsg("debug", e.message)
            #logger.printmsg("debug", sys.exe_info()[0])
            logger.printmsg("debug", "IWG not detected, using defaults")
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
            logger.printmsg("debug", "move:else got IWG")
            logger.printmsg("debug", self.parent.packetStore.getData("iwgStore"))


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
        # Neither of these two are currently being queried from probe
        # scanCount may have been implemented in model.py updateRead
        # encoderCount isn't actually useful info because the motor 
        # is attached to a chain, making the position of the motor not related
        # to the position of the mirror.
        # This is perhaps how the VB6 previously got away with the 
        # synthesyser being out of lock, but since NCAR's MTP has always had the 
        # chain (? verify) this may be speculation
        aline = aline + " " + str(self.parent.packetStore.getData("scanCount"))
        aline = aline + " " + str(self.parent.packetStore.getData("encoderCount"))
        
        # need to implement the better logic counters in bline
        # for scanCount and encoderCount
        self.parent.packetStore.setData("scanCount", int(self.parent.packetStore.getData("scanCount")) + 1)
        logger.printmsg("debug", "Aline")
        return aline

    def saveData(self, gmtime, dataFile):
        # self.parent.app.processEvents()
        logger.printmsg("debug", "saving Data to file")

        #t = time.gmtime();
        t = gmtime
        # yyyymmddhhmmss in UDP send feed
        #currentDateUDP =  "%02d%02d%02d%02d%02d%02d," %(t[0], t[1], t[2],t[3], t[4], t[5])

        # yyyymmdd hh:mm:ss in save feed
        currentDateSave =  "%02d%02d%02d %02d:%02d:%02d" %( t[0], t[1], t[2], t[3], t[4], t[5])

        saveData = "A " + currentDateSave + " " + self.parent.alineStore
        saveData = saveData + '\n'
        saveData = saveData + self.parent.packetStore.getData("iwgStore") + '\n'
        saveData = saveData + self.parent.blineStore + '\n'
        saveData = saveData + self.parent.m01Store + '\n'
        saveData = saveData + self.parent.m02Store + '\n'
        saveData = saveData + self.parent.ptStore + '\n'
        saveData = saveData + self.parent.elineStore + '\n'
        logger.printmsg("debug", "saveData %r", saveData)
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
        logger.printmsg("debug", udpArray)
        return udpArray

    def udpFormat(self, arrayToFormat, identifier):
        logger.printmsg("debug", "udpFormater")
        logger.printmsg("debug", arrayToFormat)
        # remove spaces, add commas, remove a/b/m01:/m02:/pt:/e
        # commas always after, including end line comma
        arrayToFormat = str.replace(arrayToFormat, ' ', ',')
        logger.printmsg("debug", arrayToFormat)
        end = int(len(arrayToFormat))
        logger.printmsg("debug", end)
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
            # should log as error
            logger.printmsg("debug", 'udpFormat, foreign identifier: %f', identifier)

    def decode(self, line):
        # decode M01, m02, Pt
        # translates from binary string into ascii
        # and loops over hex values recieved from probe 
        # changing them to decimal
        # This will definitely need revisiting with move replace.
        logger.printmsg("debug", 'decode')
        data = line.data().decode()
        # Strips of \r\n from end, 
        tmp = data.split('\r\n')
        # Catches M 1\r\nM01: squish
        if  len(tmp) >2:
            biggest = 0
            biggestdata = tmp[0]
            for i in tmp:
                size = len(i)
                if size>biggest:
                    biggestdata = i
            data = biggestdata       

        data = data.split(' ')
        #data = data.split(' ')
        tmp = data[0].split(':')
        ifM02tsynth = data[7]
        for i in data:
            if i == data[0]:
                # reset the dataArray with first equal
                nameOfLine = str(tmp[0])
                stringData = nameOfLine + ": " + str(int(str(tmp[1]),16)) + " "

                logger.printmsg("debug", "decode m01, m02, Pt")
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
                    if nameOfLine == "M02":
                        if i == ifM02tsynth:
                            self.checkOverheat(str(int(ifM02tsynth,16)))

            logger.printmsg("debug", " data i = %s ", i)
        return stringData

    def checkOverheat(self, value):
        # Check M02 last value = tsynth
        # Might be better to put this in formatMTP?
        logger.printmsg("debug", "Checking overheat")
        A = 0.0009376
        B = 0.0002208
        C = 0.0000001276
        logger.printmsg("debug", "Overheat value = " + str(value))
        if value == 4096 or value == 0:
            logger.printmsg("debug", "Check overheat, value = 4096 or 0")
            # set overHeatLED to yellow
            self.parent.controlWindow.setLEDyellow(self.parent.controlWindow.overHeatLED)
        else:
            counts = 4096.0 - float(value)
            RR = (1.0/(counts/4096.0)) - 1.0
            RT = 34800.0 * RR
            TSynth = (1.0/(A + B * log(RT) + C * pow(log(RT), 3)) - 273.16)
            # check that tsynth<50C

            if TSynth >= 50:
                # set overHeatLED to RED
                self.parent.controlWindow.setLEDred(self.parent.controlWindow.overHeatLED)
                # Stopping program if tsynth is to high is preferred?
                # Otherwise make debug
                logger.printmsg("warning", "TEMPERATURE OVER 50C")
            else:
                # set overHeatLED to green
                self.parent.controlWindow.setLEDgreen(self.parent.controlWindow.overHeatLED)


            logger.printmsg("debug", "Check overheat, value =" + str(TSynth))

