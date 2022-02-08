import logging
import datetime
import serial
import socket
import sys
from serial import Serial

saveTime = datetime.datetime.now(datetime.timezone.utc)
logging.basicConfig(level = logging.WARNING, filename = "MTP_" 
        + str(saveTime.year) + str(saveTime.month) + str(saveTime.day)
        + ".log")
# initial setup of time, logging, serialPort, Udp port
serialPort = serial.Serial('COM6', 9600, timeout = 0.15)
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
udpSocket.connect(('127.0.0.1', 32107)) # ip, port number

def readEchos(num):
    buf = b''
    for i in range(num):
        buf = buf + serialPort.readline()

    logging.debug("read %r", buf)
    return buf


def sanitize(data):
    data = data[data.find(b':') + 1 : len(data) - 3]
    placeholder = data.decode('ascii')
    place = placeholder.split(' ')
    ret = ''
    for datum in place:
        ret += '%06d' % int(datum,16) + ' '

    return ret

def getStatus():
    # status = 0-6, C, B, or @
    # otherwise error = -1
    # check for T in ST:0X
    # return status
    serialPort.write(b'S\r\n')
    answerFromProbe = readEchos(4)
    return findChar(answerFromProbe, b'T')

def findChar(array, binaryCharacter):
    # status = 0-6, C, B, or @
    # otherwise error = -1
    index = array.find(binaryCharacter)
    if index>-1:
        logging.debug("status: %r", array[index])
        return array[index]
    else:
        logging.error("status unknown, unable to find %r: %r",  binaryCharacter, array)
        return -1

def findAt(buf):
    ## returns true if '@' is found,
    ## needs a timeout if command not sent properly
    ##if buf.find(b'@') >= 0:
    #    return True 
    return False


def init():
    # errorStatus = 0 if all's good
    # -1 if echos don't match exact return string expected
    # -2 if unexpected status
    # 

    errorStatus = 0
    # Init1
    #serialPort.write(b'U/1f1j256V50000R\r\n')
    # returns:
    # U/1f1j256V50000R\r\n
    # U:U/1f1j256V50000R\r\n
    # Step:\xff/0@\r\n
    # if already set to this
    # last line replaced by 
    # Step:/0B\r\n
    # if too eary in boot phase (?)
    # Have seen this near boot:
    #  b'\x1b[A\x1b[BU/1f1j256V50000R\r\n'
    # And this after several cycles
    #  Step:/0C\r\n
    #

    readEchos(3)
    # check for errors/decide if resend?

    serialPort.write(b'S\r\n')
    readEchos(3)
    # Init2
    serialPort.write(b'U/1L4000h30m100R\r\n')
    # normal return:
    #
    # U/1f1j256V50000R\r\n
    # U:U/1f1j256V50000R\r\n
    # b'Step:\xff/0@\r\n'

    # error returns:
    # \x1b[A\x1b[BU/1f1j256V50000R
    # Step:\xff/0B\r\n'
    # 
    readEchos(3)


    # This is an init command
    # but it moves the motor faster, so not desired
    # in initial startup/go home ?
    # do a check for over voltage
    serialPort.write(b'U/1j128z1000000P10R\r\n')

    readEchos(3)

    # After both is status of 7 ok?
    # no
    # 4 is preferred status
    # if after both inits status = 5
    # do an integrate, then a read to clear


    return errorStatus 


def moveHome():
    errorStatus = 0
    # acutal initiate movement home
    serialPort.write(b'U/1J0f0j256Z1000000J3R\r\n')
    readEchos(3)
    # if spamming a re-init, this shouldn't be needed
    # or should be in the init phase anyway
    #serialPort.write(b'U/1j128z1000000P10R\r\n')
    #readEchos(3)

    # S needs to be 4 here
    # otherwise call again
    # unless S is 5
    # then need to clear the integrator
    # with a I (and wait 40 ms)
    return errorStatus


def moveTo(location):
    serialPort.write(location)
    readEchos(3)




# if on first move status 6 for longer than expected 
# aka command sent properly, but actual movement 
# not initiated, need a Ctrl-c then re-init, re-home

# on boot probe sends 
# MTPH_Control.c-101103>101208
# needs to be caught first before other init commands are sent
# also response to V
while (1):
    readEchos(3)
    init()
    readEchos(3)
    moveHome()
    s = getStatus()
    if s == 4:
        logging.debug("getStatus is 4")
        #continue on with moving
    elif s == 5 :
        # do an integrate/read
        logging.debug("Home, status = 5")
    else:
        logging.error("Home, status = %r", s)

    moveTo(b'U/1J0D28226J3R')
    s = getStatus()
    logging.debug("First angle, status = %r", s)




