import os
import sys
import argparse
# import time
from PyQt5.QtWidgets import (QWidget,
                             QPushButton, QButtonGroup,
                             QPlainTextEdit,
                             QRadioButton, QVBoxLayout,
                             QLabel, QHBoxLayout,
                             QInputDialog,
                             QApplication, QErrorMessage)
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QLineEdit, QDialog)
from EOLpython.Qlogger.messageHandler import QLogger as logger
from os import path, makedirs


class controlWindow(QWidget):

    # self, MTPdict with iwg(has save) dict ,config dict, serialport)
    def __init__(self, app, tempData):
        super().__init__()
        varDict = {
            'Cycling': False,
            'lastSky': -1,  # readScan sets this to actual
        }

        self.app = app
        self.tempData = tempData

        # Create the GUI
        self.initUI()

    def closeEvent(self, event):
        logger.printmsg("debug", 
            "User has clicked the red x on the main window, unsafe exit")
        # self.shutdownProbeClicked(self.serialPort)
        # self.event.accept()
        
    def iwgProcessEvents(self):
        # logger.printmsg("debug", "Log Process Events Timestamp:" + str(time.gmtime()))
        self.IWG1Box.setPlainText(self.tempData.getData('iwgStore'))
        self.app.processEvents()

    def initUI(self):
        # QToolTip.setFont(QFont('SansSerif', 10))

        # false if not gui flag

        self.setToolTip('This is a <b>QWidget</b> widget')

        # Lables
        self.probeStatus = QLabel('Probe Status', self)
        self.scanStatus = QLabel('Scan Status', self)
        self.receivingIWG = QLabel("IWG Packet Status", self)
        self.IWGPort = QLabel("IWG Port # ", self)
        self.sendingUDP = QLabel("UDP Status", self)
        self.UDPPort = QLabel("UDP out Port # ", self)
        self.overHeat = QLabel("Overheat", self)
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

        self.loopTimer = QLabel("Time since last frame")
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
        # self.numFramesSinceLastResetBox.setOverwriteMode(True)
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
        self.allScanAnglesBox.setPlainText(
            '''80.00, 55.00, 42.00, 25.00, 12.00,
0.00, -12.00, -25.00, -42.00, -80.00''')
        self.allScanAnglesBox.setFixedHeight(self.shortWidth)
        self.allScanAnglesBox.setReadOnly(True)
        # Current elevation - GUI updates before correction applied
        self.elAngleBox = QLineEdit()
        self.elAngleBox.setText('Target')
        self.elAngleBox.setFixedWidth(self.shortWidth)
        # self.elAngleBox.setOverwriteMode(True)
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
        # self.shutdownProbe.clicked.connect(self.safeSleep)

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
        # LineRunningLocation.addWidget(self.locationLocal)
        # LineRunningLocation.addWidget(self.locationRemote)
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
        # mainbox.addWidget(self.reInitProbe)
        mainbox.addLayout(LineScanStatus)
        mainbox.addLayout(LineHousekeeping)
        mainbox.addLayout(LineHousekeeping2)
        # mainbox.addWidget(self.scanStatusButton)
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
        # mainbox.addWidget(self.logLocation)
        # mainbox.addWidget(self.logLocationBox)
        mainbox.addWidget(self.IWG1)
        mainbox.addWidget(self.IWG1Box)
        mainbox.addWidget(self.shutdownProbe)
        mainbox.addStretch()

        self.setLayout(mainbox)
        self.setGeometry(100, 100, 400, 700)
        self.setWindowTitle('MTPRealTime')
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

        # sys.exit(app.exec_())
        logger.printmsg("debug", "init ui done")

    def reInitProbeClicked(self):
        logger.printmsg("debug", "reInitProbeClicked")
        # need a read to clear echo here
        self.serialPort.sendCommand(str.encode(self.commandDict.getCommand(
            "ctrl-C")))
        # set init led to yellow
        self.probeStatusLED.setPixmap(self.ICON_YELLOW_LED.scaled(40, 40))
        # Reset should just send the re-initialization again
        # regardless of previous status
        # Therefore init shuold reset every cycle function
        '''
        if self.tempData.getData("isCycling"):
            self.tempData.setData("isCycling", False)
            self.reInitProbe.setText("Finishing scan: Please wait")
        else:
        '''
        self.tempData.setData("isCycling", True)
        self.reInitProbe.setText("Initializing ...")
        # set desired mode to init
        # changed these 3 from packetDict
        self.tempData.setData("desiredMode", "init")
        self.tempData.setData("switchControl", "resetInitScan")
        self.tempData.setData("scanStatus", False)
        self.tempData.setData("calledFrom", "resetProbeClick")
        self.tempData.setData("totalCycles", 0)

        self.continueCycling = False
        # self.initProbe()

        # self.reInitProbe.setText("Re-initialize Probe/Restart Scanning")
        # self.reInitProbe.setText("Reset Probe")
        # self.mainloop(self.app, self.serialPort, \
        #    self.configStore, self.dataFile)
        # self.cycle()

        self.app.processEvents()

    def shutdownProbeClicked(self, serialPort):
        logger.printmsg("debug", "shutdownProbe/quit clicked")
        # self.closeComm(serialPort)
        self.continueCycling = False
        self.tempData.setData("quitClicked", True)
        self.app.processEvents()
        logger.printmsg("debug", "Safe exit")
        # need a timer in here to continue sending app.exits
        self.app.exit(0)

    def waitForRadiometerWindow(self, isVisible=True):
        # error_dialog = app.Q ErrorMessage()
        # error_dialog.showMessage('Oh no!')

        # Pauses program execution until ok pressed
        progress = QDialog()
        progress.setModal(False)
        if isVisible:
            progress.show()
            logger.printmsg("debug", "Show waitForRadiometerWindow")
        else:
            progress.hide()
            logger.printmsg("debug", "hide waitForRadiometerWindow")

        return False

    # @pyqtSlot() # called a decorator, to make call faster
    def safeSleep(self):
        logger.printmsg("debug", 'sleep')
        self.timer.start(5000)
        logger.printmsg("debug", 'after timer')
        logger.printmsg("debug", "after process")
        return 0

    def scanStatusClicked(self):

        logger.printmsg("debug", "scanStatusClicked")
        self.continueCycling = False
        logger.printmsg("debug", "scanStatusClicked")

    def locationLocalClicked(self):
        logger.printmsg("debug", "LocationLocalClicked")
        return 0

    def locationRemoteClicked(self):
        logger.printmsg("debug", "LocationRemoteClicked: Sorry not yet implemented")
        return 0

    def paintCircle(self, color):
        painter = QtGui.QPainter(self)
        size = 10
        if color == 'red':
            logger.printmsg("debug", 'red')
            painter.setBrush(QtGui.QColor(0, 0, 255))
            # xoffset, yoffset, diameter, diameter
            painter.drawEllipse(12, 15, size, size)
            logger.printmsg("debug", "printing red")

        if color == 'yellow':
            logger.printmsg("debug", 'Yellow')
            painter.setBrush(QtGui.QColor(0, 255, 0))
            # xoffset, yoffset, diameter, diameter
            painter.drawEllipse(12, 15, size, size)
            logger.printmsg("debug", "printing yellow")

        if color == 'green':
            logger.printmsg("debug", "green")
            painter.setBrush(QtGui.QColor(255, 0, 0))
            # xoffset, yoffset, diameter, diameter
            painter.drawEllipse(12, 15, size, size)

        else:
            logger.printmsg("debug", "Color not defined")
        painter.end()

    def setLEDred(self, led):
        led.setPixmap(self.ICON_RED_LED.scaled(40, 40))

    def setLEDyellow(self, led):
        led.setPixmap(self.ICON_YELLOW_LED.scaled(40, 40))

    def setLEDgreen(self, led):
        led.setPixmap(self.ICON_GREEN_LED.scaled(40, 40))

    def getFlightNumber(self):
        # Dialog for setting flight number
        flightNum, ok = QInputDialog.getText(self, self.tr('FlightNum'),
                                        self.tr('''Please enter flight number
                                        (eg. TF00, RF01, FF00, CF05)'''))

        # if ok is clicked
        if ok:
            logger.printmsg("debug", "flightnum %r", flightNum)
            return flightNum
        else:
            handle_error("Enter flight number")
            sys.exit()

    def atTarget(self):
        # Update GUI
        # Note that having the clear here masks the 'target, target'
        # potential long scan indicator
        self.elAngleBox.clear()
        self.elAngleBox.setText("Target")

    def updateAngle(self, angle):
        self.elAngleBox.clear()
        self.elAngleBox.setText(angle)

    def updateGUIEndOfLoop(self, elapsedTime,
                           totalCycles, cyclesSinceLastStop):
        self.loopTimerBox.clear()
        self.loopTimerBox.setText("{:0.2f}".format(elapsedTime))
        self.totalNumFramesBox.clear()
        self.totalNumFramesBox.setText(totalCycles)
        self.numFramesSinceLastResetBox.clear()
        self.numFramesSinceLastResetBox.setText(cyclesSinceLastStop)
