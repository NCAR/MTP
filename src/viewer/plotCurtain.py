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
from PyQt6.QtWidgets import QMainWindow, QGridLayout, QWidget


class Curtain(QMainWindow):

    def __init__(self, parent=None):
        """
        Create a window to hold the profile plot. The plot
        consists of altitude vs temperature
        """

        self.maxAltkm = 20  # The maximum altitude to plot, was 32
        self.minCmap = 170  # was 200
        self.maxCmap = 320  # was 300
        self.xWinSize = 750  # was 500
        self.yWinSize = 450  # was 300

        super().__init__(parent)
        self.initUI()
        self.initData()  # instantiate empty data lists

    def initData(self):
        """ Create empty lists to hold plot data """
        self.data = []    # 2-D array of temperatures
        self.alt = []     # 2-D array of altitudes
        self.time = []    # 1-D array of times (to label X-axis)
        self.acalt = []   # 1-D array of ACALT
        self.trop = []    # 1-D array of lowest tropopause (plot vs actime)
        self.mri = []     # 1-D array of MRI indicator (quality of fit)

        # Indicate first time calling plot
        self.first = True

    def initUI(self):
        """ Initialize the curtain plot window """
        # Set window title
        self.setWindowTitle('Curtain Plot for flight')

        # Set popup window size
        self.resize(self.xWinSize, self.yWinSize)

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

    def getWindow(self):

        # Return pointer to the graphics window
        return self.canvas

    def configureAxis(self, realtime):
        """ Configure axis labels and limits """

        # set limits and label for left Y axis (km)
        self.ax.set_ylabel('Pressure Altitude (km)')
        self.ax.set_ylim(0.0, self.maxAltkm)
        self.ax.yaxis.set_major_locator(MultipleLocator(5))

        # add right axis with altitude in kft 28km = 91.86kft)
        self.axR.set_ylabel('Altitude (kft)')
        self.axR.set_ylim(0, self.maxAltkm * 3.28084)

        # Add plot title
        self.ax.set_title('Temperature (K)')

        # Add X-axis
        self.ax.set_xlabel('Universal Time (hr)')

        self.cmap = plt.get_cmap('jet')  # Set the color scale

        # Label X-axis with time, not plot number.
        levels = MaxNLocator(nbins=33).tick_values(self.minCmap, self.maxCmap)
        self.norm = BoundaryNorm(levels, ncolors=self.cmap.N, clip=True)

        # Add watermark for preliminary data if in realtime mode
        if realtime:
            self.ax.text(0.5, 0.5, 'preliminary data',
                         transform=self.ax.transAxes, fontsize=40,
                         color='gray', alpha=0.5, ha='center', va='center',
                         rotation='30')

    def clear(self, realtime):
        # Clear the plot of data, labels and formatting.
        self.ax.clear()
        self.axR.clear()
        # Add back the labels and formatting
        self.configureAxis(realtime)

    def addAltTemp(self, temperature, altitude, ACAlt):
        """ Build 2-D arrays: altitudes and temperatures

        Mask out temperatures when scan is greater than 8km from aircraft
        and when altitude is missing
        """

        # Convert nans in alt to zero, so when temperature is nan, will plot
        # NaN at zero alt.
        alt = numpy.nan_to_num(altitude).tolist()
        for i in range(len(alt)):
            if self.first:
                if (alt[i] == 0.0 or abs(alt[i] - float(ACAlt)) > 8):
                    temperature[i] = numpy.nan
                self.alt.append([alt[i]])  # init array with first value
            else:
                if (alt[i] == 0.0 or abs(alt[i] - float(ACAlt)) > 8):
                    temperature[i] = numpy.nan
                self.alt[i].append(alt[i])  # Append across arrays

        self.data.append(temperature)

        # Stuff to plot values - useful for debugging. When counting
        # across second dimension, select first value in first dim, 0.
        # All lengths are the same, so this is arbitrary.
        # self.alt and self.data should have same dimensions
        # print(len(self.alt))  # altitude array vertical length
        # print(len(self.data[0]))  # temperature array vertical length
        # print(len(self.alt[0]))  # altitude array horizontal length
        # print(len(self.data))  # temperature array horizontal length
        # Now print the current profile
        # for i in range(len(temperature)):
        #     print(self.alt[i][len(self.data)-1])
        # print(temperature)

    def addTime(self, time, temperature):
        """ Create a 2-D aray of times """

        # Catch midnight rollover
        if (len(self.time) > 0):
            if (time/3600.0 < self.time[0]):  # Found midnight rollover
                time = time + 86400

        # Create 1-D array of profile times (convert seconds to hours)
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

        Plot the temperature as a color mesh. Time on X-axis. Altitude on
        Y-axis. Have to invert temperature array to match.

        From help(pcolormesh):
          If ``shading='flat'`` the dimensions of *X* and *Y* should be one
          greater than those of *C*, and the quadrilateral is colored due
          to the value at ``C[i, j]``.  If *X*, *Y* and *C* have equal
          dimensions, a warning will be raised and the last row and column
          of *C* will be ignored.

          If ``shading='nearest'`` or ``'gouraud'``, the dimensions of *X*
          and *Y* should be the same as those of *C* (if not, a ValueError
          will be raised).
            - For ``'nearest'`` the color ``C[i, j]`` is centered on
            ``(X[i, j], Y[i, j])``.
            - For ``'gouraud'``, a smooth interpolation is carried out between
              the quadrilateral corners.

          If *X* and/or *Y* are 1-D arrays or column vectors they will be
          expanded as needed into the appropriate 2-D arrays, making a
          rectangular grid.

        So gourand SHOULD give interpoalted shading, but it does not make much
        of a difference. Using nearest for now.
        """
        im = self.ax.pcolormesh(self.time, self.alt,
                                numpy.transpose(self.data), shading='nearest',
                                cmap=self.cmap,  # color scale
                                norm=self.norm,
                                axes=self.ax)

        # Only use the QuadMesh object to create the legend the first time
        if self.first:
            self.fig.colorbar(im, ax=self.ax)  # Add a legend
            self.first = False

    def plotACALT(self):
        """ Plot the aircraft altitude on the left axis """
        self.ax.plot(self.time, self.acalt, color='black',
                     linestyle='dashed')

    def plotTropopause(self):
        """ Plot the tropopause on the left axis """
        self.ax.plot(self.time, self.trop, color='white',
                     linestyle='', marker='+', markersize=2)

    def plotMRI(self):
        """
        Plot the MRI. MRI (data quality metric) ranges from .1-.2ish - plotted
        on pressure altitude scale. MRI is BestWtdRCSet['SumLnProb'])
        """
        self.ax.plot(self.time, self.mri, color='grey',
                     linestyle='', marker='.', markersize=1)

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
