#!/usr/bin/env python2
"""file patcher to get a particular crc

Usage: python crcFilePatcher --file=<file> --newcrc=<newcrc>
"""
from crc import *
from cfv import *
import getopt, sys, datetime, os

def BytesToNumber(s):
    return reduce(lambda x, y:x*256 + ord(y),s,0)

def patchFile(inputfile, newcrc):
    crc32 = Crc32Provider()
    s, l = getfilecrc(inputfile)
    crc32._hash = crc32.xorOut ^ BytesToNumber(s)
    p = crc32.patch(NumberFromHexadecimal(newcrc))
    handle = open(inputfile, "ab")
    handle.write(p)
    handle.close()
    #  
def main(argv):
    try:
        opts, args = getopt.getopt(argv, "", ["file=", "newcrc="])
    except getopt.GetoptError, exc:
        print exc.msg
        print __doc__
        sys.exit(2)
    for opt, arg in opts:
        if opt == "--file":
            inputfile = arg
        elif opt == "--newcrc":
            newcrc = arg
    patchFile(inputfile, newcrc)                      


if __name__ == "__main__":
    main(sys.argv[1:])
