import sys
import signal
#import serial
import time
from PyQt5.QtWidgets import (QWidget, QToolTip,
                             QPushButton, QButtonGroup,
                             QPlainTextEdit, QTextEdit,
                             QRadioButton, QVBoxLayout,
                             QLabel, QHBoxLayout,
                             QApplication)
from PyQt5 import QtGui 
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
#from lib.serialInst import SerialInst
from lib.serialQt import SerialInit
from lib.mtpcommand import MTPcommand 
from lib.storePacket import StorePacket
from lib.udp import doUDP
from moveMTP import moveMTP 
# from PyQt5.QtCore import QTimer
import logging


class controlWindow(QWidget):

    # self, MTPdict with iwg(has save) dict ,config dict, serialport) 
    def __init__(self, app):
        super().__init__()
        varDict = {
            'Cycling': False,
            'lastSky': -1, #readScan sets this to actual
        }

        self.vars = varDict
        self.initConfig()
        
        self.app = app

        # Create the GUI
        self.initUI()


        self.mainloop()

    def closeEvent(self, event):
        logging.debug("User has clicked the red x on the main window, unsafe exit")
        #self.shutdownProbeClicked(serialPort)
        #self.event.accept()

    def initUI(self):
        # QToolTip.setFont(QFont('SansSerif', 10))

        # false if not gui flag

        self.setToolTip('This is a <b>QWidget</b> widget')

        # Lables
        self.probeStatus = QLabel('Probe Status', self)
        self.scanStatus = QLabel('Scan Status', self)
        self.receivingUDP = QLabel("IWG Packet Status", self)
        self.sendingUDP = QLabel("UDP Status", self)
        self.projectName = QLabel("Project Name")
        self.planeName = QLabel("Plane Name")
        self.saveLocation = QLabel("Raw data saved to:")
        self.logLocation = QLabel("Log data saved to:")

        # Text boxes

        self.configFile = QPlainTextEdit()
        self.configFile.insertPlainText(':../../deployToDesktop/MTPData/Config/')
        self.configFile.insertPlainText('~/Desktop/MTPData/Config/')
        self.saveLocationBox = QPlainTextEdit()
        self.saveLocationBox.insertPlainText(':../../deployToDesktop/MTPData/RawData')
        self.saveLocationBox.insertPlainText('~/Desktop/MTPData/RawData')
        self.logLocationBox = QPlainTextEdit()
        self.logLocationBox.insertPlainText(':../../deployToDesktop/MTPData/Logs')
        self.logLocationBox.insertPlainText('~/Desktop/MTPData/Logs')
        self.projectNameBox = QPlainTextEdit()
        self.projectNameBox.insertPlainText('ACCLIP_TEST')
        self.planeNameBox = QPlainTextEdit()
        self.planeNameBox.insertPlainText('NGV')

        # Push Buttons
        self.reInitProbe = QPushButton("Reset Probe", self)
        self.reInitProbe.clicked.connect(self.reInitProbeClicked)
        self.scanStatusButton = QPushButton("Scan Status", self)
        self.scanStatusButton.clicked.connect(self.scanStatusClicked)
        self.shutdownProbe = QPushButton("Quit", self)
        self.shutdownProbe.clicked.connect(self.shutdownProbeClicked)
        #self.shutdownProbe.clicked.connect(self.safeSleep)

        # Radio Buttons
        self.locationLocal = QRadioButton("Plane")
        self.locationLocal.clicked.connect(self.locationLocalClicked)
        self.locationRemote = QRadioButton("Remote")
        self.locationRemote.clicked.connect(self.locationRemoteClicked)

        self.locationGroup = QButtonGroup()
        self.locationGroup.addButton(self.locationLocal)
        self.locationGroup.addButton(self.locationRemote)

        # staus 'LED's'
        # img.scaled(100, 100, Qt::KeepAspectRatio);
        self.ICON_RED_LED = QtGui.QPixmap(self.size())
        self.ICON_RED_LED.fill(QtGui.QColor("red"))
        self.ICON_YELLOW_LED = QtGui.QPixmap(self.size())
        self.ICON_YELLOW_LED.fill(QtGui.QColor("yellow"))
        self.ICON_GREEN_LED = QtGui.QPixmap(self.size())
        self.ICON_GREEN_LED.fill(QtGui.QColor("green"))

        self.probeStatusLED = QLabel('led')
        self.probeStatusLED.setPixmap(self.ICON_RED_LED.scaled(40, 40))
        self.scanStatusLED = QLabel('led')
        self.scanStatusLED.setPixmap(self.ICON_RED_LED.scaled(40, 40))
        self.receivingUDPLED = QLabel('led')
        self.receivingUDPLED.setPixmap(self.ICON_RED_LED.scaled(40, 40))
        self.sendingUDPLED = QLabel('led')
        self.sendingUDPLED.setPixmap(self.ICON_RED_LED.scaled(40, 40))

        # Horizontal boxes
        LineProbeStatus = QHBoxLayout()
        LineProbeStatus.addWidget(self.probeStatusLED)
        LineProbeStatus.addWidget(self.probeStatus)
        LineProbeStatus.addStretch()

        LineScanStatus = QHBoxLayout()
        LineScanStatus.addWidget(self.scanStatusLED)
        LineScanStatus.addWidget(self.scanStatus)
        LineScanStatus.addStretch()

        LineReceivingUDP = QHBoxLayout()
        LineReceivingUDP.addWidget(self.receivingUDPLED)
        LineReceivingUDP.addWidget(self.receivingUDP)
        LineReceivingUDP.addStretch()

        LineSendingUDP = QHBoxLayout()
        LineSendingUDP.addWidget(self.sendingUDPLED)
        LineSendingUDP.addWidget(self.sendingUDP)
        LineSendingUDP.addStretch()

        LineRunningLocation = QHBoxLayout()
        LineRunningLocation.addWidget(self.locationLocal)
        LineRunningLocation.addWidget(self.locationRemote)
        LineRunningLocation.addStretch()

        LineProjectName = QHBoxLayout()
        LineProjectName.addWidget(self.projectName)
        LineProjectName.addWidget(self.projectNameBox)
        LineProjectName.addStretch()

        LinePlaneName = QHBoxLayout()
        LinePlaneName.addWidget(self.planeName)
        LinePlaneName.addWidget(self.planeNameBox)
        LinePlaneName.addStretch()

        # vbox
        mainbox = QVBoxLayout()
        mainbox.addLayout(LineProbeStatus)
        mainbox.addWidget(self.reInitProbe)
        mainbox.addLayout(LineScanStatus)
        mainbox.addWidget(self.scanStatusButton)
        mainbox.addLayout(LineReceivingUDP)
        mainbox.addLayout(LineSendingUDP)
        mainbox.addLayout(LineRunningLocation)
        mainbox.addLayout(LineProjectName)
        mainbox.addLayout(LinePlaneName)
        mainbox.addWidget(self.saveLocation)
        mainbox.addWidget(self.saveLocationBox)
        mainbox.addWidget(self.logLocation)
        mainbox.addWidget(self.logLocationBox)
        mainbox.addWidget(self.shutdownProbe)
        mainbox.addStretch()

        self.setLayout(mainbox)
        self.setGeometry(100, 100, 400, 800)
        self.setWindowTitle('MTPRealTime')
