import logging
import time
import serial
import socket
import re
import argparse


class MTPProbeInit():

    def __init__(self, args, port):

        # initial setup of serialPort, UDP port
        self.serialPort = serial.Serial(args.device, 9600, timeout=0.15)

        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.udpSocket.connect(('127.0.0.1', port))  # ip, port number

    def getSerialPort(self):
        return self.serialPort

    def getUdpSocket(self):
        return self.udpSocket

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

    def readEchosUntilAllNewlines(self, num, newlinesExpected):
        buf = b''
        numNewlines = 0
        for i in range(num):
            buf = buf + self.serialPort.readline()
            newlineArray = re.findall(b'\n', buf)
            numNewlines += len(newlineArray)
            if numNewlines >= newlinesExpected:
                logging.debug("readEchosUntillAllNewlines:found all expected" +
                              " newlines %r", buf)
                return buf
            else:
                logging.debug("readEchosUntillAllNewlines:numNewLines %r < " +
                              "newlinesExpected %r", numNewlines,
                              newlinesExpected)

        logging.debug("readEchosUntillAllNewlines: %r", buf)
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

    def findChar(self, array, binaryCharacter):
        # status = 0-6, C, B, or @
        # otherwise error = -1
        index = array.find(binaryCharacter)
        if index > -1:
            # logging.debug("status: %r, %r", array[index], array)
            return array[index]
        else:
            logging.error("status unknown, unable to find %r: %r",
                          binaryCharacter, array)
            return -1

    def probeResponseCheck(self):
        self.serialPort.write(b'V\r\n')
        if self.findChar(self.readEchos(3),
                         b"MTPH_Control.c-101103>101208") > 0:
            logging.info("Probe on, responding to version string prompt")
            return True
        else:
            logging.info("Probe not responding to version string prompt")
            return False

    def truncateBotchedMoveCommand(self):
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
        self.serialPort.write(b'U/1f1j256V50000R\r\n')
        # returns:
        # U/1f1j256V50000R\r\n
        # U:U/1f1j256V50000R\r\n
        # Step:\xff/0@\r\n
        # if already set to this
        # last line replaced by
        # Step:/0B\r\n
        # if too early in boot phase (?)
        # Have seen this near boot:
        #  b'\x1b[A\x1b[BU/1f1j256V50000R\r\n'
        # And this in cycles
        #  Step:\xff/0@\r\n - makes ascii parser die
        #  Step:/0C\r\n - makes fix for above not work
        #  Step:\r\n
        #

        return self.readEchos(3)

    def sendInit2(self):
        # Init2
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
        return self.readEchos(3)

    def init(self):
        # errorStatus = 0 if all's good
        # -1 if echos don't match exact return string expected
        # -2 if unexpected status
        #
        errorStatus = 0
        # 12 is arbirtary choice. Will tune in main program.
        while errorStatus < 6:  # This is set to 12 in initMoveHomeStep - JAA
            errorStatus = errorStatus + 1
            answerFromProbe = self.sendInit1()
            # check for errors/decide if resend?
            if self.findChar(answerFromProbe, b'@') > 0:
                errorStatus = 12
                # success
            elif self.findChar(answerFromProbe, b'B') > 0:
                logging.warning(" Init 1 status B, resending.")
            elif self.findChar(answerFromProbe, b'C') > 0:
                logging.warning(" Init 1 status C, resending.")
            else:
                logging.warning(" Init 1 status else, resending.")

        self.serialPort.write(b'S\r\n')
        buf = self.readEchos(3)

        errorStatus = 0
        # 12 is arbirtary choice. Will tune in main program.
        while errorStatus < 6:
            answerFromProbe = self.sendInit2()
            # check for errors/decide if resend?
            if self.findChar(answerFromProbe, b'@') > 0:
                errorStatus = 12
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


def main():
    # initial setup of time, logging
    logging.basicConfig(level=logging.DEBUG)

    args = parse_args()

    port = 32107
    init = MTPProbeInit(args, port)

    # Can we move these comments to where they are implemented? -- JAA
    # if on first move status 6 for longer than expected
    # aka command sent properly, but actual movement
    # not initiated, need a Ctrl-c then re-init, re-home

    # overall error conditions
    # 1) no command gets any response
    # - gets one echo, but not second echo
    # - because command collision in init commands
    # Probe needs power cycle
    # 2) stuck at Status 5 wih init/home
    # - unable to find commands to recover
    # Probe needs power cycle

    probeResponding = False
    while (1):  # Why not loop until successful init then stop?? - JAA

        # Check if probe is on and responding
        if probeResponding is False:
            probeResponding = init.bootCheck()

        # Move the next three lines into init()
        time.sleep(1)
        init.readEchosUntilAllNewlines(4, 3)
        init.readEchos(3)
        init.init()
        logging.debug("init successful")


if __name__ == "__main__":
    main()
