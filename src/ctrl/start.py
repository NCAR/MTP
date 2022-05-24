import os  #path (exists, join, ), makedirs,
import sys #argv
import argparse
import logging
from PyQt5.QtWidgets import QApplication, QErrorMessage
from lib.rootdir import getrootdir
from lib.storeConfig import StoreConfig
from lib.storePacket import StorePacket
from lib.serialQt import SerialInit
from view import controlWindow

def handle_error(error):
    em = QErrorMessage()
    em.showMessage(error)
    em.exec_()


def parse_args():
    """ Instantiate a command line argument parser """

    # Define command line arguments which can be provided by users
    parser = argparse.ArgumentParser(
        description="Script to control and monitor the MTP instrument")
    parser.add_argument('--device', type=str, default='COM6',
        help="Device on which to receive messages from MTP instrument")
    parser.add_argument('--mtph', type=str, help="Path to Config.mtph",
        default=os.path.join(getrootdir(), 'Config.mtph'))

    # Parse the command line arguments
    args = parser.parse_args()

    return(args)


def main():

    # Process command line arguments
    args = parse_args()

    #    signal.signal(signal.SIGINT, ctrl_c)
    # logger = logging.getLogger('__name__')
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
            filename="MTPControl.log", level=logging.INFO)

    logging.warning("warning")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    # Check for Config.mtph/Fatal Error
    # Read it in/ declare config dict

    configStore = StoreConfig(app)
    try:
        configStore.loadConfigMTPH(args)
    except Exception as err:
        handle_error("Config.mtph: " + str(err))
        sys.exit()

    # Check for Config.yaml/Fatal Error(?)
    # try:

    # except Exception as err:
    #    handle_error(str(err))
    #    sys.exit()

    # read it in

    # Eventually have serial port # in config.yaml
    # Serial Port Check/Fatal Error
    try:
        serialPort = SerialInit(app, args.device)
    except Exception as err:
        handle_error("SerialPort: " + str(err))
        sys.exit()

    ex = controlWindow(app)
    ex.show()

    # Prompt flight number
    flightNumber = ex.getFlightNumber()
    # project name should be gotten from config file, hardcoded here for now
    projectName = 'TI3GER'

    dataFile = ex.initSaveDataFile(flightNumber, projectName)
    iwgFile = ex.initSaveIWGFile(flightNumber, projectName)
    logging.debug("dataFile: %r", dataFile)
    ex.saveLocationBox.setText('~/Desktop/' + projectName + '/data')
    ex.flightNumberBox.setText(flightNumber)
    ex.projectNameBox.setText(projectName)
    # Will need data file and config dicts too
    ex.mainloop(app, serialPort, configStore, dataFile, iwgFile)
    # sys.exit(app.exec_())
    # ex.run()


if __name__ == '__main__':
    main()
