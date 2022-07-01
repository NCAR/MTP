@echo on
call C:\Users\lrootMiniconda3\Scripts\activate.bat
cd ..\src\emulator
C:\Users\lroot\Miniconda3\python.exe C:\Users\lroot\aircraft_nc_utils\nc2iwg1\nc2iwg1 -u True ..\..\Data\NGV\DEEPWAVE\NG\DEEPWAVERF01.nc
pause
