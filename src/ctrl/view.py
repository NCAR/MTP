import sys
import signal
#import serial
import time
from PyQt5.QtWidgets import (QWidget, QToolTip,
                             QPushButton, QButtonGroup,
                             QPlainTextEdit, QTextEdit,
                             QRadioButton, QVBoxLayout,
                             QLabel, QHBoxLayout,
                             QInputDialog,
                             QApplication, QErrorMessage)
from PyQt5 import QtGui 
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from lib.serialQt import SerialInit
from lib.mtpcommand import MTPcommand 
from lib.storePacket import StorePacket
from lib.storeConfig import StoreConfig
from lib.udp import doUDP
from moveMTP import moveMTP 
import logging
import os
import glob
# following 2 are for initMoveHome
import socket
from serial import Serial


class controlWindow(QWidget):

    # self, MTPdict with iwg(has save) dict ,config dict, serialport) 
    def __init__(self, app):
        super().__init__()
        varDict = {
            'Cycling': False,
            'lastSky': -1, #readScan sets this to actual
        }

        
        self.app = app

        # Create the GUI
        self.initUI()
        

    def closeEvent(self, event):
        logging.debug("User has clicked the red x on the main window, unsafe exit")
        #self.shutdownProbeClicked(self.serialPort)
        #self.event.accept()
    def logProcessEvents(self,app):
        #logging.debug("Log Process Events Timestamp:" + str(time.gmtime()))
        self.IWG1Box.setPlainText(self.iwgStore)
        self.app.processEvents()
        self.app.processEvents()
        

    def initUI(self):
        # QToolTip.setFont(QFont('SansSerif', 10))

        # false if not gui flag

        self.setToolTip('This is a <b>QWidget</b> widget')

        # Lables
        self.probeStatus = QLabel('Probe Status', self)
        self.scanStatus = QLabel('Scan Status', self)
        self.receivingIWG = QLabel("IWG Packet Status", self)
        self.IWGPort= QLabel("IWG Port # ", self)
        self.sendingUDP = QLabel("UDP Status", self)
        self.UDPPort = QLabel("UDP out Port # ", self)
        self.overHeat= QLabel("Overheat", self)
        self.overVoltage = QLabel("Overvoltage", self)
        self.projectName = QLabel("Project Name")
        self.flightNumber = QLabel("Flight #")
        self.planeName = QLabel("Plane Name")
        self.nominalPitch = QLabel("Nominal Pitch")
        self.frequencies = QLabel("Frequencies")
        self.allScanAngles = QLabel("Elevation Angles")
        self.saveLocation = QLabel("Raw data saved to:")
        self.logLocation = QLabel("Log data saved to:")
        self.emptyLabel = QLabel("")

        self.loopTimer= QLabel("Time since last frame")
        self.totalNumFrames = QLabel("Total frames")
        self.numFramesSinceLastReset = QLabel("Frames since reset")
        self.elAngle = QLabel("Current El. Angle")
        self.IWG1 = QLabel("IWG1")

        # Text boxes
        self.longWidth = 300
        self.mediumWidth = 150
        self.shortWidth = 40
        self.configFile = QLineEdit()
        self.configFile.setText(':../../deployToDesktop/MTPData/Config/')
        self.configFile.setText('~/Desktop/$Project/config/')
        self.configFile.setReadOnly(True)
        self.configFile.setFixedWidth(self.longWidth)
        self.saveLocationBox = QLineEdit()
        self.saveLocationBox.setText(':../../deployToDesktop/$Project/data')
        self.saveLocationBox.setText('~/Desktop/$Project/data')
        self.saveLocationBox.setReadOnly(True)
        self.saveLocationBox.setFixedWidth(self.longWidth)
        self.logLocationBox = QLineEdit()
        self.logLocationBox.setText(':../../deployToDesktop/$Project/logs')
        self.logLocationBox.setText('~/Desktop/$Project/logs')
        self.logLocationBox.setReadOnly(True)
        self.logLocationBox.setFixedWidth(self.longWidth)


        self.loopTimerBox = QLineEdit()
        self.loopTimerBox.setText('Start')
        self.loopTimerBox.setFixedWidth(self.shortWidth)
        self.loopTimerBox.setReadOnly(True)
        self.totalNumFramesBox = QLineEdit()
        self.totalNumFramesBox.setText('0')
        self.totalNumFramesBox.setFixedWidth(self.shortWidth)
        self.totalNumFramesBox.setReadOnly(True)
        self.numFramesSinceLastResetBox = QLineEdit()
        self.numFramesSinceLastResetBox.setText('0')
        self.numFramesSinceLastResetBox.setFixedWidth(self.shortWidth)
        #self.numFramesSinceLastResetBox.setOverwriteMode(True)
        self.numFramesSinceLastResetBox.setReadOnly(True)

        # from config.mtph
        self.planeNameBox = QLineEdit()
        self.planeNameBox.setText('NGV')
        self.planeNameBox.setFixedWidth(self.mediumWidth)
        self.planeNameBox.setReadOnly(True)
        self.nominalPitchBox = QLineEdit()
        self.nominalPitchBox.setText('3')
        self.nominalPitchBox.setFixedWidth(self.shortWidth)
        self.nominalPitchBox.setReadOnly(True)
        # also known as channels
        self.frequenciesBox = QLineEdit()
        self.frequenciesBox.setText('55.51, 56.65, 58.8')
        self.frequenciesBox.setFixedWidth(self.mediumWidth)
        self.frequenciesBox.setReadOnly(True)
        self.allScanAnglesBox = QPlainTextEdit()
        self.allScanAnglesBox.setPlainText('80.00, 55.00, 42.00, 25.00, 12.00, 0.00, -12.00, -25.00, -42.00, -80.00')
        self.allScanAnglesBox.setFixedHeight(self.shortWidth)
        self.allScanAnglesBox.setReadOnly(True)
        # Current elevation - GUI updates before correction applied
        self.elAngleBox = QLineEdit()
        self.elAngleBox.setText('Target')
        self.elAngleBox.setFixedWidth(self.shortWidth)
        #self.elAngleBox.setOverwriteMode(True)
        self.elAngleBox.setReadOnly(True)

        # from/to (flight name) config.yaml
        self.projectNameBox = QLineEdit()
        self.projectNameBox.setText('PROJECTNAME')
        self.projectNameBox.setFixedWidth(self.mediumWidth)
        self.projectNameBox.setReadOnly(True)

        self.flightNumberBox = QLineEdit()
        self.flightNumberBox.setText('FlightNum')
        self.flightNumberBox.setFixedWidth(self.mediumWidth)
        self.flightNumberBox.setReadOnly(True)

        self.IWGPortBox = QLineEdit()
        self.IWGPortBox.setText('7071')
        self.IWGPortBox.setFixedWidth(self.shortWidth)
        self.IWGPortBox.setReadOnly(True)
        self.UDPPortBox = QLineEdit()
        self.UDPPortBox.setText('32106')
        self.UDPPortBox.setFixedWidth(self.shortWidth)
        self.UDPPortBox.setReadOnly(True)

        self.IWG1Box = QPlainTextEdit()
        self.IWG1Box.setPlainText('')
        self.IWG1Box.setFixedHeight(self.mediumWidth)
        self.IWG1Box.setReadOnly(True)



        # Push Buttons
        self.reInitProbe = QPushButton("(Re)start Scanning", self)
        self.reInitProbe.clicked.connect(self.reInitProbeClicked)
        self.reInitProbe.setEnabled(False)
        self.scanStatusButton = QPushButton("Stop Scanning", self)
        self.scanStatusButton.clicked.connect(self.scanStatusClicked)
        self.scanStatusButton.setEnabled(False)
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
        self.receivingIWGLED = QLabel('led')
        self.receivingIWGLED.setPixmap(self.ICON_RED_LED.scaled(40, 40))
        self.sendingUDPLED = QLabel('led')
        self.sendingUDPLED.setPixmap(self.ICON_RED_LED.scaled(40, 40))
        self.overHeatLED = QLabel('led')
        # Updated at end of each scan
        self.overHeatLED.setPixmap(self.ICON_GREEN_LED.scaled(40, 40))
        self.overVoltageLED = QLabel('led')
        self.overVoltageLED.setPixmap(self.ICON_GREEN_LED.scaled(40, 40))

        # Horizontal boxes
        LineProbeStatus = QHBoxLayout()
        LineProbeStatus.addWidget(self.probeStatusLED)
        LineProbeStatus.addWidget(self.probeStatus)
        LineProbeStatus.addWidget(self.emptyLabel)
        LineProbeStatus.addStretch()
        LineProbeStatus.addWidget(self.reInitProbe)
        LineProbeStatus.addWidget(self.scanStatusButton)

        LineScanStatus = QHBoxLayout()
        LineScanStatus.addWidget(self.scanStatusLED)
        LineScanStatus.addWidget(self.scanStatus)
        LineScanStatus.addWidget(self.emptyLabel)
        LineScanStatus.addStretch()

        LineTimer = QHBoxLayout()
        LineTimer.addWidget(self.loopTimerBox)
        LineTimer.addWidget(self.loopTimer)
        LineTimer.addStretch()
        
        LineHousekeeping = QHBoxLayout()
        LineHousekeeping.addWidget(self.overHeatLED)
        LineHousekeeping.addWidget(self.overHeat)
        LineHousekeeping.addWidget(self.emptyLabel)
        LineHousekeeping.addStretch()

        LineHousekeeping2 = QHBoxLayout()
        LineHousekeeping2.addWidget(self.overVoltageLED)
        LineHousekeeping2.addWidget(self.overVoltage)
        LineHousekeeping2.addStretch()

        LineNumFrames = QHBoxLayout()
        LineNumFrames.addWidget(self.totalNumFramesBox)
        LineNumFrames.addWidget(self.totalNumFrames)
        LineNumFrames.addWidget(self.emptyLabel)
        LineNumFrames.addStretch()

        LineResetFrames = QHBoxLayout()
        LineResetFrames.addWidget(self.numFramesSinceLastResetBox)
        LineResetFrames.addWidget(self.numFramesSinceLastReset)
        LineResetFrames.addStretch()

        LineElAngle = QHBoxLayout()
        LineElAngle.addWidget(self.elAngleBox)
        LineElAngle.addWidget(self.elAngle)
        LineElAngle.addWidget(self.emptyLabel)
        LineElAngle.addStretch()
        
        LineAllAngle = QHBoxLayout()
        LineAllAngle.addWidget(self.allScanAnglesBox)
        LineAllAngle.addWidget(self.allScanAngles)
        LineAllAngle.addStretch()

        LineReceivingUDP = QHBoxLayout()
        LineReceivingUDP.addWidget(self.receivingIWGLED)
        LineReceivingUDP.addWidget(self.receivingIWG)
        LineReceivingUDP.addWidget(self.emptyLabel)
        LineReceivingUDP.addStretch()
        LineReceivingUDP.addWidget(self.IWGPort)
        LineReceivingUDP.addWidget(self.IWGPortBox)

        LineSendingUDP = QHBoxLayout()
        LineSendingUDP.addWidget(self.sendingUDPLED)
        LineSendingUDP.addWidget(self.sendingUDP)
        LineSendingUDP.addWidget(self.emptyLabel)
        LineSendingUDP.addStretch()
        LineSendingUDP.addWidget(self.UDPPort)
        LineSendingUDP.addWidget(self.UDPPortBox)

        LineRunningLocation = QHBoxLayout()
        #LineRunningLocation.addWidget(self.locationLocal)
        #LineRunningLocation.addWidget(self.locationRemote)
        LineRunningLocation.addStretch()

        LineProjectName = QHBoxLayout()
        LineProjectName.addWidget(self.projectName)
        LineProjectName.addWidget(self.projectNameBox)
        LineProjectName.addWidget(self.emptyLabel)
        LineProjectName.addStretch()
        LineProjectName.addWidget(self.flightNumber)
        LineProjectName.addWidget(self.flightNumberBox)
        LineProjectName.addStretch()

        LinePlaneName = QHBoxLayout()
        LinePlaneName.addWidget(self.planeName)
        LinePlaneName.addWidget(self.planeNameBox)
        LinePlaneName.addWidget(self.emptyLabel)
        LinePlaneName.addStretch()
        LinePlaneName.addWidget(self.nominalPitch)
        LinePlaneName.addWidget(self.nominalPitchBox)
        LinePlaneName.addStretch()


        # vbox
        mainbox = QVBoxLayout()
        mainbox.addLayout(LineProbeStatus)
        #mainbox.addWidget(self.reInitProbe)
        mainbox.addLayout(LineScanStatus)
        mainbox.addLayout(LineHousekeeping)
        mainbox.addLayout(LineHousekeeping2)
        #mainbox.addWidget(self.scanStatusButton)
        mainbox.addLayout(LineTimer)
        mainbox.addLayout(LineNumFrames)
        mainbox.addLayout(LineResetFrames)
        mainbox.addLayout(LineElAngle)
        mainbox.addLayout(LineAllAngle)
        mainbox.addLayout(LineReceivingUDP)
        mainbox.addLayout(LineSendingUDP)
        mainbox.addLayout(LineRunningLocation)
        mainbox.addLayout(LineProjectName)
        mainbox.addLayout(LinePlaneName)
        mainbox.addWidget(self.saveLocation)
        mainbox.addWidget(self.saveLocationBox)
        #mainbox.addWidget(self.logLocation)
        #mainbox.addWidget(self.logLocationBox)
        mainbox.addWidget(self.IWG1)
        mainbox.addWidget(self.IWG1Box)
        mainbox.addWidget(self.shutdownProbe)
        mainbox.addStretch()

        self.setLayout(mainbox)
        self.setGeometry(100, 100, 400, 700)
        self.setWindowTitle('MTPRealTime')
        #self.show()
        '''
        self.cycleTimer = QtCore.QTimer()
        self.cycleTimer.timeout.connect(self.cycle)
        self.cycleTimer.setInterval(82) # mseconds
        '''
        # 82 ms fixes race condition that makes
        # arriving data concatinate
        # 72 mostly fixes it, but not all
        # Eline/Bline double sample
        # 62 does not 
        # 142, 82 ms can cause a pause at eline 

        #sys.exit(app.exec_())
        logging.debug("init ui done")

        '''
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
        #serialPort.close()
        serialPort=5
        logging.debug(serialPort)
        return serialPort

    # read in data from MTP, save to dict
    # signal is data to be written after
    def readCommData(self):

        self.saveProbeData()
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
        '''

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
        self.packetStore.setData("totalCycles",0) 


        self.continueCycling = False
        #self.initProbe()

        #self.reInitProbe.setText("Re-initialize Probe/Restart Scanning")
        #self.reInitProbe.setText("Reset Probe")
        #/self.homeScan()
        #self.mainloop(self.app, self.serialPort, self.configStore, self.dataFile)
        #self.cycle()

        self.app.processEvents()

    def shutdownProbeClicked(self, serialPort):
        logging.debug("shutdownProbe/quit clicked")
        self.closeComm(serialPort)
        self.continueCycling= False 
        self.packetStore.setData("quitClicked", True)
        self.app.processEvents()
        logging.debug("Safe exit")
        # need a timer in here to continue sending app.exits

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


    # will need dataFile, configs and others passed in
    def mainloop(self, app, serialPort, configStore, dataFile, iwgFile):
        # instantiate dict for commands

        self.isScanning = False
        logging.debug("1 : main loop")
        # shouldn't be in mainloop
        # Declare instance of command dictionary
        self.commandDict = MTPcommand()

        #Might not be in mainloop
        # Declare instance of packet store
        self.packetStore = StorePacket()
        # Declare instance of moveMTP class
        self.mover = moveMTP(self)
        self.udp = doUDP(self, app, iwgFile)
        # global storage for values collected from probe
        # storing them in dict introduced slowness
        self.iwgStore = 'IWG1,20101002T194729,39.1324,-103.978,4566.43,,14127.9,,180.827,190.364,293.383,0.571414,-8.02806,318.85,318.672,-0.181879,-0.417805,-0.432257,-0.0980951,2.36793,-1.66016,-35.8046,16.3486,592.062,146.734,837.903,9.55575,324.104,1.22603,45.2423,,-22    .1676,'
        # Well, there's the right way to do this
        # and the easy way. 
        # So until we're moving all the functions, 
        # this'll stay.
        self.serialPort = serialPort 
        self.configStore = configStore

        self.logProcessEvents(app)
        #self.app.processEvents()


        self.initProbe()
        #move home is part of initProbe now
        #self.homeScan()
        self.continueCycling = True
        previousTime = time.perf_counter()
        self.cyclesSinceLastStop = 0
        # First element in array is the number of angles
        # to keep the config the same as VB6 
        # for integrate
        elAngles = self.configStore.getData("El. Angles", lab=False)
        nfreq = self.configStore.getData("Frequencies", lab=True)
        #logging.debug("Frequencies from config: %r", nfreq)
        nfreq = nfreq[1: len(nfreq)]
        #logging.debug("Frequencies without size: %r", nfreq)
        self.app = app

        # loop over " scan commands"
        self.probeStatusLED.setPixmap(self.ICON_GREEN_LED.scaled(40, 40))
        self.scanStatusLED.setPixmap(self.ICON_GREEN_LED.scaled(40, 40))

        while self.continueCycling:
            self.IWG1Box.setPlainText(self.iwgStore)
            self.logProcessEvents(app)
            #self.app.processEvents()
            logging.info("mainloop                                                                                                                 asdfasdf")
            # check here to exit cycling
            logging.info("mainloop1")
            # use the MTPmove aline
            packetStartTime = time.gmtime()
            self.alineStore = self.Aline()
            logging.info("mainloop2")

            # Bline: long
            self.blineStore = 'B' + self.Bline(elAngles, nfreq)
            self.logProcessEvents(app)
            logging.info("mainloop3")

            self.m01Store = self.m01()
            self.m02Store = self.m02()
            self.ptStore = self.pt()
            self.logProcessEvents(app)
            logging.info("mainloop4")
            # Eline: long 
            self.elineStore = 'E' + self.Eline(nfreq)
            self.logProcessEvents(app)
            logging.info("mainloop5")
            # save to file
            # assumes everything's been decoded from hex
            saveData = self.mover.saveData(packetStartTime, dataFile)
            self.logProcessEvents(app)
            logging.info("mainloop6")

            # send packet over UDP
            # also replaces spaces with commas and removes start strings
            # speed may be an issue here
            #self.udp.sendUDP(self.mover.formUDP())
            udpPacket = self.mover.formUDP(packetStartTime)
            self.logProcessEvents(app)
            logging.info("mainloop6")
            print(udpPacket)
            self.udp.sendUDP(udpPacket, saveData)
            self.logProcessEvents(app)
            logging.info("mainloop8")
            logging.debug("sent UDP packet")

            # collect, update, display loop stats
            previousTime = self.cycleStats(previousTime)

            #time.sleep(1)

        logging.debug("Main Loop Stopped")
        self.scanStatusLED.setPixmap(self.ICON_RED_LED.scaled(40, 40))
        if self.packetStore.getData("quitClicked"):
            app.exit(0)

    def cycleStats(self, previousTime):
        logging.debug("cycleStats")

        # loop timer
        nowTime = time.perf_counter()
        elapsedTime = nowTime - previousTime
        logging.debug("elapsed Loop Time: %s", elapsedTime)
        previousTime = nowTime
        
        # total frames(m01,m02,pt,Eline,aline,bline, IWG) taken since startup
        totalCycles = self.packetStore.getData("totalCycles") + 1 
        self.packetStore.setData("totalCycles", totalCycles) 
        logging.info("cycleStats totalCycles/cycleNumber: %s", totalCycles)
        
        # frames taken since last "stop probe"
        self.cyclesSinceLastStop = self.cyclesSinceLastStop + 1

        # Update GUI
        self.loopTimerBox.clear()
        self.loopTimerBox.setText("{:0.2f}".format(elapsedTime))
        self.totalNumFramesBox.clear()
        self.totalNumFramesBox.setText(str(totalCycles))
        self.numFramesSinceLastResetBox.clear()
        self.numFramesSinceLastResetBox.setText(str(self.cyclesSinceLastStop))
        
        return previousTime

    def waitForRadiometerWindow(self, isVisible = True):
        i=0
        #error_dialog = app.QErrorMessage()
        #error_dialog.showMessage('Oh no!')   

        # Pauses program execution until ok pressed
        progress = QDialog()
        progress.setModal(False)
        if isVisible:
            progress.show()
            logging.debug("Show waitForRadiometerWindow")
        else: 
            progress.hide()
            logging.debug("hide waitForRadiometerWindow")

        return False




        #from initMoveHome
    def readEchos(self,num):
        buf = b''
        for i in range(num):
            self.app.processEvents()
            self.IWG1Box.setPlainText(self.iwgStore)
            # readline in class serial library vs serial Qt library
            # serial qt is uesd in main probram, so need the timeout
            readLine =self.serialPort.canReadLine(500)
            if readLine is None:
                logging.debug("Nothing to read")
            else:
                buf = buf + readLine

        logging.debug("read %r", buf)
        return buf



    def moveComplete(self,buf):
        # returns true if '@' is found,
        # needs a timeout if comand didn't send properly
        if buf.find(b'@') >= 0:
            return True
        return False


    def sanitize(self,data):
        data = data[data.data().find(b':') + 1 : len(data) - 3]
        placeholder = data.data()#.decode('ascii')
        place = placeholder.split(' ')
        ret = ''
        for datum in place:
            ret += '%06d' % int(datum,16) + ' '

        return ret

    def findChar(self,array,binaryCharacter):
        # status = 0-6, C, B, or @
        # otherwise error = -1
        #saveIndex = echo.data().find(binaryString)
        logging.debug("findChar:array %r",array)
        if array == b'':
            logging.debug("findChar:array is none %r",array)
            # if there is no data
            return -1
        else:
            index = array.data().find(binaryCharacter)
            if index>-1:
                #logging.debug("status: %r, %r", array[index], array)
                return array[index]
            else:
                logging.error("status unknown, unable to find %r: %r",  binaryCharacter, array)
                return -1

    def probeResponseCheck(self):
            self.serialPort.sendCommand(b'V\r\n')
            if self.findChar(self.readEchos(3), b"MTPH_Control.c-101103>101208") != -1:
                logging.info("Probe on, responding to version string prompt")
                return True
            else:
                logging.info("Probe not responding to version string prompt")
                return False



    def truncateBotchedMoveCommand(self):
            self.serialPort.sendCommand(b'Ctrl-C\r\n')
            if self.findChar(self.readEchos(3),b'Ctrl-C\r\n') != -1:
                logging.info("Probe on, responding to Ctrl-C string prompt")
                return True
            else:
                logging.info("Probe not responding to Ctrl-C string prompt")
                return False


    def probeOnCheck(self):
        self.app.processEvents()
        if self.findChar(self.readEchos(3), b"MTPH_Control.c-101103>101208") != -1:
            logging.info("Probe on, Version string detected")
            return True
        else:
            logging.debug("No version startup string from probe found, sending V prompt")
            if self.probeResponseCheck():
                return True
            else:
                if self.truncateBotchedMoveCommand():
                    logging.warning("truncateBotchedMoveCommand called, ctrl-c success")
                    return True
                else:
                    logging.error("probe not responding to truncateBotchedMoveCommand ctrl-c, power cycle necessary")
                    return False

        logging.error("probeOnCheck all previous logic tried, something's wrong")
        return False



    def sendInit1(self):
        # Init1
        self.serialPort.sendCommand(b'U/1f1j256V50000R\r\n')
        # returns:
        # U/1f1j256V50000R\r\n
        # U:U/1f1j256V50000R\r\n
        # Step:\xff/0@\r\n
        # if already set to this
        # last line replaced by
        # Step:/0B\r\n
        # if too eary in boot phase (?)
        # Have seen this near boot:
        #  b'\x1b[A\x1b[BU/1f1j256V50000R\r\n'
        # And this in cycles
        #  Step:\xff/0@\r\n - makes ascii parser die
        #  Step:/0C\r\n - makes fix for above not work
        #  Step:\r\n
        #

        return self.readEchos(3)
    def sendInit2(self):
        # Init2
        self.serialPort.sendCommand(b'U/1L4000h30m100R\r\n')
        # normal return:
        #
        # U/1f1j256V50000R\r\n
        # U:U/1f1j256V50000R\r\n
        # b'Step:\xff/0@\r\n'

        # error returns:
        # \x1b[A\x1b[BU/1f1j256V50000R
        # Step:\xff/0B\r\n'
        #
        return self.readEchos(3)

    def init(self):
        # errorStatus = 0 if all's good
        # -1 if echos don't match exact return string expected
        # -2 if unexpected status
        #
        errorStatus = 0
        # 12 is arbirtary choice. Will tune in main program.
        while errorStatus < 12:
            answerFromProbe = self.sendInit1()
            # check for errors/decide if resend?
            if self.findChar(answerFromProbe, b'@') != -1:
                errorStatus = 12
                # success
            elif self.findChar(answerFromProbe, b'B') != -1:
                logging.warning(" Init 1 status B, resending.")
                errorStatus = errorStatus + 1
            elif self.findChar(answerFromProbe, b'C') != -1:
                logging.warning(" Init 1 status C, resending.")
                errorStatus == errorStatus + 1
            else:
                logging.warning(" Init 1 status else, resending.")
                errorStatus == errorStatus + 1



        self.serialPort.sendCommand(b'S\r\n')
        buf = self.readEchos(3)

        errorStatus = 0
        # 12 is arbirtary choice. Will tune in main program.
        while errorStatus < 12:
            answerFromProbe = self.sendInit2()
            # check for errors/decide if resend?
            if self.findChar(answerFromProbe, b'@') != -1:
                errorStatus = 12
                # success
            elif self.findChar(answerFromProbe, b'B') != -1:
                logging.warning(" Init 2 status B, resending.")
                errorStatus = errorStatus + 1
            elif self.findChar(answerFromProbe, b'C') != -1:
                logging.warning(" Init 2 status C, resending.")
                errorStatus == errorStatus + 1
            else:
                logging.warning(" Init 2 status else, resending.")
                errorStatus = errorStatus + 1

        # After both is status of 7 ok?
        # no
        # 4 is preferred status
        # if after both inits status = 5
        # do an integrate, then a read to clear

        return errorStatus

    def moveHome(self):
        errorStatus = 0
        # acutal initiate movement home
        self.serialPort.sendCommand(b'U/1J0f0j256Z1000000J3R\r\n')
        self.readEchos(3)
        # if spamming a re-init, this shouldn't be needed
        # or should be in the init phase anyway
        #serialPort.write(b'U/1j128z1000000P10R\r\n')
        #readEchos(3)

        # Update GUI
        # Note that having the clear here masks the 'target, target'
        # potential long scan indicator
        self.elAngleBox.clear()
        self.elAngleBox.setText("Target")
        # sets 'known location' to 0
        self.packetStore.setData("currentClkStep", 0)

        # S needs to be 4 here
        # otherwise call again
        # unless S is 5
        # then need to clear the integrator
        # with a I (and wait 40 ms)
        #errorStatus = self.isMovePossibleFromHome(12,True)
        return errorStatus


    def getStatus(self):
        # status = 0-6, C, B, or @
        # otherwise error = -1
        # check for T in ST:0X
        # return status X
        self.serialPort.sendCommand(b'S\r\n')
        answerFromProbe = self.readEchos(4)
        logging.debug("echos from status read: %r", answerFromProbe)
        return self.findCharPlusNum(answerFromProbe, b'T', offset=3)

    def findCharPlusNum(self,array, binaryCharacter, offset):
        # status = 0-6, C, B, or @
        # otherwise error = -1
        logging.debug("findCharPlusNum:array %r",array)
        if array == b'':
            logging.debug("findCharPlusNum:array is none %r",array)
            # if there is no data
            return -1
        else:
            index = array.data().find(binaryCharacter)
            logging.debug("findCharPlusNum array: %r",array.data())
            if index>-1:
                #logging.debug("status with offset: %r, %r", asciiArray[index+offset], asciiArray)
                return array.data()[index+offset:index+offset+1].decode('ascii')
            else:
                logging.error("status with offset unknown, unable to find %r: %r",  binaryCharacter, array)
                return -1



    def isMovePossibleFromHome(self, maxDebugAttempts, scanStatus):
        # returns 4 if move is possible
        # otherwise does debugging
    
        # debugging needs to know if it's in the scan or starting

        # and how many debug attempts have been made
        # should also be a case statement, 6, 4, 7 being most common



        counter =0
        while counter < maxDebugAttempts:
            s = self.getStatus()
            counter = counter + 1
            if s == '0':
                # integrator busy, Stepper not moving, Synthesizer out of lock, and spare = 0
                logging.debug('isMovePossible status 0')
                return 0
            elif s == '1':
                logging.debug('isMovePossible status 1')
                return 1
            elif s == '2':
                logging.debug('isMovePossible status 2')
                return 2
            elif s == '3':
                logging.debug('isMovePossible status 3')
                return 3
            elif s == '4':
                logging.debug("isMovePossible is 4 - yes, return")
                counter = maxDebugAttempts
                return 4
                #continue on with moving
            elif s == '5' :
                # do an integrate
                self.serialPort.sendCommand(b'I\r\n')
                # Integrate takes 40 ms to clear
                time.sleep(.0040)
                self.readEchos(3)
                logging.debug("isMovePossible, status = 5")
            elif s =='6':
                # can be infinite 6's,
                # can also be just wait a bit
                #s = self.getStatus()
                if counter<12:
                    logging.debug("isMovePossible, status = 6, counter = %r", counter)
                else:
                    logging.error("isMovePossible, status = 6, counter = %r", counter)
                    return -1
            elif s == '7':
                logging.debug('isMovePossible status 7')
    

            else:
                logging.error("Home, status = %r", s)




    def initForNewLoop(self):
        # This is an init command
        # but it moves the motor faster, so not desired
        # in initial startup/go home ?
        # Correct, necessary before move-to-angle commands

        # do a check for over voltage
        # first move command in loop errors:
        # status = 6, but no move
        # step 0C
        self.serialPort.sendCommand(b'U/1j128z1000000P10R\r\n')

        self.readEchos(3)
        return True

    # if on first move status 6 for longer than expected
    # aka command sent properly, but actual movement
    # not initiated, need a Ctrl-c then re-init, re-home

    # on boot probe sends
    # MTPH_Control.c-101103>101208
    # needs to be caught first before other init commands are sent
    # also response to V
    def initProbe(self):
        self.waitForRadiometerWindow(isVisible = True)

        probeResponding = False
        while (1):
            if probeResponding == False:
                while self.probeOnCheck() == False:
                    self.app.processEvents()
                    self.IWG1Box.setPlainText(self.iwgStore)
                    logging.error("probe off or not responding")
                logging.info("Probe on check returns true")
                probeResponding = True
            self.readEchos(3)
            self.init()
            self.readEchos(3)
            self.moveHome()
            if (self.isMovePossibleFromHome(maxDebugAttempts=20, scanStatus='potato')==4):
                if self.initForNewLoop():
                    self.waitForRadiometerWindow(isVisible = False)
                    #start actual cycling
                    break











        '''

    def initProbe(self):
        i=0
        while i < 100000:
            # keep trying to initialize the probe
            # grab whatever is in the buffer
            # will terminate at \n if it finds one
            i1 = self.tryInit('init1')
            i2 = self.tryInit('init2')
            if i1 and i2:
                logging.debug('probe initialized')
                break
            i = i + 1
        i = 0
        

    def tryInit(self, whichInit):
        # init probe
        sendCommand = self.commandDict.getCommand(whichInit)
        self.serialPort.sendCommand(sendCommand)
        echo, sFlag, foundIndex = self.readUntilFound(b'@', 100, 10, isHome=False)
        while echo == b'-1':
            logging.debug("Init command failed, sending again")
            self.serialPort.sendCommand(sendCommand)
            echo, sFlag, foundIndex = self.readUntilFound(b'@', 100, 10, isHome=False)
        logging.debug("Try init's send @, no move though echo: %s", echo)
        return True
        '''

    def readUntilFound(self, binaryString, timeout, canReadLineTimeout, isHome):
        i=0
        echo = b''
        sFlag = False
        while i < timeout:
            # grab whatever is in the buffer
            # will terminate at \n if it finds one
            self.logProcessEvents(self.app)

            echo = self.serialPort.canReadAllLines(canReadLineTimeout)#msec
            logging.debug("read until found: ")
            logging.debug(binaryString)
            logging.debug(echo)
            foundIndex = -1
            #logging.debug(echo)
            if echo is None or echo == b'':
                logging.debug(" readUntilFound: none case")
                i = i + 1
            else:    
                saveIndex = echo.data().find(binaryString)
                if saveIndex >= 0: 
                    logging.debug("received binary string match %r", echo)
                    foundIndex = saveIndex
                    logging.debug("foundIndex: %r", foundIndex)
                    return echo, sFlag, foundIndex
                elif echo.data().find(b'S') >= 0:
                    logging.debug("Found an S, setting sFlag to True")
                    sFlag = True
                    if isHome:
                        return b'-1', sFlag, foundIndex
                else:
                    logging.debug("didn't recieve binary string this loop")
                    i = i + 1
        logging.debug("readUntilFound timeout: returning b'-1'")
        return b'-1', sFlag, foundIndex


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
        self.continueCycling= False 
        logging.debug("scanStatusClicked")
        '''
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
        self.serialPort.sendCommand(self.commandDict.getCommand("read_M1"))
        '''
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
        '''

    def tick(self):
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("status")))
        return
        '''
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


    def initSaveIWGFile(self, flightNumber,projectName): 
        # Make iwg file path 
        path = os.path.dirname('C:\\Users\\lroot\\Desktop\\'+projectName+'\\data\\')
        if not os.path.exists:
            os.makedirs(path)
        saveIWGFileName = path+'\\'+"IWG_"+ time.strftime("%Y%m%d") + '_' + time.strftime("%H%M%S")+'.txt'
        # reopen file, no good way to sort via IWG + flight number w/o changing initSaveDataFile
        '''
        for filename in glob.glob(path + '\\*_' + flightNumber + '.mtp'):
            logging.debug("File exists")
            saveDataFileName=filename
        '''
         
        logging.debug("initIWGDataFile")
        return saveIWGFileName



    def initSaveDataFile(self, flightNumber,projectName):    
        # Make data file path 
        path = os.path.dirname('C:\\Users\\lroot\\Desktop\\'+projectName+'\\data\\')
        if not os.path.exists:
            os.makedirs(path)
        saveDataFileName = path+'\\'+time.strftime("%Y%m%d") + '_' + time.strftime("%H%M%S") + '_' + flightNumber + '.mtp'
        for filename in glob.glob(path + '\\*_' + flightNumber + '.mtp'):
            logging.debug("File exists")
            saveDataFileName=filename

        # 'b' allows writing the data from a binary format
        with open(saveDataFileName, "ab") as datafile:
                # this will be rewritten each time the program restarts
                datafile.write(str.encode("Instrument on " + time.strftime("%X") + " " + time.strftime("%m-%d-%y") + '\r\n'))
         
        logging.debug("initSaveDataFile")
        return saveDataFileName
        '''
    def cycle(self):
        # self.cycleTimer.stop()
        '''
        '''
        logging.debug("Start of cycle")
        self.serialPort.waitReadyRead(20)
        logging.debug("After ready read")
        buf = self.serialPort.readLine(70)
        logging.debug("after readline")
        logging.debug(buf.data())
        '''
        '''
        # this process Events can really slow things down
        # still necessary because recieved data has to be processed
        # before deciding if moving to next command or no.
        self.app.processEvents()
        logging.debug("Cycle, processEvents1")
        # at startup, when cycling = false sets probe to start position
        if self.packetStore.getData("desiredMode") == "init":
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
        # continue through the cycle
        logging.debug("cycle, before dispatch, with matchword:")
        logging.debug(matchWord)
        self.mover.dispatch(matchWord)
        logging.debug("cycle, after dispatch")
        #self.app.processEvents()
        logging.debug("Cycle, processEvents4")
        '''
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

    '''
    def moveWait(self):
        logging.debug("IN moveWait")
        i = 0
        while i< 20:
            self.serialPort.sendCommand(self.commandDict.getCommand("status"))
            echo, sFlag, foundIndex = self.readUntilFound(b'S', 10, 30, isHome=False)
            # do instring of ST:0#
            # location of T +3
            if echo != b'-1':
                findTheT = echo.data().find(b'T')
                if findTheT >=0:
                    # move along if status is not 2, 6, 10 or 14
                    # status 04 is correct status to move along for
                    logging.debug(echo[findTheT + 3])
                    if(echo[findTheT +3].isalpha()):
                        #sometimes there's an s that shows up here
                        logging.debug("moveWait ST:0S4\r\n case + %s", echo)
                    elif (int(echo[findTheT +3]) &2):
                        return

            else: 
                logging.debug("moveWait not = 7 echo %s", echo)
                logging.debug("moveWait len echo %s", len(echo))
            i = i + 1
        logging.debug("move wait timeout, move along")
    '''


    def homeScan(self):
        home1 = self.commandDict.getCommand("home1")
        home2 = self.commandDict.getCommand("home2")
        home3 = self.commandDict.getCommand("home3")
        # min time before it starts shaking/grinding
        # do need the extra checkAgain bit to be sure it gets home 
        # 0.1 has 10 long homescans in 315 scans
        # 0.115 is better, but still 1/hour
        # updated so sleepTime is halved for most loops, 
        # but in case of long scan has full time
        sleepTime = 0.2
        #self.serialPort.sendCommand(home1)
        self.moveCheckAgain(home1, sleepTime, isHome=True)
        logging.debug("home1 after move home") 

        sleepTime = 0.000
        self.moveCheckAgain(home2, sleepTime, isHome=True)
        logging.debug("home2 after step ") 
        
        # Update GUI
        # Note that having the clear here masks the 'target, target'
        # potential long scan indicator
        self.elAngleBox.clear()
        self.elAngleBox.setText("Target")
        # sets 'known location' to 0
        self.packetStore.setData("currentClkStep", 0)


    def m01(self):
        logging.debug("M01")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_M1")))
        # echo will echo "M  1" so have to scan for the : in the M line
        m, sFlag, foundIndex = self.readUntilFound(b'M01:', 100, 20, isHome=False)
        # set a timer so m01 values get translated from hex?
        m01 = self.mover.decode(m)
        return m01
        

    def m02(self):
        logging.debug("M02")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_M2")))
        m, sFlag, foundIndex = self.readUntilFound(b'M02:', 100, 20, isHome=False)
        m02 = self.mover.decode(m)
        return m02

    def pt(self):
        logging.debug("pt")
        self.serialPort.sendCommand((self.commandDict.getCommand("read_P")))
        p, sFlag, foundIndex = self.readUntilFound(b':', 100, 20, isHome=False)
        pt = self.mover.decode(p)

        return pt

    def Eline(self, nfreq):
        data = 0
        logging.debug("Eline")
        self.homeScan()
        # set noise 1
        # returns echo and b"ND:01\r\n" or b"ND:00\r\n"
        self.serialPort.sendCommand(self.commandDict.getCommand("noise1"))
        echo, sFlag, foundIndex = self.readUntilFound(b'ND:01',6, 4, isHome=False)
        data = self.integrate(nfreq)

        # set noise 0
        self.serialPort.sendCommand(self.commandDict.getCommand("noise0"))
        echo, sFlag, foundIndex = self.readUntilFound(b'ND:00',6, 4, isHome=False)
        return data + self.integrate(nfreq)

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
        #self.alineStore = aline

        self.packetStore.setData("angleI", 0) # angle index
        # update instantanious angle frame?

        # read_scan and read_encode are not used
        # They were to determine location of mirror
        # before the chain was added but since that
        # came about, they no longer have useful data

        #self.serialPort.sendCommand((self.commandDict.getCommand("read_scan")))
        #echo, sFlag, foundIndex = self.readUntilFound(b':', 10, 20, isHome=False)
        #echo, sFlag, foundIndex = self.readUntilFound(b'S', 10, 20, isHome=False)
        # b'Step:\xff/0`1000010\r\n'
        # echo = self.read(200,200)
        # need to implement the better logic counters in bline
        # for scanCount and encoderCount
        #self.packetStore.setData("scanCount", int(self.packetStore.getData("scanCount")) + 1)
        logging.debug("View: Aline end")
        return aline



    def Bline(self, angles, nfreq):

        logging.debug("Bline")
        # All R values have spaces in front
        logging.debug(angles)
        numAngles = angles[0]
        zel = angles[1]
        elAngles = angles[2:numAngles+2]
        logging.debug(elAngles)
        data = ''
        angleIndex = 0 #1-10
        for angle in elAngles: 
            # update GUI
            self.elAngleBox.clear()
            self.elAngleBox.setText(str(angle))
            self.IWG1Box.setPlainText(self.iwgStore)

            angleIndex = angleIndex + 1
            logging.debug("el angle: %f, ScanAngleNumber: %f", angle, angleIndex)
            self.logProcessEvents(self.app)
            #self.app.processEvents()

            # packetStore pitchCorrect should be button

            # get pitch corrected angle and
            # sends move command
            moveToCommand = self.mover.getAngle(angle, zel)
            #self.serialPort.sendCommand(str.encode(moveToCommand))
            if angle == elAngles[1]:
                sleepTime = 0.12
                time.sleep(0.002)
            else:
                #0.01 has many fewer spikes, but average takes too long
                #0.0045 more spikes, preferred for timing ... 
                sleepTime = 0.0075
            self.moveCheckAgain(str.encode(moveToCommand), sleepTime, isHome=False)

            #logging.debug("Bline find the @: %r", echo)
            # wait until Step:\xddff/0@\r\n is received

            data = data + self.integrate(nfreq)
            logging.debug(data)
        
        #self.updateRead("read_scan")
        #self.updateRead("read_enc")
        return data   

    def moveCheckAgain(self, sentCommand, sleepTime, isHome):
        # have to check for @ and status separately
        self.serialPort.sendCommand((sentCommand))
        # I really don't like having this process events in here
        # But is currently necessary for 1/s iwg processing
        # as there are at least 2 moves a cycle 
        # that take longer than 1 s
        self.logProcessEvents(self.app)
        #self.app.processEvents()
        i = 0
        while i < 2:
            # Might be possible to reduce this a bit
            echo, sFlag, foundIndex = self.readUntilFound(b'@',100, 20, isHome)
            # Only send again if homescan and timeout
            if echo == b'-1' and isHome:
                self.serialPort.sendCommand((sentCommand))
                i = i+1
                logging.debug("moveCheckAgain: sending move again, %r", echo)
            elif echo == b'-1' and sFlag:
                # check to see if empty 'Step' was received
                # in readUntilFound - means motor didn't actually
                # move despite getting the command
                # then remove isHome flag, bline moves
                # that get empty steps wont be stacking
                self.serialPort.sendCommand((sentCommand))
                i = i+1
                logging.debug("moveCheckAgain: timeout")
            else:
                logging.debug("moveCheckAgain: @ recieved %r, i = %s", echo, i)
                i=5
        logging.debug("sentCommand %s", sentCommand)

        # Too soon and status is always 6: homescan needs longer
        i = 0
        maxLoops = 12
        while i < maxLoops:
            i = i + 1
            time.sleep(sleepTime/2)
            self.serialPort.sendCommand(self.commandDict.getCommand('status'))
            # need readUntilFound to not exit on seeing an s here
            # but also need to keep isHome in this scope as True
            # for when it is actually called by home
            status, sFlag, foundIndex = self.readUntilFound(b'T', 10, 10, False)   
            logging.debug("FindtheT status: %r", status)
            # in case statusNum ==7, S was found, but ST## wasn't
            if status != b'-1':
                findTheT = status.data().find(b'T')
                if findTheT >=0:
                    # status 04 is correct statu, others require re-prompt
                    statusNum = status[findTheT + 3]
                    logging.debug('statusnum: %r', statusNum)
                    if statusNum == '4':
                        logging.debug('status is 4')
                        return True
                    elif statusNum == '7':
                        self.serialPort.sendCommand(
                                self.commandDict.getCommand('count'))
                        self.serialPort.sendCommand(
                                self.commandDict.getCommand('count2'))
                        logging.debug("status 7: sending integrate/read to fix")
                    elif statusNum == '6':
                        #i = i + 1
                        time.sleep(sleepTime/2)
                        if i < maxLoops/2:
                            # Longer wait to prevent long homescans,
                            # malset channels (eg. ST:04\r\nS\r\nST:00)
                            time.sleep(sleepTime/2)
                            logging.debug("moveCheckAgain, i<maxLoops/2, i = %r, mL/2 = %r", i, maxLoops/2)
                        elif isHome:
                            # Status 6 needs the command (j0f0) sent again
                            self.moveCheckAgain(sentCommand, sleepTime, isHome)
                            logging.debug("moveCheckAgain, isHome %s", isHome)
                        else:
                            # Status 6 with Move commands needs a wait
                            # do the status check again
                            logging.debug('moveCheckAgain T found, status 6')
                    else:
                        logging.debug("moveCheckAgain:status not 4,6,7: %s",
                                statusNum)
                        return
                else: 
                    logging.debug("moveCheckAgain: T not found")
            else:
                # send status again
                logging.debug("moveCheckAgain: T not found")
                #i = i + 1
        logging.debug("moveCheckAgain timeout %s ", status)


        
            
    def updateRead (self, scanOrEncode):
        i =0 
        while i < 11:
            self.serialPort.sendCommand((self.commandDict.getCommand(scanOrEncode)))
            # first there's the echo, then there's the probe's echo of that echo then
            echo, sFlag, foundIndex = self.readUntilFound(b':', 10, 20, isHome=False)
            # read_scan returns b'Step:\xff/0c1378147\r\n' 
            # then returns b'Step:\xff/0`1378147\r\n' 
            echo, sFlag, foundIndex = self.readUntilFound(b':', 10, 20, isHome=False)
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
                    logging.debug(int(readScan.decode('Ascii'),16)) 
                    self.scanCount = (1000000 - int(readScan.decode('Ascii')))
                    if self.scanCount >=0: 
                        self.scanCount = '+' +'%06d' % self.scanCount
                    self.packetStore.setData('scanCount', self.scanCount)
                else:
                    logging.debug("readEncode is: ")
                    logging.debug(readScan)
                    logging.debug(int(readScan.decode('Ascii'))) 
                    logging.debug(int(readScan.decode('Ascii'),16)) 
                    
                    self.scanCount = ((1000000 - int(readScan.decode('Ascii'))*16))
                    if self.scanCount >=0: 
                        self.scanCount = '+' +'%06d' % self.scanCount
                    self.packetStore.setData('encoderCount', self.scanCount)

                break
            i = i+1
        logging.debug('readencoder size: %d', echo.size())


    def quickRead(self, timeout):
        logging.debug("quickRead start")
        echo = self.serialPort.canReadLine(timeout)
        logging.debug(echo)
        datum = self.serialPort.canReadLine(timeout)
        logging.debug(datum)
        logging.debug("quickRead end")
        return datum

    def integrate(self, nfreq):
        # returns string of data values translated from hex to decimal
        # recepit of the @ from the move command has to occur before 
        # entry into this function

        data = ''
        isFirst = True
        for freq in nfreq:
            # tune echos received in tune function
            logging.debug("Frequency/channel:"+ str(freq))
            self.tune(freq, isFirst)
            # other channels than the first need resetting ocasionally. 
            # isFirst = False
            # clear echos 
            #dataLine = self.quickRead(25) # avg is ~9, max is currently 15
            self.getIntegrateFromProbe()
            # clear echos
            # avg is ~9, max observed issue at 25
            # dataLine = self.quickRead(30) 

            # actually request the data of interest
            echo = b'-1'
            while echo == b'-1':
                self.serialPort.sendCommand((self.commandDict.getCommand("count2")))
                echo, sFlag, foundIndex = self.readUntilFound(b'R28:', 10, 20, isHome=False)
                logging.debug("reading R echo %r", echo)

            logging.debug("Echo [foundIndex] = %r, echo[foundIndex + 4] = %r", echo[foundIndex], echo[foundIndex+4])
            # above to get rid of this extra find when probe loop time is an issue again
            findSemicolon = echo.data().find(b'8')
            #logging.debug("r value data: %s, %s, %s",echo[findSemicolon], echo[findSemicolon+1], echo[findSemicolon+6])
            datum = echo[findSemicolon+2: findSemicolon+8] # generally 4:10, ocasionally not. up to, not include last val
            logging.debug(datum)


            # translate from hex:
            datum = '%06d' % int(datum.data().decode('ascii'), 16)

            # append to string:
            data = data + ' ' + datum
            logging.debug (data)
        logging.debug (data)
        return data

    def getIntegrateFromProbe(self):
        # Start integrator I 40 command    
        self.serialPort.sendCommand((self.commandDict.getCommand("count")))                 # ensure integrator starts so then can
        i=0
        looptimeMS = 2
        looping = True
        while i < looptimeMS: 
            logging.debug("integrate loop 1, checking for odd number")
            if self.waitForStatus(b'5'):
                break
            if i == looptimeMS:
                self.serialPort.sendCommand((self.commandDict.getCommand("count")))
                i = looptimeMS/2
                looptimeMS = i
            i = i+1

        # check that integrator has finished
        i=0
        while i < 3: 
            logging.debug("integrate loop 2, checking for even number")
            if self.waitForStatus(b'4'):
                break
            i = i+1 
            logging.debug("integrator has finished")
        return True

    def waitForStatus(self, status):
        # add timeout?
        i = 0
        # While loop checks to ensure tune has been properly applied
        # VB6 checks for move along status with a
        #"if (status And 4) == 0 goto continue looping"
        # But the find requires a single number
        # most often it's 6, but sometimes it's 2
        # so the while shouldn't be done more than a few times to keep 
        # time between packets down.
        # in Tune status 0 is an error that requires resending the C
        # 
        while i < 5 :
            self.serialPort.sendCommand((self.commandDict.getCommand("status")))
            logging.debug("sent status request")
            echo, sFlag, foundIndex = self.readUntilFound(
                    b'S', 37, 55, isHome=False)
            logging.debug("status: %s, received Status: %s, ", status, echo)
            if echo != b'-1':
                statusFound = echo.data().find(status)
                if statusFound >= 0:
                    logging.debug("status searched: %s , found: %s",
                            int(status), int(echo[statusFound])) 
                    return True
                else:
                    logging.debug("status searched for: %r , found: %r",
                            status, echo)
                i = i + 1
            else:
                logging.debug("waitForStatus' readUntilFound timeout")
                i = i + 1
        logging.warning(" waitForStatus timed out: %s", int(status))
        return False


    def tune(self, fghz, isFirst):
        #these are static and can be removed from loop
        # fghz is frequency in gigahertz
        fby4 = (1000 * fghz)/4 #MHz
        chan = fby4/0.5  # convert to SNP channel (integer) 0.5 MHz = step size
        logging.debug("tune: chan = %s", chan)

        # either 'C' or 'F' set in packetStore
        # F mode formatting #####.# instead of cmode formatting #####
        # not sure it makes a difference

        # mode = self.parent.packetStore.getData("tuneMode")

        mode = 'C'
        self.serialPort.sendCommand(str.encode(str(mode) + '{:.5}'.format(str(chan)) +"\r\n")) # \n added by encode I believe
        #logging.debug("Tuning: currently using mode C as that's what's called in vb6")
        # no official response, just echos
        # and echos that are indistinguishable from each other
        # eg: echo when buffer is sending to probe is same
        # as echo from probe: both "C#####\r\n"
        # catch tune echos
        # official response is a status of 4
        echo, sFlag, foundIndex = self.readUntilFound(b'C', 100, 20, isHome=False)
        # wait for tune status to be 4
        # see comment in waitForStatus for frustration
        isFour = self.waitForStatus(b'4')
        
        # if it's the first channel, resend C
        # that seems to fail with status 0
        count = 0
        while not(isFour) and count < 3:
            count = count + 1 
            self.serialPort.sendCommand(str.encode(str(mode) + '{:.5}'.format(str(chan)) +"\r\n"))
            echo, sFlag, foundIndex = self.readUntilFound(b'C', 10, 8, isHome=False)
            isFour = self.waitForStatus(b'4')

    def getFlightNumber(self):
        # Dialog for setting flight number
        flightNum, ok = QInputDialog.getText(self, self.tr('FlightNum'), 
                self.tr('Please enter flight number (eg. TF00, RF01, FF00, CF05)'))

        # if ok is clicked
        if ok:
            logging.debug("flightnum %r", flightNum)
            return flightNum
        else:
            handle_error("Enter flight number")
            sys.exit()
        
