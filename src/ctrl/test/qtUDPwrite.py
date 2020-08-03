from PyQt5.QtNetwork import QUdpSocket, QHostAddress

udp_write_port = 32107
udp_ip = QHostAddress('127.0.0.1')
print(QHostAddress.protocol(udp_ip))

sock = QUdpSocket()
# If just want to send datagrams, you don't need to call bind
while(1):
    sock.writeDatagram(b"hi", udp_ip, udp_write_port)
    #print(udp_ip.toString())
    #print(udp_write_port)
    #print("wrote a hi")
