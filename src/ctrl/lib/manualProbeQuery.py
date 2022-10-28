###############################################################################
# MTP probe control. Class to allow user to send commands to probe one at a
# time. Useful for testing.
#
# Written in Python 3
#
# Usage is:
# 1) Start emulator
# 2) python3 MTPmanualProbeQuery.py <userport_from_emulator>
#   -- or --
# 2) python3 MTPmanualProbeQuery.py COM6
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
            logger.info("")
            logger.info("Available commands are...")
            for i in range(0, len(self.commandlist)):
                logger.info(str(self.commandlist[i]))

            query = input("What command shall we send to the probe?\n" +
                          "Enter 'q' to quit and return to main menu\n" +
                          "Enter 'r' to send a readline\n")

            # Check for q to exit this fn and return to main menu
            if query == 'q':
                return

            # Manual read one line from the serial port (ending in /r/n)
            if query == 'r':
                buf = self.serialPort.readline()
                logger.info("read " + str(buf))
                continue

            query = query + '\r\n'

            if query == 'C\r\n':  # Ctrl-C
                fghz = 55.51
                fby4 = (1000 * fghz)/4  # MHz
                # convert to SNP channel (integer) 0.5 MHz = step size
                chan = '{:.5}'.format(str(fby4/0.5))
                cmd = 'C' + chan + '\r\n'
                self.sendCmd(cmd)
                continue

            if query == '\x03\r\n':  # Ctrl-C
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
                logger.info("Command not in valid cmd list")
                answer = input("Command not recognized: " + query +
                               "Enter 'y' to send anyway\n")
                if answer == 'y':
                    self.sendCmd(query)

    def sendCmd(self, query):
        """ Send command to probe """
        query = query.encode('ascii')

        # send command
        self.serialPort.write(query)
        logger.info("sending: " + str(query))

        for i in range(7):  # Read up to 6 returned lines
            print(i)
            buf = self.serialPort.readline()
            logger.info("read " + str(buf))

        # Add parsing temperature call from M line so if working for a while
        # can intermittently check probe temperature.
