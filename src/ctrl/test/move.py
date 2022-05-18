from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPProbeMove():

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
                # do an integrate
                self.serialPort.write(b'I\r\n')
                logger.printmsg('DEBUG', "isMovePossible, status = 5")
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
