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

    def __init__(self, init):
        self.serialPort = init.getSerialPort()
        self.init = init

    def changeFrequency(self, freq):
        self.serialPort.write(freq)
        # no official response, just echos
        # and echos that are indistinguishable from each other
        # eg: echo when buffer is sending to probe is same
        # as echo from probe: both "C#####\r\n"
        # Catch tune echos
        self.init.readEchos(4)

    def integrate(self):
        self.serialPort.write(b'I 40\r\n')
        self.init.readEchos(4)

        # Check that S turns to 5 (integrator starts)
        # and that S turns back to 4 (integrator finished) to move on
        self.getIntegrateFromProbe()

    def getIntegrateFromProbe(self):
        # Need better logic to check for return values than loop set number of
        # times - JAA
        i = 0
        looptimeMS = 2
        while i < looptimeMS:
            s = self.init.getStatus()
            logger.printmsg("debug", "integrate loop 1, checking for " +
                            "status=5, got status=" + s[0])
            if s == '5':
                logger.printmsg("debug", "integrate loop 1, status 5 found, " +
                                "integrator started")
                break
            if i == looptimeMS:
                logger.printmsg("warning", "integrate loop 1," +
                                " re-send Integrate")
                self.serialPort.write(b'I 40\r\n')
                i = looptimeMS/2
                looptimeMS = i
            i = i + 1

        # check that integrator has finished
        i = 0
        while i < 3:
            s = self.init.getStatus()
            logger.printmsg("debug", "integrate loop 2, checking for " +
                            "status=4, got status=" + s[0])
            if s == '4':
                logger.printmsg("debug", "integrator has finished")
                break
            logger.printmsg("debug", 'checking for finished integrator: ' +
                            str(i))
            i = i + 1
        return True

    def readDatumFromProbe(self):
        self.serialPort.write(b'R\r\n')
        data = self.init.readEchos(4)

        # Find counts in string. Expected string is R28:xxxx where xxxx is
        # 4-digit hex value.
        # Need to beef up checking return value - JAA
        logger.printmsg("debug", "Return value is " + str(data))
        findColon = data.find(b':')
        hexcounts = data[findColon+1:findColon+5]

        # translate from hex and format as 6-digit integer
        datum = '%06d' % int(hexcounts.decode('ascii'), 16)
        logger.printmsg("debug", "Counts are " + str(datum))
        return datum

    def CIR(self, freq):
        """
        At each move angle, code needs to set the Channel frequency, Integrate,
        and Read (CIR)
        """
        self.changeFrequency(freq)
        self.integrate()
        return self.readDatumFromProbe()

    def CIRS(self):
        """
        Cycle through 3 probe frequencies

        Returns a string containing three count values, one for each freq
        eg "020807 022393 022128".
        """
        data = ''

        # Convert freq to integer to send to Firmware
        # Since they don't change, this conversion could be removed from
        # the loop and just done once to save time. - per Catherine
        # Update to read from Config.mtph - JAA
        fghz = [55.51, 56.65, 58.8]  # freq in gigahertz

        # either 'C' or 'F' (set in lib/storePacket.py)
        # F mode formatting #####.# instead of cmode formatting #####
        # not sure it makes a difference
        # Eventually get from  packetStore.getData("tuneMode")
        mode = 'C'
        for f in fghz:
            fby4 = (1000 * f)/4  # MHz
            # convert to SNP channel (integer) 0.5 MHz = step size
            chan = '{:.5}'.format(str(fby4/0.5))
            logger.printmsg("debug", "tune: chan = " + chan)
            cmd = str.encode(str(mode) + str(chan) + "\r\n")
            data = data + self.CIR(cmd) + " "
            logger.printmsg("debug", "-----")
        return data.strip()  # remove trailing space

    def setNoise(self, num):
        self.serialPort.write(num)
        self.init.readEchos(4)

    def readEline(self):
        """
        Read all data at current position for noise diode on and then off.
        Since this function doesn't check probe pointing, it could be at any
        position, so pointing must be checked before using this fn.

        Returns a complete E line,
        eg "E 020807 022393 022128 019105 020672 020117"
        """
        # Determine how long it takes to create the E line
        firstTime = datetime.datetime.now()

        # Create E line
        data = 'E '
        self.setNoise(b'N 1\r\n')  # Turn noise diode on
        data = data + self.CIRS()  # Collect counts for three channels
        data = data + " "          # Add space between count sets
        self.setNoise(b'N 0\r\n')  # Turn noise diode off
        data = data + self.CIRS()  # Collect counts for three channels
        logger.printmsg("debug", "data from E line:" + str(data))

        nextTime = datetime.datetime.now()
        logger.printmsg("debug", "E line creation took " + nextTime-firstTime)

        return data
