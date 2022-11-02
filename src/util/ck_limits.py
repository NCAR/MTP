###############################################################################
# Class to hold functions that confirm that MTP data collected / housekeeping
# vals are within defined limits, allowing code to warn user if those limits
# are exceeded. This class is used by both the control and viewer software so
# that the limits only have to be modified in a single location and the
# warnings will be consistent between the two pieces of code.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################


class MTPCkLimit():

    def __init__(self):
        """ Recommended MTP Temperature and Voltage from Josh Carnes """

        # M01 Voltage limits: A good limit for the voltage supplies in M01 is
        # +/-5%. I assume VCC is nominally 5V. I am not sure about "Video V".
        self. deltaV = 0.05  # 5%

        # Accelerometer limits: Acceler could have a limit of +/-0.5 g
        self.deltaAccel = 0.5

        # M02 Temperature limits: All M02 temps should have a lower limit of
        # -40C. A closer look at data sheets might have some components with
        # higher limits, but this is a good general limit. Below -40C, many
        # electronics start going out of specification, and their accuracy may
        # degrade. Outside of datasheet limits, electro-mechanical devices may
        # have trouble moving. An upper limit of 50C could be good for
        # components you don't yet have a value for.
        self.Tlower = -40
        self.Tupper = 50

        # Some vars to determine limits on housekeeping values
        self.accmin = 999.9
        self.accmax = -999.9
        self.voltmin = [999.9] * 8
        self.voltmax = [-999.9] * 8

    def ckTemperature(self, val: float):
        # If temperature is outside limits, return False, else return True
        if val < self.Tlower or val > self.Tupper:
            return False
        else:
            return True

    def ckAccel(self, val):
        # If acceleration varies by more than deltaAccel over entire time
        # code is running, return False, else return True.
        # Note that if code is stopped and restarted, this will reset.

        # Update min and max accel
        if val < self.accmin:
            self.accmin = val
        if val > self.accmax:
            self.accmax = val

        # Check variation
        if self.accmin != 999.9 and self.accmax-self.accmin > self.deltaAccel:
            return False
        else:
            return True

    def ckVolts(self, volts, i):
        # If voltage varies by more than 5% over entire time code is running
        # return False, else return True.
        # Note that if code is stopped and restarted, this will reset.

        # There are 8 Voltages in each scan (M01 line), so keep track of 8
        # separate min- and max- voltages (using index i)
        if volts < self.voltmin[i]:
            self.voltmin[i] = volts
        if volts > self.voltmax[i]:
            self.voltmax[i] = volts

        # Check variation
        mean = (self.voltmin[i] + self.voltmax[i]) / 2
        dev = (self.voltmax[i] - self.voltmin[i])/mean

        if self.voltmin[i] != 999.9 and abs(dev) > self.deltaV:  # 5% variation
            return False  # outside acceptable range
        else:
            return True
