Be sure to call python IWG.py from same directory as the IWG1_XXX.txt file.

probeOnCheck.py
- checks for probe to send version blurb on startup
- also does basic troubleshooting for responsiveness

manualProbeQuery.py
- send individual commands to probe
- useful for debugging combined with lib mtpcommand
  if the other programs get into non-continue states

init.py
- runs just the 2 init commands to initialize the motor
- probe sound change, no movement

initMoveHome.py
- runs the init commands 
- returns the mirror to the home position (mirror moves to point at target)

initMoveHomeStep.py
- in addition to moving home, moves a pre-determined step into the loop
- then moves home again

initMoveHomeLoop.py
- currently not working

genericCommandStats.py
- not written yet
- Can be used to do stats on inits, Channel change, Integrate, Read
- Can't be used with move commands unless previously initialized
- ctrl-c kills movement. Or 'movement' that the probe thinks it's doing, but isn't
