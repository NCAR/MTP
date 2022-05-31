###############################################################################
# MTP probe initialization class
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import re
import time
import serial
import socket
import logging
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPProbeInit():

    def __init__(self, args, port, commandDict, loglevel):
        ''' initial setup of serialPort, UDP socket '''
        self.serialPort = serial.Serial(args.device, 9600, timeout=0.15)

        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.udpSocket.connect(('127.0.0.1', port))  # ip, port number

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
        answerFromProbe = self.readEchos(4)
        logger.printmsg('debug', "echos from status read: " +
                        str(answerFromProbe))

        # Offset assumes probe responds "...T:0X" where X is desired char
        status = self.findChar(answerFromProbe, b'T', offset=3)

        # Status command report status of init, move, and sythesizer
        # At this point, any status 0-7 is fine. Just make sure we
        # get a valid status.
        if int(status) not in range(0, 8):
            logger.printmsg("error", "Unexpected status value " + str(status) +
                            " should be integer in range 0-7")
            # Shouldn't ever get here, so...
            exit(1)

        return status

    def findChar(self, array, binaryString, offset=0):
        '''
        Find binary string in char array

        Return:
         - If found return first char in found string.
         - If not found (-1) return False
        '''
        index = array.find(binaryString)
        if index > -1:
            logger.printmsg('debug', "status: " +
                            chr(array[index+offset]))
            return chr(array[index+offset])
        else:
            logger.printmsg('error', "status unknown, unable to " +
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
            logger.printmsg('info', "probe off or not responding." +
                            "Will retry in 10 seconds")
        logger.printmsg('info', "Probe on check returns true")

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

        for i in range(num):
            buf = buf + self.serialPort.readline()

            # First echo will be exact duplicate of command sent. Check for
            # it to ensure command wasn't corrupted on way to/from probe.
            # Echo begins and ends with \r\n so need to read 2 lines to get
            # first echo (lines 0 and 1). Add \r\n to cmd to match echo.
            if i == 1 and len(cmd) != 0:
                if buf != b'\r\n' + cmd:
                    logger.printmsg("warning", "initial echo from probe did " +
                                    "NOT match command sent. Sent " + str(cmd))

        if self.loglevel == "DEBUG":
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
                    logger.printmsg('debug', 'Needed more readEchos!! ' +
                                    str(buf) + '**** Need to update code.')
                # Guard against the case where the probe is returning data
                # forever (no idea if/when this would happen, but just in case)
                if i > 20:  # No legit command should return 20 lines => error!
                    self.handleNonemptyBuffer()

            # And one final check that you got it all
            self.clearBuffer()

        logger.printmsg('info', "read " + str(buf))
        return buf

    def handleNonemptyBuffer(self):
        """
        Put this in it's own function so later it can be updated to gracefully
        warn user when in realtime mode
        """
        logger.printmsg("warning", "Buffer not empty but it should be. " +
                        "BUG IN CODE #### Needs to update code.")
        exit(1)

    def clearBuffer(self):
        ''' Confirm that buffer is clear before send next command '''
        buf = self.serialPort.readline()
        logger.printmsg('debug', "clearBuffer read " + str(buf))
        if len(buf) == 0:
            logger.printmsg("debug", "Buffer empty. OK to continue")
        else:
            self.handleNonemptyBuffer()

    def moveComplete(self, buf):
        '''
        Check if a command has been completed by the firmware.

        Returns:
         - true if '@' is found, indicating successful completion
         - false if '@' not found
        '''
        # needs a timeout if command didn't send properly
        if buf.find(b'@') >= 0:
            return True
        return False

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

    def findStat(self, array):
        '''
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
        '''
        # UART returns "Step:\xff/0<status char>\r\n". To differentiate
        # this from noise, search for entire string. - JAA
        # otherwise error = -1
        ustat = [b'@', b'`', b'A', b'a', b'B', b'b', b'C', b'c', b'D', b'd',
                 b'E', b'e', b'G', b'g', b'I', b'i', b'K', b'k', b'O', b'o']

        i = 0
        index = -1
        while index == -1 and i < len(ustat):
            index = array.find(ustat[i])
            i = i + 1

        if index > -1:
            # logger.printmsg('debug', "status: " + str(array[index]) + ", " +
            #                  str(array))
            return chr(array[index])
        else:
            logger.printmsg('error', "status unknown, unable to find status " +
                            "in: " + str(array))
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
            logger.printmsg('info',
                            "Probe on, responding to version string prompt")
            return True
        else:
            logger.printmsg('info',
                            "Probe not responding to version string prompt")
            return False

    def truncateBotchedMoveCommand(self):
        ''' Restart the firmware '''
        # This fn sends ‘0X03’ (Ascii 3, actual Control-C) which is caught by
        # the interrupt routine and restarts the firmware.

        cmd = self.commandDict.getCommand("ctrl-C")
        self.serialPort.write(cmd)
        if self.findChar(self.readEchos(3), cmd):
            logger.printmsg('info',
                            "Probe on, responding to Ctrl-C prompt")
            return True
        else:
            logger.printmsg('info',
                            "Probe not responding to Ctrl-C prompt")
            return False

    def probeOnCheck(self):
        '''
        Check if probe is on by looking for version string.
        '''
        if self.findChar(self.readEchos(3),
                         b"MTPH_Control.c-101103>101208"):
            logger.printmsg('info', "Probe on, Version string detected")
            return True
        else:
            logger.printmsg('debug', "No version startup string from " +
                            "probe found, sending V prompt")
            if self.probeResponseCheck():
                return True
            else:
                # Probe not responding. Attempt firmware reboot.
                if self.truncateBotchedMoveCommand():
                    logger.printmsg('warning',
                                    "truncateBotchedMoveCommand called, " +
                                    "ctrl-c success")
                    return True
                else:
                    logger.printmsg('error', "probe not responding to " +
                                    "truncateBotchedMoveCommand ctrl-c, " +
                                    "power cycle necessary")
                    return False

        logger.printmsg('error', "probeOnCheck all previous logic tried, " +
                        "something's wrong")
        return False

    def sendInit1(self):
        # Init1
        #  - Set polarity of home sensor to 1 ('f1')
        #  - Adjust the resolution to 256 micro-steps per step ('j256')
        #  - Set the top motor speed to 50000 micro-steps per second ('V50000')
        cmd = self.commandDict.getCommand("init1")
        self.serialPort.write(cmd)

        # Returns:
        #   U/1f1j256V50000R\r\n
        #   U:U/1f1j256V50000R\r\n
        #   Step:\xff/0@\r\n - indicating success
        #
        # if already set to this last line replaced by
        #   Step:\xff/0B\r\n - indicating Illegal command sent
        #
        # Have seen this near boot: ( too early in boot phase (?) )
        #  b'\x1b[A\x1b[BU/1f1j256V50000R\r\n'
        # And this in cycles
        #  Step:\xff/0@\r\n - makes ascii parser die
        #  Step:/0C\r\n - makes fix for above not work
        #  Step:\r\n
        #

        return self.readEchos(5, cmd)

    def sendInit2(self):
        # Init2
        #  - Set acceleration factor to 4000 micro-steps per second^2 ('L4000')
        #  - Set hold current to 30% of 3.0 Amp max ('h30')
        #  - Set running current to 100% of 3.0 Amp max ('m100')
        cmd = self.commandDict.getCommand("init2")
        self.serialPort.write(cmd)

        # normal return:
        # U/1f1j256V50000R\r\n
        # U:U/1f1j256V50000R\r\n
        # b'Step:\xff/0@\r\n'

        # error returns:
        # \x1b[A\x1b[BU/1f1j256V50000R
        # Step:\xff/0B\r\n'
        #
        return self.readEchos(5, cmd)
        # By the time we have sent maxAttempts (6) Init1 and 6 init2, we need
        # 12 readEchos to get all the responses.

    def init(self, maxAttempts=6):
        """
        Initialize the probe

        Returns: maxAttemps if success, any other integer is failure
        """

        # The first time the probe is initialized, this returns b''.
        # If we want to re-initialise probe, there may be content in the
        # buffer. In that case, something should be done with the returned
        # values.
        answerFromProbe = self.readEchos(3)
        emptyAnswer = re.compile(b'')
        if not emptyAnswer.match(answerFromProbe):
            logger.printmsg('error', " Need to handle probe response " +
                            str(answerFromProbe) + "#### Need to update code")

        errorStatus = 0
        while errorStatus < maxAttempts:
            answerFromProbe = self.sendInit1()
            # check for errors/decide if resend? It is common on boot to
            # get a 'B' = Illegal command sent on first init1 and success
            # immediately after send second init1
            status = self.findStat(answerFromProbe)
            if status == '@':
                # success - no error. Break out of loop
                errorStatus = maxAttempts
            else:
                logger.printmsg('warning', " Init 1 status " + str(status) +
                                ", resending init1 command.")
                errorStatus = errorStatus + 1
            # if on first move status 6 for longer than expected
            # aka command sent properly, but actual movement
            # not initiated, need a Ctrl-c then re-init, re-home
            # Since this is not implemented, if get status=6 in status window,
            # must power cycle probe to clear and get code working

            # overall error conditions
            # 1) no command gets any response
            # - gets one echo, but not second echo
            # - because command collision in init commands
            # Probe needs power cycle
            # 2) stuck at Status 5 wih init/home
            # - unable to find commands to recover
            # Probe needs power cycle

        status = self.getStatus()

        errorStatus = 0
        while errorStatus < maxAttempts:
            answerFromProbe = self.sendInit2()
            # check for errors/decide if resend?
            status = self.findStat(answerFromProbe)
            if status == '@':
                # success
                errorStatus = maxAttempts
            else:
                logger.printmsg('warning', " Init 2 status " + str(status) +
                                ", resending init2 command.")
                errorStatus = errorStatus + 1

        status = self.getStatus()

        # After both init commands,
        # status = 6,7 indicates probe thinks it is moving, clears when home1
        # status = 5,7 indicates probe thinks it is integrating, send "I" to
        #              clear
        # status = 4 is preferred status

        # We can get here if init fails after maxAttempts. We should
        # catch that case and not report successful init.
        logger.printmsg('info', "init successful")
        return errorStatus
