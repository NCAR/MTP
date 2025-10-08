###############################################################################
# Routines related to generating TimeSeries plots
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import (
       FigureCanvasQTAgg as FigureCanvas)
from PyQT6.QtWidgets import QComboBox
from EOLpython.Qlogger.messageHandler import QLogger

logger = QLogger("EOLlogger")


class TimeSeries():

    def __init__(self, client):
        """ Create a plot window to hold a timeseries plot.  """

        self.client = client

        # Create a figure instance to hold the plot
        (self.fig, self.ax) = plt.subplots(constrained_layout=True)

        # A canvas widget that displays the figure
        self.canvas = FigureCanvas(self.fig)

        # Configure axis label and limits so looks like what expect even if
        # data not flowing. When data is plotting, this is cleared and
        # re-configured.
        self.configureAxis('select a variable above')

    def configureAxis(self, text):
        self.ax.clear()
        self.ax.set_ylabel(text)

    def getWindow(self):
        """ Return a pointer to the graphics window """
        return self.canvas

    def varSelector(self, varlist):
        """ Add a dropdown to select the variable to plot """
        varSel = QComboBox()
        for item in varlist:
            varSel.addItem(item)

        varSel.activated[str].connect(self.selectPlotVar)
        return varSel

    def selectPlotVar(self, text):
        """
        When the user selects a timeseries variable from the dropdown, clear
        the plot window, initialize the data with values for the selected
        variable, reset the y-axis label to display the selected variable
        """
        self.configureAxis(text)

        # Test and make sure there is data in the flightData array. If empty,
        # prompt user to load some data and return.
        if self.client.reader.getNumRecs() == 0:
            logger.error("No data available. Try loading some raw data")
            return

        # Find the date in the data (YYYYMMDD) and convert to base
        # datetime object
        startdate = self.client.reader.getVarArray('Aline', 'DATE')
        base = []
        for date in startdate:
            base.append(datetime.datetime.strptime(date, "%Y%m%d"))

        # Convert seconds in file to numpy datetime object
        x = self.client.reader.getVarArray('Aline', 'TIME')  # seconds
        dates = []
        for i in range(len(x)):
            dates.append(base[i] + datetime.timedelta(seconds=x[i]))

        # Format the ticks
        minutes = mdates.MinuteLocator(byminute=[0])  # every hour on the hour
        self.ax.xaxis.set_major_locator(minutes)
        minutes_fmt = mdates.DateFormatter('%H:%M')
        self.ax.xaxis.set_major_formatter(minutes_fmt)

        # Read in the values in the E line by index (index 0 is Channel 1,
        # ND on, etc) and plot
        # Eline SHOULD NOT BE HARDCODED - TBD**
        y = self.client.reader.getVarArrayi('Eline', text, 0)  # Ch 1, ND on
        self.plotDataXY(dates, y, 'red')
        y = self.client.reader.getVarArrayi('Eline', text, 1)  # Ch 2, ND on
        self.plotDataXY(dates, y, 'grey')
        y = self.client.reader.getVarArrayi('Eline', text, 2)  # Ch 3, ND on
        self.plotDataXY(dates, y, 'blue')
        y = self.client.reader.getVarArrayi('Eline', text, 3)  # Ch 1, ND off
        self.plotDataXY(dates, y, 'pink')
        y = self.client.reader.getVarArrayi('Eline', text, 4)  # Ch 2, ND off
        self.plotDataXY(dates, y, 'lightgrey')
        y = self.client.reader.getVarArrayi('Eline', text, 5)  # Ch 3, ND off
        self.plotDataXY(dates, y, 'lightblue')

        # rotate labels
        for label in self.ax.get_xmajorticklabels():
            label.set_rotation(40)

        self.canvas.draw()

    def plotDataXY(self, x, y, color):
        """ Get the latest XY data and add it to the xyplot. """
        self.xyplot = self.ax.plot(x, y, color=color)
