###############################################################################
# This script uses the readMTP module to read in an MTP .RAW file, combine it
# into an ASCII Packet suitable to sending around the plane, and sends it out
# over UDP. This script is used to generate "fake" real-time data from a raw
# file on disk to be used for testing the realtime MTP GUI.
#
# Written in Python 3 - run using "python3 snd_MTP_udp.py <rawfile>"
#
# COPYRIGHT:   University Corporation for Atmospheric Research, 2019
###############################################################################
# import os
import socket
import sys
import time
from optparse import OptionParser

sys.path.append('../')  # so can run this from inside emulator dir
from util.readmtp import readMTP
# from util.readiwg import IWG
# from util.readascii_parms import AsciiParms
# from lib.rootdir import getrootdir


def main(args):

    # Parse command line options
    parser = OptionParser(
        usage="Graphical interface to run or view the running status of " +
              "the Microwave Temperature Profiler")
    parser.add_option('--rawfile', type="string", default="N2014060606.22",
                      help="Defaults to N2014060606.22 in this dir")
    (options, args) = parser.parse_args(args)

    # Configure UDP ports
    # iwg1_port = 7071       # IWG1 packets from GV
    udp_send_port = 32107  # Communication from MTP
    # udp_read_port = 30106  # Communication to MTP; not used by this emulator
    udp_ip = socket.gethostname()

    # Location of default ascii_parms file
    # ascii_parms_file = os.path.join(getrootdir(), 'config', 'ascii_parms')

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Read in a record from the raw data file. A record consists of 6 lines
    # starting with, in order, A, B, M01, M02, Pt, and E. Output as a single
    # comma separated UDP packet like that expected by nimbus.
    raw_data_file = open(options.rawfile, 'r')

    # Instantiate an instance of an MTP reader
    reader = readMTP()

    # Instantiate an instance of an IWG reader. Have it point to the same
    # MTP dictionary as the MTP reader
    # rawscan = reader.getRawscan()
    # iwg = IWG(rawscan['IWG1line'])
    # Init and open ascii parms file
    # status = True
    # ascii_parms = AsciiParms(ascii_parms_file)
    # Attempt to open ascii_parms file. Exit on failure.
    # if ascii_parms.open() is False:
    #     exit(1)

    # while status:
    #     newVar = ascii_parms.readVar()  # Read var from ascii_parms file
    #     status = iwg.createPacket(newVar)

    # ascii_parms.close()

    haveData = True

    while haveData:

        # Read raw_data_file until get a single complete raw scan
        # Returns False when reaches EOF
        haveData = reader.readRawScan(raw_data_file)

        buffer = reader.getAsciiPacket()
        print(buffer)

        # Send MTP ascii packet out over UDP
        if sock:
            sock.sendto(buffer.encode(), (udp_ip, udp_send_port))

        # buffer = iwg.getIwgPacket()
        # print(buffer)

        # Send IWG ascii packet out over UDP
        # if sock:
        #     sock.sendto(buffer.encode(), (udp_ip, iwg1_port))

        # Wait before retrieve next scan, to emulate MTP 17 second gap between
        # scans. For testing, I am using 1 sec data so I don't have to wait as
        # long.
        time.sleep(17)  # Sleep for 17 second - average time between MTP scans

    raw_data_file.close()


if __name__ == "__main__":
    main(sys.argv)
