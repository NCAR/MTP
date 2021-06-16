###############################################################################
# Code to read in the project yaml configuration file
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import os
import pathlib
import yaml
from lib.rootdir import getrootdir
from EOLpython.util.fileselector import FileSelector
from EOLpython.Qlogger.messageHandler import QLogger as logger


class config():

    def __init__(self):
        self.projConfig = {}  # initialize dictionary to hold yamlfile contents

    def read(self, yamlfile):

        self.yamlfile = yamlfile

        # Check if config file exists
        if os.path.exists(yamlfile):
            try:
                self.readConfig(yamlfile)
            except Exception as err:
                logger.printmsg("ERROR", str(err), "Click OK to select" +
                                " correct file.")
                self.selectConfig()

            # If in debug mode, print contents of config file
            for key, value in self.projConfig.items():
                logger.printmsg("DEBUG", key + ": " + str(value))
        else:
            self.selectConfig()

    def selectConfig(self):
        """
        Let user select a config file. Called if config file given on command
        line doesn't exist (or if user used default and that doesn't exist)

        Will loop until correct file is selected or user clicks "Quit" in
        printmsg dialog
        """
        logger.printmsg("ERROR", "config file" + self.yamlfile + " doesn't " +
                        "exist.", "Click OK to select correct file.")

        # Launch a file selector for user to select correct config file
        self.loader = FileSelector()
        self.loader.set_filename("loadConfig", getrootdir())
        self.yamlfile = os.path.join(getrootdir(), self.loader.get_file())

        # Try read again
        self.read(self.yamlfile)

    def readConfig(self, yamlfile):
        try:
            infile = open(yamlfile)
        except Exception:
            raise

        self.projConfig = yaml.load(infile, Loader=yaml.BaseLoader)
        infile.close()

    def getVal(self, key):
        """ Get value for given key in the yaml file """
        if key in self.projConfig.keys():
            return(self.projConfig[key])
        else:
            # Projdir defaults so OK. If no filelist, all RCF files are used
            if key != 'projdir' and key != 'filelist':
                logger.printmsg("ERROR", key + " not defined in configfile " +
                                self.yamlfile)
                raise Exception()

            return(None)

    def getInt(self, key):
        """ Read a param from the config file that should be an integer """
        val = self.getVal(key)
        if val.isdigit():
            return(int(val))
        else:
            logger.printmsg("ERROR", "Error in config file - " + key +
                            " should be an integer. Edit config file " +
                            self.yamlfile + " then" +
                            " click OK to be prompted to reload it")
            self.readConfig(self.yamlfile)
            self.getInt(key)  # Try again. Will loop until user fixes issue.

    def getPath(self, key):
        """ Read a param from the config file that should be a path """
        newpath = self.prependDir(key, self.getProjDir())
        return(newpath)

    def prependDir(self, key, projdir):
        val = self.getVal(key)
        # Split the path into components - OS-independent
        path_components = val.split('/')
        # Join correctly for OS we are running on. The splat operator (*)
        # unpacks a list - who knew?
        if projdir is None:
            # Assume paths are relative to code checkout - for testing
            newpath = os.path.join(getrootdir(), *path_components)
        else:
            # Use project directory given in config file as rootdir for data
            # and config files.
            newpath = os.path.join(projdir, *path_components)

        # Check that new path exists. If not, warn user
        if not os.path.exists(newpath):
            logger.printmsg('ERROR', 'Invalid path given in config file: ' +
                            newpath, "Edit config file " + self.yamlfile +
                            " then click OK to reload it")
            self.readConfig(self.yamlfile)
            self.prependDir(key, projdir)  # Loop until user fixes issue

        return(newpath)

    def getProjDir(self):
        """ Read proj dir, if defined, from config file. """
        pathHere = pathlib.Path(__file__).parent.absolute()
        pathtoMTP = (str(pathHere).split("src\lib"))[0]
        if (self.getVal("projdir") == None):
            return None
        return(str(pathtoMTP) + self.getVal("projdir"))
