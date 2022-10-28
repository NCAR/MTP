###############################################################################
# Routines related to generating the Profile plot
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import numpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
       FigureCanvasQTAgg as FigureCanvas)
from matplotlib.ticker import (MultipleLocator)


class Profile():

    def __init__(self):
        """
        Create a window to hold the profile plot. The plot
        consists of altitude vs temperature
        """

        self.tbxlimL = 180  # Left x-limit for profile plot
        self.tbxlimR = 300  # Right x-limit for profile plot
        self.maxAltkm = 32  # The maximum altitude to plot

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
        return self.canvas

    def configureAxis(self):
        """ Configure axis labels and limits """

        # set limits and label for left Y axis (km)
        self.ax.set_ylabel('Altitude (km)')
        self.ax.set_ylim(0, self.maxAltkm)
        self.ax.yaxis.set_major_locator(MultipleLocator(2))

        # add right axis with altitude in kft 28km = 91.86kft)
        self.axR.set_ylabel('Altitude (kft)')
        self.axR.set_ylim(0, self.maxAltkm * 3.28084)

    def clear(self):
        """ Clear the plot of data, labels and formatting for both axes """
        self.ax.clear()
        self.axR.clear()

        # Since clear removed the labels and formatting, have to add it back
        self.configureAxis()

    def configure(self):
        """
        Layout the plot axis and range
        """
        # set limits and label for X axis specific to profile
        self.ax.set_xlabel('Temperature (K)')
        self.ax.set_xlim(self.tbxlimL, self.tbxlimR)
        self.ax.xaxis.set_minor_locator(MultipleLocator(5))

        # Add a faint grid behind the plot
        self.ax.tick_params(which='minor', color='grey')
        self.ax.grid(which='both', color='lightgrey', linestyle='dotted')

    def watermark(self, msg):
        # If the retrieval failed, call this fn to add a watermark to the
        # profile plot that states this, so user knows who profile is not
        # being plotted.
        self.ax.text(0.5, 0.5, msg, transform=self.ax.transAxes, fontsize=18,
                     color='gray', alpha=0.5, ha='center', va='center',
                     rotation='40')

    def plotProfile(self, temperature, altitude):
        """
        Plot profile vs temperature in the self.profile plot window
        """
        # Plot the temperature on the left axis
        self.ax.plot(temperature, altitude, marker='o', markersize=2,
                     color='#FFE433')

    def plotTemplate(self, temperature, altitude):
        """
        Plot template profile vs temperature in the plot window
        """
        self.ax.plot(temperature, altitude, color='lightgrey')

    def plotACALT(self, SAAT, ACAltKm):
        """ Plot the aircraft altitude on the left axis """
        self.ax.plot([float(SAAT)-10, float(SAAT)+10],
                     [float(ACAltKm), float(ACAltKm)],
                     color='black')

    def plotTropopause(self, trop):
        """ Plot the tropopause on the left axis """
        # Only plot tropopause if it exists (prevent nan errors)
        if not numpy.isnan(trop['altc']):
            self.ax.hlines(float(trop['altc']), self.tbxlimL, self.tbxlimR,
                           color='lightgrey', linestyle='dashed')

    def plotLapseRate(self, trop, lapseRate):
        """
        Plot a 2K/km adiabatic lapse rate as a diagonal dashed line with a
        fixed slope anchored to the ambient temperature point on the profile
        """
        self.ax.plot([float(trop['tempc']),
                      float(trop['tempc']) + -1 * float(trop['altc'] *
                      lapseRate)],
                     [float(trop['altc']), 0], color='lightgrey',
                     linestyle='dashed')

    def draw(self):
        self.canvas.draw()
