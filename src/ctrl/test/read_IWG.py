#import socket 
from PyQt5.QtNetwork import QUdpSocket, QHostAddress
from time import sleep

class sstib():
  def __init__(self):
    self.hostAddress = QHostAddress.LocalHost
    udp_read_port= 7071
  def newsocket(self):
    self.sock = QUdpSocket()
    self.sock.bind(self.hostAddress, 7071, QUdpSocket.ReuseAddressHint)
    self.sock.readyRead.connect(self.thing())
  def thing(self):
    print("In thing")
    line = self.sock.readAll()
    print("line %r", line)
    return line
  def test(self):
      print("test")



temp = sstib()
temp.test()
temp.newsocket()



    

#if sock.readyRead:
#    thing()

'''
def var():
    print("in var")
print (" binding to socket")
sock_read = QUdpSocket(aF_INET, SOCK_DGRAM)

sock_read.bind(udp_ip,udp_read_port,QUdpSocket.ReuseAddressHint)
while(1):
    sock_read.readyRead.connect(var)
'''
'''
print("binding to socket")
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT_IWG))
print(sock.proto)
while (1):
    data, addr = sock.recvfrom(1024)
    print(data)
    print(addr)

'''


