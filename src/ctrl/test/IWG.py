import socket 
import time 

UDP_IP = "127.0.0.1"
UDP_PORT = 7071
Message = " hi there"

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)



f = open("IWG1_20200211_091106.txt", "r")
f1 = f.readlines()
for i in f1:
    sock.sendto(str.encode(i), (UDP_IP, UDP_PORT))
    time.sleep(1)


