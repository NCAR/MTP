###############################################################################
# MTP probe control. Class contains functions that move the probe
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPProbeMove():

    def __init__(self, init, commandDict):
        self.serialPort = init.getSerialPort()
        self.init = init
        self.commandDict = commandDict

    def moveHome(self):
        errorStatus = 0
        # initiate movement home
        cmd = self.commandDict.getCommand("home1")
        self.serialPort.write(cmd)
        self.init.readEchos(4)

        return errorStatus

    def moveTo(self, location):
        self.serialPort.write(location)
        return self.init.readEchos(4)

    def initForNewLoop(self):
        # This is an init command
        # but it moves the motor faster, so not desired
        # in initial startup/go home ?
        # Correct, necessary before move-to-angle commands

        # do a check for over voltage
        # first move command in loop errors:
        # status = 6, but no move
        # step 0C
        cmd = self.commandDict.getCommand("home2")
        self.serialPort.write(cmd)

        self.init.readEchos(4)

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
                logger.printmsg('DEBUG', 'isMovePossible status 0')
                return 0
            elif s == '1':
                logger.printmsg('DEBUG', 'isMovePossible status 1')
                return 1
            elif s == '2':
                logger.printmsg('DEBUG', 'isMovePossible status 2')
                return 2
            elif s == '3':
                logger.printmsg('DEBUG', 'isMovePossible status 3')
                return 3
            elif s == '4':
                logger.printmsg('DEBUG', "isMovePossible is 4 - yes, return")
                return 4
                # continue on with moving
            elif s == '5':
                logger.printmsg('DEBUG', "isMovePossible, status 5")
                return 5
            elif s == '6':
                # can be infinite,
                # can also be just wait a bit
                s = self.init.getStatus()
                if counter < maxDebugAttempts:
                    logger.printmsg('debug',
                                    "isMovePossible, status = 6, counter = " +
                                    str(counter))
                else:
                    logger.printmsg('error',
                                    "isMovePossible, status = 6, counter = " +
                                    str(counter))
                    return -1
            elif s == '7':
                logger.printmsg('debug', 'isMovePossible status 7')
            else:
                logger.printmsg('error', "Home, status = " + str(s))
