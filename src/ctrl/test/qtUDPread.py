from PyQt5.QtNetwork import QUdpSocket, QHostAddress

udp_read_port = 32107
udp_ip = QHostAddress('127.0.0.1')

sock = QUdpSocket()
err = sock.bind(udp_ip, udp_read_port, QUdpSocket.ReuseAddressHint)
# err is true when binding is correct
if err:
    while(1):
        s, ip, port = sock.readDatagram(10)
        if s is not None:
            print(s)
            print(ip.toString())
            print(port)
else:
    print(err)
