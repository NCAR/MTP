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

        self.tbxlimL = 200  # Left x-limit for TB plot
        self.tbxlimR = 270  # Right x-limit for TB plot

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
        return(self.canvas)

    def getAngles(self):
        """ Create an array of the angles corresponding to each SCNT value """
        angles = numpy.array(range(10))+1

        return(angles)

    def configureAxis(self):
        """ Configure axis labels and limits, inc. invert right axis """

        # set limits and label for left Y axis
        self.ax.set_ylabel('Altitude')
        self.ax.set_ylim(0, 20)

        # set limits and label for right Y axis
        self.axR.set_ylabel('Scan Angle')
        self.axR.set_ylim(10, 1)  # Inverted Y axis 10 -> 1

    def plotDataScnt(self, scnt_inv):
        """
        Plot scan counts vs channel in the self.scnt plot window

        This is not done in the VB code. I added this during development so
        I would have something to plot before I added the brightness
        temperature calcs. Keep it in case it's useful in the future.

        As of Nov 13, 2019, this function is not called.
        """

        # Clear the plot of data, labels and formatting for the right axis
        self.axR.clear()

        # Since clear removed the labels and formatting, have to add it back
        self.configureAxis()

        # set limits and label for X axis specific to counts
        self.ax.set_xlabel('Counts')
        self.ax.set_xlim(16000, 21000)

        # Plot the three channel counts on the right axis
        # channel 1 is red, channel 2 is white, and channel 3 is blue
        # Channel 1 counts are scnt_inv indices 0-9
        # Channel 2 counts are scnt_inv indices 10-19
        # Channel 3 counts are scnt_inv indices 20-29
        self.axR.plot(scnt_inv[0:10], self.getAngles(), color='red')
        self.axR.plot(scnt_inv[10:20], self.getAngles(), color="grey")
        self.axR.plot(scnt_inv[20:30], self.getAngles(), color="blue")
        self.canvas.draw()

    def plotTB(self, tb):
        """
        Plot brightness temperature vs channel in the self.scnt plot window
        """

        # Clear the plot of data, labels and formatting for the right axis
        self.axR.clear()

        # Since clear removed the labels and formatting, have to add it back
        self.configureAxis()

        # set limits and label for X axis specific to counts
        self.ax.set_xlabel('Brightness Temperature')
        self.ax.set_xlim(self.tbxlimL, self.tbxlimR)

        # Plot the three channel counts on the right axis
        # channel 1 is red, channel 2 is white, and channel 3 is blue
        # Channel 1 counts are scnt_inv indices 0-9
        # Channel 2 counts are scnt_inv indices 10-19
        # Channel 3 counts are scnt_inv indices 20-29
        self.axR.plot(tb[0:10], self.getAngles(), color='red')
        self.axR.plot(tb[10:20], self.getAngles(), color="grey")
        self.axR.plot(tb[20:30], self.getAngles(), color="blue")
        self.canvas.draw()

    def plotTemplate(self, template):
        self.axR.plot(template[0:10], self.getAngles(), color='pink')
        self.axR.plot(template[10:20], self.getAngles(), color='lightgrey')
        self.axR.plot(template[20:30], self.getAngles(), color='lightblue')
        self.canvas.draw()

    def plotACALT(self, ACAltKm):
        self.ax.clear()
        self.ax.hlines(float(ACAltKm), self.tbxlimL-10, self.tbxlimR+10,
                       color='black')
