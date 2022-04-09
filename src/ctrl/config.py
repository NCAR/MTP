###############################################################################
# Class defining a dictionary to hold all the various configurations for s
# the MTP instrument.
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
from math import nan


class MTPconfig():

    def __init__(self):

        config_list = {
            'Program': 'MTPH_control.py',     # vb6 or python3
            'Aircraft': 'NGV',                #Has never flown on another, but when it does check this  
            'NominalPitch': "3",        
            'OffsetYi': -1.600, 
            'OffsetPi': -3.576, 
            'OffsetRi': -0.123, 
            'Frequencies': [3,56.363,57.612,58.363],    
                                      
            'Integ. Time': '200.0',           #mS  

            'El. Angles': 
            [
                10,     	#10 sky views + target = 11
                -179.8, 	# location of fiduciary 2008/03/17
                80.00,	# first sky view 20080317
                55.00,
                42.00,
                25.00,
                12.00,
                0.00,	# Horizon
                -12.00,
                -25.00,
                -42.00,
                -80.00	#last skyview 
             ],
                                  
            'Project': 'METHANE_AIR',    
                                

            # From VB6 sub Noise() - called by Eline(). Noise diode.
            'Flight': '00', 
            'Date': 'Today\r', 
            'MAM':[[nan,nan,nan][nan,nan,nan][nan,nan,nan]],      # MTP Attitude Matrix
        }

        self.configs = config_list  # dictionary to hold all initial configs

    def getConfig(self, key):
        """ Return the config for a given user-requested key """
        return(self.configs[key])

    def getAllConfigs(self):
        """ Return a list of all configurations """
        return(self.configs.keys())

    def setConfig(self, key, value):
        """ Sets the new value for the key """
        self.configs[key]=value

    def setMAM(self, key1, key2, value):
        """ Sets the new value for key pair """
        MAM = self.getConfig('MAM')
        MAM[key1][key2]=value
        self.setConfigs('MAM',MAM)

    def getFromMAM(self, key1, key2):
        MAM = self.getConfig('MAM')
        return self.configs[MAM[key1][key2]]
    
    def configMAM(self):
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

        yi = self.getConfig(OffsetYi)
        pi = self.getConfig(OffsetPi)
        ri = self.getConfig(OffsetRi)
        rpd = 0.0174532925199433    # Radians per degree = arctan(1)/45


        cY = cos(yi * rpd)
        cP = cos(pi * rpd)
        cR = cos(ri * rpd)
        sy = sin(yi * rpd)
        sP = sin(pi * rpd)
        sR = sin(ri * rpd)
        
        self.setMAM(1, 1, cP * cY)
        self.setMAM(1, 2, -cP * sY)
        self.setMAM(1, 3, sP)
        self.setMAM(2, 1, sR * sP * cY + cR * sY)
        self.setMAM(2, 2, -sR * sP * sY + cR * cY)
        self.setMAM(2, 3, -sR * cP)
        self.setMAM(3, 1, -cR * sP * cY + sR * sY)
        self.setMAM(3, 2, cR * sP * sY + sR * cY)
        self.setMAM(3, 3, cR * cP)
        return

    def fSc(self):
        """ Given the commanded elevation angle (Ec) this routine should return the desired
' elevation angle (Elevation) with respect to the horizon.
' It is a check that the correct Ec value was calculated by fEc
'
' MJ Mahoney, January 10, 2002
' Enter with MTP Attitude Matrix MAM, aircraft Pitch and Roll in degrees, and
' commanded elevation angle wrt to horizon.
'
' Return with desired elevation angle

' rpd = Atn(1) / 45#      'Radians per degree

' Convert angle from degrees to radians
  """
        P = Pd * rpd
        R = Rd * rpd
        E = Ec * rpd

        cP = cos(P)
        sP = sin(P)
        cR = cos(R)
        sR = sin(R)

        alpha = -cR * sP * self.setMAM(1, 1) + sR * self.setMAM(2, 1) + cR * cP * self.setMAM(3, 1)
        beta = -1 * (-cR * sP * self.setMAM(1, 3) + sR * self.setMAM(2, 3) + cR * cP * self.setMAM(3, 3))
        fSe = -ASN(alpha * cos(E) + beta * sin(E)) / rpd

    def fEc(self):
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
        
        # Then fEc = 180#: Return
        if Elevation is 180: 
            return 180

        # rpd = Atn(1) / 45#       'Radians per degree 3.14159265358979

        P = Pd * rpd
        R = Rd * rpd
        E = Elevation * rpd

        cP = cos(P)
        sP = sin(P)
        cR = cos(R)
        sR = sin(R)
        sE = sin(E)
        alpha = -cR * sP * self.getMAM(1, 1) + sR * self.getMAM(2, 1) + cR * cP * self.getMAM(3, 1)
        beta = -1 * (-cR * sP * self.getMAM(1, 3) + sR * self.getMAM(2, 3) + cR * cP * self.getMAM(3, 3))

        A = alpha ^ 2 + beta ^ 2
        B = 2 * sE * beta
        C = sE ^ 2 - alpha ^ 2
        Arg = B ^ 2 - 4 * A * C

        if alpha is 0:
            if beta > 0: 
                Ec_at_Emax = 90
            else:
                Ec_at_Emax = -90
        else:
            Ec_at_Emax = Atn(beta / alpha) / rpd

        E_max = -ASN(alpha * cos(Ec_at_Emax * rpd) + beta * sin(Ec_at_Emax * rpd))
        Emax = E_max / rpd #Always + since it is maximum elevation angle
          #Debug.Print alpha; beta; Ec_at_Emax; alpha * cos(Ec_at_Emax) + beta * sin(Ec_at_Emax)
        Ep90 = abs(-ASN(beta) / rpd)
        Em90 = -Ep90
        E_Ec_0 = -ASN(alpha) / rpd  #Elevation at which Ec=0

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
                fEc1 = ASN((-B - sqrt(Arg)) / (2 * A)) / rpd
                fEc2 = ASN((-B + sqrt(Arg)) / (2 * A)) / rpd
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
    
            return fEc

    def ASN(self, x):
        # Take arcsine of a number
        # Valid only for +- 90 degrees

        # note that both math and numpy libs have an arcsin()
        # and an arctan() incedentally. Going with current 
        # functions for reproducability
        
     if abs(x) > 0.99999:
         ASN = x * 3.14159 / 2 
     else:
         ASN = arctan(x / sqrt(1 - x ^ 2))
     return ASN

