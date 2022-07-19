###############################################################################
# MTP probe control. Class contains functions that move the probe
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import datetime
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPProbeCIR():

    def __init__(self, init, commandDict):
        self.serialPort = init.getSerialPort()
        self.init = init
        self.commandDict = commandDict

        self.fcmd = []
        # Update to read from Config.mtph - JAA
        fghz = [55.51, 56.65, 58.8]  # freq in gigahertz

        # either 'C' or 'F' (set in lib/storePacket.py)
        # F mode formatting #####.# instead of cmode formatting #####
        # Eventually get from  packetStore.getData("tuneMode") always = 'C'
        mode = 'C'  # Always use 'C'. 'F' prone to frequency collapse

        # Convert freq to integer to send to Firmware
        for f in fghz:
            fby4 = (1000 * f)/4  # MHz
            # convert to SNP channel (integer) 0.5 MHz = step size
            chan = '{:.5}'.format(str(fby4/0.5))
            logger.printmsg("debug", "tune: chan = " + chan)
            self.fcmd.append(str.encode(str(mode) + str(chan) + "\r\n"))

    def changeFrequency(self, freq, wait):
        """
        Input:
        freq - Command to send to UART to change freq
        wait - boolean indicating whether or not to wait for synthesizer to
               lock. 1 = wait, 0 = do not wait
        """
        self.serialPort.write(freq)

        # Catch tune echos
        self.init.readEchos(2, freq)

        # Wait for synthesizer to lock
        if wait:
            self.synthesizerWait()

    def integrate(self):
        cmd = self.commandDict.getCommand("count")
        self.serialPort.write(cmd)
        self.init.readEchos(2, cmd)  # b'I 40\r\nI28\r\n'

        # Check that integrator starts
        self.integratorWait("start")

        # Check that integrator finished
        self.integratorWait("done")

    def synthesizerWait(self):
        stat = self.init.getStatus()
        while not self.init.synthesizerBusy(int(stat)):
            stat = self.init.getStatus()

    def integratorWait(self, state):
        loopStartTime = datetime.datetime.now()
        timeinloop = datetime.datetime.now() - loopStartTime
        while timeinloop.total_seconds() < 3:  # 3 seconds (not in VB6)
            stat = False
            # Loop until get valid stat (0-7)
            while not stat:  # While stat False
                stat = self.init.getStatus()

            # Got a valid stat (0-7). Depending on state check and see if
            # integrator started or done
            if state == "start":
                if self.init.integratorBusy(int(stat)):
                    return(True)  # Integrator busy

            elif state == "done":
                if not self.init.integratorBusy(int(stat)):
                    return(True)  # Integrator finished

            else:
                logger.printmsg("error", "unknown state")

            # Increment timeinloop
            timeinloop = datetime.datetime.now() - loopStartTime

        # If looped for 3 seconds and integrator never started, return False
        logger.printmsg("error", "Integrator never started")
        return(False)

    def readDatumFromProbe(self):
        cmd = self.commandDict.getCommand("count2")
        self.serialPort.write(cmd)
        data = self.init.readEchos(2, cmd)

        # Find counts in string. Expected string is R28:xxxx where xxxx is
        # 4-digit hex value.
        # Need to beef up checking return value - JAA
        logger.printmsg("debug", "Return value is " + str(data))
        findColon = data.find(b':')
        hexcounts = data[findColon+1:findColon+7]
        logger.printmsg("debug", "Return hex counts is " + str(hexcounts))

        # translate from hex and format as 6-digit integer
        datum = '%06d' % int(hexcounts.decode('ascii'), 16)
        logger.printmsg("debug", "Counts are " + str(datum))
        return datum

    def CIR(self, freq):
        """
        At each move angle, code needs to set the Channel frequency, Integrate,
        and Read (CIR)
        """
        self.changeFrequency(freq, 1)  # change freq and wait for lock
        self.integrate()
        return self.readDatumFromProbe()

    def CIRS(self):
        """
        Cycle through 3 probe frequencies

        Returns a string containing three count values, one for each freq
        eg "020807 022393 022128".
        """
        data = ''

        for cmd in self.fcmd:
            data = data + self.CIR(cmd) + " "
            logger.printmsg("debug", "freq set to " + str(cmd))
        return data.strip()  # remove trailing space
