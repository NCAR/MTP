@echo on
call C:\Users\lroot\Miniconda3\Scripts\activate.bat
C:\Users\lroot\Miniconda3\python.exe C:\Users\lroot\MTP\scripts\mtpudpd --path C:\Users\lroot\MTP\LAB\RAW --host 192.168.84.255 --port 30101 --ric 32106 --logfile C:\Users\lroot\MTP\LAB\logs\mtp2udp.log
