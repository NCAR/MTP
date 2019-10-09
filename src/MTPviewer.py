###############################################################################
# Top-level program to launch the MTPviewer application.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import sys
from PyQt5.QtWidgets import QApplication
from viewer.MTPviewer import MTPviewer


def main():

    app = QApplication(sys.argv)

    MTPviewer(app)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
