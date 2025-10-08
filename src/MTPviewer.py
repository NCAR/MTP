###############################################################################
# Top-level program to launch the MTPviewer application.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import os
import sys
import datetime
from viewer.MTPviewer import MTPviewer
from PyQt6.QtWidgets import QApplication
from viewer.MTPclient import MTPclient
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


def main():

    # Instantiate an MTP controller
    client = MTPclient()

    # Process command line arguments.
    args = client.parse_args()

    # Configure logging
    stream = sys.stdout
    logger.initStream(stream, args.loglevel, args.logmod)

    # Every GUI app must have exactly one instance of QApplication. The
    # QApplication class manages the GUI application's control flow and
    # main settings.
    app = QApplication(sys.argv)

    # Read in config file and set up MTP controller. Needs app to be
    # instantiated first in case it needs to call a fileselector.
    # This also connects to the MTP and IWG feeds
    client.config(args.config)

    # In addition, send all messages to logfile
    logdir = client.configfile.getPath('logdir')
    nowTime = datetime.datetime.now(datetime.timezone.utc)
    fileDate = nowTime.strftime("N%Y%m%d%H.%M")
    logger.initLogfile(os.path.join(logdir, "viewlog." + fileDate),
                       args.loglevel)

    # Instantiate the GUI
    viewer = MTPviewer(client, app, args)
    viewer.loadJson(client.getMtpRealTimeFilename())
    viewer.show()

    # Run the application until the user closes it
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
