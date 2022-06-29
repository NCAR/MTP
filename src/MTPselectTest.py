############################################################################### # Script to demonstrate select between IWG and MTP. Useful for testing
#
# To use, start an MTP and IWG feed and then run this script. In a testing
# environment, in three separate xterms:
# > cd emulator
# > ./snd_IWG.sh
#
# > cd emulator
# > python3 mtp_emulator.py
#
# > python3 MTPselectTest.py --device=...
#
# To use with the MTP instrument, leave off --device and this script will
# default to COM6.
#
# Written in Python 3
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2022
###############################################################################
import sys
import time
import select
import socket
import serial
import argparse


class IWG1():

    def __init__(self):
        self.sockI = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockI.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sockI.bind(("0.0.0.0", 7071))

    def socket(self):
        return(self.sockI)

    def readPacket(self):
        """ Use recvfrom to print out ip and port """
        # return(self.sockI.recv(1024).decode())
        return(self.sockI.recvfrom(1024))


class MTP():

    def __init__(self, device):
        try:
            self.serialPort = serial.Serial(device, 9600, timeout=0.15)
        except serial.SerialException:
            print("Device " + device + " does not exist on this machine." +
                  " Please specify a valid device using the --device command" +
                  " line option. Type '" + sys.argv[0] + " --help' for the " +
                  "help menu")
            exit(1)

    def write(self, cmd):
        time.sleep(.25)
        self.serialPort.write(cmd)

    def read(self):
        # Print True if serialPort is readable
        # Documentation at
        # https://docs.python.org/3/library/io.html#io.IOBase.readline
        print(self.serialPort.readable())

        return(self.serialPort.readline())

    def serial(self):
        return(self.serialPort)


def main():

    # Parse command line args
    parser = argparse.ArgumentParser(
        description="Script to send manual commands to the MTP probe")
    parser.add_argument(
        '--device', type=str, default='COM6',
        help="Device on which to receive messages from MTP instrument")
    args = parser.parse_args()

    iwg1 = IWG1()
    mtp = MTP(args.device)

    while True:

        mtp.write(b'S\r\n')

        # read_ready with 3 second timeout
        ports = [iwg1.socket(), mtp.serial()]
        read_ready, _, _ = select.select(ports, [], [], 3)

        if len(read_ready) == 0:
            print('timed out')

        if mtp.serial() in read_ready:
            # Read in echo and response from status command
            line = b''
            line = line + mtp.read()
            line = line + mtp.read()
            if not line:
                break
            print(str(line))

        if iwg1.socket() in read_ready:
            data, addr = iwg1.readPacket()
            print(addr)  # print IP and port packet received from
            print(data.decode())


if __name__ == "__main__":
    main()
