import logging
import datetime
import time
import serial
import socket
import sys
from serial import Serial

logging.basicConfig(level = logging.DEBUG)
# initial setup of time, logging, serialPort, Udp port
serialPort = serial.Serial('COM6', 9600, timeout = 0.15)
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
udpSocket.connect(('127.0.0.1', 32107)) # ip, port number

def readEchos(num):
    buf = b''
    for i in range(num):
        buf = buf + serialPort.readline()

    logging.debug("read %r", buf)
    return buf



def moveComplete(buf):
    # returns true if '@' is found,
    # needs a timeout if comand didn't send properly
    if buf.find(b'@') >= 0:
        return True 
    return False


def sanitize(data):
    data = data[data.find(b':') + 1 : len(data) - 3]
    placeholder = data.decode('ascii')
    place = placeholder.split(' ')
    ret = ''
    for datum in place:
        ret += '%06d' % int(datum,16) + ' '

    return ret

def findChar(array, binaryCharacter):
    # status = 0-6, C, B, or @
    # otherwise error = -1
    index = array.find(binaryCharacter)
    if index>-1:
        #logging.debug("status: %r, %r", array[index], array)
        return array[index]
    else:
        logging.error("status unknown, unable to find %r: %r",  binaryCharacter, array)
        return -1

def probeResponseCheck():
        serialPort.write(b'V\r\n')
        if findChar(readEchos(3), b"MTPH_Control.c-101103>101208")>0:
            logging.info("Probe on, responding to version string prompt")
            return True
        else:
            logging.info("Probe not responding to version string prompt")
            return False

def truncateBotchedMoveCommand():
        serialPort.write(b'Ctrl-C\r\n')
        if findChar(readEchos(3),b'Ctrl-C\r\n')>0:
            logging.info("Probe on, responding to Ctrl-C string prompt")
            return True
        else:
            logging.info("Probe not responding to Ctrl-C string prompt")
            return False


def probeOnCheck():
    if findChar(readEchos(3), b"MTPH_Control.c-101103>101208")>0:
        logging.info("Probe on, Version string detected")
        return True
    else:
        logging.debug("No version startup string from probe found, sending V prompt")
        if probeResponseCheck():
            return True
        else:
            if truncateBotchedMoveCommand():
                logging.warning("truncateBotchedMoveCommand called, ctrl-c success")
                return True
            else:
                logging.error("probe not responding to truncateBotchedMoveCommand ctrl-c, power cycle necessary")
                return False

    logging.error("probeOnCheck all previous logic tried, something's wrong")
    return False



def sendInit1():
    # Init1
    serialPort.write(b'U/1f1j256V50000R\r\n')
    # returns:
    # U/1f1j256V50000R\r\n
    # U:U/1f1j256V50000R\r\n
    # Step:\xff/0@\r\n
    # if already set to this
    # last line replaced by
    # Step:/0B\r\n
    # if too eary in boot phase (?)
    # Have seen this near boot:
    #  b'\x1b[A\x1b[BU/1f1j256V50000R\r\n'
    # And this in cycles
    #  Step:\xff/0@\r\n - makes ascii parser die
    #  Step:/0C\r\n - makes fix for above not work
    #  Step:\r\n
    #

    return readEchos(3)

def sendInit2():
    # Init2
    serialPort.write(b'U/1L4000h30m100R\r\n')
    # normal return:
    #
    # U/1f1j256V50000R\r\n
    # U:U/1f1j256V50000R\r\n
    # b'Step:\xff/0@\r\n'

    # error returns:
    # \x1b[A\x1b[BU/1f1j256V50000R
    # Step:\xff/0B\r\n'
    #
    return readEchos(3)

def init():
    # errorStatus = 0 if all's good
    # -1 if echos don't match exact return string expected
    # -2 if unexpected status
    #
    errorStatus = 0
    # 12 is arbirtary choice. Will tune in main program.
    while errorStatus < 12:
        answerFromProbe = sendInit1()
        # check for errors/decide if resend?
        if findChar(answerFromProbe, b'@') >0:
            errorStatus = 12
            # success
        elif findChar(answerFromProbe, b'B') >0:
            logging.warning(" Init 1 status B, resending.")
            errorStatus = errorStatus + 1
        elif findChar(answerFromProbe, b'C') >0:
            logging.warning(" Init 1 status C, resending.")
            errorStatus == errorStatus + 1
        else:
            logging.warning(" Init 1 status else, resending.")
            errorStatus == errorStatus + 1



    serialPort.write(b'S\r\n')
    buf = readEchos(3)

    errorStatus = 0
    # 12 is arbirtary choice. Will tune in main program.
    while errorStatus < 12:
        answerFromProbe = sendInit2()
        # check for errors/decide if resend?
        if findChar(answerFromProbe, b'@') >0:
            errorStatus = 12
            # success
        elif findChar(answerFromProbe, b'B') >0:
            logging.warning(" Init 2 status B, resending.")
            errorStatus = errorStatus + 1
        elif findChar(answerFromProbe, b'C') >0:
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



def moveHome():
    errorStatus = 0
    # acutal initiate movement home
    serialPort.write(b'U/1J0f0j256Z1000000J3R\r\n')
    readEchos(3)
    # if spamming a re-init, this shouldn't be needed
    # or should be in the init phase anyway
    #serialPort.write(b'U/1j128z1000000P10R\r\n')
    #readEchos(3)
    
    # S needs to be 4 here
    # otherwise call again
    # unless S is 5
    # then need to clear the integrator
    # with a I (and wait 40 ms)

    return errorStatus

def initForNewLoop():
    # This is an init command
    # but it moves the motor faster, so not desired
    # in initial startup/go home ?
    # Correct, necessary before move-to-angle commands

    # do a check for over voltage
    # first move command in loop errors:
    # status = 6, but no move
    # step 0C
    serialPort.write(b'U/1j128z1000000P10R\r\n')

    readEchos(3)


# if on first move status 6 for longer than expected 
# aka command sent properly, but actual movement 
# not initiated, need a Ctrl-c then re-init, re-home

# on boot probe sends 
# MTPH_Control.c-101103>101208
# needs to be caught first before other init commands are sent
# also response to V
probeResponding = False
while (1):
    if probeResponding == False:
        while probeOnCheck() == False:
            time.sleep(1)
            logging.error("probe off or not responding")
        logging.info("Probe on check returns true")
        probeResponding = True

    readEchos(3)
    init()
    readEchos(3)
    moveHome()
    initForNewLoop()

# overall error conditions
# 1) no command gets any response
# - gets one echo, but not second echo 
# - because command collision in init commands
# Probe needs power cycle
# 2) stuck at Status 5 wih init/home
# - needs a integrate 
# Probe needs power cycle




