###############################################################################
# Routines related to generating the Profile plot
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
       FigureCanvasQTAgg as FigureCanvas)


class Profile():

    def __init__(self):
        """
        Create a window to hold the profile plot. The plot
        consists of altitude vs temperature
        """

        self.tbxlimL = 180  # Left x-limit for profile plot
        self.tbxlimR = 300  # Right x-limit for profile plot

        # Create a figure instance to hold the plot
        (self.fig, self.ax) = plt.subplots(constrained_layout=True)

        # instantiate a right axis that shares the same x-axis
        self.axR = self.ax.twinx()

        # A canvas widget that displays the figure
        self.canvas = FigureCanvas(self.fig)

        # Configure axis label and limits so looks like what expect even if
        # data not flowing. When data is plotting, this is cleared and
        # re-configured. See plotProfile()
        self.configureAxis()

    def getWindow(self):

        # Return pointer to the graphics window
        return(self.canvas)

    def configureAxis(self):
        """ Configure axis labels and limits """

        # set limits and label for left Y axis (km)
        self.ax.set_ylabel('Altitude (km)')
        self.ax.set_ylim(0, 28)

        # add right axis with altitude in kft 28km = 91.86kft)
        self.axR.set_ylabel('Altitude (kft)')
        self.axR.set_ylim(0, 91.86) 

    def plotProfile(self, temperature, altitude):
        """
        Plot profile vs temperature in the self.profile plot window
        """

        # Clear the plot of data, labels and formatting for the left axis
        self.ax.clear()

        # Since clear removed the labels and formatting, have to add it back
        self.configureAxis()

        # set limits and label for X axis specific to counts
        self.ax.set_xlabel('Temperature (K)')
        self.ax.set_xlim(self.tbxlimL, self.tbxlimR)

        # Plot the temperature on the left axis
        self.ax.plot(temperature, altitude, marker='o', markersize=2,
                     color='#FFE433')
        self.canvas.draw()
