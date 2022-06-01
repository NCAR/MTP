###############################################################################
# Class defining a dictionary to hold all the various firmware commands used to
# control the MTP instrument.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################


class MTPcommand():

    def __init__(self):
        """
        Initialize a dictionary of serial commands accepted by the MTP
        instrument. Assign user-understandable keys for each command.  The
        commands are passed to the MTP firmware file firmware/MTPH_Control.

        Commands that begin with something other than 'U' are processed by the
        firmware.  Descriptions taken from firmware/MTPH_Control.C and/or
        MTP-VB6/MTPH_ctrl/MTPH_Control.frm.

        Firmware commands include:
        A, C, F, I, M, N, P, R, S, U, V, X

        A U at the beginning of the command indicates String to Stepper UART,
        i.e. U/1$$$$$$$ = send string $$$$$$$ to stepper #1 (the MTP only uses
        Address 1). In other words, the firmware just passes the command thru
        to the stepper motor.

        See the Lin Engineering manual for 23-CE controller for a command list.
        (https://github.com/NCAR/MTP-VB6/tree/master/firmware/doc)

        The DT Protocol allows the unit to be commanded over a simple serial
        port. The command format is:

        start char | Address | Commands        |  Run  | End of string
        --------------------------------------------------------------
            /      |   1     | Command strings |   R   |   <CR>

        A description of select commands taken from the Lin Engineering manual
        are given here:
        R - Run the command string that is currently in the execution buffer
            Always end commands with 'R'
        J - Turn On/Off the driver (I/O's are bidirectional). It's a two bit
            binary value: 3 = 1 1 = Both drivers on
                          2 = 1 0 = Driver2 on, Driver 1 off, etc

        Query commands can be executed while other commands are still running
        ?0 - Return the current motor position
        ?8 - Return the Encoder Position. Can be seroed by 'z' command
        T  - Terminate current commands

        'init': 'U/1f1j256V5000L5000h30m100R\r':  # initialize
        f1    - Set polarity of direction of home sensor, default is 0.
        j256  - Adjust the resolution in micro-steps per step.
        V5000 - Set the top speed of the motor in micro-steps/sec.
        L5000 - Set the acceleration factor micro-steps per sec^2 = (Lvalue X
                6103.5) i.e. L1 takes 16.384 seconds to get to a speed of V =
                100000 micro-steps per sec.
        h30   - Set the hold current on a scale of 0-50% of the max current,
                3.0 Amps. Default is h10
        m100  - Set the running current on a scale of 0-100% of the max current
                , 3.0 Amps. Default is m30

        'home1': 'U/1J0f0j256Z1000000J3R\r':
        J0       - Both drivers off
        f0       - Set polarity of direction of home sensor, default is 0.
        j256     - Adjust the resolution in micro-steps per step.
        Z1000000 - Home & Initialize the motor. Motor will turn towards 0 until
                   home opto sensor is interrupted. Current motor position is
                   set to zero. Take 1,000,000 steps to find the home sensor.
                   If sensor is still not found after 1,000,000 steps, stop
                   motion.
        J3       - Both drivers on

        'home2': 'U/1j128z1000000P10R\r':
        j128     - Adjust the resolution in micro-steps per step.
        Z1000000 - Home & Initialize the motor.
        P10      - Move Motor relative number of steps in positive direction. A
                   'P0' command rotates the motor indefinitely, which enters
                   into Velocity mode. Any other finite number sets the mode to
                   Position mode.

        'home3': 'U/1j64z1000000P10R\r':
        j64      - Adjust the resolution in micro-steps per step.
        z1000000 - Home & Initialize the motor.
        P10      - Move Motor relative number of steps in positive direction.

        'move_fwd': 'U/1J0P' + Nsteps + 'J3R\r:
        J0        - Both drivers off
        P<Nsteps> - Move Motor Nsteps steps in positive direction.
        J3        - Both drivers on

        'move_bak': 'U/1J0D' + Nsteps + 'J3R\r':
        J0        - Both drivers off
        D<Nsteps> - Move Motor Nsteps steps in negative direction.
        J3        - Both drivers on

        'init1': 'U/1f1j256V50000R\r':
        f1     - Set polarity of direction of home sensor, default is 0.
        j256   - Adjust the resolution in micro-steps per step.
        V50000 - Set the top speed of the motor in micro-steps/sec.

        'init2': 'U/1L4000h30m100R\r':
        L4000  - Set the acceleration factor micro-steps per sec^2
        h30    - Set the hold current
        m100   - Set the running current


        Python3 requires the strings to either use the b'' syntax or
        be passsed through a str.encode(), which cumulatively causes
        some slowness.
        The \n after the \r is not strictly necessary for the probe,
        but pyQt's canReadLine checks for a \n, so not having it was
        causing concatination of the command echo and the probe's response
        """

        command_list = {
            # This first set of commands are firmware commands. The firmware
            # contains the actual command sent to the stepper motor.
            'version': b'V\r\n',      # Request the MTP Firmware Version. The
                                      # firmware version is hardcoded in
                                      # MTPH_Control.C
            'status': b'S\r\n',       # Request the MTP Firmware Status
                                      # - Bit 0 = integrator busy
                                      # - Bit 1 = Stepper moving
                                      # - Bit 2 = Synthesizer out of lock
                                      # - Bit 3 = spare
            'ctrl-C': chr(3).encode('ascii'), # Send ascii char "3" = Ctrl-C.
                                      # Is caught in firmware interrupt
                                      # routine and restarts the program.
            'read_P': b'P\r\n',       # Read all 8 platinum RTD channels
                                      # Return components of P line
            'read_M1': b'M 1\r\n',    # Read all 8 channels of multiplexer 1
                                      # Return components of M1 line
            'read_M2': b'M 2\r\n',    # Read all 8 channels of multiplexer 2
                                      # Return components of M2 line

            # From VB6 sub integrate()
            'count': b'I 40\r\n',     # Count up the chCounts array; integrate
                                      # for 40 * 20mS
            'count2': b'R\r\n',       # Read results of last integration from
                                      # counter (counts for each channel)

            # From VB6 sub Noise() - called by Eline(). Noise diode.
            'noise1': b'N 1\r\n',  # Set Noise Diode On  ( I may have these )
            'noise0': b'N 0\r\n',  # Set Noise Diode Off ( backward - TBD   )

            # The next set of commands are passed to the stepper motor as-is.

            'terminate': b'U/1TR\r\n',   # Terminate the stepper motion
            'read_scan': b'U/1?0R\r\n',  # Read a scan
            'read_enc': b'U/1?8R\r\n',   # Read encoder

            # VB6 sub tune(); set frequency for synthesizer, in MHz - 7 digits,
            # decimal always required.
            # operate with "C" mode ( New SNP-1216 Synthesizers in 'C' mode )
            # This won't work because chan is not defined. Just a placeholder

            # Have switch in storePacket called tuneMode that stores either C
            # or F to switch between these
            # must be a manual switch, can't find anything that would copy the
            # tuneF or tuneC functions to tune (actually called) in vb6
            # 'tuneC': 'C ' + chan + '\r',

            # VB6 sub nwtune();
            # 'tuneF': 'F ' + chan + '\r',

            # From VB6 sub Init()
            #'init': b'U/1f1j256V5000L5000h30m100R\r\n',  # initialize

            # From VB6 sub initScan() - looks like these two togeter accomplish
            # same set of commands as one above - with different values.
            'init1': b'U/1f1j256V50000R\r\n',  # direction,top speed,
                                               # uSteps/step
            'init2': b'U/1L4000h30m100R\r\n',  # acceration, holding current,
                                               # motor current
            #'init3': b'U/1j8v800V3000L20m70R\r\n',  # from WFP_Init.txt believe
                                                    # to be unused

            # From VB6 sub homeScan() - These three step down in resolution, so
            # maybe finer and finer adjustment of home position?
            'home1': b'U/1J0f0j256Z1000000J3R\r\n',
            'home2': b'U/1j128z1000000P10R\r\n',
            # while vb6 does send this, it immediately overrides with
            # another home2. Keeping this as the last one
            # makes the steps (with the same move command)
            # taken by the mirror about 2x as large
            #'home3': b'U/1j64z1000000P10R\r\n',

            # From VB6 sub moveScan(). Move the MTP Nsteps.
            # This syntax won't work because Nsteps is not defined - just a
            # placeholder.
            'move_fwd_front': 'U/1J0P',  # + Nsteps + 'J3R\r', # If Nsteps >= 0
            'move_bak_front': 'U/1J0D',  # + Nsteps + 'J3R\r', # If Nsteps < 0
            'move_end': 'J3R\r\n',
        }

        self.command = command_list  # dictionary to hold all MTP commands

    def getCommand(self, key):
        """ Return the command for a given user-requested key """
        return(self.command[key])

    def getCommands(self):
        """ Return a list of all possible user commands """
        return(self.command.keys())

    def getCommandValues(self):
        """ Return a list of all possible MTP commands """
        list = []
        for value in self.command.values():
            list.append(value)

        return(list)
