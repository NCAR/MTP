###############################################################################
# Top-level program to launch the MTPviewer application.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import os
import sys
from PyQt5.QtWidgets import QApplication
from viewer.MTPviewer import MTPviewer
from viewer.MTPclient import MTPclient
from lib.rootdir import getrootdir
from proc.MTPprocessor import MTPprocessor
from EOLpython.Qlogger.messageHandler import QLogger as logger


def main():

    # For testing purposes, data and configuration information for the DEEPWAVE
    # project have been copied to Data/NGV/DEEPWAVE within this code checkout.
    # For transparency, set that hardcoded path here.
    testDataDir = os.path.join(getrootdir(), 'Data', 'NGV', 'DEEPWAVE')

    # Instantiate an MTP controller
    client = MTPclient()

    # Process command line arguments. get_args needs to know where config info
    # resides. Pass in testDataDir as the default. User can also set this on
    # the command line. See the argParse functionality in viewer/MTPclient.py
    args = client.get_args(testDataDir)

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
    if args.realtime:
        processor = None
        client.connect_udp()
    else:
        processor = MTPprocessor(client)
        processor.readSetup(client.configfile.getPath("PRODdir"))

    # Get project dir from config. If dir not set, default to test dir
    projdir = client.configfile.getProjDir()
    if projdir is None:
        projdir = testDataDir

    # Get name of file JSON data (potentially) saved to. The name of the JSON
    # file is aotumatically generated and includes the project and flight
    # number.
    filename = client.reader.getJson(projdir, client.getProj(),
                                     client.getFltno())

    # Instantiate the GUI
    viewer = MTPviewer(client, processor, app, filename, args)
    viewer.show()

    # Run the application until the user closes it.
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