# overall error conditions
# 1) no command gets any response
# - gets one echo, but not second echo 
# - because command collision in init commands
# Probe needs power cycle
# 2) stuck at Status 5 wih init/home
# - unable to find commands to recover
# Probe needs power cycle



while (1):
    
    udpLine = ''
    serialPort.write(b'S\r\n')
    readEchos(3)
    # move home, home1
    serialPort.write(b'U/1J0f0j256Z1000000J3R\r\n')
    print('home')
    readEchos(3)
    serialPort.write(b'S\r\n')
    readEchos(3)
    print('echo2')

    # optional m 0, m 1, pt query
    serialPort.write(b'M 1\r\n') 
    m1 = readEchos(5)
    m1 = sanitize(m1)
    udpLine = udpLine + m1
    m1 = 'M01: ' + m1

    serialPort.write(b'M 2\r\n') 
    m2 = readEchos(5)
    m2 = sanitize(m2)
    udpLine = udpLine + m2
    m2 = 'M02: ' + m2

    serialPort.write(b'P\r\n') 
    pt = readEchos(5)
    pt = sanitize(pt)
    udpLine = udpLine + pt
    pt = 'Pt: ' + pt 

    # eline
    eline = 'E '
    serialPort.write(b'N 1\r\n')
    readEchos(3)
    serialPort.write(b'S\r\n')
    readEchos(3)
    eline = eline + CIRS() + ' '
    serialPort.write(b'N 0\r\n')
    readEchos(3)
    serialPort.write(b'S\r\n')
    readEchos(3)
    eline = eline + CIRS()
    udpLine = udpLine + eline
    
    #bline 
    moveTo('U/1J0D28226J3R')
    print("Move1")
    bline = CIRS() + ' '
    moveTo('U/1J0D7110J3R')
    bline += CIRS() + ' '
    moveTo('U/1J0D3698J3R')
    bline += CIRS() + ' '
    moveTo('U/1J0D4835J3R')
    bline += CIRS() + ' '
    moveTo('U/1J0D3698J3R')
    bline += CIRS() + ' '
    moveTo('U/1J0D3413J3R')
    bline += CIRS() + ' '
    moveTo('U/1J0D3414J3R')
    bline += CIRS() + ' '
    moveTo('U/1J0D3697J3R')
    bline += CIRS() + ' '
    moveTo('U/1J0D4836J3R')
    bline += CIRS() + ' '
    moveTo('U/1J0D10810J3R')
    bline += CIRS()
    udpLine = bline + ' ' + udpLine
    bline = 'B ' + bline 

    nowTime = datetime.datetime.now(datetime.timezone.utc)
    print('total loop time: ', nowTime - saveTime)
    formattedTime = str(nowTime.year) + str(nowTime.month) + str(nowTime.day) + ' ' + str(nowTime.hour) + ':' + str(nowTime.minute) + ':' + str(nowTime.second) + ' '
    saveTime = nowTime
    aline = '0 0 0 0 0 0 0 0 0 0 0 0 +567307 +787184 '
    IWG = 'IWG1,20101002T194729,39.1324,-103.978,4566.43,,14127.9,,180.827,190.364,293.383,0.571414,-8.02806,318.85,318.672,-0.181879,-0.417805,-0.432257,-0.0980951,2.36793,-1.66016,-35.8046,16.3486,592.062,146.734,837.903,9.55575,324.104,1.22603,45.2423,,-22    .1676, '

    with open("MTP_data.txt", "a") as datafile:
        # may need to .append instead of +
        datafile.write('A ' + formattedTime + aline + '\n')
        datafile.write(IWG + '\n')
        datafile.write(bline + '\n')
        datafile.write(m1 + '\n')
        datafile.write(m2 + '\n')
        datafile.write(pt + '\n')
        datafile.write(eline + '\n')
        # this \n doesn't leave the ^M's
        datafile.write('\n')

    # to use udp lib move this program up a directory temporarily
    formattedTime = str(nowTime.year) + str(nowTime.month) + str(nowTime.day) + 'T' + str(nowTime.hour) + str(nowTime.minute) + str(nowTime.second) + ' '
    udpLine =  "MTP " + formattedTime + aline + udpLine 
    udpLine = udpLine.replace(' ', ',')
    print(udpLine)
    # print( "MTP, " + aline + IWG + udpLine)
    udpSocket.send(udpLine.encode('utf-8')) 





    #serialPort.write()
    #readEchos(3)
    #serialPort.write(b'S\r\n')
    #readEchos(3)
    




