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
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

from PyQt5.QtWidgets import QApplication,QGridLayout,QMdiArea,QWidget,QMainWindow

sys.path.append('.')
from readmtp import readMTP

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('TEST')

def main():

    app = QtGui.QApplication(sys.argv)
    win = pg.GraphicsWindow(title="MTP plots") # Creates a window
    p1 = win.addPlot(title="SAPITCH") # Creates empty space for the plot in the win
    saplot = p1.plot()      # Creates an empty plot
    windowWidth = 500
    ptr = -windowWidth

    # Listen for UDP packets
    udp_send_port = 32106 # from viewer to MTP
    udp_read_port = 32107 # from MTP to viewer
    #udp_ip = "127.0.0.1"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", udp_read_port))

    # Instantiate an instance of an MTP reader
    reader = readMTP()
    sapitch = []

    # For each UDP packet received from the MTP, parse it into the reader data
    # dictionary so it can be retrieved by variable name via calls like
    # reader.getData(variableName)
    try:
        while True:
            data = sock.recv(1024).decode()
            #print(data)
            reader.parseAsciiPacket(data)
            #print (reader.getData('SAPITCH'))
            sapitch.append(float(reader.getData('SAPITCH')))
            saplot.setData(sapitch)
            saplot.setPos(ptr,0)
            QtGui.QApplication.processEvents()
    except KeyboardInterrupt:
        interrupted = True


    pg.QtGui.QApplication.exec_()
    sys.exit()


if __name__ == "__main__":
    main()
