###############################################################################
# Program to emulate the MTP firmware
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
"""
This module can be used to emulate the MTP by starting it from the command
line. It will read commands from a serial port and respond as the instrument
would.

Firmware command list:

| Command               | Description        |
|-----------------------|--------------------|
| F ddddd.d             | Sets frequency for synthesizer, in MHz - 7 digits,
|                       | decimal always required
| I dd                  | integrate for dd * 20mS
| Cddddd                | Change SPI sequence
| R                     | Read results of last integration from counter
| M 1                   | Read all 8 channels of multiplexer 1
| M 2                   | Read all 8 channels of multiplexer 2
| P                     | Read all 8 platinum RTD channels
| U/1$$$$$$$            | Send string $ to stepper #1 (only one now)
|                       | - See [Linn Engineering manual for 23-CE controller]
|                       | (doc) for command list
| V                     | Return version date, etc. for this program
| X ss dd ff gg etc.... | Sends bytes directly to SPI bus for diagnostic
|                       |  purposes
| Control-C (ascii 3)   | is caught in interrupt routine and restarts this
|                       | program
| S                     | read status byte. Status byte meanings:
|                       |                    *  Bit 0 = integrator busy
|                       |                    *  Bit 1 = Stepper moving
|                       |                    *  Bit 2 = Synthesizer out of lock
|                       |                    *  Bit 3 = spare

"""
import os
import serial
import sys
import time
import random
import argparse
import logging
import subprocess as sp
import shutil
import tempfile
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPEmulator():

    def __init__(self, device):
        """ Open the given serial device """

        self.sport = serial.Serial(device, 9600, timeout=0)
        self.sport.nonblocking()
        self.status = '04'  # Even number indicates integrator not busy
        self.statusset = False
        self.commandstatus = {
            "lastcommand": "start",
            "timeoflastcommand": time.time(),  # float of seconds since epoc
            "expectedduration":  0.004  # usec

        }

    def setcommandstatus(self, command, duration):
        self.commandstatus['lastcommand'] = command
        self.commandstatus['timeoflastcommand'] = time.time()
        self.commandstatus['expectedduration'] = duration

    def listen(self, chaos, state):
        """ Loop and wait for commands to arrive """

        while (True):
            # Read data from the serial port and echo it back
            rdata = self.sport.read(128)

            # Convert to ASCII string (from binary)
            self.cdata = rdata.decode('utf-8')

            # Only handle lines whose newline has been received.
            lines = self.cdata.splitlines()
            remainder = ""
            if lines and not self.cdata.endswith("\n"):
                remainder = lines[-1]
                lines = lines[:-1]
            self.cdata = remainder
            for line in lines:
                logger.printmsg("DEBUG", "Found: " + line)

                # Parse command and send appropriate response back over port
                self.interpretCommand(line, chaos, state)

    def interpretCommand(self, line, chaos, state):
        """ Parse command and send appropriate response back over port """
        # All lines echo immediately, then have actual responses
        string = '\r\n' + line + '\r\n'
        self.sport.write(string.encode('utf-8'))

        if line[0] == 'V':  # Firmware Version
            # Return version date, etc. for this program.
            # Emulator mimics firmware.
            if state == 'noresp':
                time.sleep(200)
            self.sport.write(b'Version:MTPH_Control.c-101103>101208\r\n')

        elif line[0] == '0X03':  # Restart firmware
            logger.printmsg("DEBUG", "hex Control-C char")
            # This emulator does NOT emulate a firmware restart.
            # Only thing visible from firmware restart is another V command.
            time.sleep(20)
            if chaos == 'low':
                time.sleep(1)
            elif chaos == 'medium':
                # find example of firmware overload string
                self.sport.write(b'\r\n0123456789ABCDEF\\x21\\x43\\x65\r\n')
            elif chaos == 'high':
                # Uncertain what this response would do
                self.sport.write(b'\r\n0x03\r\n')
            elif chaos == 'extreme':
                # To emulate completely unresponsive probe
                self.sport.write(b'')
            self.sport.write(b'Version:MTPH_Control.c-101103>101208\r\n')

        elif line[0] == 'C':  # Change SPI sequence
            logger.printmsg("DEBUG", "string starting with C" + line)
            # there are two echos for C's, both are identical
            # neither seems to have any status info about if it
            # actually set correctly
            self.sport.write(string.encode('utf-8'))

        elif line[0] == 'U':  # Parse UART commands
            # all commands echo exact command, then other responses
            if chaos == 'low':
                duration = 0.03
            else:
                # emulate that long first and last step
                # random between 0 and 10 seconds
                duration = 10
            self.setcommandstatus('U', duration)
            self.statusset = False
            self.UART(line, chaos, state)

        elif line[0] == 'I':  # Integrate channel counts array "I 40"
            self.status = '05'  # Odd number indicates integrator busy
            # Parse number out of line
            (cmd, value) = line.split()
            # Convert byte to two ascii digits in hex
            val = int(value)
            self.hex = self.ntox((val >> 4) & 0x0f) + self.ntox(val & 0x0f)
            string = '\r\nI' + self.hex + '\r\n'
            # This command starts the integrator,
            # sets the integrator busy bit (status = 05)
            # then waits 40us
            # so the S should, if
            duration = random.randrange(4, 5, 3)
            self.setcommandstatus('I', duration)
            self.sport.write(string.encode('utf-8'))

        elif line[0] == 'R':  # Return counts from last integration
            # Sending back 19000 counts for all channels/angles
            string = '\r\nR' + self.hex + ':4A38\r\n'
            self.sport.write(string.encode('utf-8'))

        elif line[0] == 'S':  # Return firmware status
            if chaos == 'low':
                self.status = '04'  # Even number indicated integrator NOT busy
            else:
                self.status = self.conditionalStatus(chaos, state)
            string = '\r\nST:' + self.status + '\r\n'
            self.sport.write(string.encode('utf-8'))

        elif line == 'M 1':  # Read M1
            # Line being sent (in hex) is:
            # M01:2928 2300 2898 3083 1920 2920 2431 2946
            self.sport.write(
                b'\r\nM01:B70 8FC B52 C0B 780 B68 97F B82 \r\n')

        elif line == 'M 2':  # Read M2
            # Line being sent (in hex) is:
            # M02:2014 1209 1550 2067 1737 1131 4095 1077
            # Tsynth of 3D0 translates to 50.03 C,
            # Tsynth of 3E0 translates to 49.64 C
            if state == 'overheat':
                a = random.randrange(10)
                if a % 2 == 0:
                    self.sport.write(
                        b'\r\nM02:7DF 494 539 5FF 614 436 FFF 3E0 \r\n')
                else:
                    self.sport.write(
                        b'\r\nM02:7DF 494 539 5FF 614 436 FFF 3D0 \r\n')
            else:
                self.sport.write(
                    b'\r\nM02:7DF 494 539 5FF 614 436 FFF 3F0 \r\n')

        elif line[0] == 'P':  # Read P
            # Line being sent (in hex) is:
            # Pt:2159 13808 13809 4370 13414 13404 13284 14439
            self.sport.write(
                b'\r\nPt:B70 8FC B52 C0B 780 B68 97F B82 \r\n')

        elif line == 'N 1':  # Set Noise Diode On
            self.sport.write(b'\r\nND:01\r\n')

        elif line == 'N 0':  # Set Noise Diode Off
            self.sport.write(b'\r\nND:00\r\n')

    def ntox(self, nx):
        """ Convert nibble to asc hex 0-f """

        hx = "0123456789ABCDEF"
        return(hx[nx])

    def UART(self, line, chaos, state):
        """
        Send string $ to stepper

        Stepper string command meanings:
        | f | Set polarity or direction of home sensor, default is zero
        | j | Adjust the resolution in micro-steps per step.
                    [1,2,4,8,16,32,64,128,256]
        | V | Set top speed of motor in micro-steps per second.
        | L | Set acceleration factor micro-steps per second^2.
        | h | Set hold current 0-50% of 3.0 Amp max
        | m | Set running current 0-100% of 3.0 Amp max
        | J | On/off driver. 0-both off; 3-both on; 2 - driver2 on, driver1 off
        | Z | Home and Initialize motor
        | z | Set current position without moving motor.
        | P | Move motor relative number of steps in positive direction
        | D | Move motor relative number of steps in negative direction
        | R | run command string

        Returned value meanings (e.g. ff/0@ = No error):
            ff - RS485 line turnaround char; starts message
            /  - start char
            0  - address of message recipient
            @  - status char (upper case device busy, lower not)
                Ascii @/` =Hex 40/60 - No error
                Ascii A/a =Hex 41/61 - Initialization Error
                Ascii B/b =Hex 42/62 - Illegal Command sent
                Ascii C/c =Hex 43/63 - Out of range operand value
                Ascii E/e =Hex 45/65 - Internal communication err
                Ascii G/g =Hex 47/67 - Not initialized before move
                Ascii I/i =Hex 49/69 - Overload error (too fast)
                Ascii K/k =Hex 4B/6B - Move not allowed
                Ascii O/o =Hex 4F/6F - Already executing command
                                        when another received
        """
        # including D,d for 'unknown'
        # D is a UART command - move negative. Better to use value not used
        # otherwise. - JAA
        error = ['@', '`', 'A', 'a', 'B', 'b', 'C', 'c', 'D', 'd', 'E', 'e',
                 'G', 'g', 'I', 'i', 'K', 'k', 'O', 'o']
        # Note: The MTP control program sends strings like
        # b'U/1J0D######J3R\r\n'. This *appears* to indicate the stepper
        # motor is moving backward (negative direction). However, in actuality
        # negative steps cause the motor to rotate from top to bottom when
        # the mirror is facing forward.
        string = 'U:' + line + '\r\n'
        if chaos == 'low':
            self.sport.write(string.encode('utf-8'))
            self.sport.write(b'Step:\xff/0@\r\n')  # No error
        if chaos == 'medium':
            self.sport.write(string.encode('utf-8'))
            # delay @ by 0-30us skipping first 3 numbers generated
            time.sleep(random.randrange(0, 30, 3))
            # ` means the move is happening
            self.sport.write(b'Step:\xff/0`\r\n')
            # @ means the move has stopped
            self.sport.write(b'Step:\xff/0@\r\n')
        if chaos == 'high':
            # one in 5 chance of not getting an @
            # this lack should casuse a re-init/powercycle
            self.sport.write(string.encode('utf-8'))
        if chaos == 'extreme':
            # Report other stepper motor states
            rand = random.choice(error)
            # String is not output. What is the intention here?? - JAA
            string = b'\r\nStep:\xff/0' + error[rand].encode('utf-8') + '\r\n'
            self.sport.write(b'\r\nStep:\xff/0c\r\n')

    def conditionalStatus(self, chaos, state):
        # Two command types have conditions, I (integrate) and U (move)
        # Function returns string of status eg '04'
        # - Bit 0 = integrator busy
        # - Bit 1 = Stepper moving
        # - Bit 2 = Synthesizer out of lock
        # - Bit 3 = spare
        lastcommand = self.commandstatus['lastcommand']
        commandtime = self.commandstatus['timeoflastcommand']
        dur = self.commandstatus['expectedduration']

        if lastcommand == "I":
            # integrator has to start (05)
            # and after 40 s integrator has to finish (04)
            # even/odd checking will get data in more cases
            # but it accuracy suffers.
            # if even/odd check perhaps log, but take anyway?
            # the more robust move should limit these.
            logging.debug("conditional status I detected")
            if time.time() <= commandtime + dur:
                if chaos == 'low':
                    return '05'
                elif chaos == 'medium':
                    # possibility that integrator doesn't start
                    # or finishes quickly
                    return random.choice(['04', '05'])
                else:
                    # possibility that move went wrong, but integrator still
                    # started
                    return random.choice(['01', '03', '05', '07'])
            else:
                if chaos == 'low':
                    return '04'
                elif chaos == 'medium':
                    # integrate goes long, or
                    return random.choice(['04', '05'])
                else:
                    return random.choice(['00', '02', '04', '06'])

        elif lastcommand == "U":
            self.statusset = True
            if time.time() <= commandtime+dur:
                # emulate moving
                if chaos == 'low':
                    return '05'
                elif chaos == 'medium' or chaos == 'high':
                    if not self.statusset:
                        return random.choice(['01', '03', '05', '07'])
                elif chaos == 'extreme':
                    if not self.statusset:
                        self.status = random.choice(['00', '01', '02', '03',
                                                     '04', '05', '06', '07'])
            else:
                # emulate stop
                # this else should only run once per 'stop'
                # except when the status is not 04 -
                # then there's logic about what commands need
                # to be called to successfully return to 4. Ugh.

                if chaos == 'low':
                    # successful stop
                    return '04'
                elif chaos == 'medium':
                    return '04'
                elif chaos == 'high':
                    # currently emulates that the probe is stuck
                    # signifigant investment to logic out the rest
                    if not self.statusset:
                        return random.choice(['00', '02', '04', '06'])
                elif chaos == 'extreme':
                    # currently emulates that the probe is stuck
                    # signifigant investment to logic out the rest
                    if not self.statusset:
                        self.status = random.choice(['00', '01', '02', '03',
                                                     '04', '05', '06', '07'])
            # most of this is done, tested with probe so implementation
            # here will be minimal.
            logging.debug("conditional status U detected")
        return '04'

    def close(self):
        """ Close port when exit """
        self.sport.close()


