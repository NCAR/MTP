###############################################################################
# MTP probe control. Class to allow user to send commands to probe one at a
# time. Useful for testing.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
from ctrl.lib.mtpcommand import MTPcommand
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPQuery():

    def __init__(self, port):
        self.serialPort = port

        # Dictionary containing list of valid commands to send to MTP probe
        self.command = MTPcommand()
        self.commandlist = self.command.getCommandValues()

    def query(self):
        """ query/wait which command to send from user """
        while 1:  # Loop until user types 'q'

            # Print available options
            logger.printmsg("info", "")
            logger.printmsg("info", "Available commands are...")
            for i in range(0, len(self.commandlist)):
                logger.printmsg("info", str(self.commandlist[i]))

            query = input("What command shall we send to the probe?\n" +
                          "Enter 'q' to quit and return to main menu\n" +
                          "Enter 'r' to send a readline\n")

            # Check for q to exit this fn and return to main menu
            if query == 'q':
                return()

            # Manual read one line from the serial port (ending in /r/n)
            if query == 'r':
                buf = self.serialPort.readline()
                logger.printmsg("info", "read " + str(buf))

            query = query + '\r\n'

            if query == '\x03':  # Ctrl-C
                self.sendCmd(query)
                continue

            # Check to make sure command is a valid command, i.e.
            # exists in command dict in ctrl/lib/mtpcommand.py
            for i in range(0, len(self.commandlist)):
                if query.encode('ascii') == self.commandlist[i]:
                    print(query.encode('ascii'))
                    print(self.commandlist[i])
                    self.sendCmd(query)
                    break

            if i == len(self.commandlist)-1:
                # If didn't find a valid command, warn user
                logger.printmsg("info", "Command not in valid cmd list")

    def sendCmd(self, query):
        """ Send command to probe """
        query = query.encode('ascii')

        # send command
        self.serialPort.write(query)
        logger.printmsg("info", "sending: " + str(query))

        for i in range(7):  # Read up to 6 returned lines
            print(i)
            buf = self.serialPort.readline()
            logger.printmsg("info", "read " + str(buf))
