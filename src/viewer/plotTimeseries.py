###############################################################################
# Routines related to generating Timeseries plots
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import pyqtgraph as pg
from PyQt5.QtWidgets import QGridLayout, QComboBox


class Timeseries():

    def __init__(self, client):
        """
        Create a plot window to hold the timeseries plot of IWG data. Won't use
        this in final GUI - it was practice. Keep in case we ever want it.
        """

        self.client = client

        self.xy = pg.GraphicsWindow()

        # We need a grid layout inside our Graphics window to hold the plot
        # and dropdown.
        self.layout = QGridLayout()
        self.layout.addWidget(self.xy, 0, 0)

        # Create an empty plot
        self.xy = self.xy.addPlot(bottom=self.client.xvar,
                                  left=self.client.yvar)

        # Add a dropdown to select the variable to plot
        varSelector = QComboBox()
        for item in self.client.varlist:
            varSelector.addItem(item)

        varSelector.activated[str].connect(self.selectPlotVar)
        self.layout.addWidget(varSelector, 1, 0)

    def getWindow(self):

        # Return a pointer to the graphics window
        return(self.layout)

    def plotDataXY(self, x, y):
        """
        Get the latest XY data from the client and add it to the xyplot. In
        order to make the plot scroll, delete the previous plot and plot with
        the new shifted data.
        """
        self.xy.clear()
        self.xyplot = self.xy.plot()
        self.xyplot.setData(x, y, connect="finite")

    def selectPlotVar(self, text):
        """
        When the user selects a timeseries variable from the dropdown, clear
        the plot window, initialize the data with values for the selected
        variable, reset the y-axis label to display the selected variable and
        set the yvar in the client to the selected var.
        """
        self.xy.clear()
        self.client.initData()
        self.xy.setLabel('left', text)
        self.client.yvar = text
