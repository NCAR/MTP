import sys
import logging
import argparse
from init import MTPProbeInit


class MTPMoveHomeStep():

    def __init__(self, init):
        self.serialPort = init.getSerialPort()
        self.init = init

    def moveHome(self):
        # When call move home during probe operation, check for existing
        # return strings and handle them. - JAA
        self.init.readEchos(3)

        errorStatus = 0
        # initiate movement home
        self.serialPort.write(b'U/1J0f0j256Z1000000J3R\r\n')
        self.init.readEchos(3)

        # if spamming a re-init, this shouldn't be needed
        # or should be in the init phase anyway
        # self.serialPort.write(b'U/1j128z1000000P10R\r\n')
        # self.init.readEchos(3)

        # S needs to be 4 here
        # otherwise call again
        # unless S is 5
        # then need to clear the integrator
        # with a I (and wait 40 ms)
        return errorStatus

    def moveTo(self, location):
        self.serialPort.write(location)
        return self.init.readEchos(3)

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

        self.init.readEchos(3)

    def isMovePossibleFromHome(self, maxDebugAttempts, scanStatus):
        # returns 4 if move is possible otherwise does debugging
        # debugging needs to know if it's in the scan or starting
        # and how many debug attempts have been made
        # should also be a case statement, 6, 4, 7 being most common

        counter = 0
        while counter < maxDebugAttempts:
            s = self.init.getStatus()
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
                s = self.init.getStatus()
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


def printMenu():
    """ List user options """
    print("Please issue a command:")
    print("0 = Status")
    print("1 = Init")
    print("2 = Move Home")
    print("3 = Step")

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

    move = MTPMoveHomeStep(init)

    probeResponding = False
    while (1):

        cmdInput = printMenu()

        # Check if probe is on and responding
        if probeResponding is False:
            probeResponding = init.bootCheck()

        if cmdInput == '0':
            # Print status
            status = init.getStatus()
            # Should check status here. What are we looking for? - JAA

        elif cmdInput == '1':
            # Initialize probe
            init.init()

        elif cmdInput == '2':
            move.moveHome()

        elif cmdInput == '3':
            if (move.isMovePossibleFromHome(maxDebugAttempts=12,
                                            scanStatus='potato') == 4):
                move.initForNewLoop()

                echo = move.moveTo(b'U/1J0D28226J3R\r\n')
                s = init.findChar(echo, b'@')
                logging.debug("First angle, status = %r", s)


if __name__ == "__main__":
    main()
