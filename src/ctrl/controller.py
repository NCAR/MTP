import sys #argv
from os import makedirs, path  # exists, join, dirname
from time import strftime
from glob import glob
import argparse
import logging
from PyQt5.QtWidgets import QApplication, QErrorMessage
from lib.rootdir import getrootdir
from lib.storeConfig import StoreConfig
from lib.storePacket import StorePacket
from model import modelMTP
from lib.serialQt import SerialInit
from lib.storePacket import StorePacket
from view import controlWindow

def initSaveIWGFile(flightNumber, projectName):
    # Make iwg file path
    IWG1Path = path.dirname(
        'C:\\Users\\lroot\\Desktop\\'+ projectName +'\\data\\')
    if not path.exists:
        makedirs(IWG1Path)
    saveIWGFileName = IWG1Path + '\\' + "IWG_" + strftime("%Y%m%d") +\
        '_' + strftime("%H%M%S")+'.txt'
    # reopen file, no good way to sort via IWG and
    # flight number w/o changing initSaveDataFile
    '''
    for filename in glob.glob(path + '\\*_' + flightNumber + '.mtp'):
        logging.debug("File exists")
        saveDataFileName=filename
    '''

    logging.debug("initIWGDataFile")
    return saveIWGFileName

def initSaveDataFile(flightNumber, projectName):
    # Make data file path
    dataPath = path.dirname('C:\\Users\\lroot\\Desktop\\' + projectName +
                           '\\data\\')
    if not path.exists:
        makedirs(dataPath)
    saveDataFileName = dataPath + strftime("%Y%m%d") + '_' + \
        strftime("%H%M%S") + '_' + flightNumber + '.mtp'
    for filename in glob(dataPath + '\\*_' + flightNumber + '.mtp'):
        logging.debug("File exists")
        saveDataFileName = filename

    # 'b' allows writing the data from a binary format
    with open(saveDataFileName, "ab") as datafile:
        # this will be rewritten each time the program restarts
        datafile.write(str.encode("Instrument on " +
                                  strftime("%X") + " " +
                                  strftime("%m-%d-%y") + '\r\n'))
    logging.debug("initSaveDataFile")
    return saveDataFileName


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
        default=path.join(getrootdir(), 'Config.mtph'))
    parser.add_argument('--gui', type=bool,
            help="True (for gui) or False (for no gui)",
            default = True)

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

    tempData = StorePacket()
    # Currently IWG is updated only during process events
    # select may change this
    ex = controlWindow(app, tempData)
    ex.show()

    # Prompt flight number
    flightNumber = ex.getFlightNumber()
    # project name should be gotten from config file, hardcoded here for now
    projectName = 'TI3GER'

    dataFile = initSaveDataFile(flightNumber, projectName)
    iwgFile = initSaveIWGFile(flightNumber, projectName)
    logging.debug("dataFile: %r", dataFile)
    ex.saveLocationBox.setText('~/Desktop/' + projectName + '/data')
    ex.flightNumberBox.setText(flightNumber)
    ex.projectNameBox.setText(projectName)

    mtp = modelMTP(ex, serialPort, configStore, dataFile,
            iwgFile, tempData, args.gui )
    # Will need data file and config dicts too
    mtp.mainloop(isScanning = True)
    # sys.exit(app.exec_())
    # ex.run()


if __name__ == '__main__':
    main()