class MTPVirtualPorts():
    """
    Shamelessly stolen from the GNI emulator code. -JAA 4/13/2022

    Setup virtual serial devices.

    This creates two subprocesses: the socat process which manages the pty
    devices for us, and the socat "serial relay" to which the emulator process
    will connect.

    The MTP emulator opens the "MTP port", or mtpport, while the MTP control
    program opens the "user port", or userport.
    """
    def __init__(self):
        self.socat = None
        self.mtpport = None
        self.userport = None
        self.tmpdir = None

    def getUserPort(self):
        return self.userport

    def getMTPPort(self):
        return self.mtpport

    def startPorts(self, loglevel):
        " Start just the ports. The emulator is run separately."
        self.tmpdir = tempfile.mkdtemp()
        self.userport = os.path.join(self.tmpdir, "userport")
        self.mtpport = os.path.join(self.tmpdir, "mtpport")
        cmd = ["socat"]
        # Verbose if in debug mode
        if loglevel == 'DEBUG':
            cmd.extend(["-v"])

        cmd.extend(["PTY,echo=0,link=%s" % (self.mtpport),
                    "PTY,echo=0,link=%s" % (self.userport)])
        logger.printmsg("DEBUG", " ".join(cmd))

        # Open ports
        self.socat = sp.Popen(cmd, close_fds=True, shell=False)
        started = time.time()

        found = False
        while time.time() - started < 5 and not found:
            time.sleep(1)
            found = bool(os.path.exists(self.userport) and
                         os.path.exists(self.mtpport))

        # Error handling
        if not found:
            raise Exception("serial port devices still do not exist "
                            "after 5 seconds")
        return self.mtpport

    def stop(self):
        logger.printmsg("INFO", "Stopping...")
        if self.socat:
            logger.printmsg("DEBUG", "killing socat...")
            self.socat.kill()
            self.socat.wait()
            self.socat = None
        if self.tmpdir:
            logger.printmsg("DEBUG", "removing %s" % (self.tmpdir))
            shutil.rmtree(self.tmpdir)
            self.tmpdir = None