#        self.show()

        self.cycleTimer = QtCore.QTimer()
        self.cycleTimer.timeout.connect(self.cycle)
        self.cycleTimer.setInterval(82) # mseconds
        # 82 ms fixes race condition that makes
        # arriving data concatinate
        # 72 mostly fixes it, but not all
        # Eline/Bline double sample
        # 62 does not 
        # 142, 82 ms can cause a pause at eline 

#        sys.exit(app.exec_())
        logging.debug("init ui done")

    def openComm(self, serialPort):

        # close port to make sure 
        serial = self.closeComm(serialPort)
        # open port
        logging.debug("in view.openComm")
        logging.debug(serial)
        serial = 6
        logging.debug(serial)
        return serial
        # on receipt of datad signal readCommData

        return 0

    def closeComm(self, serialPort):
        logging.debug("closing serial port")
        #self.serialPort.close()
        serialPort=5
        logging.debug(serialPort)
        return serialPort

    # read in data from MTP, save to dict
    # signal is data to be written after
    def readCommData(self):

        self.saveProbeData()
        self.writeUDP()
        return 0
    
    def saveProbeData(self):
        # save current dict vals to file in local directory

        # eventually reset so saves to desktop directory
        return 0

    # will need to read iwg
    # and write probe data
    # will need to close other udp connections first
    def openUDP(self):
        return 0

    # write udp string to main program
    def writeUDP(self):
        return 0 

    # read in and save iwg packet to dict
    def readUDP():
        self.SavePacket.saveData()
        return 0

    def reInitProbeClicked(self):
        logging.debug("reInitProbeClicked")
        # need a read to clear echo here
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("ctrl-C")))
        # set init led to yellow
        self.probeStatusLED.setPixmap(self.ICON_YELLOW_LED.scaled(40, 40))
        # Reset should just send the re-initialization again
        # regardless of previous status
        # Therefore init shuold reset every cycle function
        '''
        if self.packetStore.getData("isCycling"): 
            self.packetStore.setData("isCycling", False)
            self.reInitProbe.setText("Finishing scan: Please wait")
        else:
        '''
        self.packetStore.setData("isCycling", True)
        self.reInitProbe.setText("Initializing ...")
        # set desired mode to init
        # changed these 3 from packetDict
        self.packetStore.setData("desiredMode", "init")
        self.packetStore.setData("switchControl", "resetInitScan")
        self.packetStore.setData("scanStatus", False)
        self.packetStore.setData("calledFrom", "resetProbeClick")
        self.cycleTimer.start()
        #self.cycle()

        self.app.processEvents()

    def shutdownProbeClicked(self, serialPort):
        logging.debug("shutdownProbe/quit clicked")
        self.closeComm(serialPort)
        logging.debug("Safe exit")
        app.exit(0)

    def readClear(self, waitReadyReadTime, readLineTime):
        # clear a buffer, discarding whatever is in it
        # will read until either the buffer is empty
        # or it finds a \n, whichever is first
        self.serialPort.readLine(readLineTime)
        if self.serialPort.canReadLine(readLineTime):
            self.serialPort.readLine(readLineTime)

    def read(self, waitReadyReadTime, readLineTime):
        logging.debug( 'waitreadyreadtime = %f', waitReadyReadTime)
        return self.serialPort.canReadLine(readLineTime)


    def mainloop(self):
        # instantiate dict for commands

        self.isScanning = False
        logging.debug("1 : main loop")
        self.commandDict = MTPcommand()
        self.packetStore = StorePacket()
        # global storage for values collected from probe
        # storing them in dict introduced slowness
        self.alineStore = 'A 20101002 19:47:30 -00.59 00.13 -00.26 00.13 +04.37 0.04 270.99 00.38 +39.123 +0.016 -103.967 +0.044 +072727 +071776'
        self.blineStore = 'B 017828 019041 018564 017846 019061 018572 017874 019069 018603 017906 019095 018625 017932 019124 018637 017949 019139 018655 017968 019151 018665 017979 019164 018665 017997 019161 018691 018029 019181 018705'
        self.iwgStore = 'IWG1,20101002T194729,39.1324,-103.978,4566.43,,14127.9,,180.827,190.364,293.383,0.571414,-8.02806,318.85,318.672,-0.181879,-0.417805,-0.432257,-0.0980951,2.36793,-1.66016,-35.8046,16.3486,592.062,146.734,837.903,9.55575,324.104,1.22603,45.2423,,-22    .1676,'
        self.m01Store = 'M01: 2928 2457 3023 3085 1925 2923 2434 2948'
        self.m02Store = 'M02: 2109 1299 2860 2691 2962 1116 4095 1805'
        self.ptStore = 'Pt: 2157 13804 13796 10311 13383 13327 13144 14440'
        self.elineStore = 'E 020541 021894 021874 018826 020158 019813 '
        self.pitch15 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]    # Arrays of last 15 s
        self.roll15 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]     # taken from iwg
        self.Zp15 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.oat15 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.lat15 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.lon15 = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.elAngles= [10,-179.8, 80.00, 55.00, 42.00, 25.00, 12.00, 0.00, -12.00, -25.00, -42.00, -80.00]
        self.udp = doUDP(self,self.app)
        # UDP LED's
        # need to figure out the logic behind making them red if they aren't
        # actually sending/recieving data
        # self.receivingUDPLED.setPixmap(self.ICON_YELLOW_LED.scaled(40, 40))
        # self.sendingUDPLED.setPixmap(self.ICON_YELLOW_LED.scaled(40, 40))
        #logging.debug("2 : main loop")
        # Don't need two of these:
        # self.packetDict = StorePacket()
        
        # instantiate serial port
        # comment out next n lines to test non serial port code       
        self.serialPort = SerialInit(self, app)
        # self.serialPort.readyRead.connect(self.tick(packetDict))
        # self.serialPort.sendCommand(self.commandDict.getCommand("status"))
        # sPort = self.openComm(serialPort)
        self.app.processEvents()
        '''
        '''
        logging.debug("main loop")
        # Declare instance of moveMTP class
        self.mover = moveMTP(self)


        # init probe
        self.serialPort.sendCommand(self.commandDict.getCommand("init1"))
        i=0
        echo = b''
        while i < 100000:
            # grab whatever is in the buffer
            # will terminate at \n if it finds one

            echo = self.serialPort.canReadLine(20)#msec
            logging.debug("init 1 loop echo: ")
            logging.debug(echo)

            #logging.debug(echo)
            if echo is None or echo == b'':
                #logging.debug("checking init1")
                self.app.processEvents()
                i = i + 1
            elif echo.data().find(b'S') >= 0:
                logging.debug("received S from init1")
                break;
            else:
                logging.debug("init1 loop echo else case")
                self.app.processEvents()
                i = i + 1



        self.serialPort.sendCommand(self.commandDict.getCommand("init2"))
        self.readUntilFound(b'S', 100000, 20)
        self.homeScan()

        # loop over " scan commands"
        while (1):
            logging.debug("loop                                                                                                                 asdfasdf")
            self.m01Store = self.m01()
            self.m02Store = self.m02()
            self.ptStore = self.pt()
            # Eline: long 
            self.elineStore = self.Eline()
            # check here to exit cycling

            # use the MTPmove aline
            self.alineStore = self.Aline()

            # Bline: long
            # doesn't do any scan correcting 
            self.blineStore = self.Bline()

            # save to file
            # assumes everything's been decoded from hex
            # returns UDP packet
            # currently crashes here, either currentDateUDP or self.parent.alineStore 
            # is nonetype trying to concatinate to string
            udp = self.mover.saveData()

            # send packet over UDP



            #time.sleep(1)

        return 0

    def readUntilFound(self, binaryString, timeout, canReadLineTimeout):
        i=0
        echo = b''

        while i < timeout:
            # grab whatever is in the buffer
            # will terminate at \n if it finds one

            echo = self.serialPort.canReadAllLines(canReadLineTimeout)#msec
            logging.debug("init 1 loop echo: ")
            logging.debug(binaryString)
            logging.debug(echo)

            #logging.debug(echo)
            if echo is None or echo == b'':
                #logging.debug("checking init1")
                self.app.processEvents()
                i = i + 1
            elif echo.data().find(binaryString) >= 0:
                logging.debug("received S")
                return echo
            else:
                logging.debug("init1 loop echo else case")
                self.app.processEvents()
                i = i + 1
        logging.debug("readUntilStep timeout")
        return echo


    def tick(self, buff):
        logging.debug("tick")
        logging.debug(buff)
        
        #self.timer.stop()
        return 0

    # @pyqtSlot() # called a decorator, to make call faster
    def safeSleep(self):
        logging.debug('sleep')
        self.timer.start(5000)
        logging.debug('after timer')
        logging.debug("after process")
        return 0

    def scanStatusClicked(self):
        logging.debug("scanStatusClicked")
        if self.packetStore.getData("isCycling"): 
            self.packetStore.setData("isCycling", False)
            self.scanStatusButton.setText("Start Scanning")
        else:
            self.packetStore.setData("isCycling", True)
        # set desiredMode = scan
        self.packetStore.setData("desiredMode", "scan")
        # uncomment for actual functionality
        #self.cycleTimer.start()
        #self.cycle()
        #logging.debug(self.commandDict.getCommand(""))
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("read_M1")))
        '''
        self.safeSleep()
        self.app.processEvents()
        self.app.processEvents()
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("init1")))
        time.sleep(2)
        self.app.processEvents()
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("init2")))
        self.app.processEvents()
        '''
        #time.sleep(8)
        #self.serialPort.sendCommand(str.encode("U/1J0P1j3R\r"))
            #self.scanStatusButton.setText("End Scanning")
            #check that probe is at home position
            #put it there if not
            #self.doScan()

        return 0

    def tick(self):
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("status")))
        return

    def locationLocalClicked(self):
        logging.debug("LocationLocalClicked")
        return 0

    def locationRemoteClicked(self):
        logging.debug("LocationRemoteClicked: Sorry not yet implemented")
        return 0
    '''
    def paintEvent(self, event):
        if self.Modified:
            pixmap = QPixmap(self.size())
            pixmap.fill(Qt.blue)
            painter = QPainter(pixmap)
            painter.drawPixmap(0, 0, self.mPixmap)
            self.drawBackground(painter)
            self.mPixmap = pixmap
            self.mModified = False
        qp = QPainter(self)
        qp.drawPixmap(0, 0, self.mPixmap)
    '''
    def paintCircle(self, color):
        painter = QtGui.QPainter(self)
        size = 10
        if color == 'red':
            logging.debug('red')
            painter.setBrush(QtGui.QColor(0, 0, 255))
            # xoffset, yoffset, diameter, diameter
            painter.drawEllipse(12, 15, size, size)
            logging.debug("printing red")

        if color == 'yellow':
            logging.debug('Yellow')
            painter.setBrush(QtGui.QColor(0, 255, 0))
            # xoffset, yoffset, diameter, diameter
            painter.drawEllipse(12, 15, size, size)
            logging.debug("printing yellow")

        if color == 'green':
            logging.debug("green")
            painter.setBrush(QtGui.QColor(255, 0, 0))
            # xoffset, yoffset, diameter, diameter
            painter.drawEllipse(12, 15, size, size)

        else:
            logging.debug("Color not defined")
        painter.end()

    def initConfig(self):
        # check for config file
        # reload config
        #    - calculate MAM
        # initializes the saveData file
        ''' reads config file into dictionary to change default values '''
        ''' to be implemented '''
        #self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("read_scan")))

        with open("MTP_data.txt", "ab") as datafile:
                # this will be rewritten each time the program restarts
                datafile.write(str.encode("Instrument on " + time.strftime("%X") + " " + time.strftime("%m-%d-%y")))
        logging.debug("initConfig")

    def cycle(self):
        # self.cycleTimer.stop()
        '''
        logging.debug("Start of cycle")
        self.serialPort.waitReadyRead(20)
        logging.debug("After ready read")
        buf = self.serialPort.readLine(70)
        logging.debug("after readline")
        logging.debug(buf.data())
        '''
        # this process Events can really slow things down
        # still necessary because recieved data has to be processed
        # before deciding if moving to next command or no.
        self.app.processEvents()
        logging.debug("Cycle, processEvents1")
        # at startup, when cycling = false sets probe to start position
        if self.packetStore.getData("desiredMode") is "init":
            self.probeStatusLED.setPixmap(self.ICON_YELLOW_LED.scaled(40, 40))
            self.packetStore.setData("switchControl", 'initScan')
        elif self.packetStore.getData("isCycling"):
            self.probeStatusLED.setPixmap(self.ICON_GREEN_LED.scaled(40, 40))
        else:
            self.probeStatusLED.setPixmap(self.ICON_RED_LED.scaled(40, 40))


        # make an enum and only move on from first function when returned status

        # open save file
        # add header "Instrument on " + time + " " + date

        logging.debug("cycle")
        # state machine like behavior to ensure all tasks complete before next
        # command is sent. Somewhat like enum's 
        matchWord = self.packetStore.getData("switchControl")
        logging.debug(matchWord)
        # Check that there isn't an exit condition
        if not self.packetStore.getData("isCycling"):
            # stop timer that continues to call cycle
            self.cycleTimer.stop()
            # set button text to "stopping"
            self.scanStatusButton.setText("Stopping ...")
            # set cycling light to yellow
            # self.scanStatusLED.setPixmap(self.ICON_YELLOW_LED.scaled(40.40))
            if matchWord is "sendUDP":  # or bline, not sure which would be better
                # just to be absolutely sure, try stopping the timer again
                self.cycleTimer.stop()
                # set Cycling light to red
                # self.scanStatusLED.setPixmap(self.ICON_RED_LED.scaled(40.40))
                # set button text to stoped cycle
                self.scanStatusButton.setText("Start Scanning")
            # self.mover.dispatch(matchWord)
            #self.app.processEvents()
            logging.debug("Cycle, processEvents2")
            
        if self.packetStore.getData("currentMode") is 'init':
            # stop if matchword = Aline
            if matchWord is "Aline":
                # stop timer
                self.cycleTimer.stop()
                # set the button text back to reset
                self.packetStore.setData("isCycling", False)
                self.reInitProbe.setText("Reset Probe")
                # set the init light to green
                # self.probeStatusLED.setPixmap(self.ICON_GREEN_LED.scaled(40,40))
            # otherwise continue with cycle

        # if bline, set new frame? or set in bline

        # with timer these should become unnecessary     
        # self.app.processEvents()
        logging.debug("Cycle, processEvents3")
        '''
        time.sleep(0.2)
        self.app.processEvents()
        '''
        # continue through the cycle
        logging.debug("cycle, before dispatch, with matchword:")
        logging.debug(matchWord)
        self.mover.dispatch(matchWord)
        logging.debug("cycle, after dispatch")
        #self.app.processEvents()
        logging.debug("Cycle, processEvents4")
        '''
        switch (matchWord){
                case 1: matchWord == 'initConfig';
                    self.initConfig()
                    break;
                case 2: matchWord == 'initScan';
                    self.initScan()
                    break;
                case 3: matchWord == 'homeScan';
                    self.homeScan()
                    break;
                case 4: matchWord == 'm01';
                    self.m01()
                    break;
                case 5: matchWord == 'm02';
                    self.m02()
                    break;
                case 6: matchWord == 'pt';
                    self.pt()
                    break;

                case 7: matchWord == 'Eline';
                    self.Eline()
                    break;
                case 8: matchWord == 'Aline';
                    self.Aline()
                    break;
                case 9: matchWord == 'Bline';
                    self.Bline()
                    break;
                case 10: matchWord == 'saveFrame';
                    self.saveFrame()
                    break;
                case 11: matchWord == 'sendUDP';

                    self.sendUDP()
                    break;



                }

        self.initConfig()
        self.initScan()
        self.homeScan()
        self.m01()        # Thats a zero
        self.m02()
        self.pt()
        self.Eline()
        if self.cycling:
            self.Aline()
            self.Bline()
            self.m01()
            self.m02()
            self.pt()
            self.Eline()
            self.saveFrame() # should make this a signal for this and sendUDP
            self.sendUDP()
        '''

    def readScan(self):
        logging.debug("cycle")
        #getcommand read_scan
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("read_scan")))
        return 0
        '''
    def initScan(self):
        logging.debug("cycle")
        gearRatio = 80/20                           # 2007/11/29, assumes "j256" for 
        stepsDegree = gearRatio * (128 * (200/300)) # fiduciary and "j128" for normal run
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("init1")))
        logging.debug("cycle1")
        if (initSwitch):
            self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("init2")))
            logging.debug("cycle2")
    '''


    def homeScan(self):
        self.serialPort.sendCommand(self.commandDict.getCommand("home1"))
        self.readUntilFound(b':', 100000, 20)
        self.readUntilFound(b'S', 100000, 20)
        self.serialPort.sendCommand(self.commandDict.getCommand("home2"))
        self.readUntilFound(b':', 100000, 20)
        self.readUntilFound(b'S', 100000, 20)
        self.serialPort.sendCommand(self.commandDict.getCommand("home3"))
        self.readUntilFound(b':', 100000, 20)
        self.readUntilFound(b'S', 100000, 20)
        echo = self.read(200,20)
        logging.debug("home3 1st echo =:%s",echo) 
        echo = self.read(200,20)
        logging.debug("home3 2nd echo =:%s",echo) 


    def m01(self):
        logging.debug("M01")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_M1")))
        # echo will echo "M  1" so have to scan for the : in the M line
        self.readUntilFound(b':', 100000, 20)
        # set a timer so m01 values get translated from hex?
        

    def m02(self):
        logging.debug("M02")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_M2")))
        self.readUntilFound(b':', 100000, 20)

    def pt(self):
        logging.debug("pt")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_P")))
        self.readUntilFound(b':', 100000, 20)

    def Eline(self):
        self.elineStore = "E "
        logging.debug("Eline")
        self.homeScan()
        # set noise 1
        # returns echo and b"ND:01\r\n" or b"ND:00\r\n"
        self.serialPort.sendCommand(self.commandDict.getCommand("noise1"))
        echo = self.readUntilFound(b'N',100, 4)
        #echo = self.serialPort.canReadLine(20)
        logging.debug(echo.size())
        # the echo and return value concatonate to form a size of 12
        # want to move along if we don't need to check for the second
        # return value
        if not(echo.size() is 12):
            echo = self.readUntilFound(b'N',100, 4)
        #echo = self.serialPort.canReadLine(20)
        logging.debug(echo.size())
        
        data = 0
        data = self.integrate()
        # set noise 0
        self.serialPort.sendCommand(self.commandDict.getCommand("noise0"))
        echo = self.readUntilFound(b'N',100, 4)
        #echo = self.serialPort.canReadLine(20)
        logging.debug(echo)
        if not(echo.size() is 12):
            echo = self.readUntilFound(b'N',100, 4)
        #echo = self.serialPort.canReadLine(20)
        logging.debug(echo)
        self.elineStore = data + self.integrate()
        logging.debug(self.elineStore)

    def Aline(self):
        logging.debug("View Aline")
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
            pitchavg = self.packetStore.getData("pitchavg")
            logging.debug("after pitch avg")
            pitchrms = self.packetStore.getData("pitchrms")
            logging.debug("after pitch rms1")
            rollavg = self.packetStore.getData("rollavg")
            logging.debug("after pitch rms2")
            rollrms = self.packetStore.getData("rollrms")
            logging.debug("after pitch rms3")
            Zpavg = self.packetStore.getData("Zpavg")
            logging.debug("after pitch rms4")
            Zprms = self.packetStore.getData("Zpavg")
            logging.debug("after pitch rms5")
            oatavg = self.packetStore.getData("oatavg")
            logging.debug("after pitch rms6")
            oatrms = self.packetStore.getData("oatrms")
            logging.debug("after pitch rms7")
            latavg = self.packetStore.getData("latavg")
            logging.debug("after pitch rms8")
            latrms = self.packetStore.getData("latrms")
            logging.debug("after pitch rms9")
            lonavg = self.packetStore.getData("lonavg")
            logging.debug("after pitch rms10")
            lonrms = self.packetStore.getData("lonrms")
            logging.debug("after pitch rms end")
        except Exception as e:
            logging.debug("after pitch rms, in exception")
            logging.error(repr(e))
            logging.error(e.message)
            logging.error(sys.exe_info()[0])
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
            logging.debug("else got IWG")

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
        aline = aline + " " + str(self.packetStore.getData("scanCount"))
        aline = aline + " " + str(self.packetStore.getData("encoderCount"))
        self.alineStore = aline

        self.packetStore.setData("angleI", 0) # angle index

        self.serialPort.sendCommand((self.commandDict.getCommand("read_scan")))
        echo = self.readUntilFound(b':', 100000, 20)
        echo = self.readUntilFound(b'S', 100000, 20)
        # b'Step:\xff/0`1000010\r\n'
        # echo = self.read(200,200)
        # need to implement the better logic counters in bline
        # for scanCount and encoderCount
        self.packetStore.setData("scanCount", int(self.packetStore.getData("scanCount")) + 1)
        logging.debug("View: Aline end")



    def Bline(self):
        logging.debug("Bline")
        # clear blineStore
        # All R values have spaces in front
        self.blineStore = 'B'
        angles = self.packetStore.getData("El. Angles")
        # First element in array is the number of angles
        # to keep the config the same 
        numAngles = angles[0]
        zel = angles[1]
        elAngles = angles[2:numAngles]
        data = ''
        for angle in elAngles: 
            self.mover.getAngle(angle)
            if self.packetStore.getData("pitchCorrect"):
                #
                logging.debug('Pitch correct mode on')
                data = data + integrate()
        self.scanCount = 1000000 - self.readScan
        self.encoderCount = (1000000 - self.readEnc) * 16

            
        #    scanNum = 1000000 - self.readScan()

    def quickRead(self, timeout):
        logging.debug("quickRead start")
        echo = self.serialPort.canReadLine(timeout)
        logging.debug(echo)
        datum = self.serialPort.canReadLine(timeout)
        logging.debug(datum)
        logging.debug("quickRead end")
        return datum

    def integrate(self):
        # returns string of data values translated from hex to decimal
        nfreq = self.packetStore.getData("nFreq")
        data = ''
        for freq in nfreq:
            # tune echos received in tune function
            self.tune(freq)

            self.serialPort.sendCommand((self.commandDict.getCommand("count")))
            # clear echos 
            dataLine = self.quickRead(25) # avg is ~9, max is currently 15
            # ensure integrator starts so then can
            i=0
            while i < 50: 
                logging.debug("integrate infinite loop 1")
                self.serialPort.sendCommand((self.commandDict.getCommand("status")))
                # echo is b'S\r\n'
                status = self.readUntilFound(b'T', 100000, 10)
                #if status[4] or 7
                if status.size() is 10:
                    # echo and status return concatinated
                    num = int(status[7])
                elif status.size() is 4:
                    num = int(status[4])
                else: 
                    num = 0
                logging.debug(num)
                if num is 5:
                    # VB6 code has a bitwise and to check if this status is odd
                    # instead of checking if it is 5
                    # As of writing this I haven't seen anything that 
                    # would prompt this other than speed
                    # so I'm ignoring it
                    logging.debug("break, integrator started")
                    break   
                logging.debug(status.size())
                i = i + 1
                self.app.processEvents()

            logging.debug("integrator has started")
            # check that integrator is done
            i=0
            while i < 50: 
                logging.debug("integrate infinite loop 2")
                self.serialPort.sendCommand((self.commandDict.getCommand("status")))
                # echo is b'S\r\n'
                status = self.readUntilFound(b'T', 100000, 10)
                #if status[4] or 7
                if status.size() is 10:
                    # echo and status return concatinated
                    num = int(status[7])
                elif status.size() is 4:
                    num = int(status[4])
                else: 
                    num = 0
                if num is 4:
                    # VB6 code has a bitwise and to check if this status is even
                    # instead of checking if it is 4
                    # As of writing this I haven't seen anything that 
                    # would prompt this other than speed
                    # so I'm ignoring it
                    logging.debug("break, integrator finished")
                    break   
                logging.debug(status.size())
                i = i + 1
                self.app.processEvents()


            logging.debug("integrator has finished")
            # actually request the data of interest
            self.serialPort.sendCommand((self.commandDict.getCommand("count2")))
            echo = self.readUntilFound(b'R', 100000, 20)
            echo = self.readUntilFound(b':', 100000, 20)
            #logging.debug("integrate echo 1 : %s", echo.decode(ascii))
            # grab value from string, translate from hex, append to string
            datum = echo[4:10]
            logging.debug("r value data")
            # translate from hex:
            datum = str(int(datum.data().decode('ascii'), 16))

            # append to string:
            data = data + ' ' + datum
            self.serialPort.sendCommand((self.commandDict.getCommand("read_scan")))
            # read_scan returns b'Step:\xff/0`1000010\r\n' 
            echo = self.readUntilFound(b':', 100000, 20)
            #logging.debug("integrate echo 1 : %s", echo.decode(ascii))
            echo = self.readUntilFound(b'S', 100000, 20)
        logging.debug (data)
        return data

    def waitForStatus(self, status):
        # add timeout?
        while status is not receivedStatus:
            self.serialPort.sendCommand((self.commandDict.getCommand("status")))
            echo = self.readUntilFound(b'S', 100000, 20)
            logging.debug("status echo 1 : %s", echo.decode(ascii))
            echo = self.readUntilFound(b'S', 100000, 20)
            logging.debug("status echo 1 : %s", echo.decode(ascii))
            logging.debug("status: %s, received Status: %s, ", status, echo)
        


    def tune(self, fghz):
        # fghz is frequency in gigahertz
        fby4 = (1000 * fghz)/4 #MHz
        chan = fby4/0.5  # convert to SNP channel (integer) 0.5 MHz = step size
        #logging.debug("tune: chan = %s", chan)

        # either 'C' or 'F' set in packetStore
        # F mode formatting #####.# instead of cmode formatting #####
        # not sure it makes a difference

        # mode = self.parent.packetStore.getData("tuneMode")

        mode = 'C'
        self.serialPort.sendCommand(str.encode(str(mode) + '{:.5}'.format(str(chan)) +"\r")) # \n added by encode I believe
        #logging.debug("Tuning: currently using mode C as that's what's called in vb6")
        # no official response, just echos
        # and echos that are indistinguishable from each other
        # eg: echo when buffer is sending to probe is same
        # as echo from probe: both "C#####\r\n"
        # catch tune echos
        echo = self.readUntilFound(b'C', 100000, 20)
        echo = self.readUntilFound(b'C', 100000, 20)


    def goAngle(self, targetEl, zel):
        if self.packetStore.getData("pitchCorrect"):
            logging.info("correcting Pitch")
            targetClkAngle = targetEl + fec(MAM(), Pitch_Frame, Roll_Frame, targetEl, EmaxFlag)
        else:
            targetClkAngle = targetEl + zel
        targetClkStep = targetClkAngle * self.parentl.getData("stepsDegree")

if __name__ == '__main__':
    #    signal.signal(signal.SIGINT, ctrl_c)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',filename="MTPCtrl.log",level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logging.warning("warning")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    ex = controlWindow(app)
    ex.show()
    sys.exit(app.exec_())
    # ex.run()
