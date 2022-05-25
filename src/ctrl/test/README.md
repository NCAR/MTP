# MTP control library functions

Be sure to call python IWG.py from the same directory as the IWG1_XXX.txt file.


####  Manual Probe Query is called from src/MTPcontrolTest.py
 * send individual commands to probe
 * useful for debugging if the other programs get into non-continue states
 * reference lib/mtpcommand.py for common commands.

#### The following functions are stand-alone.

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
