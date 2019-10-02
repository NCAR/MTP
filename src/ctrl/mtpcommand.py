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
        instrument. Assign user-understandable keys for each command.
        Some descriptions taken from firmware/MTPH_Control.C and some from
        MTP-VB6/MTPH_ctrl/MTPH_Control.frm
        """

        command_list = {
            'version': 'V\r',         # Request the MTP Firmware Version
            'status': 'S\r',          # Request the MTP Firmware Status
                                      # - Bit 0 = integrator busy
                                      # - Bit 1 = Stepper moving
                                      # - Bit 2 = Synthesizer out of lock
                                      # - Bit 3 = spare
            'ctrl-C': chr(3),         # Send ascii char "3" = Ctrl-C. Is caught
                                      # in firmware interrupt routine and
                                      # restarts the program.
            'terminate': 'U/1TR\r',   # Terminate the stepper motion
            'read_scan': 'U/1?0R\r',  # Read a scan
            'read_enc': 'U/1?8R\r',   # Read encoder
            'read_P': 'P\r',          # Read all 8 platinum RTD channels
                                      # Return components of P line
            'read_M1': 'M 1\r',       # Read all 8 channels of multiplexer 1
                                      # Return components of M1 line
            'read_M2': 'M 2\r',       # Read all 8 channels of multiplexer 2
                                      # Return components of M2 line

            # The next two commands are in VB6 sub integrate()
            'count': 'I 40\r',        # Count up the chCounts array; integrate
                                      # for 40 * 20mS
            'count2': 'R\r',          # Read results of last integration from
                                      # counter (counts for each channel)

            # A U at the beginning of the command indicates
            # String to Stepper UART, i.e. U/1$$$$$$$ = send string $ to
            # stepper #1 (only one now). See Linn Engineering manual for
            # 23-CE controller for command list.

            # The next command is in VB6 sub Init()
            'init': 'U/1f1j256V5000L5000h30m100R\r',  # initialize
            # The next three are in VB6 sub homeScan()
            'home1': 'U/1J0f0j256Z1000000J3R\r',
            'home2': 'U/1j128z1000000P10R\r',
            'home3': 'U/1j64z1000000P10R\r',
            # The next two are in VB6 sub moveScan(). Move the MTP Nsteps.
            # This won't work because Nsteps is not defined. Just a placeholder
            # 'move1': 'U/1J0P' + Nsteps + 'J3R\r',  # If Nsteps >= 0; forward
            # 'move2': 'U/1J0D' + Nsteps + 'J3R\r',  # If Nsteps < 0; backward
            # Sub initScan()
            'init1': 'U/1f1j256V50000R\r',  # direction,top speed, uSteps/step
            'init2': 'U/1L4000h30m100R\r',  # acceration, holding current,
                                            # motor current
            # VB6 sub Noise() - called by Eline(). Noise diode.
            'noise1': 'N 1\r',  # Set Noise Diode On  ( I may have these )
            'noise0': 'N 0\r',  # Set Noise Diode Off ( backward - TBD   )

            # VB6 sub tune(); set frequency for synthesizer, in MHz - 7 digits,
            # decimal always required.
            # operate with "C" mode ( New SNP-1216 Synthesizers in 'C' mode )
            # This won't work because chan is not defined. Just a placeholder
            # 'tune': 'F ' + chan + '\r',
        }

        self.command = command_list  # dictionary to hold all MTP commands

        def getCommand(self, key):
            """ Return the command for a given user-requested key """
            return(self.command[key])

        def getCommands(self):
            """ Return a list of all possible user commands """
            return(self.command.keys())
