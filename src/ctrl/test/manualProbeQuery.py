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
            query = input("What command shall we send to the probe?\n" +
                          "Enter 'q' to quit and return to main menu\n")

            # Check for q to exit this fn and return to main menu
            if query == 'q':
                return()

            query = query + '\r\n'
            # Check to make sure command is a valid command, i.e.
            # exists in command dict in ctrl/lib/mtpcommand.py
            for i in range(0, len(self.commandlist)):
                try:
                    if query == self.commandlist[i].decode('ascii'):
                        self.sendCmd(query)
                except Exception:
                    if query == self.commandlist[i]:
                        self.sendCmd(query)

    def sendCmd(self, query):
        """ Send command to probe """
        query = query.encode('ascii')
        print("Sending: " + str(query))

        # send command
        self.serialPort.write(query)
        logger.printmsg("debug", "sending: " + str(query))

        for i in range(4):  # Read up to 4 returned lines
            print(i)
            buf = self.serialPort.readline()
            logger.printmsg("debug", "read " + str(buf))
