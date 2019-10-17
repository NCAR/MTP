###############################################################################
# Routines related to generating the Scan and Template plot
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
import numpy
import pyqtgraph as pg


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

        # Create a GraphicsWindow to hold this plot
        self.stp = pg.GraphicsWindow()

        # Create a ViewBox QGraphicsItem to hold the profile plot (left axis)
        self.profile = pg.ViewBox()

        # Add the profile plot to the graphics window scene with a Yrange of
        # 0-20
        self.stp.scene().addItem(self.profile)
        self.profile.setYRange(0, 20, padding=0)

        # STILL NEED TO FIGURE OUT HOW TO SET THE Yaxis LABEL FOR THE PROFILE
        # PLOT.
        # WANT THE VALUE ON THE Xaxis TO BE FROM THE PROFILE PLOT. SINCE THE
        # TWO PLOTS HAVE DIFFERENT Xvalues, NOT SURE HOW TO OVERPLOT. MAYBE
        # DON"T LINK THE X axis BELOW??
        # NEED TO FIGURE OUT HOW TO SET THE Xaxis LABEL

        # Add a scan count PlotItem (right axis) with a Yrange of 10-0
        self.scnt = self.stp.addPlot(title="Scan and Template Plot",
                                     right='Scan Angle')
        self.scnt.setYRange(10, 1, padding=0)

        # Invert the right Y axis so goes from 10 at bottom to 1 at top
        self.scnt.invertY(True)

        # Allow X axis to be rescaled via mouse interaction, but not Y
        self.scnt.setMouseEnabled(True, False)

        # Link the left axis of the scan count plot to the profile QGraphics
        # item.
        self.scnt.getAxis('left').linkToView(self.profile)

        # Link the X axis of both plots
        self.profile.setXLink(self.scnt)

    def getWindow(self):

        # Return pointer to the graphics window
        return(self.stp)

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

        # Clear the plot and invert the Y axis
        self.scnt.clear()
        self.scnt.invertY(True)

        # Plot the three channels: channel1 is red, channel2 is white, and
        # channel 3 is blue
        plot = self.scnt.plot(pen=pg.mkPen('r'))
        plot.setData(self.getSCNT(1), self.getAngles(), connect="finite")

        plot = self.scnt.plot(pen=pg.mkPen('w'))
        plot.setData(self.getSCNT(2), self.getAngles(), connect="finite")

        plot = self.scnt.plot(pen=pg.mkPen('b'))
        plot.setData(self.getSCNT(3), self.getAngles(), connect="finite")
