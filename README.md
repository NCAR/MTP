```
CAUTION: When running the MTP instrument, if Tsynth under the Engineering tab gets to 50 degreesC, the
probe needs to be shutdown to avoid overheating
```
# MTP

The Microwave Temperature Profiler (MTP) is a HAIS instrument which was developed by JPL for the NSF/NCAR GV.

The [original VB6 code base](https://github.com/NCAR/MTP-VB6) from JPL that supports data processing and display was written in Microsoft Visual Basic 6. Since Microsoft has chosen to depracate Visual Basic, RAF has embarked on a re-write of some components of the original code. This repository contains those rewrites.

The MTPviewer software currently uses the following versions of code:
 * Python 3.7.2
 * Qt5 5.12.2
 * PyQt5 5.12.1
 * pyserial 3.4
 * psycopg2 2.7.7
 * pyqtgraph 0.10.0

## To install on a MAC

 * brew upgrade python (to 3.7.2)
 * unset PYTHONPATH
 * python3 -m pip install PyQt5
 * pip3 install pyserial
 * pip3 install psycopg2
 * Install the EOL-Python packages per instructions in https://github.com/NCAR/EOL-Python
 
## To install on Windows10
 
 * See installation instructions for RAOBget: https://github.com/NCAR/RAOBget
 * Copy bat files from windows10 dir to Desktop
 * Install the EOL-Python packages per instructions in https://github.com/NCAR/EOL-Python
 
## To operate the MTP from Windows10

 * Install the driver for the USOPTL4 USB to serial converter
 * Download the driver from https://support.advantech.com/support/DownloadSRDetail_New.aspx?SR_ID=1-HIPU-30&Doc_Source=Download 

 * Extract the zip file to the desktop
 * Run C:\Documents and Settings\mtp\Desktop\USB_Drivers_PKG_v2-08-28\BBSmartWorx\Windows\dpinst64
 * Plug in the USB cable from the MTP to the laptop
 * Go to the device manager and change the port to comm 6
   * This PC -> right click -> manage -> device manager -> Other Devices or COM & PORT (I think) -> USOPTL4
 * Comfirm port settings as 9600|8|None|1|None

Information on operating the MTP, and other documentation, can be found on the (UCAR SEW MTP wiki)[https://wiki.ucar.edu/display/SEW/MicrowaveTemperatureProfiler]

## To run this code:
 * Copy project ascii_parms file from proj dir to config/
 * cd src
 * On Windows10:
 ```
 * click on MTPviewer icon on the desktop. If this is not available:
     > conda activate (to get the base environment where libraries have been installed)
     > C:\Users\lroot\Miniconda3\python.exe MTPviewer.py

 ```
 * On a MAC:
 ```
 > python3 MTPviewer.py
 ```

## To run in test mode, generate fake "real-time" data by running
 * cd src/emulator
 * On Windows10:
 ```
 * Click on MTPemulator icon on the desktop. If this is not available:
    > conda activate
    > C:\Users\lroot\Miniconda3\python.exe snd_MTP_udp.py
 * Click on IWGemulator icon on the desktop. If this is not available:
    > git clone http://github.com/NCAR/aircraft_nc2iwg1
    > conda activate
    > C:\Users\lroot\Miniconda3\python.exe C:\Users\lroot\aircraft_nc2iwg1\nc2iwg1.py -i DEEPWAVERF01.nc -s 1 -u True -er True

 ```
 * On a MAC:
 ```
> python3 snd_MTP_udp.py
> ./snd_IWG.sh  (need to install http://github.com/NCAR/aircraft_nc2iwg1)
```

## Developer Notes

For complete documentation on each class/method, useful if you need to modify the code, use pydoc to extract embedded documentation from each file:

```
> cd src
> python3 -m pydoc <filename>
e.g. python3 -m pydoc lib/rwget.py
```

To manually run all unittests:

```
> cd src
> python3 -m unittest discover -s ../tests -v
```

If you run into memory issues (unexplainable crashes are a good indicator), use
run_tests.sh under the src dir.
