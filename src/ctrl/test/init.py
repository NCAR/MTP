import sys
import logging
import time
import serial
import socket
import argparse


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
        ''' Query probe for status '''

        # status = 0-6, C, B, or @  otherwise error = -1
        # staus can have many other values: I, K, O, etc. Handle those - JAA
        # check for T in ST:0X
        # return status
        self.serialPort.write(b'S\r\n')
        answerFromProbe = self.readEchos(4)
        logging.debug("echos from status read: %r", answerFromProbe)
        # Offset assumes probe responds "\r\nST:" before desired status char
        return self.findCharPlusNum(answerFromProbe, b'T', offset=5)

    def findCharPlusNum(self, array, binaryCharacter, offset):
        # status = 0-6, C, B, or @
        # staus can have many other values: I, K, O, etc. Handle those - JAA
        # otherwise error = -1
        index = array.find(binaryCharacter)
        asciiArray = array.decode('ascii')
        if index > -1:
            # logging.debug("status with offset: %r, %r",
            #               asciiArray[index+offset], asciiArray)
            return asciiArray[index+offset]
        else:
            logging.error("status with offset unknown, unable to find %r: %r",
                          binaryCharacter, array)
            return -1

    def bootCheck(self):
        # on boot probe sends MTPH_Control.c-101103>101208
        # needs to be caught first before other init commands are sent
        # (This string is also sent as a response to sending a V.)
        while self.probeOnCheck() is False:
            time.sleep(10)
            logging.error("probe off or not responding")
        logging.info("Probe on check returns true")

        return True

    def readEchos(self, num):
        buf = b''
        for i in range(num):
            buf = buf + self.serialPort.readline()

        logging.debug("read %r", buf)
        return buf

    def moveComplete(self, buf):
        # returns true if '@' is found,
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

    def findChar(self, array, binaryString):
        # Make this more restrictive. When Firmware is working, these chars
        # are unique, but if there is noise it is possible to get an
        # erroneous match
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
        # Status return values = 0-6
        # otherwise error = -1
        index = array.find(binaryString)
        if index > -1:
            # logging.debug("status: %r, %r", array[index], array)
            return array[index]
        else:
            logging.error("status unknown, unable to find %r: %r",
                          binaryString, array)
            return -1

    def probeResponseCheck(self):
        '''
        Send request for probe to return Firmware version. This is a good
        way to confirm the probe is on and responding to commands.
        '''
        self.serialPort.write(b'V\r\n')
        if self.findChar(self.readEchos(3),
                         b"MTPH_Control.c-101103>101208") > 0:
            logging.info("Probe on, responding to version string prompt")
            return True
        else:
            logging.info("Probe not responding to version string prompt")
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
        if self.findChar(self.readEchos(3), b'Ctrl-C\r\n') > 0:
            logging.info("Probe on, responding to Ctrl-C string prompt")
            return True
        else:
            logging.info("Probe not responding to Ctrl-C string prompt")
            return False

    def probeOnCheck(self):
        if self.findChar(self.readEchos(3),
                         b"MTPH_Control.c-101103>101208") > 0:
            logging.info("Probe on, Version string detected")
            return True
        else:
            logging.debug("No version startup string from probe found, " +
                          "sending V prompt")
            if self.probeResponseCheck():
                return True
            else:
                if self.truncateBotchedMoveCommand():
                    logging.warning("truncateBotchedMoveCommand called, " +
                                    "ctrl-c success")
                    return True
                else:
                    logging.error("probe not responding to " +
                                  "truncateBotchedMoveCommand ctrl-c, " +
                                  "power cycle necessary")
                    return False

        logging.error("probeOnCheck all previous logic tried, " +
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
        #
        # U/1f1j256V50000R\r\n
        # U:U/1f1j256V50000R\r\n
        # b'Step:\xff/0@\r\n'

        # error returns:
        # \x1b[A\x1b[BU/1f1j256V50000R
        # Step:\xff/0B\r\n'
        #
        return self.readEchos(4)

    def init(self, maxAttempts=6):

        # Why do we need this?? - JAA
        self.readEchos(3)

        errorStatus = 0
        while errorStatus < maxAttempts:
            # Move error checking into function to call from both init1 and
            # init2. Handle all possible values
            errorStatus = errorStatus + 1
            answerFromProbe = self.sendInit1()
            # check for errors/decide if resend?
            if self.findChar(answerFromProbe, b'@') > 0:
                # success - no error. Break out of loop
                errorStatus = maxAttempts
            elif self.findChar(answerFromProbe, b'B') > 0:
                # Illegal Command Sent
                logging.warning(" Init 1 status B, resending.")
            elif self.findChar(answerFromProbe, b'C') > 0:
                # Out of range operand value
                logging.warning(" Init 1 status C, resending.")
            else:
                logging.warning(" Init 1 status else, resending.")
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
            if self.findChar(answerFromProbe, b'@') > 0:
                errorStatus = maxAttempts
                # success
            elif self.findChar(answerFromProbe, b'B') > 0:
                logging.warning(" Init 2 status B, resending.")
                errorStatus = errorStatus + 1
            elif self.findChar(answerFromProbe, b'C') > 0:
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

        logging.debug("init successful")
        return errorStatus


def parse_args():
    """ Instantiate a command line argument parser """

    # Define command line arguments which can be provided by users
    parser = argparse.ArgumentParser(
        description="Script to initialize the MTP instrument")
    parser.add_argument('--device', type=str, default='COM6',
                        help="Device on which to receive messages from MTP " +
                        "instrument")

    # Parse the command line arguments
    args = parser.parse_args()

    return(args)


def printMenu():
    """ List user options """
    print("Please issue a command:")
    print("0 = Status")
    print("1 = init")

    cmdInput = sys.stdin.readline()
    cmdInput = str(cmdInput).strip('\n')

    return(cmdInput)


def main():
    # initial setup of time, logging
    logging.basicConfig(level=logging.DEBUG)

    args = parse_args()

    # Move readConfig out of viewer/MTPclient to lib/readConfig and
    # get port from there. Add --config to parse_args - JAA
    port = 32107
    init = MTPProbeInit(args, port)

    probeResponding = False
    while (1):

        cmdInput = printMenu()

        # Check if probe is on and responding
        if probeResponding is False:
            probeResponding = init.bootCheck()

        if cmdInput == '0':
            # Print status
            init.getStatus()

        elif cmdInput == '1':
            # Initialize probe
            init.init()


if __name__ == "__main__":
    main()
