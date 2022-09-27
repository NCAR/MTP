###############################################################################
# MTP probe control. Class contains functions that move the probe
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import time
import datetime
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class MTPProbeMove():

    def __init__(self, init, commandDict):
        self.serialPort = init.getSerialPort()
        self.init = init
        self.commandDict = commandDict

    def readScan(self, delay):
        """
        Return current position of stepper motor. Gets output as ScanCount at
        end of A line.
        ScanCount = 1000000 - readScan
        """
        cmd = self.commandDict.getCommand("read_scan")
        # Emperically, read scan needs about .3 seconds delay before
        # command is sent or don't get response when called after home
        # command. When called after B line, works without delay.
        time.sleep(delay)
        self.serialPort.write(cmd)
        answerFromProbe = self.init.readEchos(3, cmd)
        if answerFromProbe.find(b'`') != -1:
            index = answerFromProbe.find(b'`') + 1  # Find backtick
            # Saw "Step:/0b0\r\n", "Step:/0`1000010", "Step:/0`927130"
            stlen = answerFromProbe.find(b'\r\n$')
            logger.info("readScan success with value " +
                        str(answerFromProbe[index:stlen-1]))
            return(answerFromProbe[index:stlen-1])
        else:
            logger.warning("Didn't find backtick in readScan")
            return("-99999")

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
            stlen = answerFromProbe.find(b'\r\n$')
            logger.info("readEnc success with value " +
                        str(answerFromProbe[index:stlen-1]))
            return(answerFromProbe[index:stlen])
        else:
            logger.warning("Didn't find backtick in readEnc")
            return("-99999")

    def moveHome(self):
        """
        Initiate movement home. Home is accomplished by sending two separate
        commands one after the other.

        Return: True if successful or False if command failed
        """
        success = True

        # home1 command components:
        # - turn off both drivers ('J0')
        # - b’U/1f0R’ -> set polarity of home sensor to 0
        # - b’U/1j256R’ -> adjust step resolution to 256
        # - b’U/1Z1000000R’ -> Home and Initialize motor
        # - b’U/1J3R’ -> turn on both drivers
        if not self.sendHome("home1"):  # not success - warn user
            # VB6 code does NOT check for success - it just continues
            logger.warning("Continuing on even though stepper " +
                           "still reports moving")

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
        success = self.sendHome("home2")
        i = 0
        while not success and i < 2:  # not success - try twice more
            # After a Bline, home2 needs more time to complete so sleep
            # and try again.
            time.sleep(0.03)
            success = self.sendHome("home2")  # not success - warn user
            if not success:
                logger.warning("Stepper still reports moving, keep trying.")
            i = i + 1

        if success:
            logger.info("home successful")
        else:
            logger.warning("Continuing on even though stepper " +
                           "still reports moving")

        return True

    def sendHome(self, home):
        """ Send home command to probe """
        # Home returns command with two echos
        # (b'U/1J0f0j256Z1000000J3R\r\nU:U/1J0f0j256Z1000000J3R\r\n)
        # followed by two UART status commands
        # Step:\xff/0`\r\nStep:\xff/0@\r\n'
        cmd = self.commandDict.getCommand(home)
        self.serialPort.write(cmd)
        answerFromProbe = self.init.readEchos(3, cmd)
        # Wait up to 3 seconds for stepper to complete moving
        # Return True of stepper done moving
        return(self.moveWait(home, answerFromProbe, 1.3))

    def moveWait(self, cmdstr, answerFromProbe, delay):
        """
        Wait for stepper to quit moving. Wait for a maximum of delay seconds.
        Recheck every 0.03 seconds
        """
        # See if got status @ = No error. Step @ does NOT mean move is
        # completed. Still need to check status. Just note received @ and
        # continue
        status = self.init.findStat(answerFromProbe)
        if status == '@':
            logger.info(cmdstr + " sent successfully (@)")

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
                time.sleep(0.00)  # VB6 has a placeholder here with no wait
                # and 0.07 commented out with lots of exclamation points.

            # Got a valid stat (0-7), so check and see if stepper is busy
            # If it is not busy, return
            if not self.init.stepperBusy(int(stat)):
                # success
                logger.info(cmdstr + " successful")
                return(True)

            # Increment timeinloop
            timeinloop = datetime.datetime.now() - loopStartTime

        # If looped for delay seconds and stepper still moving, return
        # False
        logger.warning("MTP reports stepper still moving")
        return(False)

    def moveTo(self, location, data):
        # VB6 has if nsteps < 20, don't move. Not sure this ever occurs since
        # this fn is only called when cycling through angles, not on move home
        self.serialPort.write(location)
        echo = self.init.readEchos(3, location)

        # After move and before wait, tune Freq to 1 GHz
        chan = '{:.5}'.format(str(500))
        init = str.encode('C' + str(chan) + "\r\n")
        data.changeFrequency(init, 0)  # 0 = Do not wait for synth to lock

        # Wait up to 3 seconds for stepper to complete moving
        # Return True if stepper done moving
        return(self.moveWait("move", echo, 3))

    def isMovePossibleFromHome(self):
        """
        Returns: True if move is possible otherwise does debugging
        """

        # Check that we are in the HOME position
        # First time through, position reported as 10. Then for each
        # subsequent scan, it is reported as 1000010.
        position = self.readScan(.3)
        if position != "-99999":
            if abs(1000000 - int(position)) < 20 or abs(int(position)) < 20:
                logger.info("MTP in home position")
            else:
                logger.error("Move not possible. Not in home" +
                             " position")
                return(False)
        else:
            logger.error("readScan() failed. Unknown position")
            return(False)

        # Check that integrator has finished
        s = self.init.getStatus()
        status = self.init.integratorBusy(int(s))  # True is integrator busy
        i = 0
        while status and i < 2:  # while intergrator busy - try twice more
            # send integrate and read to clear integrator bit.
            cmd = self.commandDict.getCommand("count")
            self.serialPort.write(cmd)
            self.init.readEchos(2, cmd)
            cmd = self.commandDict.getCommand("count2")
            self.serialPort.write(cmd)
            self.init.readEchos(2, cmd)

            s = self.init.getStatus()
            status = self.init.integratorBusy(int(s))
            if status:  # Couldn't clear integrator
                logger.warning("Integrator not clearing, keep trying.")
            i = i + 1

        if status:
            # Move not possible because couldn't clear integrator
            logger.warning("Continuing on even though could not" +
                           " clear integrator")
        else:
            logger.info("Integrator finished - OK to move")

        # Check if stepper moving
        s = self.init.getStatus()
        if self.init.stepperBusy(int(s)):
            # moveHome() should have cleared this. Warn user.
            logger.error("Clear stepper moving failed. This " +
                         "check should only be called AFTER moveHome." +
                         " Something is wrong. " +
                         "#### Need to update code")
            return False
        else:
            logger.info("Stepper stable - OK to move")

        # Check if synthesizer out of lock.
        s = self.init.getStatus()
        if not self.init.synthesizerBusy(int(s)):
            # synthesizer out of lock
            logger.warning("synthesizer out of lock")
            return False
        else:
            logger.info("Synthesizer locked - OK to move")

        # Passed all tests
        return True
