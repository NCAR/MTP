import logging
import datetime
import serial
import socket
import sys
from serial import Serial

# initial setup of time, logging, serialPort, Udp port
saveTime = datetime.datetime.now(datetime.timezone.utc)
logging.basicConfig(level = logging.WARNING, filename = "MTP_" 
        + str(saveTime.year) + str(saveTime.month) + str(saveTime.day)
        + ".log")
serialPort = serial.Serial('COM6', 9600, timeout = 0.15)
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
udpSocket.connect(('127.0.0.1', 32107)) # ip, port number

def readEchos(num):
    buf = b''
    for i in range(num):
        buf += serialPort.readline()

    logging.debug("read %r", buf)
    return buf

def waitStatusOdd(num):
    # Have to check that integrator starts
    for i in range(num):
        serialPort.write(b'S\r\n')
        buf = readEchos(3)
        if buf.find(b'05') >= 0 or buf.find(b'07') >= 0 or buf.find(b'03') >= 0:
            return 
    logging.debug("Timeout waitStatusOdd")

def waitStatusEven(num):
    # check that integrator finishes
    for i in range(num):
        serialPort.write(b'S\r\n')
        buf = readEchos(3)
        if buf.find(b'04') >= 0 or buf.find(b'06') >= 0 or buf.find(b'02') >=0:
            return 
    logging.debug("Timeout waitStatusEven")


def CIR(channel):
    # Set channel
    channel = channel + '\r\n'
    serialPort.write(channel.encode('ascii'))
    readEchos(2)
    serialPort.write(b'S\r\n')
    readEchos(2)
    serialPort.write(channel.encode('ascii'))
    readEchos(2)
    serialPort.write(b'S\r\n')
    readEchos(2)
    # start/clear integrator
    serialPort.write(b'I 40\r\n')
    readEchos(2)
    # these really should always be 05 and 04
    # for now going with even/odd to help debug why they're not
    # and if that matters
    waitStatusOdd(2)
    waitStatusEven(2)
    # do a read, to clear integrate bit
    serialPort.write(b'R\r\n')
    buf = readEchos(2)
    serialPort.write(b'S\r\n')
    readEchos(2)
    datum = '%06d' % int(buf[9:13].decode('ascii'), 16)
    return datum



def CIRS():
    # status should be either 6 or 4 after this
    # preferably 4, but 6 seems annoyingly common
    data = str( CIR('C28182') ) + ' ' 
    data += str( CIR('C28806') ) + ' '
    data += str( CIR('C29182') ) 
    return data


def moveNotComplete(buf):
    # returns false if '@' is found,
    if buf.find(b'@') >= 0:
        return False 
    return True

def moveTo(location):
    location = location + '\r\n'
    serialPort.write(location.encode('ascii'))
    buf = readEchos(3)
    serialPort.write(b'S\r\n')
    buf += readEchos(3)
    while moveNotComplete(buf):
        serialPort.write(location.encode('ascii'))
        buf = readEchos(3)
        serialPort.write(b'S\r\n')
        buf += readEchos(3)
    # after received '@' terminate stepper motion
    serialPort.write(b'U/1TR\r\n')
    buf = readEchos(3)
    serialPort.write(b'S\r\n')
    buf += readEchos(3)
    

def sanitize(data):
    data = data[data.find(b':') + 1 : len(data) - 3]
    placeholder = data.decode('ascii')
    place = placeholder.split(' ')
    ret = ''
    for datum in place:
        ret += '%06d' % int(datum,16) + ' '

    return ret



CIRS()
# init
serialPort.write(b'U/1f1j256V50000R\r\n')
readEchos(3)
serialPort.write(b'S\r\n')
readEchos(3)
serialPort.write(b'U/1L4000h30m100R\r\n')
readEchos(3)



while (1):
    
    udpLine = ''
    serialPort.write(b'S\r\n')
    readEchos(3)
    # move home
    serialPort.write(b'U/1J0f0j256Z1000000J3R\r\n')
    readEchos(3)
    serialPort.write(b'S\r\n')
    readEchos(3)

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
    serialPort.write(b'N 1\r\n')
    readEchos(3)
    serialPort.write(b'S\r\n')
    readEchos(3)
    eline = CIRS() + ' '
    serialPort.write(b'N 0\r\n')
    readEchos(3)
    serialPort.write(b'S\r\n')
    readEchos(3)
    eline += CIRS()
    udpLine = udpLine + eline
    eline = 'E ' + eline 
    
    #bline 
    moveTo('U/1J0D28226J3R')
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
    




