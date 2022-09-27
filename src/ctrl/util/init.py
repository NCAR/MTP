###############################################################################
# MTP probe initialization class
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import re
import sys
import time
import serial
import socket
import select
import logging
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class MTPProbeInit():

    def __init__(self, args, port, commandDict, loglevel, iwg):
        ''' initial setup of serialPort, UDP socket '''
        self.iwg = iwg

        try:
            self.serialPort = serial.Serial(args.device, 9600, timeout=0.15)
            self.udpSocket = socket.socket(socket.AF_INET,
                                           socket.SOCK_DGRAM, 0)
            self.udpSocket.connect(('127.0.0.1', port))  # ip, port number
        except serial.SerialException:
            print("Device " + args.device + " doesn't exist on this machine." +
                  " Please specify a valid device using the --device command" +
                  " line option. Type '" + sys.argv[0] + " --help' for the " +
                  "help menu")
            exit(1)

        # Dictionary of allowed commands to send to firmware
        self.commandDict = commandDict

        self.loglevel = logging.getLevelName(loglevel)

    def getSerialPort(self):
        ''' return serial port '''
        return self.serialPort

    def getUdpSocket(self):
        ''' return UDP socket '''
        return self.udpSocket

    def getStatus(self):
        '''
        Query probe for status

        status can have values X=[0-7], otherwise error = -1
        check for T in ST:0X

        Return: status
        '''
        cmd = self.commandDict.getCommand("status")
        self.serialPort.write(cmd)
        answerFromProbe = self.readEchos(2)
        logger.debug("echos from status read: " + str(answerFromProbe))

        # Offset assumes probe responds "...T:0X" where X is desired char
        # Returns false if T not found
        status = self.findChar(answerFromProbe, b'T', offset=3)

        # Status command report status of init, move, and sythesizer
        # At this point, any status 0-7 is fine. Just make sure we
        # get a valid status.
        if int(status) not in range(0, 8):
            logger.error("Unexpected status value " + str(status) +
                         " should be integer in range 0-7")
            # Shouldn't ever get here, so...
            exit(1)

        return status

    def integratorBusy(self, status):
        """
        Determine integrator status

        Return:
            True - integrator busy
            False - integrator not busy
        """
        state = status & 1  # Get Bit 0
        if state == 1:  # Integrator busy
            return(True)
        else:
            return(False)

    def stepperBusy(self, status):
        """ Return True if stepper moving, False if not moving """
        state = status & 2  # Get Bit 1
        if state == 2:  # Stepper moving
            return(True)
        else:
            return(False)

    def synthesizerBusy(self, status):
        """ Return True if synthesizer locked, False if out of lock """
        state = status & 4  # Get Bit 2
        if state == 4:  # Synthesizer locked
            return(True)
        else:
            return(False)  # Synthesizer out of lock

    def findChar(self, array, binaryString, offset=0):
        '''
        Find binary string in char array

        Return:
         - If found return first char in found string.
         - If not found (-1) return False
        '''
        index = array.find(binaryString)
        if index > -1:
            logger.debug("status: " + chr(array[index+offset]))
            return chr(array[index+offset])
        else:
            logger.info("status unknown, unable to " +
                        "find " + str(binaryString) + " in " + str(array))
            return False

    def bootCheck(self):
        '''
        Check if probe is booted and responding

        On boot probe returns MTPH_Control.c-101103>101208
        This needs to be caught first before other init commands are sent
        This string is also sent as a response to sending a V.)

        Loop indefinitely if probe is off. This allows user to boot probe
        and have code respond and begin probe operation.
        '''
        while self.probeOnCheck() is False:
            time.sleep(10)
            logger.info("probe off or not responding." +
                        "Will retry in 10 seconds")
        logger.info("Probe on check returns true")

        return True

    def readEchos(self, num, cmd=b''):
        '''
        Read num newlines into buffer. So if port has a string \r\nS\r\n
        it takes num=2 to read it.

        Also confirms that first echo matches command sent to probe if
        command is supplied to this function. (Default cmd=b'' skips this test.

        Values returned from probe follow the pattern:
         - one or more empty lines (b'') ; may be all empty lines because
           probe returns nothing
         - Then three or more lines denoted by presence of \r\n
         - When you get empty lines again, you are done.
        '''
        buf = b''

        # First echo will be exact duplicate of command sent. Check for
        # it immediately to ensure command wasn't corrupted on way to/from
        # probe.  Echo ends with \r\n so only need to read 1 line to get
        # first echo (lines 0)
        buf = buf + self.serialPort.readline()
        if len(cmd) != 0 and buf != cmd:
            logger.warning("initial echo from probe did " +
                           "NOT match command sent. Sent " + str(cmd))

        # Read remaining responses from probe, interleave with checking for
        # IWG packets.
        for i in range(num-1):  # Loop until get num-1 non-empty responses

            # read_ready with .01 second timeout
            ports = [self.iwg.socket()]
            read_ready, _, _ = select.select(ports, [], [], 0.002)

            if self.loglevel == "DEBUG":
                if len(read_ready) == 0:
                    print('timed out')

            if self.iwg.socket() in read_ready:
                self.iwg.readIWG()

            response = self.serialPort.readline()
            if len(response) == 0:
                # Read returned empty response so need to loop back and try
                # again to get this response
                i = i - 1
                # Pause for 2 milliseconds so don't hang up CPU
                time.sleep(0.002)
            else:
                # Got response - add to buffer
                buf = buf + response

        if self.loglevel == "DEBUG":
            buf = self.checkReadComplete(buf)  # Confirm got all responses

        logger.info("read " + str(buf))
        return buf

    def checkReadComplete(self, buf):
        # Make sure you found ALL the data - only do this in debug mode
        # because it adds too much time to scan cycle. When run with this
        # enabled, CIRS scan takes 5 seconds, but when comment out this
        # block, CIRS takes .03 seconds!!!

        i = 0
        while True:
            line = self.serialPort.readline()
            i = i + 1
            if len(line) == 0:  # Found a blank line
                break
            else:
                buf = buf + line
                logger.debug('Needed more readEchos!! ' +
                             str(buf) + '**** Need to update code.')
            # Guard against the case where the probe is returning data
            # forever (no idea if/when this would happen, but just in case)
            if i > 20:  # No legit command should return 20 lines => error!
                self.handleNonemptyBuffer()

        # And one final check that you got it all
        self.clearBuffer()

        return(buf)

    def handleNonemptyBuffer(self):
        """
        Warn user when buffer expected to be empty, but it isn't
        """
        logger.warning("Buffer not empty but it should be. " +
                       "BUG IN CODE #### Needs to update code.")

    def clearBuffer(self):
        ''' Confirm that buffer is clear before send next command '''
        buf = self.serialPort.readline()
        logger.debug("clearBuffer read " + str(buf))
        if len(buf) == 0:
            logger.info("Buffer empty. OK to continue")
        else:
            self.handleNonemptyBuffer()

    def sanitize(self, data):
        """
        Clean up buffer returned by multiplxr calls

        Input: buffer as returned by firmware, e.g. b'\r\nM 1...
        Output: string containing series of mutliplxr values,
        e.g. 2928 2300 2898 3083 1920 2920 2431 2946
        """
        # Remove stuff before colon and \r\n from end of line. Effectively
        # converts buffer returned from probe from binary to ascii.
        data = data[data.find(b':') + 1: len(data) - 3]
        placeholder = data.decode('ascii')  # Convert ascii back to bytes
        place = placeholder.split(' ')  # Split into list
        ret = ''
        for datum in place:
            ret += '%d' % int(datum, 16) + ' '  # Convert from hex to ascii

        return ret

    def findStat(self, buf):
        '''
        Find status value returned by probe after UART command

        UART returned value meanings (e.g. ff/0@ = No error):
            ff - RS485 line turnaround char; starts message
            /  - start char
            0  - address of message recipient
            @  - status char (upper case device busy, lower not)
                Ascii @/` =Hex 40/60 - No error
                Ascii A/a =Hex 41/61 - Initialization Error
                Ascii B/b =Hex 42/62 - Illegal Command sent
                Ascii C/c =Hex 43/63 - Out of range operand value
                Ascii E/e =Hex 45/65 - Internal communication err
                Ascii G/g =Hex 47/67 - Not initialized before move
                Ascii I/i =Hex 49/69 - Overload error (too fast)
                Ascii K/k =Hex 4B/6B - Move not allowed
                Ascii O/o =Hex 4F/6F - Already executing command
                                        when another received

        Return: Character indicating UART status, or -1 if status could not
                be determined.
        '''
        ustat = [b'@', b'`', b'A', b'a', b'B', b'b', b'C', b'c', b'D', b'd',
                 b'E', b'e', b'G', b'g', b'I', b'i', b'K', b'k', b'O', b'o']

        i = 0
        index = -1
        while index == -1 and i < len(ustat):
            # UART returns "Step:\xff/0<status char>\r\n". To differentiate
            # this from noise which might randomly return a char in ustat,
            # search for entire string.
            statStr = b'Step:\xff/0' + ustat[i] + b'\r\n'
            index = buf.find(statStr)
            offset = 8  # Length of 'Step:\xff/0'
            i = i + 1

        i = 0
        while index == -1 and i < len(ustat):
            # Sometimes \xff is missing from status string
            statStr = b'Step:/0' + ustat[i] + b'\r\n'
            index = buf.find(statStr)
            offset = 7  # Length of 'Step:/0'
            i = i + 1

        if index > -1:
            logger.debug("Found status " + chr(buf[index+offset]) +
                         " in " + str(buf) + " at index " + str(i))
            return chr(buf[index+offset])
        else:
            logger.warning("status unknown, unable to find " +
                           "status in: " + str(buf))
            return -1

    def probeResponseCheck(self):
        '''
        Send request for probe to return Firmware version. This is a good
        way to confirm the probe is on and responding to commands.
        '''
        cmd = self.commandDict.getCommand("version")
        self.serialPort.write(cmd)
        if self.findChar(self.readEchos(3),
                         b"MTPH_Control.c-101103>101208"):
            logger.info("Probe on, responding to version string prompt")
            return True
        else:
            logger.info("Probe not responding to version string prompt")
            return False

    def truncateBotchedMoveCommand(self):
        ''' Restart the firmware '''
        # This fn sends ‘0X03’ (Ascii 3, actual Control-C) which is caught by
        # the interrupt routine and restarts the firmware.

        cmd = self.commandDict.getCommand("ctrl-C")
        self.serialPort.write(cmd)
        if self.findChar(self.readEchos(3), cmd):
            logger.info("Probe on, responding to Ctrl-C prompt")
            return True
        else:
            logger.info("Probe not responding to Ctrl-C prompt")
            return False

    def probeOnCheck(self):
        '''
        Check if probe is on by looking for version string.
        '''
        if self.findChar(self.readEchos(3),
                         b"MTPH_Control.c-101103>101208"):
            logger.info("Probe on, Version string detected")
            return True
        else:
            logger.debug("No version startup string from " +
                         "probe found, sending V prompt")
            if self.probeResponseCheck():
                return True
            else:
                # Probe not responding. Attempt firmware reboot.
                if self.truncateBotchedMoveCommand():
                    logger.warning("truncateBotchedMoveCommand called, " +
                                   "ctrl-c success")
                    return True
                else:
                    logger.error("probe not responding to " +
                                 "truncateBotchedMoveCommand ctrl-c, " +
                                 "power cycle necessary")
                    return False

        logger.error("probeOnCheck all previous logic tried, " +
                     "something's wrong")
        return False

    def init(self):
        """
        Initialize the probe

        Returns: True on success, False on failure
        """
        # The first time the probe is initialized, this returns b''.
        # If we want to re-initialize probe because something has gone wrong,
        # there may be content in the buffer. In that case, something should be
        # done with the returned values. - JAA
        answerFromProbe = self.readEchos(3)
        emptyAnswer = re.compile(b'')
        if not emptyAnswer.match(answerFromProbe):
            logger.error(" Need to handle probe response " +
                         str(answerFromProbe) + "#### Need to update code")
            return(False)

        # Init1
        #  - Set polarity of home sensor to 1 ('f1')
        #  - Adjust the resolution to 256 micro-steps per step ('j256')
        #  - Set the top motor speed to 50000 micro-steps per second ('V50000')
        #
        # Returns:
        #   U/1f1j256V50000R\r\n
        #   U:U/1f1j256V50000R\r\n
        #   Step:\xff/0@\r\n - indicating success
        #
        # if already set to this last line replaced by
        #   Step:\xff/0B\r\n - indicating Illegal command sent
        if self.sendInit("init1"):
            self.getStatus()  # If getStatus returns -1, status not found
            # Status can be any of 0-7, so don't check getStatus return
            logger.info("init1 succeeded")
        else:
            logger.warning("init1 failed #### Need to update code")
            return(False)

        time.sleep(0.2)  # From VB6 code

        # Init2
        #  - Set acceleration factor to 4000 micro-steps per second^2 ('L4000')
        #  - Set hold current to 30% of 3.0 Amp max ('h30')
        #  - Set running current to 100% of 3.0 Amp max ('m100')
        #
        # normal return:
        # U/1f1j256V50000R\r\n
        # U:U/1f1j256V50000R\r\n
        # b'Step:\xff/0@\r\n'
        if self.sendInit("init2"):
            self.getStatus()
            # Status can be any of 0-7, so don't check getStatus return
            logger.info("init2 succeeded")
        else:
            logger.warning("init2 failed #### Need to update code")
            return(False)

        # After both init commands,
        # status = 6,7 indicates probe thinks it is moving, clears when home1
        # status = 5,7 indicates probe thinks it is integrating, send "I" to
        #              clear
        # status = 4 is preferred status

        logger.info("init successful")
        return(True)

    def sendInit(self, init, maxAttempts=6):
        """ Send init command to probe. Handles init1 and init2 """
        errorStatus = 0
        while errorStatus < maxAttempts:
            cmd = self.commandDict.getCommand(init)
            self.serialPort.write(cmd)
            answerFromProbe = self.readEchos(5, cmd)

            # check for errors/decide if resend? It is common on boot to
            # get a 'B' = Illegal command sent on first init1 and success
            # immediately after send second init1
            status = self.findStat(answerFromProbe)
            if status == '@':
                # success - no error. Break out of loop
                return(True)
            else:
                logger.warning(init + " status " + str(status) +
                               ", resending " + init + " command.")
                errorStatus = errorStatus + 1

        return(False)
