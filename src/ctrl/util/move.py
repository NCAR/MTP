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

    def isMovePossibleFromHome(self, maxDebugAttempts=12):
        """
        Determine if status allows probe to begin a complete scan.

        This should only be called after home command when probe is in home
        position, i.e. pointed at target.

        Returns: 0, 4 if move is possible otherwise does debugging
        """

        counter = 0
        while counter < maxDebugAttempts:
            s = self.init.getStatus()
            counter = counter + 1

            # Check if integrator busy (status = 1,3,5,7)
            # Integrate logic ensures integrate has completed, so here just
            # send b'I/r/n' to clear integrator bit.
            if s == '1' or s == '3' or s == '5' or s == '7':
                cmd = self.commandDict.getCommand("clear")
                self.serialPort.write(cmd)
                self.init.readEchos(4)
                # What does this return? How do we determine success? - JAA

            # Check if stepper moving (status = 2, 3, 6, 7)
            # but success clearing integrator means we only need to check 2, 6
            if s == '3' or s == '7':
                # Clear integrator failed
                logger.printmsg("error", "Clear integrator failed. " +
                                "#### Need to update code")
                exit(1)
            elif s == '2' or s == '6':
                # moveHome() should have cleared this. Warn user.
                # If this occurs, can we send a 'z' to fix it? - JAA (try it)
                #  - z = Set current position without moving motor.
                logger.printmsg("error", "Clear stepper moving failed. This " +
                                "check should only be called AFTER moveHome." +
                                " Something is wrong. " +
                                "#### Need to update code")
                exit(1)

            # OK to move if synthesizer out of lock (4) or if all clear (0)
            if s == '0' or s == '4':
                # synthesizer out of lock
                logger.printmsg("debug", "isMovePossible is 4 - yes, return")
                return True
                # continue on with moving

            else:
                logger.printmsg("error", "Home, status = " + str(s) +
                                " Something is wrong. ### Need to update code")
                exit(1)