'''

    def goAngle(self, targetEl, zel):
        # pitch and roll need to be instant values from IWG, updated 1x per cycle (??!?) in Aline
        if self.packetStore.getData("pitchCorrect"):
            targetClkAngle = targetEl + self.mover.fEc(Pitch_Frame, Roll_Frame, targetEl, EmaxFlag)
        else:
            logging.info("correcting Pitch")
            targetClkAngle = targetEl + self.mover.fEc(Pitch_Frame, Roll_Frame, targetEl, EmaxFlag)
            #targetClkAngle = targetEl + zel
        targetClkStep = targetClkAngle * self.packetStore.getData("stepsDegree")
        currentClkStep = self.packetStore.getData("currentClkStep")
        nsteps = targetClkStep - currentClkStep
        self.packetStore.setData("Nsteps", nsteps)

        # check that nsteps isn't 0
        if nstep == 0:
            logging.info("Nstep is zero loop!")
            # ? set nstep to nan?

        # drop anything after decimal point:
        nstepSplit = str(nstep).split('.')
        nstep = nstepSplit[0]
        if self.nstep[0] is '-':
            # nstep is negative
            nstepSplit = str(nstep).split("+")
            nstep = nstepSplit[1].rjust(6,'0')
        else:
            self.nstepSplit = str(nstep).split('-')
            nstep = nstepSplit[0].rjust(6,'0')

        if nstep is 0.0:
            logging.error("moving 0 steps, nstep calculation returned 0")

        backCommand = nstep + self.commandDict.getCommand("move_end")
        if self.nstepSplit[0] is '-':
            frontCommand= self.commandDict.getCommand("move_bak_front")
        else:
            frontCommand = self.commandDict.getCommand("move_fwd_front")
        # return should have switch value of "Step:"
        self.serialPort.sendCommand(str.encode(frontCommand + backCommand))
        self.packetStore.setData("targetClkStep", targetClkStep)
        # read echo 
        echo, sFlag, foundIndex = self.readUntilFound(b'C', 100, 20, isHome=False)
        logging.debug("goAngle echo: %s", echo)


        # wait until status returns @
        echo, sFlag, foundIndex = self.readUntilFound(b'@', 10, 20, isHome=False)
        logging.warning("goAngle, @ echo %r", echo)

        # self.parent.packetStore.setData("currentClkStep", self.targetClkStep)
        # set in serial to avoid infinite loop of zero nstep
        angleI = self.packetStore.getData("angleI") # angle index, zenith at 1
'''




