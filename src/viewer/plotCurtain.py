###############################################################################
# Routines related to generating the Curtain plot
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2020
###############################################################################
import numpy
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
       FigureCanvasQTAgg as FigureCanvas)
from matplotlib.ticker import (MultipleLocator)
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget


class Curtain(QMainWindow):

    def __init__(self, parent=None):
        """
        Create a window to hold the profile plot. The plot
        consists of altitude vs temperature
        """

        self.maxAltkm = 30  # The maximum altitude to plot

        super(Curtain, self).__init__(parent)
        self.initUI()

        # Create a 2-D array of temperatures
        self.data = []

        # Create a 2-D array of altitudes
        self.alt = []

        # Create a 1-D array of times (to label X-axis)
        self.time = []

        # Indicate first time calling plot
        self.first = True

    def initUI(self):
        """ Initialize the curtain plot window """
        # Set window title
        self.setWindowTitle('Curtain Plot for flight')

        # Copy more from initUI in viewer.MTPviewer
        self.resize(500, 300)

        # Define central widget to hold everything
        self.view = QWidget()
        self.setCentralWidget(self.view)

        # Create the layout for the viewer
        self.initView()

    def initView(self):
        self.layout = QGridLayout()
        self.view.setLayout(self.layout)

        # Create a figure instance to hold the plot
        (self.fig, self.ax) = plt.subplots(constrained_layout=True)

        # instantiate a right axis that shares the same x-axis
        self.axR = self.ax.twinx()

        # A canvas widget that displays the figure
        self.canvas = FigureCanvas(self.fig)

        self.layout.addWidget(self.canvas, 0, 0)

        # Configure axis label and limits so looks like what expect even if
        # data not flowing. When data is plotting, this is cleared and
        # re-configured. See plotCurtain()
        self.configureAxis()

    def getWindow(self):

        # Return pointer to the graphics window
        return(self.canvas)

    def configureAxis(self):
        """ Configure axis labels and limits """

        # set limits and label for left Y axis (km)
        self.ax.set_ylabel('Altitude (km)')
        self.ax.set_ylim(0, self.maxAltkm)
        self.ax.yaxis.set_major_locator(MultipleLocator(5))  # Does this work?

        # add right axis with altitude in kft 28km = 91.86kft)
        self.axR.set_ylabel('Altitude (kft)')
        self.axR.set_ylim(0, self.maxAltkm * 3.28084)

        self.ax.set_xlabel('Time (hr)')
        self.ax.xaxis.set_minor_locator(MultipleLocator(2))

        self.cmap = plt.get_cmap('jet')  # Set the color scale

        # Label X-axis with time, not plot number.
        levels = MaxNLocator(nbins=33).tick_values(200, 300)
        self.norm = BoundaryNorm(levels, ncolors=self.cmap.N, clip=True)

    def plotCurtain(self, time, temperature, altitude):
        """
        Plot profile vs temperature in the self.profile plot window

        Requires:
          time - time of scan (in seconds)
          altitude - array of altitudes of scan
          temperature - array of temperatures of scan
        """
        # Clear the plot of data, labels and formatting.
        self.ax.clear()
        self.axR.clear()
        # Add back the labels and formatting
        self.configureAxis()

        # Build 2-D array of altitudes
        # Convert nans in alt to zero, so when temperature is nan, will plot
        # NaN at zero alt.
        alt = numpy.nan_to_num(altitude).tolist()
        for i in range(len(alt)):
            if self.first:
                self.alt.append([alt[i], alt[i]])
            else:
                self.alt[i].append(alt[i])

        # Begin building up 2-D array of temperatures
        self.data.append(temperature)

        # Create 1-D array of profile times (convert seconds to hours)
        if self.first:
            self.time.append((time-17)/3600.0)
        self.time.append(time/3600.0)
        # Now build a 2-D array of self.time arrays
        timearr = []
        timearr.append([self.time] * (len(temperature)+1))

        # Plot the temperature as a color mesh. Time on X-axis. Altitude on
        # Y-axis. Have to invert temperature array to match.
        im = self.ax.pcolormesh(self.time, self.alt, numpy.transpose(self.data),
                                cmap=self.cmap, norm=self.norm)

        # Only use the QuadMesh object to create the legend the first time
        if self.first:
            self.fig.colorbar(im, ax=self.ax)  # Add a legend
            self.ax.set_title('Temperature (K)')
            self.first = False
            #self.ax.set_xlim(self.time[0], self.time[0]+8)

        # Invert label
        # Plot froze up - entire GUI froze up. Fix that.
        # Other requirements:
        # https://docs.google.com/spreadsheets/d/12L2Nhr1QroweEAh1BjZO37TcdNnZffr18AaKtAFtobk/edit#gid=0

#   def plotACALT(self, SAAT, ACAltKm):
#       """ Plot the aircraft altitude on the left axis """
#       self.ax.plot([float(SAAT)-10, float(SAAT)+10],
#                    [float(ACAltKm), float(ACAltKm)],
#                    color='black')

#   def plotTropopause(self, trop):
#       """ Plot the tropopause on the left axis """
#       self.ax.hlines(float(trop['altc']), self.tbxlimL, self.tbxlimR,
#                      color='lightgrey', linestyle='dashed')

#   Plot the MRI. MRI (data quality metric) ranges from 1-2ish - plotted on pressure altitude scale
#   "Eliminate “bad” scans (the white lines in the plot) - What criteria to identify a scan as bad? mtpbin editref"
    def draw(self):
        self.canvas.draw()
