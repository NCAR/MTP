import logging
# import datetime
import time
import argparse
from init import MTPProbeInit


class MTPMoveHomeStep():

    def __init__(self, serialPort):
        self.serialPort = serialPort

    def getStatus(self):
        ''' Move this to init.py and call it from init - JAA '''
        # status = 0-6, C, B, or @  otherwise error = -1
        # check for T in ST:0X
        # return status
        self.serialPort.write(b'S\r\n')
        answerFromProbe = init.readEchos(4)
        logging.debug("echos from status read: %r", answerFromProbe)
        return self.findCharPlusNum(answerFromProbe, b'T', offset=3)

    def findCharPlusNum(self, array, binaryCharacter, offset):
        ''' Move to init.py - JAA '''
        # status = 0-6, C, B, or @
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

    def moveHome(self):
        errorStatus = 0
        # acutal initiate movement home
        self.serialPort.write(b'U/1J0f0j256Z1000000J3R\r\n')
        init.readEchos(3)
        # if spamming a re-init, this shouldn't be needed
        # or should be in the init phase anyway
        # self.serialPort.write(b'U/1j128z1000000P10R\r\n')
        # init.readEchos(3)

        # S needs to be 4 here
        # otherwise call again
        # unless S is 5
        # then need to clear the integrator
        # with a I (and wait 40 ms)
        return errorStatus

    def moveTo(self, location):
        self.serialPort.write(location)
        return init.readEchos(3)

    def initForNewLoop(self):
        # This is an init command
        # but it moves the motor faster, so not desired
        # in initial startup/go home ?
        # Correct, necessary before move-to-angle commands

        # do a check for over voltage
        # first move command in loop errors:
        # status = 6, but no move
        # step 0C
        self.serialPort.write(b'U/1j128z1000000P10R\r\n')

        init.readEchos(3)

    def isMovePossibleFromHome(self, maxDebugAttempts, scanStatus):
        # returns 4 if move is possible otherwise does debugging
        # debugging needs to know if it's in the scan or starting
        # and how many debug attempts have been made
        # should also be a case statement, 6, 4, 7 being most common

        counter = 0
        while counter < maxDebugAttempts:
            s = self.getStatus()
            counter = counter + 1
            if s == '0':
                # integrator busy, Stepper not moving, Synthesizer out of lock,
                # and spare = 0
                logging.debug('isMovePossible status 0')
                return 0
            elif s == '1':
                logging.debug('isMovePossible status 1')
                return 1
            elif s == '2':
                logging.debug('isMovePossible status 2')
                return 2
            elif s == '3':
                logging.debug('isMovePossible status 3')
                return 3
            elif s == '4':
                logging.debug("isMovePossible is 4 - yes, return")
                return 4
                # continue on with moving
            elif s == '5':
                # do an integrate
                self.serialPort.write(b'I\r\n')
                logging.debug("isMovePossible, status = 5")
                return 5
            elif s == '6':
                # can be infinite,
                # can also be just wait a bit
                s = self.getStatus()
                if counter < maxDebugAttempts:
                    logging.debug("isMovePossible, status = 6, counter = %r",
                                  counter)
                else:
                    logging.error("isMovePossible, status = 6, counter = %r",
                                  counter)
                    return -1
            elif s == '7':
                logging.debug('isMovePossible status 7')
            else:
                logging.error("Home, status = %r", s)


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


# initial setup of time, logging
logging.basicConfig(level=logging.DEBUG)

args = parse_args()

port = 32107
init = MTPProbeInit(args, port)
move = MTPMoveHomeStep(init.getSerialPort())

# if on first move status 6 for longer than expected
# aka command sent properly, but actual movement
# not initiated, need a Ctrl-c then re-init, re-home

probeResponding = False
while (1):

    # Check if probe is on and responding
    if probeResponding is False:
        probeResponding = init.bootCheck()

    init.readEchos(3)
    init.init()
    logging.debug("init successful")

    init.readEchos(3)
    move.moveHome()
    if (move.isMovePossibleFromHome(maxDebugAttempts=12,
                                    scanStatus='potato') == 4):
        move.initForNewLoop()
        time.sleep(3)
        echo = move.moveTo(b'U/1J0D28226J3R\r\n')
        s = init.findChar(echo, b'@')
        logging.debug("First angle, status = %r", s)

    time.sleep(3)
