#!/usr/local/bin/python3

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
    #win = QWidget()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
