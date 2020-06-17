@echo on
call C:\Users\lroot\Miniconda3\Scripts\activate.bat
cd ..\MTP\src\ctrl\
C:\Users\lroot\Miniconda3\python.exe -m cProfile view.py 1>> MTP.log 2>&1
pause
