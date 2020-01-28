import sys
import signal
#import serial
import logging
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
        # set init led to yellow
        self.probeStatusLED.setPixmap(self.ICON_YELLOW_LED.scaled(40, 40))

        if self.packetStore.getData("isCycling"): 
            self.packetStore.setData("isCycling", False)
            self.reInitProbe.setText("Finishing scan: Please wait")
        else:
            self.packetStore.setData("isCycling", True)
            self.reInitProbe.setText("Initializing ...")
        #set desired mode to init
        # changed these 3 from packetDict
        self.packetStore.setData("desiredMode", "init")
        self.packetStore.setData("scanStatus", False)
        self.packetStore.setData("calledFrom", "resetProbeClick")
        self.cycleTimer.start()
        self.cycle()

        self.app.processEvents()

    def shutdownProbeClicked(self, serialPort):
        logging.debug("shutdownProbe/quit clicked")
        self.closeComm(serialPort)
        logging.debug("Safe exit")
        app.exit(0)

    def mainloop(self):
        # instantiate dict for commands

        self.isScanning = False
        logging.debug("1 : main loop")
        self.commandDict = MTPcommand()
        self.packetStore = StorePacket()
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
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("status")))
        # sPort = self.openComm(serialPort)
        self.app.processEvents()
        '''
        '''
        logging.debug("main loop")
        # Declare instance of moveMTP class
        self.mover = moveMTP(self)


        return 0

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
        #check for config file
        #reload config
        #    - calculate MAM
        logging.debug("initConfig")

    def cycle(self):
        self.app.processEvents()
        # at startup, when cycling = false sets probe to start position
        if self.packetStore.getData("desiredMode") is "init":
            self.probeStatusLED.setPixmap(self.ICON_YELLOW_LED.scaled(40, 40))
        elif self.packetStore.getData("isCycling"):
            self.probeStatusLED.setPixmap(self.ICON_GREEN_LED.scaled(40, 40))
        else:
            self.probeStatusLED.setPixmap(self.ICON_RED_LED.scaled(40, 40))


        # make an enum and only move on from first function when returned status

        # open save file
        # add header "Instrument on " + time + " " + date

        self.cycleTimer.stop()
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
            self.app.processEvents()
            
        if self.packetStore.getData("currentMode") is 'init':
            # stop if matchword = Aline
            if matchWord is "Aline":
                # stop timer
                self.cycleTimer.stop()
                # set the button text back to reset
                self.reInitProbe.setText("Reset Probe")
                # set the init light to green
                # self.probeStatusLED.setPixmap(self.ICON_GREEN_LED.scaled(40,40))

        # if bline, set new frame? or set in bline

        # with timer these should become unnecessary     
        self.app.processEvents()
        time.sleep(0.2)
        self.app.processEvents()
        # continue through the cycle
        logging.debug("cycle, before dispatch, with matchword:")
        logging.debug(matchWord)
        self.mover.dispatch(matchWord)
        logging.debug("cycle, after dispatch")
        self.app.processEvents()
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


    def initConfig(self):
        ''' reads config file into dictionary to change default values '''
        ''' to be implemented '''
        logging.debug("initConfig")
        #self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("read_scan")))

    def initScan(self):
        logging.debug("cycle")
        gearRatio = 80/20                           # 2007/11/29, assumes "j256" for 
        stepsDegree = gearRatio * (128 * (200/300)) # fiduciary and "j128" for normal run
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("init1")))
        logging.debug("cycle1")
        if (initSwitch):
            self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("init2")))
            logging.debug("cycle2")



    def homeScan(self):
        logging.debug("homeScan")
        lastSky = self.readScan()


    def m01(self):
        logging.debug("M01")
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("read_M1")))

    def m02(self):
        logging.debug("M02")
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("read_M2")))

    def pt(self):
        logging.debug("pt")
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand("read_P")))

    def Eline(self):
        logging.debug("Eline")

    def Aline(self):
        logging.debug("Aline")

    #def Bline(self):
    #    logging.debug("Bline")
    #    scanNum = 1000000 - self.readScan()

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
