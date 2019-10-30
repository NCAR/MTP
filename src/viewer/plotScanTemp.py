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

    def getWindow(self):

        # Return pointer to the graphics window
        return(self.canvas)

    def invertSCNT(self, scnt):
        """
        The scan counts are stored in the ads file as cnts[angle,channel],
        i.e. {a1c1,a1c2,a1c3,a2c1,...}. Processing requires, and the final
        data are output as {c1a1,c1a2,c1a3,c1a4,...}. Invert the array here.
        """
        self.scnt_inv = [numpy.nan]*30
        NUM_SCAN_ANGLES = 10
        NUM_CHANNELS = 3
        for j in range(NUM_SCAN_ANGLES):
            for i in range(NUM_CHANNELS):
                self.scnt_inv[i*10+j] = int(scnt[j*3+i])

    def getSCNT(self, channel):
        """ Return the scan counts for a single channel.

        Channel 1 counts are scnt_inv indices 0-9
        Channel 2 counts are scnt_inv indices 10-19
        Channel 3 counts are scnt_inv indices 20-29
        """

        return(self.scnt_inv[(channel-1)*10:channel*10])

    def getAngles(self):
        """ Create an array of the angles corresponding to each SCNT value """
        angles = numpy.array(range(10))+1

        return(angles)

    def plotDataScnt(self):
        """
        Plot scan counts vs channel in the self.scnt plot window
        """

        # Clear the plot of data, labels and formatting for the right axis
        self.axR.clear()

        # Since clear removed the labels and formatting, have to add it back
        # set limits and label for X axis
        self.ax.set_xlabel('Counts')
        self.ax.set_xlim(16000, 21000)

        # set limits and label for left Y axis
        self.ax.set_ylabel('Altitude')
        self.ax.set_ylim(0, 20)

        # set limits and label for right Y axis
        self.axR.set_ylabel('Scan Angle')
        self.axR.set_ylim(10, 1)  # Inverted Y axis 10 -> 1

        # Plot the three channel counts on the right axis
        # channel 1 is red, channel 2 is white, and channel 3 is blue
        self.axR.plot(self.getSCNT(1), self.getAngles(), color='red')
        self.axR.plot(self.getSCNT(2), self.getAngles(), color="grey")
        self.axR.plot(self.getSCNT(3), self.getAngles(), color="blue")
        self.canvas.draw()
