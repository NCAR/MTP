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
        """
        Initiate movement home. Home is accomplished by sending two separate
        commands one after the other.

        Return: True if successful or False if command failed
        """
        # home1
        # - turn off both drivers ('J0')
        # - b’U/1f0R’ -> set polarity of home sensor to 0
        # - b’U/1j256R’ -> adjust step resolution to 256
        # - b’U/1Z1000000R’ -> Home and Initialize motor
        # - b’U/1J3R’ -> turn on both drivers
        if self.sendHome("home1"):  # success
            status = self.init.getStatus()
        else:
            logger.printmsg('warning', " **** Need to update code.")
            exit(1)

        # home2
        # After home1, probe returns success but any subsequent clockwise move
        # ('D' commands) don't actually move the probe (though counter-
        # clockwise'P' commands DO move it - not sure why). After a home2, 'D'
        # commands work.
        # - b'U/1j128' -> Adjust the resolution to 128 micro-steps per step.
        #        (critical because subsequent move commands assume a 128
        #         resolution. If resolution is left at 256 from home1, movement
        #         will be twice as big.)
        # - b'U/1Z1000000' -> Home & Initialize the motor.
        #        (sets the current position; suspect this is the magic that
        #         lets the 'D' command work.)
        # - b'U/1P10' -> Move motor 10 steps in positive direction.
        #        (No idea why this backup is needed.
        #         Need to double check the VB6. - JAA)
        if self.sendHome("home2"):  # success
            status = self.init.getStatus()
        else:
            logger.printmsg('warning', " **** Need to update code.")
            exit(1)

        return status

    def sendHome(self, home):
        """ Send home command to probe """
        cmd = self.commandDict.getCommand(home)
        self.serialPort.write(cmd)
        answerFromProbe = self.init.readEchos(4)

        status = self.init.findStat(answerFromProbe)
        if status == '@':
            # success
            logger.printmsg('info', home + " successful")
            status = True
        else:
            # failure
            logger.printmsg('warning', home + " failed with status: " + status)
            status = False

        return status

    def moveTo(self, location):
        self.serialPort.write(location)
        return self.init.readEchos(4)

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
