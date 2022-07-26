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

    def readScan(self):
        """
        Return current position of stepper motor. Gets output as ScanCount at
        end of A line.
        ScanCount = 1000000 - readScan
        """
        cmd = self.commandDict.getCommand("read_scan")
        self.serialPort.write(cmd)
        answerFromProbe = self.init.readEchos(3, cmd)
        if answerFromProbe.find(b'`') != -1:
            index = answerFromProbe.find(b'`') + 1  # Find backtick
            # Saw "Step:/0b0\r\n", "Step:/0`1000010", "Step:/0`927130"
            stlen = answerFromProbe.find(b'\r\n$')
            return(int(answerFromProbe[index:stlen-1]))
        else:
            logger.printmsg("warning", "Didn't find backtick in readScan")
            return(False)

    def readEnc(self):
        """
        Return the encoder position. Gets output as EncoderCount at
        end of A line. Can be zeroed by "z" command
        EncoderCount = (1000000 - readEnc) * 16
        """
        cmd = self.commandDict.getCommand("read_enc")
        self.serialPort.write(cmd)
        answerFromProbe = self.init.readEchos(3, cmd)
        if answerFromProbe.find(b'`') != -1:
            index = answerFromProbe.find(b'`') + 1  # Find backtick
            stlen = answerFromProbe.find(b'>>')
            return(int(answerFromProbe[index:stlen]))
        else:
            logger.printmsg("warning", "Didn't find backtick in readEnc")
            return(False)

    def moveHome(self):
        """
        Initiate movement home. Home is accomplished by sending two separate
        commands one after the other.

        Return: True if successful or False if command failed
        """
        success = True

        # Start with read_scan. Seems like this would be more useful AFTER
        # home command because it would report how accurately pointing home
        # LastSky = self.readScan()

        # home1 command components:
        # - turn off both drivers ('J0')
        # - b’U/1f0R’ -> set polarity of home sensor to 0
        # - b’U/1j256R’ -> adjust step resolution to 256
        # - b’U/1Z1000000R’ -> Home and Initialize motor
        # - b’U/1J3R’ -> turn on both drivers
        if not self.sendHome("home1"):  # not success - warn user
            # VB6 code does NOT check for success - it just continues
            logger.printmsg('warning', "Continuing on even though stepper" +
                                       "still reports moving")
            success = False

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
            # VB6 code does NOT check for success - it just continues
            logger.printmsg('warning', "Continuing on even though stepper" +
                                       "still reports moving")
            success = False

        if success:
            logger.printmsg('info', "home successful")
        else:
            logger.printmsg('info', "home nominally successful")

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
        # Wait up to 3 seconds for stepper to complete moving
        # Return True of stepper done moving
        return(self.moveWait(home, answerFromProbe, 3))

    def moveWait(self, cmdstr, answerFromProbe, delay):
        """
        Wait for stepper to quit moving. Wait for a maximum of delay seconds.
        Recheck every 0.07 seconds
        """
        # See if got status @ = No error.
        status = self.init.findStat(answerFromProbe)
        if status == '@':
            # success
            logger.printmsg('info', cmdstr + " successful")
            return(True)

        # If readEchos called before probe finished moving, get "Step:"
        # without \xff/0@ eg status has not yet been appended to response
        # so go into loop until move has completed. This code assumes
        # that when move is complete, UART has status @ = No error
        loopStartTime = datetime.datetime.now()
        timeinloop = datetime.datetime.now() - loopStartTime
        while timeinloop.total_seconds() < delay:  # loop for delay seconds
            stat = False
            # Loop until get valid stat (0-7)
            while not stat:  # While stat False
                stat = self.init.getStatus()
                time.sleep(0.07)

            # Got a valid stat (0-7), so check and see if stepper is busy
            # If it is not busy, return
            if not self.init.stepperBusy(int(stat)):
                # success
                logger.printmsg('info', cmdstr + " successful")
                return(True)

            # Increment timeinloop
            timeinloop = datetime.datetime.now() - loopStartTime

        # If looped for delay seconds and stepper still moving, return
        # False
        logger.printmsg("warning", "MTP reports stepper still moving")
        return(False)

    def moveTo(self, location, data):
        # VB6 has if nsteps < 20, don't move. Not sure this ever occurs since
        # this fn is only called when cycling through angles, not on move home
        self.serialPort.write(location)
        echo = self.init.readEchos(4, location)

        # After move and before wait, tune Freq to 1 GHz
        chan = '{:.5}'.format(str(500))
        init = str.encode('C' + str(chan) + "\r\n")
        data.changeFrequency(init, 0)  # 0 = Do not wait for synth to lock

        # Wait up to 3 seconds for stepper to complete moving
        # Return True if stepper done moving
        return(self.moveWait("move", echo, 3))

    def isMovePossibleFromHome(self, maxDebugAttempts=12):
        """
        Returns: True if move is possible otherwise does debugging
        """

        counter = 0
        while counter < maxDebugAttempts:
            counter = counter + 1

            # Check that we are in the HOME position
            # First time through, position reported as 10. Then for each
            # subsequent scan, it is reported as 1000010.
            position = self.readScan()
            if position:
                if abs(1000000 - position) < 20 or abs(position) < 20:
                    logger.printmsg("info", "MTP in home position")
                else:
                    logger.printmsg('error', "Move not possible. Not in home" +
                                    " position")
                    return(False)
            else:
                logger.printmsg('error', "readScan() failed")

            # Check that integrator has finished
            s = self.init.getStatus()
            if self.init.integratorBusy(int(s)):
                # send integrate and read to clear integrator bit.
                cmd = self.commandDict.getCommand("count")
                self.serialPort.write(cmd)
                self.init.readEchos(2, cmd)
                cmd = self.commandDict.getCommand("count2")
                self.serialPort.write(cmd)
                self.init.readEchos(2, cmd)

                s = self.init.getStatus()
                if self.init.integratorBusy(int(s)):
                    # Move not possible because couldn't clear integrator
                    logger.printmsg('error', "Move not possible. Couldn't" +
                                    " clear integrator")
                    return(False)
                else:
                    logger.printmsg('info', "Integrator finished - OK to move")
            else:
                logger.printmsg('info', "Integrator finished - OK to move")

            # Check if stepper moving
            s = self.init.getStatus()
            if self.init.stepperBusy(int(s)):
                # moveHome() should have cleared this. Warn user.
                logger.printmsg("error", "Clear stepper moving failed. This " +
                                "check should only be called AFTER moveHome." +
                                " Something is wrong. " +
                                "#### Need to update code")
                return False
            else:
                logger.printmsg("info", "Stepper stable - OK to move")

            # Check if synthesizer out of lock.
            s = self.init.getStatus()
            if not self.init.synthesizerBusy(int(s)):
                # synthesizer out of lock
                logger.printmsg("warning", "synthesizer out of lock")
                return False
            else:
                logger.printmsg("info", "Synthesizer locked - OK to move")

            # Passed all tests
            return True
