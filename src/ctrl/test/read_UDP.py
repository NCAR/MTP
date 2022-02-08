import socket 

UDP_IP = "127.0.0.1"
#UDP_PORT_Not_Ric = 32107
UDP_PORT_Not_Ric = 32106
#UDP_PORT_Not_Ric = 7071

sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT_Not_Ric))
print(sock.proto)
while (1):
    data, addr = sock.recvfrom(1024)
    print(data)
    print(addr)




