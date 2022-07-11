###############################################################################
# MTP probe control. Class contains functions that move the probe
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import time
import datetime
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
        # home1 command components:
        # - turn off both drivers ('J0')
        # - b’U/1f0R’ -> set polarity of home sensor to 0
        # - b’U/1j256R’ -> adjust step resolution to 256
        # - b’U/1Z1000000R’ -> Home and Initialize motor
        # - b’U/1J3R’ -> turn on both drivers
        if not self.sendHome("home1"):  # not success - warn user
            logger.printmsg('warning', " **** Need to update code.")
            return False

        # home2
        # After home1, probe returns success but any subsequent clockwise move
        # ('D' commands) don't actually move the probe (though counter-
        # clockwise'P' commands DO move it - not sure why). After a home2, 'D'
        # commands work. home2 command components:
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
        if not self.sendHome("home2"):  # not success - warn user
            logger.printmsg('warning', " **** Need to update code.")
            return False

        logger.printmsg('info', "home successful")
        return True

    def sendHome(self, home):
        """ Send home command to probe """
        # Home returns command with two echos
        # (b'U/1J0f0j256Z1000000J3R\r\nU:U/1J0f0j256Z1000000J3R\r\n)
        # followed by two UART status commands
        # Step:\xff/0`\r\nStep:\xff/0@\r\n'
        cmd = self.commandDict.getCommand(home)
        self.serialPort.write(cmd)
        answerFromProbe = self.init.readEchos(4, cmd)
        # If readEchos called before probe finished moving, get "Step:"
        # without \xff/0@ eg status has not yet been appended to response
        # so go into moveWait loop until move has completed. This code assumes
        # that when move is complete, UART has status @ = No error

        return(self.moveWait)  # Returns true of stepper done moving

    def moveWait(self):
        """
        Wait for stepper to quit moving. Wait for a maximum of 3 seconds.
        Recheck every 0.07 seconds
        """
        loopStartTime = datetime.datetime.now()
        timeinloop = datetime.datetime.now() - loopStartTime
        while timeinloop.total_seconds() < 3:  # 3 seconds
            stat = False
            # Loop until get valid stat (0-7)
            while not stat:  # While stat False
                stat = self.init.getStatus()
                time.sleep(0.07)

            # Got a valid stat (0-7), so check and see if stepper is busy
            # If it is not busy, return
            if not self.init.stepperBusy(int(stat)):
                return(True)

            # Increment timeinloop
            timeinloop = datetime.datetime.now() - loopStartTime

        # If looped for 3 seconds and stepper still moving, return False
        logger.printmsg("error", "Stepper still moving")
        return(False)

    def moveTo(self, location):
        self.serialPort.write(location)
        # If move is not complete, might return "Step:\xff/0`\r\n" instead
        # of @. Either loop until get @ or accept `. What does MJ do?
        # MJ waits for status to return stepper not moving (bit 1 = 0) before
        # reading response.

        echo  = self.init.readEchos(4, location)
        if self.moveWait():  # Returns true of stepper done moving
            return(echo)

    def isMovePossibleFromHome(self, maxDebugAttempts=12):
        # returns 4 if move is possible otherwise does debugging
        # debugging needs to know if it's in the scan or starting
        # and how many debug attempts have been made
        # should also be a case statement, 6, 4, 7 being most common

        counter = 0
        while counter < maxDebugAttempts:
            s = self.init.getStatus()
            counter = counter + 1
            # Check if integrator busy (status = 1,3,5,7)
            # Integrate logic ensures integrate has completed, so here just
            # send b'I/r/n' to clear integrator bit.
            if int(s) % 2 != 0:  # s is odd
                cmd = self.commandDict.getCommand("count")
                self.serialPort.write(cmd)
                self.init.readEchos(4, cmd)
                cmd = self.commandDict.getCommand("count2")
                self.serialPort.write(cmd)
                self.init.readEchos(4, cmd)
                s = self.init.getStatus()
                # What does this return? How do we determine success? - JAA

            # Check if stepper moving (status = 2, 3, 6, 7)
            # but success clearing integrator means we only need to check 2, 6
            if s == '3' or s == '7':
                # Clear integrator failed
                logger.printmsg("error", "Clear integrator failed. " +
                                "#### Need to update code")
                return False
            elif s == '2' or s == '6':
                # moveHome() should have cleared this. Warn user.
                # If this occurs, can we send a 'z' to fix it? - JAA (try it)
                #  - z = Set current position without moving motor.
                logger.printmsg("error", "Clear stepper moving failed. This " +
                                "check should only be called AFTER moveHome." +
                                " Something is wrong. " +
                                "#### Need to update code")
                return False

            # OK to move if synthesizer out of lock (4) or if all clear (0)
            if s == '0' or s == '4':
                # synthesizer out of lock
                logger.printmsg("debug", "isMovePossible is " + str(s) +
                                " - yes, return")
                return True
