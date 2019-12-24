###############################################################################
# Code to read in the project yaml configuration file
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import os
import re
import numpy
import yaml
from lib.rootdir import getrootdir


class config():

    def __init__(self):
        self.projConfig = {}  # initialize dictionary to hold yamlfile contents

    def read(self, yamlfile):

        # Check if config file exists
        if os.path.exists(yamlfile):
            infile = open(yamlfile)
            self.projConfig = yaml.load(infile, Loader=yaml.BaseLoader)
            infile.close()
            # for key, value in self.projConfig.items():
            #     printmsg(self.log, key + ": " + str(value))

    def getVal(self, key):
        """ Get value for given key in the yaml file """
        if key in self.projConfig.keys():
            return(self.projConfig[key])
        else:
            return(numpy.nan)

    def getInt(self, key):
        """ Read a param from the config file that should be an integer """
        val = self.getVal(key)
        if val.isdigit():
            return(int(val))
        else:
            print(" Error in config file - " + key + " should be an integer")
            exit()

    def getPath(self, key):
        """ Read a param from the config file that should be a path """
        val = self.getVal(key)
        # Split the path into components - OS-independent
        path_components = re.split(r'/W', val)
        # Join correctly for OS we are running on. The splat operator (*)
        # unpacks a list - who knew?
        return(os.path.join(getrootdir(), *path_components))
