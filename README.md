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
 * pyyaml 5.3.1
 * metpy
 * netCDF4

## To install on a MAC

 * brew upgrade python (to 3.7.2)
 * unset PYTHONPATH
 * python3 -m pip install PyQt5
 * pip3 install pyserial
 * pip3 install psycopg2
 * Install the EOL-Python packages per instructions in https://github.com/NCAR/EOL-Python
 * pip3 install netCDF4
 
## To install on Windows10
 
Use miniconda to install all needed packages:
 * https://docs.conda.io/en/latest/miniconda.html
   * download win 64 bit installer for python3.7 and install
 * (Optional) Add Miniconda3 and Miniconda3\condabin to your path
   * Windows search -> type "env" -> click "Edit the system environment variables"
   * In lower "System variables" window, click the "Path" row and click edit
   * Click "New" and add the new paths, e.g.
     * C:\Users\lroot\Miniconda3
     * C:\Users\lroot\Miniconda3\condabin
 * Activate a conda environment (I used the default base environment) - see - https://conda.io/activation
```
   > conda activate
```
 * Update conda if warned following instructions
 * Install packages
```
   > conda install -c conda-forge metpy
     - Drags in pyqt5 and cartopy. If it doesn't, install pyqt directly...
   > conda install -c conda-forge pyqt
   > conda install -c conda-forge pyyaml
   > conda install netcdf4
```
If the packages are not available via the conda-forge channel, you can search for alternative channels at https://anaconda.org

Change you environment variable and add a PYTHONPATH that points to the netCDF installation (You will also add the path to EOL-Python to this env var below.)

Then install Git (if not already there) and download MTP:
 * https://git-scm.com/ -> Download latest per automatic OS detection. Run .exe file to install. I used default settings as suggested by installer, except that I asked to install a desktop icon for “Git Bash”
 * Launch “Git Bash”
 * At the prompt
```
    git clone http://github.com/NCAR/MTP
```
 * Copy bat files from windows10 dir to Desktop
 * Install the EOL-Python packages per instructions in https://github.com/NCAR/EOL-Python

Check your PYTHONPATH
```
    > echo %PYTHONPATH%
```
It should contain a path to EOL-Python and a path to the anaconda site-packages.

## To operate the MTP from Windows10

You only need to do this if you will be connecting your computer directly to the MTP instrument in the lab or on the aircraft. If you are only running MTPviewer to monitor collected data, you don't need to install the driver.

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
 * In order to parse the IWG packet on the aircraft, copy project ascii_parms file from proj dir to config/
 * Create/update config/<project>.yml
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
** NOTE that on a MAC you will use python3, but on Windows it's python.exe (no 3) **

## To run in test mode, generate fake "real-time" data by running

 * On Windows10:
 ```
 * Click on MTPemulator icon on the desktop. If this is not available:
    > conda activate
    > cd C:\Users\lroot\MTP\src\emulator
    > C:\Users\lroot\Miniconda3\python.exe snd_MTP_udp.py

 * Click on IWGemulator icon on the desktop. If this is not available:
    > git clone http://github.com/NCAR/aircraft_nc2iwg1
    > conda activate
    > cd C:\Users\lroot\MTP\Data\NGV\DEEPWAVE\NG
    > C:\Users\lroot\Miniconda3\python.exe C:\Users\lroot\aircraft_nc2iwg1\nc2iwg1.py -s 1 -u True -er True DEEPWAVERF01.nc

 ```
 * On a MAC:
 ```
> cd MTP/src/emulator
> python3 snd_MTP_udp.py
> ./snd_IWG.sh  (need to install http://github.com/NCAR/aircraft_nc2iwg1)
```
* Then run the GUI in real-time mode, using the platform-specific python call, e.g. on Windows:
```
>python MTPviewer.py
```

## Developer Notes

### Documentation

For complete documentation on each class/method, useful if you need to modify the code, use pydoc to extract embedded documentation from each file:

* On a MAC: (Change python3 to python for Windows)
```
> cd src
> python3 -m pydoc <filename>
e.g. python3 -m pydoc lib/rwget.py
```

### Unit tests

If the unittests are all run sequentially from the same command (python3 -m unittest discover -s ../tests -v), earlier tests seem to leave the unittest code in a state that causes subsequent tests to fail. An attempt was made to get each test to clean up after itself by adding setUp and tearDown functions. But Python's unittest holds on to all sorts of memory until the entire test suite has been run. For a good explanation see: https://stackoverflow.com/questions/26915115/unittest-teardown-del-all-attributes/35001389

To get around this, a shell script has been written that breaks up the test suite into smaller chunks. To manually run all unittests, use this script:

* On a MAC: (Change python3 to python for Windows) 
```
> cd src
> ./run_tests.sh
```

* On a WINDOWS10:
```
> powershell -noexit "& ""C:\...\MTP\tests\run_tests_Windows.ps1"""
```