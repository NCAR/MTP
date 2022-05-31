###############################################################################
# Class for all the math done to calculate pointing angle
#
# MJ Mahoney, June 17, 2002
# Note that the values of yaw, pitch and roll given below were based
# on field measurements of insturment yaw A at zero elevation angle and
# pitch-like and roll-like parameters B and T along the MTP Sensor Unit
# edges: The measured angles in degrees were:
#
# ER2:     A=20.0  B=10.3  T=25.0
# DC8:     A=15.0  B=00.0  T=08.3  
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
from math import cos, sin, atan, asin, sqrt, log, pow
import logging
from PyQt5 import QtCore
from lib.mtpcommand import MTPcommand

class pointMTP():
    
    
    def __init__(self, parent, grandparent):
        varDict = {
            'Cycling': False,    
            'lastSky': -1, #readScan sets this to actual 
        }
        self.parent = parent
        self.vars = varDict 
        self.MAM = [['nan','nan','nan', 'nan'],['nan','nan','nan', 'nan'],['nan','nan','nan','nan'],['nan','nan','nan','nan']]
        self.MAM =  self.configMAM(self.MAM)
        self.commandDict = MTPcommand()

    
    def configMAM(self, MAM):
        """ 
         Calculates and stores values in mam from yi,pi,ri 
         Initialized MAM in Cycle
         Note: Inst Tilt is in roll axis 
               Inst Azimuth is in yaw axis
               Inst Pitch is in pitch axis, but is included in correction
        These were converted to the U P and R values below by numerically 
        solving equations given at URL: 
        http://mtp.jpl.nasa.gov/notes/pointing/pointing.html
        Note that as of 6/4/2019 this url is defunc, these 
        equations were coppied over from the vb6 pointing.bas
        (currently on github)
        """
        
        #specific to NSF HAIPER GV
        # This will change if it changes planes


        yi = -1.600 
        pi = -3.576
        ri = -0.123 
        rpd = 0.0174532925199433    # Radians per degree = arctan(1)/45


        cY = cos(yi * rpd)
        cP = cos(pi * rpd)
        cR = cos(ri * rpd)
        sY = sin(yi * rpd)
        sP = sin(pi * rpd)
        sR = sin(ri * rpd)

        MAM[0][0] = cP * cY
        MAM[0][2] = -cP * sY
        MAM[0][2] = sP
        MAM[1][0] = sR * sP * cY + cR * sY
        MAM[1][1] = -sR * sP * sY + cR * cY
        MAM[1][2] = -sR * cP
        MAM[2][0] = -cR * sP * cY + sR * sY
        MAM[2][1] = cR * sP * sY + sR * cY
        MAM[2][2] = cR * cP
        self.MAM = MAM
        return MAM

    def getAngle(self, targetEl, zel):
        # changed from goAngle because editor says that would be overriding something
        # though I can't find what or where that would be
        # logging.debug("moveMTP goAngle/getAngle called, targetEl: %s", targetEl)
        logging.debug("Zel to be added to targetEl: %s", zel)
        if self.parent.packetStore.getData("pitchCorrect"):
            logging.info("Correcting Pitch")
            # targetClkAngle = self.configMam()
        else:
            logging.info("Using instantanious MAM")
            targetClkAngle = zel + targetEl

        stepDeg = self.parent.packetStore.getData("stepsDegree") 
        logging.debug("stepDeg: %s", stepDeg)
        targetClkStep = targetClkAngle * stepDeg
        logging.debug("targetClkStep: %s", targetClkStep)

        currentClkStep = self.parent.packetStore.getData("currentClkStep")
        logging.debug("currentClkStep: %s", currentClkStep)
        #self.parent.packetStore.setData("Nsteps", self.targetClkStep - self.parent.packetStore.getData("currentClkStep"))
        # nsteps check here
        nstep = targetClkStep - currentClkStep
        logging.debug("calculated nstep: %r", nstep)
        if nstep == 0:
            logging.info("nstep is zero loop")
            # suspect this occurs when pitch/roll/z are 0
            # need to have a catch case when above are nan's
            return
        # abs( nsteps)  should never be less than 20
        # move to moveScan/ check logic against that
        # save current step so difference is actual step difference 
        self.parent.packetStore.setData("currentClkStep", currentClkStep + int(nstep))
        logging.debug("currentClkStep + nstep: %s ", currentClkStep + int(nstep))

        # drop everything after the decimal point:
        nstepSplit = str(nstep).split('.')
        nstep = nstepSplit[0]
        #logging.debug(" strip nstp of everything after (and including) the decimal point: %s", self.nstepSplit[0])
        # Split '-' off
        #right justify, pad with zeros if necessary to get to 6 numerical values
        if nstep[0] == '-':
            nstepSplit = str(nstep).split('-')
            nstep = nstepSplit[1].rjust(6,'0')
        else:
            nstepSplit = str(nstep).split('+') 
            # this split shouldn't actually do anything
            # other than add continuity to the nsteps
            nstep = nstepSplit[0].rjust(6,'0')
        ''' Shouldn't need mulitple checks for this?
        # preceeded with a + or -
        #logging.debug("unrounded: %s, rounded nstep value to 0, does this get rid of '.' ?: 6.0f", str(self.nstep)) 
        if self.nstep is 0.0:
            logging.error(" moving 0 steps, nstep calculation turned to 0")
            # suspect this occurs when pitch/roll/z are 0
            # need to have a catch case when above are nan's
        '''
        

        # This could be functionized, keeping all the commands in the move. 
        # would have to figure out what goAngle returns then and change it.
        backCommand = nstep + self.commandDict.getCommand("move_end")
        if nstepSplit[0] == '-':
            frontCommand = self.commandDict.getCommand("move_fwd_front")
        else:
            frontCommand = self.commandDict.getCommand("move_bak_front")  

        #self.parent.serialPort.sendCommand(str.encode(self.frontCommand + self.backCommand))
        #self.angleI = self.parent.packetStore.getData("angleI") # angle index, zenith at 1

        return frontCommand + backCommand    
    
    def fEc(self, pitch, roll, Elevation, EmaxFlag):
        # Pitch and roll can be either by frame (post) or instantaneous (realtime)
        """ Needed by goAngle in cycle in move.py """
        # Calculate commanded elevation angle needed to be at a specified
        # elevation angle (Elevation) with respect to the horizon
        #
        # MJ Mahoney, November 19, 2002
        # Enter with MTP Attitude Matrix MAM, aircraft Pitch and Roll in degrees, 
        # and desired elevation angle wrt to horizon.
        #
        # Return with commanded elevation angle
        # if Elevation = 180 degrees, the returned value will be the target position
        # In this case the pitch and roll values are irrelevant
        # Excel spreadsheet shows that LHS and RHS are the only 
        # difference in solutions
        

        print("testfECprint")
        # Then fEc = 180#: Return
        if Elevation == 180: 
            return 180
        MAM = self.MAM

        rpd = atan(1) / 45#       'Radians per degree 3.14159265358979

        # convert
        P = pitch * rpd
        R = roll * rpd
        E = Elevation * rpd

        cP = cos(P)
        sP = sin(P)
        cR = cos(R)
        sR = sin(R)
        sE = sin(E)
        alpha = -cR * sP * MAM[0][0] + sR * MAM[1][0] + cR * cP * MAM[2][0]
        beta = -1 * (-cR * sP * MAM[0][2] + sR * MAM[1][2] + cR * cP * MAM[2][2])

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
            Ec_at_Emax = atan(beta / alpha) / rpd

        # VB6 has a less accurate, but presumably faster ASN function for arcsin
        E_max = -asin(alpha * cos(Ec_at_Emax * rpd) + beta * sin(Ec_at_Emax * rpd))
        Emax = E_max / rpd #Always + since it is maximum elevation angle
        #Debug.Print alpha; beta; Ec_at_Emax; alpha * cos(Ec_at_Emax) + beta * sin(Ec_at_Emax)
        Ep90 = abs(-asin(beta) / rpd)
        Em90 = -Ep90
        E_Ec_0 = -asin(alpha) / rpd  #Elevation at which Ec=0

        EmaxFlag = False
        
        # The WB aircraft option has a special case here in the VB6 code
        if abs(Elevation) > abs(Emax): #Go to highest or lowest elevation angle possible
            EmaxFlag = True
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
                # next two lines ambiguously indented in vb6
                fEc1 = asin((-B - sqrt(Arg)) / (2 * A)) / rpd
                fEc2 = asin((-B + sqrt(Arg)) / (2 * A)) / rpd
                if E_Ec_0 < 0:
                    # logical equivalent of Vb6 that follows 
                    if Elevation >= E_Ec_0 and Elevation >= Ep90:
                        fEc = 180 - fEc2
    
                    else:
                        fEc = fEc2
                      
                    ''' VB6 
                   If Elevation < E_Ec_0 Then
                       fEc = fEc2       '180 - fEc1
                   Else
                    Select Case Elevation
                    Case Is >= Ep90
                        fEc = 180 - fEc2
                    Case Is >= -Emax
                        fEc = fEc2
                    Case Else
                        fEc = fEc2
                    End Select
                  End If
                    '''
                  
                else:
                    if Elevation >= E_Ec_0:
                        # Vb6 - man pages suggest the last 4 lines won't be executed
                        '''
                      Select Case Elevation
                      Case Is >= Emax: fEc = fEc1
                      Case Else:  fEc = fEc1
                      End Select
                      
                      Case Is >= Em90: fEc = fEc1
                      Case Is > -Emax: fEc = -180 - fEc1
                      Case Else: fEc = Ec_at_Emax - 180
                      End Select
                        '''
                        #if Elevation >= Emax:
                        fEc = fEc1
                print("in fEc, original value = " + str(Elevation) + " corrected el = " + str(fEc))
                Elevation = fEc

            return Elevation


