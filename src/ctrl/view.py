###############################################################################
# Code to display a GUI front-end to MTPcontrol
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import time
import select
from PyQt5.QtWidgets import QWidget, QPushButton, QPlainTextEdit, \
                            QVBoxLayout, QLabel, QHBoxLayout, QGroupBox, QFrame
from PyQt5 import QtGui
from PyQt5.QtCore import QSize, QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import (QLineEdit, QDialog)
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class Worker(QObject):
    looping = pyqtSignal()

    def __init__(self):
        super(Worker, self).__init__()
        self._isRunning = True

    def loop(self):
        """ Just loop and emit a signal every 0.1 seconds """
        while self._isRunning is True:
            time.sleep(0.1)
            self.looping.emit()

    def stop(self):
        self.run = False
        self._isRunning = False


class MTPControlView(QWidget):

    def __init__(self, app, client):

        self.app = app
        self.client = client

        # The QMainWindow class provides a main application window
        super().__init__()

        # Catch if user closes window via red circle in upper left
        app.aboutToQuit.connect(self.shutdownProbeClicked)

        # Create the GUI
        self.initUI()
        self.show()

        # On launch of GUI, start a thread that loops and attempts to connect
        # to the IWG socket and check for a new UDP packet once every tenth
        # of a second. Using a thread keeps the GUI responsive.
        self.thread = QThread()  # Instantiate the threaad
        self.worker = Worker()   # Instantiate a worker to loop & emit signals
        self.worker.moveToThread(self.thread)  # Put the worker in the thread
        self.thread.started.connect(self.worker.loop)  # Start the worker
        self.worker.looping.connect(self.connectIWG)  # On signal, read IWG
        self.thread.start()  # Start the thread

    def connectIWG(self):
        """
        Connect to IWG data stream and see if there is a packet available to
        read
        """
        iwg = self.client.getIWG()
        ports = [iwg.socket()]
        read_ready, _, _ = select.select(ports, [], [], 0.01)

        self.client.processIWG(read_ready, self.IWG1Box)

    def initUI(self):
        """ Create the GUI """

        # Lables
        self.probeStatus = QLabel("Probe Status")
        self.scanStatus = QLabel("Scan Status ")  # space is so layout is even
        self.receivingIWG = QLabel("IWG Packet Status")
        self.IWGPort = QLabel("IWG Port #")
        self.sendingUDP = QLabel("UDP Status")
        self.UDPPort = QLabel("UDP out Port #")
        self.NIDASPort = QLabel("NIDAS Port #")
        self.overHeat = QLabel("Overheat    ")  # space is so layout is even
        self.overVoltage = QLabel("Overvoltage ")  # space is so layout is even
        self.projectName = QLabel("Project Name")
        self.flightNumber = QLabel("Flight #")
        self.planeName = QLabel("Aircraft Name")
        self.nominalPitch = QLabel("Nominal Pitch")
        self.nominalRoll = QLabel("Nominal Roll")
        self.frequencies = QLabel("Frequencies")
        self.allScanAngles = QLabel("Elevation Angles:")
        self.projectLocation = QLabel("Data/logs saved to:")

        self.loopTimer = QLabel("Scan interval")
        self.totalNumFrames = QLabel("Total scans")
        self.numFramesSinceLastReset = QLabel("Scans since reset")
        self.elAngle = QLabel("Current El. Angle")
        self.IWG1 = QLabel("IWG1")

        # Text boxes
        self.shortWidth = 60  # Width of small text boxes

        self.projectLocationBox = QLineEdit()
        self.projectLocationBox.setStyleSheet("padding-left:5")
        self.projectLocationBox.setText('~/Desktop/$Project')
        self.projectLocationBox.setReadOnly(True)

        self.loopTimerBox = QLineEdit()
        self.loopTimerBox.setText('Start')
        self.loopTimerBox.setStyleSheet("padding-left:5")
        self.loopTimerBox.setFixedWidth(self.shortWidth)
        self.loopTimerBox.setReadOnly(True)
        self.totalNumFramesBox = QLineEdit()
        self.totalNumFramesBox.setText('0')
        self.totalNumFramesBox.setStyleSheet("padding-left:5")
        self.totalNumFramesBox.setFixedWidth(self.shortWidth)
        self.totalNumFramesBox.setReadOnly(True)
        self.numFramesSinceLastResetBox = QLineEdit()
        self.numFramesSinceLastResetBox.setText('0')
        self.numFramesSinceLastResetBox.setStyleSheet("padding-left:5")
        self.numFramesSinceLastResetBox.setFixedWidth(self.shortWidth)
        self.numFramesSinceLastResetBox.setReadOnly(True)

        # from config.mtph
        self.planeNameBox = QLineEdit()
        self.planeNameBox.setText(self.client.configfile.getVal('platformID'))
        self.planeNameBox.setStyleSheet("padding-left:5")
        self.planeNameBox.setReadOnly(True)
        self.nominalPitchBox = QLineEdit()
        self.nominalPitchBox.setText('2.7')
        self.nominalPitchBox.setStyleSheet("padding-left:5")
        self.nominalPitchBox.setFixedWidth(self.shortWidth)
        self.nominalPitchBox.setReadOnly(True)
        self.nominalRollBox = QLineEdit()
        self.nominalRollBox.setText('0')
        self.nominalRollBox.setStyleSheet("padding-left:5")
        self.nominalRollBox.setFixedWidth(self.shortWidth)
        self.nominalRollBox.setReadOnly(True)
        self.frequenciesBox = QLineEdit()  # also known as channels
        textfrequencies = ", "
        self.frequenciesBox.setText(textfrequencies.join(
            self.client.configfile.getVal('Frequencies')))
        self.frequenciesBox.setFixedWidth(155)
        self.frequenciesBox.setStyleSheet("padding-left:5;")
        self.frequenciesBox.setReadOnly(True)
        self.allScanAnglesBox = QPlainTextEdit()
        textScanAngles = ", "
        self.allScanAnglesBox.setPlainText(textScanAngles.join(
            self.client.configfile.getVal('ElAngles')))
        self.allScanAnglesBox.setFixedHeight(25)
        self.allScanAnglesBox.setReadOnly(True)
        # Current elevation - GUI updates before correction applied
        self.elAngleBox = QLineEdit()
        self.elAngleBox.setText('Target')
        self.elAngleBox.setStyleSheet("padding-left:5")
        self.elAngleBox.setFixedWidth(self.shortWidth)
        self.elAngleBox.setReadOnly(True)

        # from/to (flight name) config.yaml
        self.projectNameBox = QLineEdit()
        self.projectNameBox.setText(self.client.configfile.getVal('project'))
        self.projectNameBox.setStyleSheet("padding-left:5")
        self.projectNameBox.setReadOnly(True)

        self.flightNumberBox = QLineEdit()
        self.flightNumberBox.setText(self.client.configfile.getVal('fltno'))
        self.flightNumberBox.setStyleSheet("padding-left:5")
        self.flightNumberBox.setReadOnly(True)

        self.IWGPortBox = QLineEdit()
        self.IWGPortBox.setText(str(
                                self.client.configfile.getInt('iwg1_port')))
        self.IWGPortBox.setStyleSheet("padding-left:5")
        self.IWGPortBox.setFixedWidth(self.shortWidth)
        self.IWGPortBox.setReadOnly(True)
        self.UDPPortBox = QLineEdit()
        self.UDPPortBox.setText(str(self.client.configfile.getInt(
                                    'inst_read_port')))
        self.UDPPortBox.setStyleSheet("padding-left:5")
        self.UDPPortBox.setFixedWidth(self.shortWidth)
        self.UDPPortBox.setReadOnly(True)

        self.NIDASPortBox = QLineEdit()
        self.NIDASPortBox.setText(str(self.client.configfile.getInt(
                                    'nidas_port')))
        self.NIDASPortBox.setStyleSheet("padding-left:5")
        self.NIDASPortBox.setFixedWidth(self.shortWidth)
        self.NIDASPortBox.setReadOnly(True)

        self.IWG1Box = QPlainTextEdit()
        self.IWG1Box.setPlainText('IWG1,YYYYMMDDTHHMMSS,-xx.xxxx,xxx.xxx,')
        self.IWG1Box.setReadOnly(True)
        self.IWG1Box.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.client.init.setIWG1Box(self.IWG1Box)

        # Push Buttons
        self.initProbe = QPushButton("(Re)init Probe")
        self.initProbe.clicked.connect(self.initProbeClicked)
        self.initProbe.setEnabled(True)
        self.scanStatusButton = QPushButton("Start Scanning")
        self.scanStatusButton.clicked.connect(self.scanStatusClicked)
        self.scanStatusButton.setEnabled(True)
        self.shutdownProbe = QPushButton("Quit")
        self.shutdownProbe.clicked.connect(self.shutdownProbeClicked)

        # staus 'LED's'
        self.probeStatusLED = QLabel('')
        self.setLEDred(self.probeStatusLED)
        self.scanStatusLED = QLabel('')
        self.setLEDred(self.scanStatusLED)
        self.receivingIWGLED = QLabel('')
        self.setLEDred(self.receivingIWGLED)
        self.sendingUDPLED = QLabel('')
        self.setLEDred(self.sendingUDPLED)
        self.overHeatLED = QLabel('')  # Updated at end of each scan
        self.setLEDgreen(self.overHeatLED)
        self.overVoltageLED = QLabel('')  # Updated at end of each scan
        self.setLEDgreen(self.overVoltageLED)

        # Control Buttons
        LineProbeStatus = QHBoxLayout()
        LineProbeStatus.addWidget(self.planeName)
        LineProbeStatus.addWidget(self.planeNameBox)
        LineProbeStatus.addStretch()
        LineProbeStatus.addWidget(self.initProbe)
        LineProbeStatus.addStretch()
        LineProbeStatus.addWidget(self.scanStatusButton)

        # Probe Status Indicators
        ProbeStatus = QVBoxLayout()
        ProbeStatus.addWidget(self.probeStatus)
        ProbeStatus.addWidget(self.probeStatusLED)
        ScanStatus = QVBoxLayout()
        ScanStatus.addWidget(self.scanStatus)
        ScanStatus.addWidget(self.scanStatusLED)
        overHeatStatus = QVBoxLayout()
        overHeatStatus.addWidget(self.overHeat)
        overHeatStatus.addWidget(self.overHeatLED)
        overVoltageStatus = QVBoxLayout()
        overVoltageStatus.addWidget(self.overVoltage)
        overVoltageStatus.addWidget(self.overVoltageLED)

        ProbeBox = QGroupBox()
        ProbeBox.setLayout(ProbeStatus)
        ScanBox = QGroupBox()
        ScanBox.setLayout(ScanStatus)
        overHeatBox = QGroupBox()
        overHeatBox.setLayout(overHeatStatus)
        overVoltageBox = QGroupBox()
        overVoltageBox.setLayout(overVoltageStatus)

        LineScanStatus = QHBoxLayout()
        LineScanStatus.setSpacing(0)  # Tighten up grey boxes
        LineScanStatus.setContentsMargins(2, 2, 2, 2)
        LineScanStatus.addWidget(ProbeBox)
        LineScanStatus.addStretch()
        LineScanStatus.addWidget(ScanBox)
        LineScanStatus.addStretch()
        LineScanStatus.addWidget(overHeatBox)
        LineScanStatus.addStretch()
        LineScanStatus.addWidget(overVoltageBox)

        # Scan timer
        LineTimer = QHBoxLayout()
        LineTimer.addWidget(self.loopTimerBox)
        LineTimer.addWidget(self.loopTimer)
        LineTimer.addStretch()
        LineTimer.addWidget(self.frequencies)
        LineTimer.addWidget(self.frequenciesBox)

        # Total scans received and scan frequencies
        LineNumFrames = QHBoxLayout()
        LineNumFrames.addWidget(self.totalNumFramesBox)
        LineNumFrames.addWidget(self.totalNumFrames)
        LineNumFrames.addStretch()
        LineNumFrames.addWidget(self.nominalPitch)
        LineNumFrames.addWidget(self.nominalPitchBox)

        # Total scans since last reset
        LineResetFrames = QHBoxLayout()
        LineResetFrames.addWidget(self.numFramesSinceLastResetBox)
        LineResetFrames.addWidget(self.numFramesSinceLastReset)
        LineResetFrames.addStretch()
        LineResetFrames.addWidget(self.nominalRoll)
        LineResetFrames.addWidget(self.nominalRollBox)

        # Data/logs save line
        LineLog = QHBoxLayout()
        LineLog.addWidget(self.projectLocation)
        LineLog.addStretch()
        LineLog.addWidget(self.NIDASPort)
        LineLog.addWidget(self.NIDASPortBox)

        # Elevation angles
        LineElAngle = QHBoxLayout()
        LineElAngle.addWidget(self.allScanAngles)
        LineElAngle.addStretch()
        LineElAngle.addWidget(self.elAngle)
        LineElAngle.addWidget(self.elAngleBox)

        LineAllAngle = QHBoxLayout()
        LineAllAngle.addWidget(self.allScanAnglesBox)

        # IWG receive info
        LineReceivingUDP = QHBoxLayout()
        LineReceivingUDP.addWidget(self.receivingIWGLED)
        LineReceivingUDP.addWidget(self.receivingIWG)
        LineReceivingUDP.addStretch()
        LineReceivingUDP.addWidget(self.IWGPort)
        LineReceivingUDP.addWidget(self.IWGPortBox)

        # UDP data packet send info
        LineSendingUDP = QHBoxLayout()
        LineSendingUDP.addWidget(self.sendingUDPLED)
        LineSendingUDP.addWidget(self.sendingUDP)
        LineSendingUDP.addStretch()
        LineSendingUDP.addWidget(self.UDPPort)
        LineSendingUDP.addWidget(self.UDPPortBox)

        # Project name and flight number
        LineProjectName = QHBoxLayout()
        LineProjectName.addWidget(self.projectName)
        LineProjectName.addWidget(self.projectNameBox)
        LineProjectName.addStretch()
        LineProjectName.addWidget(self.flightNumber)
        LineProjectName.addWidget(self.flightNumberBox)

        # Put it all together
        mainbox = QVBoxLayout()
        mainbox.addLayout(LineProjectName)
        mainbox.addLayout(LineProbeStatus)
        mainbox.addLayout(LineScanStatus)
        mainbox.addLayout(LineTimer)
        mainbox.addLayout(LineNumFrames)
        mainbox.addLayout(LineResetFrames)
        mainbox.addLayout(LineElAngle)
        mainbox.addLayout(LineAllAngle)
        mainbox.addLayout(LineReceivingUDP)
        mainbox.addLayout(LineSendingUDP)
        mainbox.addLayout(LineLog)
        mainbox.addWidget(self.projectLocationBox)
        mainbox.addWidget(self.IWG1)
        mainbox.addWidget(self.IWG1Box)
        mainbox.addWidget(self.shutdownProbe)

        self.setLayout(mainbox)

        # Set the initial size of the window created and where it will appear
        # on the screen (x locn, y locn, width, ht). It is user resizeable
        self.setGeometry(50, 50, 400, 500)

        # Set window title
        self.setWindowTitle('MTPControl')

    def initProbeClicked(self):
        """ Reinitialize probe. Used if the probe gets in an error state """
        logger.debug("initProbeClicked")
        # set init led to yellow
        self.setLEDyellow(self.probeStatusLED)
        self.initProbe.setText("Initializing ...")
        self.initProbe.repaint()  # Need this to show change immediately
        self.app.processEvents()
        status = self.client.initProbe()  # Initialize probe
        if status is True:  # init succeeded
            self.setLEDgreen(self.probeStatusLED)
            self.initProbe.setText("(Re)init Probe")
        else:  # init failed
            self.setLEDred(self.probeStatusLED)
            self.initProbe.setText("Init Failed - (Re)init Probe")

    def shutdownProbeClicked(self):
        logger.debug("shutdownProbe/quit clicked")
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        self.client.close()
        logger.debug("Safe exit")
        self.app.exit(0)

    def waitForRadiometerWindow(self, isVisible=True):
        # Pauses program execution until ok pressed
        progress = QDialog()
        progress.setModal(False)
        if isVisible:
            progress.show()
            logger.debug("Show waitForRadiometerWindow")
        else:
            progress.hide()
            logger.debug("hide waitForRadiometerWindow")

        return False

    def scanStatusClicked(self):
        """ Start/Stop probe from scanning """
        logger.debug("scanStatusClicked")
        # Read current text to find out if we are cycling or not
        label = self.scanStatusButton.text()
        # set status led to yellow
        self.setLEDyellow(self.scanStatusLED)
        self.scanStatusButton.setText("...")
        self.scanStatusButton.repaint()  # Need this to show change immediately
        self.app.processEvents()
        if label == "Start Scanning":
            self.setLEDgreen(self.scanStatusLED)
            self.scanStatusButton.setText("Stop Scanning")
            self.client.cycle()
        if label == "Stop Scanning":
            self.setLEDred(self.scanStatusLED)
            self.scanStatusButton.setText("Start Scanning")
            self.client.stopCycle()
            self.setLEDred(self.sendingUDPLED)

    def setLEDred(self, led):
        ICON_RED_LED = QtGui.QPixmap(QSize(30, 30))
        ICON_RED_LED.fill(QtGui.QColor("red"))
        led.setPixmap(ICON_RED_LED)

    def setLEDyellow(self, led):
        ICON_YELLOW_LED = QtGui.QPixmap(QSize(30, 30))
        ICON_YELLOW_LED.fill(QtGui.QColor("yellow"))
        led.setPixmap(ICON_YELLOW_LED)

    def setLEDgreen(self, led):
        ICON_GREEN_LED = QtGui.QPixmap(QSize(30, 30))
        ICON_GREEN_LED.fill(QtGui.QColor("green"))
        led.setPixmap(ICON_GREEN_LED)

    def updateUDPStatus(self, status):
        if status is True:
            self.setLEDgreen(self.sendingUDPLED)
        else:
            self.setLEDred(self.sendingUDPLED)

    def setFlightNumber(self):
        # Dialog for setting flight number
        self.flightNumber.clear()
        self.flightNumber.setText("Target")

    def updateLogfile(self, filename: str):
        self.projectLocationBox.clear()
        self.projectLocationBox.setText(filename)

    def updateAngle(self, angle: str):
        self.elAngleBox.clear()
        self.elAngleBox.setText(angle)

    def updatePitch(self, pitch: str):
        self.nominalPitchBox.clear()
        self.nominalPitchBox.setText(pitch)

    def updateRoll(self, pitch: str):
        self.nominalRollBox.clear()
        self.nominalRollBox.setText(pitch)

    def updateGUIEndOfLoop(self, elapsedTime,
                           totalCycles, cyclesSinceLastStop):
        self.loopTimerBox.clear()
        self.loopTimerBox.setText("%0.2f" % elapsedTime.total_seconds())
        self.totalNumFramesBox.clear()
        self.totalNumFramesBox.setText(str(totalCycles))
        self.numFramesSinceLastResetBox.clear()
        self.numFramesSinceLastResetBox.setText(str(cyclesSinceLastStop))
