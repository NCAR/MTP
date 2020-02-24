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
from viewer.MTPclient import MTPclient
from Qlogger.messageHandler import QLogger as logger


def main():

    # Instantiate an MTP controller
    client = MTPclient()

    # Process command line arguments
    args = client.get_args()

    # Configure logging
    stream = sys.stdout
    logger.initLogger(stream, args.loglevel, args.logmod)

    # Every GUI app must have exactly one instance of QApplication. The
    # QApplication class manages the GUI application's control flow and
    # main settings.
    app = QApplication(sys.argv)

    # Read in config file and set up MTP controller. Needs app to be
    # instantiated first in case it needs to call a fileselector.
    # This also connects to the MTP and IWG feeds
    client.config(args.config)

    # Get name of file JSON data (potentially) saved to
    filename = client.reader.getJson(client.getProj(), client.getFltno())

    # Instantiate the GUI
    viewer = MTPviewer(client, app, filename)
    viewer.show()

    # Run the application until the user closes it.
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
