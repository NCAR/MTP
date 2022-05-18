# MTP control library functions

These functions work as stand-alone testing functions. They will eventually
be integrated into the main code.

Be sure to call python IWG.py from the same directory as the IWG1_XXX.txt file.

These tests work with the mtp_emulator (in MTP/src/emulator) via the --device command line argument.

To run these testing functions, from MTP/src, run
```
> conda activate mtp
(mtp) > python3 MTPcontrolTest.py
```

Currently updated functions are: init.py, move.py, manualProbeQuery.py

The user menu provides the following functionality:

#### 0 = Status (init, move)
 * return probe status

#### 1 = Init (init, move)
 * confirm probe is on
 * run the 2 init commands to initialize the motor
 * probe sound change, no movement

#### 2 = Move Home (move)
 * return the mirror to the home position (mirror moves to point at target)

#### 3 = Step (move)
 * move a pre-determined step into the loop
 * then move home again

#### 9 = Probe On Check (init)
 * checks for probe to send version blurb on startup
 * also does basic troubleshooting for responsiveness

#### q = Manual Probe Query
 * send individual commands to probe
 * useful for debugging if the other programs get into non-continue states
 * reference lib/mtpcommand.py for common commands.

#### x = Exit
 * Quit this code.


## Not updated yet

initMoveHomeLoop.py
- currently not working

genericCommandStats.py
- not written yet
- Can be used to do stats on inits, Channel change, Integrate, Read
- Can't be used with move commands unless previously initialized
- ctrl-c kills movement. Or 'movement' that the probe thinks it's doing, but isn't

IWGDaisy.py

Qt_manualProbeQuery.py

dehex.py

initMoveHomeStepCIR.py

initMoveHomeStepCIRALLTIME.py

loopProbeQuery.py

qtUDPread.py

qtUDPwrite.py

read_IWG.py

read_UDP.py

spikes.py

statsManualProbeQuery.py
