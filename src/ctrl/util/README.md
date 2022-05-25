# MTP control library functions

These functions are currently used for manual testing via
src/MTPcontrolTest.py.  They work with the mtp_emulator (in MTP/src/emulator)
via the --device command line argument.

They will eventually be integrated into the main code.

To run these testing functions, from MTP/src, run
```
> conda activate mtp
(mtp) > python3 MTPcontrolTest.py
```

The user menu of MTPcontrolTest provides the following functionality:

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

#### 4 = generic CIRS (CIR)
 * read data at current position for three frequencies

#### 5 = create E line (CIR)
 * read data at current position for three frequencies and for noise diode on
   then off

#### 6 = create B line (move, CIR)
 * Move through 10 positions and combine data into a B line

#### 7 = read M1/M2/Pt housekeeping data (CIR)
 * Read all Multiplxr data
 * Done in three separate calls to firmware

#### 8 = create Raw data and UDP packet
 * combines option 5, 6, and 7 and generates a UDP packet and Raw record

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

IWGDaisy.py

Qt_manualProbeQuery.py
- Script that opens port to MTP using PyQt5.QSerialPort

dehex.py

qtUDPread.py

qtUDPwrite.py

read_IWG.py

read_UDP.py

spikes.py
- checks for spikes in B data line
