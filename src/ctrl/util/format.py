###############################################################################
# MTP probe control. Class contains functions that move the probe
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import datetime
from ctrl.util.pointing import pointMTP
from EOLpython.Qlogger.messageHandler import QLogger as logger


class MTPDataFormat():

    def __init__(self, init, data, commandDict, iwg):
        self.serialPort = init.getSerialPort()
        self.init = init
        self.commandDict = commandDict
        self.data = data
        self.iwg = iwg

        # functions that control pointing adjustments that correct for
        # aircraft attitute and canister mounting on aircraft
        self.pointing = pointMTP()

        # Read elAngles from Config.mtph, for now... - JAA
        self.zel = -179.8
        self.elAngles = [80, 55, 42, 25, 12, 0, -12, -25, -42, -80]

    def createRawRecord(self, move):
        """ Create a complete Raw record """
        # Determine how long it takes to create a raw record
        firstTime = datetime.datetime.now(datetime.timezone.utc)

        # Clear the list of IWG records so can collect records during the
        # current scan
        self.iwg.clearIWG()

        # Get the Bline data
        move.moveHome()
        raw = self.readBline(move) + '\n'  # Read B data from probe

        # UTC timestamp of Raw record is right after B line is collected
        self.nowTime = datetime.datetime.now(datetime.timezone.utc)

        # Generate timestamp for Raw data record
        RAWformattedTime = "%04d%02d%02d %02d:%02d:%02d " % (
                           self.nowTime.year, self.nowTime.month,
                           self.nowTime.day, self.nowTime.hour,
                           self.nowTime.minute, self.nowTime.second)

        # Get the scan and encoder counts
        position = move.readScan(0)
        if position != "-99999":
            ScanCount = 1000000 - int(position)
        else:
            ScanCount = 1000000  # Emulate value reported by VB6

        position = move.readEnc()
        if position != "-99999":
            EncoderCount = (1000000 - int(position)) * 16
        else:
            EncoderCount = 16000000  # Emulate value reported by VB6

        # Get all the housekeeping data
        move.moveHome()
        raw = raw + self.readM1line() + '\n'  # Read M1 data from the probe
        raw = raw + self.readM2line() + '\n'  # Read M2 data from the probe
        raw = raw + self.readPTline() + '\n'  # Read PT data from the probe
        raw = raw + self.readEline() + '\n'  # Read E data from the probe

        # Average the IWG over the scan and reset the dictionary in prep for
        # next scan averaging
        if self.iwg.averageIWG():
            # Generate A line
            self.aline = self.readAline()

            # Save average, including time, so that if IWG drops out we can use
            # previous values for up to 10 minutes.
            self.iwg.saveAvg(self.nowTime, self.aline)

        else:
            # No new IWG data, so use previous average for up to 10 minutes,
            # else report missing.
            lastTime = self.iwg.getLastAvgTime()
            if lastTime != "" \
               and self.nowTime-lastTime < datetime.timedelta(minutes=10):
                self.aline = self.iwg.getAvgAline()
            else:
                self.aline = self.readAline()  # Create missing A line

        # Get the IWG line
        # This will be the most recent instantaneous IWG line receive from the
        # GV and so might be a second more recent than the lines used in the
        # scan average above
        IWG = self.iwg.getIWG()
        if IWG == "":  # Have not received any IWG data at all yet.
            IWG = 'IWG1,99999999T999999'

        # Format ScanCount and EncoderCount and add to end of aline
        self.aline = self.aline + "%+07d %+07d " % (ScanCount, EncoderCount)

        # Put it all together to create the RAW record
        rawRecord = 'A ' + RAWformattedTime + self.aline + '\n' + IWG + \
                    '\n' + raw

        logger.printmsg("info", "Raw record creation took " +
                        str(self.nowTime-firstTime))

        return(rawRecord)

    def createUDPpacket(self):
        """ Create the UDP packet to send to nidas and RIC """
        udpLine = ''
        udpLine = self.getBdata() + ' ' + udpLine
        udpLine = udpLine + self.getM1data()
        udpLine = udpLine + self.getM2data()
        udpLine = udpLine + self.getPTdata()
        udpLine = udpLine + self.getEdata()

        # Generate timestamp used in UDP packet
        UDPformattedTime = "%04d%02d%02dT%02d%02d%02d " % (
                           self.nowTime.year, self.nowTime.month,
                           self.nowTime.day, self.nowTime.hour,
                           self.nowTime.minute, self.nowTime.second)

        # Put it all together to create the UDP packet
        udpLine = "MTP " + UDPformattedTime + self.aline + udpLine
        udpLine = udpLine.replace(' ', ',')
        logger.printmsg("info", "UDP packet: " + udpLine)

        return(udpLine)

    def readAline(self):
        """
        Create Aline from the average over IWG packets received during the scan
        interval
        """
        aline = "%+06.2f " % float(self.iwg.getSAPitch())  # SAPITCH
        aline = aline + "%05.2f " % float(self.iwg.getSRPitch())  # SRPITCH
        aline = aline + "%+06.2f " % float(self.iwg.getSARoll())  # SAROLL
        aline = aline + "%05.2f " % float(self.iwg.getSRRoll())   # SRROLL
        aline = aline + "%+06.2f " % float(self.iwg.getSAPalt())  # SAPALT
        aline = aline + "%04.2f " % float(self.iwg.getSRPalt())   # SRPALT
        aline = aline + "%+06.2f " % float(self.iwg.getSAAtx())   # SAAT
        aline = aline + "%05.2f " % float(self.iwg.getSRAtx())    # SRAT
        aline = aline + "%+07.3f " % float(self.iwg.getSALat())   # SALAT
        aline = aline + "%+06.3f " % float(self.iwg.getSRLat())   # SRLAT
        aline = aline + "%+07.3f " % float(self.iwg.getSALon())   # SALON
        aline = aline + "%+06.3f " % float(self.iwg.getSRLon())   # SRLON

        return(aline)

    def setNoise(self, cmd):
        self.serialPort.write(cmd)
        self.init.readEchos(2, cmd)

    def readBline(self, move):
        """
        Read data at 10 positions for B line.

        Returns a complete B line,
        eg "B 019110 020510 019944 019133 020540 019973 019101 020507 ...
        """

        # Determine how long it takes to create the B line
        firstTime = datetime.datetime.now()

        self.b = ''
        currentClkStep = 0

        # Confirm in home position and ready to move (not integrating or
        # already moving)
        if not move.isMovePossibleFromHome():
            # VB6 doesn't do this check so still does scan here. We will add
            # something to the log and go ahead and scan.
            logger.printmsg("error", "B line created anyway")

        # GV angles are b'U/1J0D28226J3R', b'U/1J0D7110J3R', b'U/1J0D3698J3R',
        #               b'U/1J0D4835J3R', b'U/1J0D3698J3R', b'U/1J0D3413J3R',
        #               b'U/1J0D3414J3R', b'U/1J0D3697J3R', b'U/1J0D4836J3R',
        #               b'U/1J0D10810J3R']:
        for angle in self.elAngles:

            # Correct angle based on aircraft pitch/roll from latest IWG packet
            angle = self.pointing.fEc(self.iwg.getPitch(), self.iwg.getRoll(),
                                      angle)

            moveToCommand, currentClkStep = self.getAngle(angle,
                                                          currentClkStep)

            if (move.moveTo(moveToCommand, self.data)):

                # Collect counts for 3 channels
                self.b += self.data.CIRS() + ' '
            else:
                # Problem with move - command not completed.
                logger.printmsg("warning", "Bline move not returning " +
                                "completion... terminate stepper motion " +
                                "and continue anyway")

                # Collect counts for 3 channels
                self.b += self.data.CIRS() + ' '

        # remove trailing white space
        self.b = self.b.strip()

        data = "B " + str(self.b)

        logger.printmsg("info", "data from B line:" + data)

        nextTime = datetime.datetime.now()
        logger.printmsg("info", "B line creation took " +
                        str(nextTime-firstTime))

        return data

    def getAngle(self, targetEl, currentClkStep):
        """
        Calculate move command needed to point probe at target elevation.

        Input: Target elevation
               current location of probe

        Return: move command
        """
        logger.printmsg("debug", "Zel to be added to targetEl: "
                        + str(self.zel))
        targetEl = targetEl + self.zel

        # 128 step resolution from init.py::moveHome
        stepDeg = 80/20 * (128 * (200/360))
        logger.printmsg("debug", "stepDeg: " + str(stepDeg))

        targetClkStep = targetEl * stepDeg
        logger.printmsg("debug", "targetClkStep: " + str(targetClkStep))

        logger.printmsg("debug", "currentClkStep: " + str(currentClkStep))

        # nsteps check here
        nstep = targetClkStep - currentClkStep
        logger.printmsg("debug", "calculated nstep: " + str(nstep))
        # Figure out if need this when implement MAM correction - JAA
        # if nstep == 0:
        #     logger.printmsg("info", "nstep is zero loop")
        #     # suspect this occurs when pitch/roll/z are 0
        #     # need to have a catch case when above are nan's
        #     return

        # save current step so difference is actual step difference
        currentClkStep = currentClkStep + int(nstep)
        logger.printmsg("debug", "currentClkStep + nstep: " +
                        str(currentClkStep))

        # drop everything after the decimal point:
        nstepSplit = str(nstep).split('.')
        nstep = nstepSplit[0]

        if nstep[0] == '-':  # first char of nstep -> negative number
            nstepSplit = str(nstep).split('-')  # Split '-' off
            # right justify, pad with zeros if necessary to get to 6 digits
            nstep = nstepSplit[1].rjust(6, '0')
            frontCommand = 'U/1J0D'  # + Nsteps + 'J3R\r', # If Nsteps < 0
        else:
            # Should never get here
            # frontCommand = 'U/1J0P'  # + Nsteps + 'J3R\r', # If Nsteps >= 0
            logger.printmsg("debug", "positive step found" +
                            "*** SOMETHING IS WRONG *** Need to update code")
            exit(1)

        backCommand = nstep + 'J3R\r\n'

        logger.printmsg("DEBUG", "Command to move to " + str(targetEl) +
                        " is " + frontCommand + backCommand)
        return (frontCommand + backCommand).encode('ascii'), currentClkStep

    def getBdata(self):
        """ Return the B data only (without B at the front) """
        return(self.b)

    def readEline(self):
        """
        Read all data at current position for noise diode on and then off.
        Since this function doesn't check probe pointing, it could be at any
        position, so pointing must be checked before using this fn.

        Returns a complete E line,
        eg "E 020807 022393 022128 019105 020672 020117"
        """
        # Determine how long it takes to create the E line
        firstTime = datetime.datetime.now()

        # Create E line
        self.setNoise(b'N 1\r\n')      # Turn noise diode on
        self.e = self.data.CIRS()           # Collect counts for three channels
        self.e = self.e + " "          # Add space between count sets
        self.setNoise(b'N 0\r\n')      # Turn noise diode off
        self.e = self.e + self.data.CIRS()  # Collect counts for three channels
        data = "E " + str(self.e)

        logger.printmsg("info", "data from E line:" + data)

        nextTime = datetime.datetime.now()
        logger.printmsg("info", "E line creation took " +
                        str(nextTime-firstTime))

        return data

    def getEdata(self):
        """ Return the E data only (without E at the front) """
        return(self.e)

    def readM1line(self):
        """
        Read Engineering Multiplxr (M01) housekeeping data

        Returns a complete M01 line,
        eg M01: 2928 2307 2898 3078 1922 2919 2432 2945
        """
        cmd = self.commandDict.getCommand("read_M1")
        self.serialPort.write(cmd)
        self.m1 = self.init.readEchos(6, cmd)
        self.m1 = self.init.sanitize(self.m1)  # clean up buffer & return data
        data = "M01: " + str(self.m1)

        logger.printmsg("info", "data from M01 line - " + data)

        return(data)

    def getM1data(self):
        """ Return the M01 data only (without M01: at the front) """
        return(self.m1)

    def readM2line(self):
        """
        Read Engineering Multiplxr (M02) housekeeping data

        Returns a complete M02 line,
        eg M02: 2009 1240 1533 1668 1699 1395 4095 1309
        """
        cmd = self.commandDict.getCommand("read_M2")
        self.serialPort.write(cmd)
        self.m2 = self.init.readEchos(6, cmd)
        self.m2 = self.init.sanitize(self.m2)  # clean up buffer & return data
        data = "M02: " + str(self.m2)

        logger.printmsg("info", "data from M02 line - " + data)

        return(data)

    def getM2data(self):
        """ Return the M02 data only (without M02: at the front) """
        return(self.m2)

    def readPTline(self):
        """
        Read Platinum Multiplxr (Pt) housekeeping data

        Returns a complete Pt line,
        eg Pt: 2159 13808 13799 11732 13385 13404 13296 14439
        """
        cmd = self.commandDict.getCommand("read_P")
        self.serialPort.write(cmd)
        self.pt = self.init.readEchos(6, cmd)
        self.pt = self.init.sanitize(self.pt)  # clean up buffer & return data
        data = "Pt: " + str(self.pt)

        logger.printmsg("info", "data from Pt line - " + data)

        return(data)

    def getPTdata(self):
        """ Return the Pt data only (without Pt: at the front) """
        return(self.pt)
