###############################################################################
# Class for all the math done to calculate pointing angle
#
# Adapted from:
# https://github.com/NCAR/MTP-VB6/blob/master/MTPH_ctrl/Pointing.bas
# (private repo)
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
from math import cos, sin, atan, asin, sqrt
from EOLpython.Qlogger.messageHandler import QLogger as logger


class pointMTP():

    def __init__(self):
        self.MAM = [['nan', 'nan', 'nan', 'nan'], ['nan', 'nan', 'nan', 'nan'],
                    ['nan', 'nan', 'nan', 'nan'], ['nan', 'nan', 'nan', 'nan']]

        # Pitch, roll and yaw specific to NSF HAIPER GV
        # This will change if the way the canister is mounted on the GV
        # changes.
        self.yi = -1.600   # Read in from Config.mtph
        self.pi = -3.576
        self.ri = -0.123

        # Radians per degree = arctan(1)/45
        self.rpd = atan(1) / 45

        # Calculate MTP Attitude Matrix
        self.configMAM()

    def getMAM(self):
        return self.MAM

    def configMAM(self):
        """
         Calculates and stores values in mam from yi,pi,ri
         Initialized MAM in Cycle
         Note: Inst Tilt is in roll axis
               Inst Azimuth is in yaw axis
               Inst Pitch is in pitch axis, but is included in correction
        These were converted to the U P and R values below by numerically
        solving equations given at URL:
        https://archive.eol.ucar.edu/raf/instruments/MTP/www/notes/pointing/
             pointing.html

        Calculations developed by MJ Mahoney, June 17, 2002
        """

        cY = cos(self.yi * self.rpd)
        cP = cos(self.pi * self.rpd)
        cR = cos(self.ri * self.rpd)
        sY = sin(self.yi * self.rpd)
        sP = sin(self.pi * self.rpd)
        sR = sin(self.ri * self.rpd)

        self.MAM[0][0] = cP * cY
        self.MAM[0][2] = -cP * sY
        self.MAM[0][2] = sP
        self.MAM[1][0] = sR * sP * cY + cR * sY
        self.MAM[1][1] = -sR * sP * sY + cR * cY
        self.MAM[1][2] = -sR * cP
        self.MAM[2][0] = -cR * sP * cY + sR * sY
        self.MAM[2][1] = cR * sP * sY + sR * cY
        self.MAM[2][2] = cR * cP

    def fEc(self, pitch, roll, Elevation):
        """
        Calculate commanded elevation angle needed to be at a specified
        elevation angle (Elevation) with respect to the horizon

        Calculations developed by MJ Mahoney, November 19, 2002

        Inputs: MTP Attitude Matrix MAM
                aircraft Pitch and Roll in degrees
                desired elevation angle wrt to horizon.

        Returns: commanded elevation angle
        """
        # if Elevation = 180 degrees, the returned value will be the target
        # position. In this case the pitch and roll values are irrelevant
        if Elevation == 180:
            return 180

        # convert
        P = pitch * self.rpd
        R = roll * self.rpd
        E = Elevation * self.rpd

        cP = cos(P)
        sP = sin(P)
        cR = cos(R)
        sR = sin(R)
        sE = sin(E)
        alpha = -cR * sP * self.MAM[0][0] + sR * self.MAM[1][0] + \
            cR * cP * self.MAM[2][0]
        beta = -1 * (-cR * sP * self.MAM[0][2] + sR * self.MAM[1][2] +
                     cR * cP * self.MAM[2][2])

        A = alpha * alpha + beta * beta
        B = 2 * sE * beta
        C = sE * sE - alpha * alpha
        Arg = B * B - 4 * A * C

        if alpha == 0:
            if beta > 0:
                Ec_at_Emax = 90
            else:
                Ec_at_Emax = -90
        else:
            Ec_at_Emax = atan(beta / alpha) / self.rpd

        # VB6 has less accurate, but presumably faster ASN function for arcsin
        E_max = -asin(alpha * cos(Ec_at_Emax * self.rpd) +
                      beta * sin(Ec_at_Emax * self.rpd))

        # Convert radians to degrees (will always be positive since it is a
        # maximum elevation angle)
        Emax = E_max / self.rpd

        Ep90 = abs(-asin(beta) / self.rpd)
        Em90 = -Ep90
        E_Ec_0 = -asin(alpha) / self.rpd  # Elevation at which Ec=0

        if abs(Elevation) > abs(Emax):
            # Go to highest or lowest elevation angle possible
            if E_Ec_0 >= 0:
                if Elevation >= 0:
                    fEc = Ec_at_Emax
                else:
                    fEc = Ec_at_Emax - 180
            else:
                if Elevation >= 0:
                    fEc = 180 + Ec_at_Emax
                else:
                    fEc = Ec_at_Emax
        else:
            if Arg < 0:
                Arg = 0
            fEc1 = asin((-B - sqrt(Arg)) / (2 * A)) / self.rpd
            fEc2 = asin((-B + sqrt(Arg)) / (2 * A)) / self.rpd
            if E_Ec_0 < 0:
                # logical equivalent of Vb6 follows
                if Elevation >= E_Ec_0 and Elevation >= Ep90:
                    fEc = 180 - fEc2
                else:
                    fEc = fEc2
            else:
                if Elevation >= E_Ec_0:
                    fEc = fEc1
                else:
                    if Elevation >= Em90:
                        fEc = fEc1
                    elif Elevation > -Emax:
                        fEc = -180 - fEc1
                    else:
                        fEc = Ec_at_Emax - 180

        logger.printmsg("debug", "in fEc, original value = " +
                        str(Elevation) + " corrected el = " + str(fEc))

        return fEc
