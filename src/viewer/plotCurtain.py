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
from matplotlib.ticker import MultipleLocator
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QWidget


class Curtain(QMainWindow):

    def __init__(self, parent=None):
        """
        Create a window to hold the profile plot. The plot
        consists of altitude vs temperature
        """

        self.maxAltkm = 32  # The maximum altitude to plot

        super(Curtain, self).__init__(parent)
        self.initUI()

        # Create a 2-D array of temperatures
        self.data = []

        # Create a 2-D array of altitudes
        self.alt = []

        # Create a 1-D array of times (to label X-axis)
        self.time = []

        # Create a 1-D array of ACALT
        self.actime = []
        self.acalt = []

        # Create 1-D array of first tropopause (use time from ACALT)
        self.trop = []

        # Create 1-D array of MRI indicator (quality of fit)
        self.mri = []

        # Indicate first time calling plot - flag for special cases
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
        self.ax.set_ylabel('Pressure Altitude (km)')
        self.ax.set_ylim(0.0, self.maxAltkm)
        self.ax.yaxis.set_major_locator(MultipleLocator(5))
        self.ax.set_yticklabels(numpy.arange(-5, self.maxAltkm, 5))

        # add right axis with altitude in kft 28km = 91.86kft)
        self.axR.set_ylabel('Altitude (kft)')
        self.axR.set_ylim(0, self.maxAltkm * 3.28084)

        # Add plot title
        self.ax.set_title('Temperature (K)')

        # Add X-axis
        self.ax.set_xlabel('Universal Time (hr)')

        self.cmap = plt.get_cmap('jet')  # Set the color scale

        # Label X-axis with time, not plot number.
        levels = MaxNLocator(nbins=33).tick_values(200, 300)
        self.norm = BoundaryNorm(levels, ncolors=self.cmap.N, clip=True)

    def clear(self):
        # Clear the plot of data, labels and formatting.
        self.ax.clear()
        self.axR.clear()
        # Add back the labels and formatting
        self.configureAxis()

    def addAlt(self, altitude):
        """ Build 2-D array of altitudes """
        # Convert nans in alt to zero, so when temperature is nan, will plot
        # NaN at zero alt.
        alt = numpy.nan_to_num(altitude).tolist()
        for i in range(len(alt)):
            if self.first:
                self.alt.append([alt[i], alt[i]])
            else:
                self.alt[i].append(alt[i])

    def addTemp(self, temperature):
        """ Build 2-D array of temperatures """
        self.data.append(temperature)

    def addTime(self, time, temperature):
        """ Create a 2-D aray of times """
        # Create 1-D array of profile times (convert seconds to hours)
        if self.first:
            self.time.append((time-17)/3600.0)
        self.time.append(time/3600.0)

        # Now build a 2-D array of self.time arrays
        timearr = []
        timearr.append([self.time] * (len(temperature)+1))

    def addACtime(self, time):
        self.actime.append(time/3600.0)

    def addACalt(self, acalt):
        """ Build array of aircraft altitudes """
        self.acalt.append(float(acalt))

    def addTrop(self, trop):
        self.trop.append(trop['altc'])

    def addMRI(self, mri):
        self.mri.append(mri)

    def plotCurtain(self):
        """
        Plot profile vs temperature in the self.profile plot window
        """

        # Plot the temperature as a color mesh. Time on X-axis. Altitude on
        # Y-axis. Have to invert temperature array to match.
        im = self.ax.pcolormesh(self.time, self.alt,
                                numpy.transpose(self.data), cmap=self.cmap,
                                norm=self.norm, axes=self.ax)

        # Only use the QuadMesh object to create the legend the first time
        if self.first:
            self.fig.colorbar(im, ax=self.ax)  # Add a legend
            self.first = False

    def plotACALT(self):
        """ Plot the aircraft altitude on the left axis """
        self.ax.plot(self.actime, self.acalt, color='black')

    def plotTropopause(self):
        """ Plot the tropopause on the left axis """
        self.ax.plot(self.actime, self.trop, color='white')

    def plotMRI(self):
        """
        Plot the MRI. MRI (data quality metric) ranges from .1-.2ish - plotted
        on pressure altitude scale. MRI is BestWtdRCSet['SumLnProb'])
        """
        self.ax.vlines(self.actime, 0, self.mri, color='black')

#   def markBadScan(self):  # TBD
#       """
#       Mark “bad” scans so we skip plotting them (or maybe just overwrite with
#       a while line after plotting). Bad scans are the vertical white lines in
#       the curtain plot. What criteria to identify a scan as bad? mtpbin
#       editref; CalculateArrayMAfast() in MTPbin.frm looks promising - boxcar
#       averaging on sky counts
#       """

    def draw(self):
        self.canvas.draw()
