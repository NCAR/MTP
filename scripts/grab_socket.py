###############################################################################
# QUdpSocket script to grab and hold a socket - for testing sharing of sockets
# Use Ctrl-C to exit
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
from PyQt5.QtNetwork import QUdpSocket, QHostAddress


class grabSocket():

    def __init__(self):
        sock_read = QUdpSocket()
        udp_ip = QHostAddress.LocalHost
        udp_read_port = 7071
        # share the iwg packet port
        sock_read.bind(udp_ip, udp_read_port, QUdpSocket.ReuseAddressHint)
        sock_read.readyRead.connect(self.getIWG)
        print("grabbed")
        while (True):
            next

    def getIWG(self):
        return()


if __name__ == "__main__":
    grabSocket()
