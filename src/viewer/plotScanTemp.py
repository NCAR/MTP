###############################################################################
# Routines related to generating the Scan and Template plot
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import numpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
       FigureCanvasQTAgg as FigureCanvas)


class ScanTemp():

    def __init__(self):
        """
        Create a window to hold the scan and temperature plot. The plot
        consists of two overlaid plots:
        - Left axis: a plot of each channel of the template's Brightness
          Temperature for the elevation nearest to flight level, plotted in
          dimmer red, white, and blue lines. Left axis is elevation.
        - Right axis: plot of counts from each channel of the scan. Right axis
          is counts.
        - X-axis is brightness temperature
        - Overplot GV altitude as horizontal white line.
        """

        # Create a figure instance to hold the plot
        (self.fig, self.ax) = plt.subplots(constrained_layout=True)

        # instantiate a right axis that shares the same x-axis
        self.axR = self.ax.twinx()

        # A canvas widget that displays the figure
        self.canvas = FigureCanvas(self.fig)

        # Configure axis label and limits so looks like what expect even if
        # data not flowing. When data is plotting, this is cleared and
        # re-configured. See plotDataScnt()
        self.configureAxis()

    def getWindow(self):

        # Return pointer to the graphics window
        return self.canvas

    def getAngles(self):
        """ Create an array of the angles corresponding to each SCNT value """
        angles = numpy.array(range(10))+1

        return angles

    def configureAxis(self):
        """ Configure axis labels and limits, inc. invert right axis """

        # set limits and label for left Y axis
        self.ax.set_ylabel('Altitude (km)')
        self.ax.set_ylim(0, 20)

        # set limits and label for right Y axis
        self.axR.set_ylabel('Scan Angle')
        self.axR.yaxis.label.set_color('grey')
        self.axR.spines['right'].set_color('grey')
        self.axR.tick_params(axis='y', colors='grey')
        self.axR.set_ylim(10, 1)  # Inverted Y axis 10 -> 1

    def clear(self):
        """ Clear the plot of data, labels and formatting for both axes """
        self.ax.clear()
        self.axR.clear()

        # Since clear removed the labels and formatting, have to add it back
        self.configureAxis()

    def plotDataScnt(self, scnt_inv):
        """
        Plot scan counts vs channel in the self.scnt plot window

        This is not done in the VB code. I added this during development so
        I would have something to plot before I added the brightness
        temperature calcs.

        It is not called during standard use, but can be accessed via the
        --cnts command line option to vet counts without processing them.
        """
        # set limits and label for X axis specific to counts
        self.ax.set_xlabel('Counts')
        self.ax.set_xlim(16000, 22000)

        # Plot the three channel counts on the right axis
        # channel 1 is red, channel 2 is white, and channel 3 is blue
        # Channel 1 counts are scnt_inv indices 0-9
        # Channel 2 counts are scnt_inv indices 10-19
        # Channel 3 counts are scnt_inv indices 20-29
        self.axR.plot(scnt_inv[0:10], self.getAngles(), color='red')
        self.axR.plot(scnt_inv[10:20], self.getAngles(), color="grey")
        self.axR.plot(scnt_inv[20:30], self.getAngles(), color="blue")

    def plotTB(self, tb):
        """
        Plot brightness temperature vs channel in the self.scnt plot window
        Plot will be autoscaled
        """
        # set limits and label for X axis specific to counts
        self.ax.set_xlabel('Brightness Temperature (K)')

        # Plot the three channel counts on the right axis
        # channel 1 is red, channel 2 is white, and channel 3 is blue
        # Channel 1 counts are scnt_inv indices 0-9
        # Channel 2 counts are scnt_inv indices 10-19
        # Channel 3 counts are scnt_inv indices 20-29
        self.axR.plot(tb[0:10], self.getAngles(), color='red')
        self.axR.plot(tb[10:20], self.getAngles(), color="grey")
        self.axR.plot(tb[20:30], self.getAngles(), color="blue")

    def plotTemplate(self, template):
        """
        Plot brightness temperature vs channel from the template. Plot will be
        autoscaled
        """
        self.axR.plot(template[0:10], self.getAngles(), color='pink')
        self.axR.plot(template[10:20], self.getAngles(), color='lightgrey')
        self.axR.plot(template[20:30], self.getAngles(), color='lightblue')

    def minTemp(self, tb, template):
        """
        Get the minimum temperature from the union of tb and temperature scans.
        Used for auto-scaling plots
        """
        return min(tb + template)

    def maxTemp(self, tb, template):
        """
        Get the maximum temperature from the union of tb and temperature scans.
        Used for auto-scaling plots
        """
        return max(tb + template)

    def plotACALT(self, ACAltKm, xmin, xmax):
        """ Plot aircraft altitude in black. Corresponds to left axis """
        self.ax.hlines(float(ACAltKm), xmin, xmax, color='black')

    def plotHorizScan(self, xmin, xmax):
        self.axR.plot([xmin, xmax], [6, 6], color='grey')

    def draw(self):
        self.canvas.draw()