def handle_error(error):
    em = QErrorMessage()
    em.showMessage(error)
    em.exec_()

def main():
    #    signal.signal(signal.SIGINT, ctrl_c)
    #logger = logging.getLogger('__name__')
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
            filename="MTPControl.log", level=logging.INFO)

    logging.warning("warning")
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)


    # Check for Config.mtph/Fatal Error
    # Read it in/ declare config dict
    path = os.path.dirname('C:\\Users\\lroot\\MTP\\src\\ctrl\\')
    configStore = StoreConfig(app)
    try:
        configStore.loadConfigMTPH()
    except Exception as err:
        handle_error("Config.mtph: " + str(err))
        sys.exit()

    # Check for Config.yaml/Fatal Error(?)
    #try:

    #except Exception as err:
    #    handle_error(str(err))
    #    sys.exit()

    # read it in

    # Eventually have serial port # in config.yaml
    # Serial Port Check/Fatal Error
    try:
        serialPort = SerialInit(app)
    except Exception as err:
        handle_error("SerialPort: " + str(err))
        sys.exit()



    ex = controlWindow(app)
    ex.show()

    # Prompt flight number
    flightNumber = ex.getFlightNumber()
    # project name should be gotten from config file, hardcoded here for now 
    projectName = 'TI3GER'

    dataFile = ex.initSaveDataFile(flightNumber,projectName)
    iwgFile = ex.initSaveIWGFile(flightNumber,projectName)
    logging.debug("dataFile: %r", dataFile)
    ex.saveLocationBox.setText('~/Desktop/'+ projectName +'/data')
    ex.flightNumberBox.setText(flightNumber)
    ex.projectNameBox.setText(projectName)
    # Will need data file and config dicts too
    ex.mainloop(app, serialPort, configStore, dataFile, iwgFile)
    # sys.exit(app.exec_())
    # ex.run()
    
if __name__ == '__main__':
    main()
