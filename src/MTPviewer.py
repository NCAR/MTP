################################################################################
# 
# This MTP client program runs on the user host, receives the MTP data packet
# and creates plots and other displays to allow the user to monitor the status
# and function of the MTP.
# 
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
################################################################################

import socket
import sys
import PyQt5

from PyQt5.QtWidgets import QApplication,QGridLayout,QMdiArea,QWidget,QMainWindow

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('TEST')

def main():

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()

    # Listen for UDP packets
    udp_send_port = 32106 # from viewer to MTP
    udp_read_port = 32107 # from MTP to viewer
    #udp_ip = "127.0.0.1"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", udp_read_port))
    try:
        while True:
            data = sock.recv(1024)
            print(data)
    except KeyboardInterrupt:
        interrupted = True

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
