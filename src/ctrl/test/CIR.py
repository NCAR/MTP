###############################################################################
# MTP probe control. Class contains functions that move the probe
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import time
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPProbeCIR():

    def __init__(self, init):
        self.serialPort = init.getSerialPort()
        self.init = init

    def changeFrequency(self, freq):
        self.serialPort.write(freq)
        self.init.readEchos(2)
        # possible answers:

    def integrate(self):
        self.serialPort.write(b'I 40\r\n')
        time.sleep(0.350)
        self.init.readEchos(2)
        # this needs to check that S turns to 5 (integrator starts)
        # and that S turns back to 4 (integrator finished) to move on

    def readDatumFromProbe(self):
        self.serialPort.write(b'R\r\n')
        return self.init.readEchos(2)

    def CIR(self, freq):
        """
        At each move angle, code needs to set the Channel frequency, Integrate,
        and Read (CIR)
        """
        self.changeFrequency(freq)
        self.integrate()
        return self.readDatumFromProbe()

    def CIRS(self):
        """ Cycle through 3 probe frequencies """
        # frequencies 56.363,57.612,58.383
        data = self.CIR(b'C28180\r\n')
        data = data + self.CIR(b'C28805\r\n')
        data = data + self.CIR(b'C229180\r\n')  # 229 or 29? Typo?? - JAA
        return data

    def setNoise(self, num):
        self.serialPort.write(num)
        self.init.readEchos(2)

    def read(self):
        """ read all data at current position """
        self.setNoise(b'N 1\r\n')
        self.init.readEchos(2)
        data = self.CIRS()
        self.setNoise(b'N 0\r\n')
        self.init.readEchos(2)
        data = data + self.CIRS()
        logger.printmsg("debug", "data from one position, " + str(data))

        return data
