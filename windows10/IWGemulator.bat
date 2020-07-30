@echo on
call C:\Users\janine\AppData\Local\Continuum\miniconda3\Scripts\activate.bat
cd ..\MTP\src\emulator
C:\Users\janine\AppData\Local\Continuum\miniconda3\python.exe C:\Users\janine\aircraft_nc2iwg1\nc2iwg1.py -i DEEPWAVERF01.nc -s 1 -u True -er True
pause
