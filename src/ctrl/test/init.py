import re
import time
import serial
import socket
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPProbeInit():

    def __init__(self, args, port):
        ''' initial setup of serialPort, UDP socket '''
        self.serialPort = serial.Serial(args.device, 9600, timeout=0.15)

        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.udpSocket.connect(('127.0.0.1', port))  # ip, port number

    def getSerialPort(self):
        ''' return serial port '''
        return self.serialPort

    def getUdpSocket(self):
        ''' return UDP socket '''
        return self.udpSocket

    def getStatus(self):
        '''
        Query probe for status

        status can have values X=[0-6], otherwise error = -1
        check for T in ST:0X

        Return: status
        '''
        self.serialPort.write(b'S\r\n')
        answerFromProbe = self.readEchos(4)
        logger.printmsg('debug', "echos from status read: " +
                        str(answerFromProbe))
        # Offset assumes probe responds "...T:0X" where X is desired char
        return self.findChar(answerFromProbe, b'T', offset=3)

    def findChar(self, array, binaryString, offset=0):
        '''
        Find binary string in char array

        Return:
         - If found return first char in found string.
         - If not found (-1) return False
        '''
        index = array.find(binaryString)
        if index > -1:
            logger.printmsg('debug', "status with offset: " +
                            chr(array[index+offset]))
            return chr(array[index+offset])
        else:
            logger.printmsg('error', "status with offset unknown, unable to " +
                            "find " + str(binaryString) + ": " + str(array))
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
            logger.printmsg('error', "probe off or not responding")
        logger.printmsg('info', "Probe on check returns true")

        return True

    def readEchos(self, num):
        ''' Read num lines ending in newline into buffer '''
        buf = b''
        for i in range(num):
            buf = buf + self.serialPort.readline()

        logger.printmsg('debug', "read " + str(buf))
        return buf

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
        data = data[data.find(b':') + 1: len(data) - 3]
        placeholder = data.decode('ascii')
        place = placeholder.split(' ')
        ret = ''
        for datum in place:
            ret += '%06d' % int(datum, 16) + ' '

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
        self.serialPort.write(b'V\r\n')
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
        # This fn sends string ‘Ctrl-C’, which is handled by the case
        # statement in main() in the firmware that matches the first C and
        # changes the SPI sequence (whatever that means) and then echos back
        # “\r\nCtrl-C\r\n”. We actually want to send ‘0X03’ (Ascii 3, actual
        # Control-C) which is caught by the interrupt routine and restarts the
        # firmware.
        #
        # Before we change this, Catherine would like to test the current
        # version with the probe. She believes she has seen a status change
        # when sending the 'Ctrl-C' and would like to confirm we understand
        # exactly what the 'C' case does.

        self.serialPort.write(b'Ctrl-C\r\n')
        if self.findChar(self.readEchos(3), b'Ctrl-C\r\n'):
            logger.printmsg('info',
                            "Probe on, responding to Ctrl-C string prompt")
            return True
        else:
            logger.printmsg('info',
                            "Probe not responding to Ctrl-C string prompt")
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
        self.serialPort.write(b'U/1f1j256V50000R\r\n')

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

        return self.readEchos(4)

    def sendInit2(self):
        # Init2
        #  - Set acceleration factor to 4000 micro-steps per second^2 ('L4000')
        #  - Set hold current to 30% of 3.0 Amp max ('h30')
        #  - Set running current to 100% of 3.0 Amp max ('m100')
        self.serialPort.write(b'U/1L4000h30m100R\r\n')

        # normal return:
        # U/1f1j256V50000R\r\n
        # U:U/1f1j256V50000R\r\n
        # b'Step:\xff/0@\r\n'

        # error returns:
        # \x1b[A\x1b[BU/1f1j256V50000R
        # Step:\xff/0B\r\n'
        #
        return self.readEchos(4)
        # By the time we have sent maxAttempts (6) Init1 and 6 init2, we need
        # 12 readEchos to get all the responses.

    def init(self, maxAttempts=6):

        # The first time the probe is initialized, this returns b''.
        # If we want to re-initialise probe, there may be content in the
        # buffer. In that case, something should be done with the returned
        # values.
        answerFromProbe = self.readEchos(3)
        emptyAnswer = re.compile(b'')
        if not emptyAnswer.match(answerFromProbe):
            logger.printmsg('error', " Need to handle probe response " +
                            str(answerFromProbe))

        errorStatus = 0
        while errorStatus < maxAttempts:
            errorStatus = errorStatus + 1
            answerFromProbe = self.sendInit1()
            # check for errors/decide if resend?
            status = self.findStat(answerFromProbe)
            if status == '@':
                # success - no error. Break out of loop
                errorStatus = maxAttempts
            else:
                logger.printmsg('warning', " Init 1 status " + status +
                                ", resending init1 command.")
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
        # Should check status here. What are we looking for? - JAA

        errorStatus = 0
        while errorStatus < maxAttempts:
            answerFromProbe = self.sendInit2()
            # check for errors/decide if resend?
            status = self.findStat(answerFromProbe)
            if status == '@':
                # success
                errorStatus = maxAttempts
            else:
                logger.printmsg('warning', " Init 2 status " + status +
                                ", resending init2 command.")
                errorStatus = errorStatus + 1

        # After both is status of 7 ok?
        # no
        # 4 is preferred status
        # if after both inits status = 5
        # do an integrate, then a read to clear

        # We can get here if init fails after maxAttempts. We should
        # catch that case and not report successful init.
        logger.printmsg('debug', "init successful")
        return errorStatus