def parse_args():
    """ Instantiate a command line argument parser """

    # Define command line arguments which can be provided
    parser = argparse.ArgumentParser(
        description="Script to emulate the NCAR MTP instrument")
    parser.add_argument(
        '--debug', dest='loglevel', action='store_const', const=logging.DEBUG,
        default=logging.INFO, help="Show debug log messages")
    parser.add_argument(
        '--logmod', type=str, default=None, help="Limit logging to " +
        "given module")
    parser.add_argument(
        '--chaos', dest='chaos', default='medium', help=" [low, medium, " +
        "high, extreme] where low is ideal probe operation where all " +
        "commands are sent immediately, medium approximates nominal probe " +
        "operation, high includes variable times for commands and high " +
        "incidences of error conditons, extreme includes theoretical states " +
        "of the probe/motor that have been observed very rarely or never")
    parser.add_argument(
        '--state', dest='state', default='normal', help="[normal, overheat, " +
        "overvolt, noresp ] to emulate specific error conditions that are " +
        "either highly concerning or require signifigant deviation from " +
        "normal loop. overheat should warn with red toggle, overvolt should " +
        "warn with red toggle, noresp should warn with popup and return to " +
        "re-init")

    # Parse the command line arguments
    args = parser.parse_args()

    return(args)


def main():

    # Process command line arguments
    args = parse_args()

    # Configure logging
    stream = sys.stdout
    logger.initLogger(stream, args.loglevel, args.logmod)

    # Instantiate a set of virtual ports for MTP emulator and control code
    # to communicate over. When the control program is manually started, it
    # needs to connect to the userport.
    vports = MTPVirtualPorts()
    if args.loglevel:
        level = logging.getLevelName(args.loglevel)

    mtpport = vports.startPorts(level)
    print("Emulator connecting to virtual serial port: %s" % (mtpport))
    print("User clients connect to virtual serial port: %s" %
          (vports.getUserPort()))

    # Instantiate MTPemulator and connect to mtpport.
    mtp = MTPEmulator(mtpport)

    # Loop and listen for commands from control program
    mtp.listen(args.chaos, args.state)

    # Clean up
    mtp.close()
    vports.stop()


if __name__ == "__main__":
    sys.exit(main())
