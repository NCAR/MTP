# MTP

The Microwave Temperature Profiler (MTP) is a HAIS instrument which was developed by JPL for the NSF/NCAR GV.

The [original VB6 code base](https://github.com/NCAR/MTP-VB6) from JPL that supports data processing and display was written in Microsoft Visual Basi 6. Since Microsoft has chosen to depracate Visual Basic, RAF has embarked on a re-write of some components of the original code. This repository contains those rewrites.

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
 * pip3 install pyqtgraph
