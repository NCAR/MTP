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

    # Every GUI app must have exactly one instance of QApplication. The
    # QApplication class manages the GUI application's control flow and
    # main settings.
    app = QApplication(sys.argv)

    # Instantiate the GUI
    viewer = MTPviewer(app)
    viewer.show()

    # Run the application until the user closes it.
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
