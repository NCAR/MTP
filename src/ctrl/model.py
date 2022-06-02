from ctrl.lib.mtpcommand import MTPcommand
from ctrl.lib.udp import doUDP
from ctrl.moveMTP import moveMTP
from ctrl.formatMTP import formatMTP
from EOLpython.Qlogger.messageHandler import QLogger as logger
import time


# keeps the mainloop, references to things to store
# acutal code that talks to the probe/wait for responses
# is in move MTP, formatthing the returned code/saving/sending
# is in format MTP
class modelMTP():

    # self, MTPdict with iwg(has save) dict ,config dict, serialport)
    def __init__(self, controlWindow, serialPort, configStore,
            dataFile, IWGFile, tempData, gui):
        super().__init__()
        varDict = {
            'Cycling': False,
            'lastSky': -1,  # readScan sets this to actual
        }
        self.controlWindow = controlWindow
        self.dataFile = dataFile
        self.IWGFile = IWGFile
        # Passing instance of command dictionary
        self.commandDict = MTPcommand()
        # Passing instance of UDP (IWG1, send and receive)
        self.udp = doUDP(self, controlWindow, IWGFile)
        # Passing instance of packet store
        self.packetStore = tempData
        # Passing instance of serialPort
        self.serialPort = serialPort
        # Passing instance of moveMTP class
        self.mover = moveMTP(self, serialPort)
        # Passing instance of configStore
        self.configStore = configStore
        # Passing instance of formatMTP 
        self.formatMTP = formatMTP(self)
        # pointing is initialized in moveMTP
        # Default GUI to true, from args
        self.gui = gui

    def readClear(self, waitReadyReadTime, readLineTime):
        # clear a buffer, discarding whatever is in it
        # will read until either the buffer is empty
        # or it finds a \n, whichever is first
        self.serialPort.readLine(readLineTime)
        if self.serialPort.canReadLine(readLineTime):
            self.serialPort.readLine(readLineTime)

    def read(self, waitReadyReadTime, readLineTime):
        logger.printmsg("debug",
                'waitreadyreadtime = %f', waitReadyReadTime)
        return self.serialPort.canReadLine(readLineTime)

    # will need dataFile, configs and others passed in
    def mainloop(self, isScanning):
        # instantiate dict for commands

        logger.printmsg("debug", "1: mainloop")
        self.controlWindow.iwgProcessEvents()

        self.mover.initProbe()
        # move home is part of initProbe now
        self.continueCycling = True
        previousTime = time.perf_counter()
        self.cyclesSinceLastStop = 0
        # First element in array is the number of angles
        # to keep the config the same as VB6
        # for integrate
        elAngles = self.configStore.getData("El. Angles", lab=False)
        nfreq = self.configStore.getData("Frequencies", lab=True)
        # logger.printmsg("debug", "Frequencies from config: %r", nfreq)
        nfreq = nfreq[1: len(nfreq)]
        # logger.printmsg("debug", "Frequencies without size: %r", nfreq)

        # loop over " scan commands"
        self.controlWindow.setLEDgreen(self.controlWindow.probeStatusLED)
        self.controlWindow.setLEDgreen(self.controlWindow.scanStatusLED)

        while self.continueCycling:
            self.controlWindow.iwgProcessEvents()
            # printmsg of info stops cycling with a popup window
            # that has to be clicked through
            logger.printmsg("debug",
                "mainloop--------------------------------------------mainloop")
            # check here to exit cycling
            logger.printmsg("debug", "mainloop1")
            # use the MTPmove aline
            packetStartTime = time.gmtime()
            self.alineStore = self.formatMTP.Aline()
            logger.printmsg("debug", "mainloop2")

            # Bline: long
            self.blineStore = 'B' + self.mover.Bline(elAngles, nfreq)
            self.controlWindow.iwgProcessEvents()
            logger.printmsg("debug", "mainloop3")

            self.m01Store = self.mover.m01()
            self.m02Store = self.mover.m02()
            self.ptStore = self.mover.pt()
            self.controlWindow.iwgProcessEvents()
            logger.printmsg("debug", "mainloop4")
            # Eline: long
            self.elineStore = 'E' + self.mover.Eline(nfreq)
            self.controlWindow.iwgProcessEvents()
            logger.printmsg("debug","mainloop5")
            # save to file
            # assumes everything's been decoded from hex
            self.iwgStore = self.packetStore.getData('iwgStore')
            saveData = self.formatMTP.saveData(packetStartTime, self.dataFile)
            self.controlWindow.iwgProcessEvents()
            logger.printmsg("debug", "mainloop6")

            # send packet over UDP
            # also replaces spaces with commas and removes start strings
            # speed may be an issue here
            # self.udp.sendUDP(self.mover.formUDP())
            udpPacket = self.formatMTP.formUDP(packetStartTime)
            self.controlWindow.iwgProcessEvents()
            logger.printmsg("debug", "mainloop6")
            #print(udpPacket)
            self.udp.sendUDP(udpPacket, saveData)
            self.controlWindow.iwgProcessEvents()
            logger.printmsg("debug", "sent UDP packet")
            # collect, update, display loop stats
            previousTime = self.cycleStats(previousTime)

            # time.sleep(1)

        logger.printmsg("debug", "Main Loop Stopped")
        self.controlWindow.setLEDred(self.controlWindow.scanStatusLED)
        if self.packetStore.getData("quitClicked"):
            controlWindow.exit(0)

    def cycleStats(self, previousTime):
        logger.printmsg("debug", "cycleStats")

        # loop timer
        nowTime = time.perf_counter()
        elapsedTime = nowTime - previousTime
        logger.printmsg("debug", "elapsed Loop Time: %s", elapsedTime)
        previousTime = nowTime

        # total frames(m01,m02,pt,Eline,aline,bline, IWG) taken since startup
        totalCycles = self.packetStore.getData("totalCycles") + 1
        self.packetStore.setData("totalCycles", totalCycles)
        logger.printmsg("debug", "cycleStats totalCycles/cycleNumber: %s", totalCycles)

        # frames taken since last "stop probe"
        self.cyclesSinceLastStop = self.cyclesSinceLastStop + 1
        self.controlWindow.updateGUIEndOfLoop(elapsedTime,
                str(totalCycles), str(self.cyclesSinceLastStop))
        # increase scan count
        self.packetStore.setData("scanCount",
                int(self.packetStore.getData("scanCount")) + 1)
        return previousTime

    '''
    # keep for now because of scanCount for aline 
    def updateRead(self, scanOrEncode):
        i = 0
        while i < 11:
            self.serialPort.sendCommand((self.commandDict.getCommand(
                scanOrEncode)))
            echo, sFlag, foundIndex = self.readUntilFound(b':',
                                                          10, 20, isHome=False)
            # read_scan returns b'Step:\xff/0c1378147\r\n'
            # then returns b'Step:\xff/0`1378147\r\n'
            echo, sFlag, foundIndex = self.readUntilFound(b':',
                                                          10, 20, isHome=False)
            # have a does string contain bactic `
            logging.debug(echo.size())
            # 17 or 18 depending on size of value returned
            findBactic = echo.data().find(b'`')
            if findBactic > 0:
                readScan = echo.data()[findBactic + 1: echo.size() - 2]
                # readScan = echo.data()[9:15]
                # despite the first echo being formated 0c123456
                # The return echo turns the 0c into ` (proper hex translation)
                # and leaves the rest of the numbers alone
                # I'm forced to assume this and encoderCount are
                # the only case where numbers return in decimal, not hex
                # given that is the only way to get near the correct numbers
                # from previous flight data
                #
                # Also note that while the VB6 does append a ">>" to the data
                # that is only used as a deliminator, not a bit shift,
                # and only locally in the vb6 for these two cases.
                # So in intrest of sanity, and because python can manage
                # without a deliminator in this case, I'm not
                # going to re-implement that.
                if scanOrEncode == "read_scan":
                    logging.debug("readScan is: ")
                    logging.debug(readScan)
                    logging.debug(int(readScan.decode('Ascii'), 16))
                    self.scanCount = (1000000 - int(readScan.decode('Ascii')))
                    if self.scanCount >= 0:
                        self.scanCount = '+' + '%06d' % self.scanCount
                    self.packetStore.setData('scanCount', self.scanCount)
                else:
                    logging.debug("readEncode is: ")
                    logging.debug(readScan)
                    logging.debug(int(readScan.decode('Ascii')))
                    logging.debug(int(readScan.decode('Ascii'), 16))

                    self.scanCount = ((1000000 - int(readScan.decode(
                        'Ascii'))*16))
                    if self.scanCount >= 0:
                        self.scanCount = '+' + '%06d' % self.scanCount
                    self.packetStore.setData('encoderCount', self.scanCount)

                break
            i = i + 1
        logging.debug('readencoder size: %d', echo.size())
        '''

