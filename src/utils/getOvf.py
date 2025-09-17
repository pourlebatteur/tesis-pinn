__author__ = 'gru'

import os
import numpy as np
import struct

def getData(filename):
    # https://github.com/deparkes/OOMMFTools/blob/master/OOMMFTools-src/oommfdecode.py
    with open(filename, 'rb') as f:
        headers = {} #I know valuemultiplier isn't always present. This is checked later.
        extraCaptures = {'SimTime':-1, 'Iteration':-1, 'Stage':-1, "MIFSource":""}
        #Parse headers
        a = ""
        while not "Begin: Data" in a:
            a = f.readline().strip()
            #Determine if it's actually something we need as header data
            for key in ["xbase", "ybase", "zbase", "xstepsize", "ystepsize", "zstepsize", "xnodes", "ynodes", "znodes", "valuemultiplier"]:
                if key in a:
                    headers[key] = float(a.split()[2]) #Known position FTW
            #All right, it may also be time data, which we should capture
            if "Total simulation time" in a:
                #Split on the colon to get the time with units; strip spaces and split on the space to separate time and units
                #Finally, pluck out the time, stripping defensively (which should be unnecessary).
                extraCaptures['SimTime'] = float(a.split(":")[-1].strip().split()[0].strip())
            if "Iteration:" in a:
                #Another tricky split...
                extraCaptures['Iteration'] = float(a.split(":")[2].split(",")[0].strip())
            if "Stage:" in a:
                extraCaptures['Stage'] = float(a.split(":")[2].split(",")[0].strip())
            if "MIF source file" in a:
                extraCaptures['MIFSource'] = a.split(":",2)[2].strip()
        
        #Initialize array to be populated
        outArray = np.zeros((int(headers["xnodes"]),
                             int(headers["ynodes"]),
                             int(headers["znodes"]),
                             3))

        #Determine decoding mode and use that to populate the array
        decode = a.split()
        if decode[3] == "Text":
            pass
            #return textDecode(f, outArray, headers, extraCaptures)
        elif (decode[3] == "Binary" or decode[3] == "binary")  and decode[4] == "4":
            #Determine endianness
            endianflag = f.read(4)
            if struct.unpack(">f", endianflag)[0] == 1234567.0:
                dc = struct.Struct(">f")
            elif struct.unpack("<f", endianflag)[0] == 1234567.0:
                dc = struct.Struct("<f")
            else:
                raise Exception("Can't decode 4-byte byte order mark: " + hex(endianflag))
            return _binaryDecode(f, 4, dc, outArray, headers, extraCaptures)
        elif decode[3] == "Binary" and decode[4] == "8":
            #Determine endianness
            endianflag = f.read(8)
            if struct.unpack(">d", endianflag)[0] == 123456789012345.0:
                dc = struct.Struct(">d")
            elif struct.unpack("<d", endianflag)[0] == 123456789012345.0:
                dc = struct.Struct("<d")
            else:
                raise Exception("Can't decode 8-byte byte order mark: " + hex(endianflag))
            return _binaryDecode(f, 8, dc, outArray, headers, extraCaptures)
        else:
            raise Exception("Unknown OOMMF data format:" + decode[3] + " " + decode[4])

def _binaryDecode(filehandle, chunksize, decoder, targetarray, headers, extraCaptures):
    valm = headers.get("valuemultiplier",1)
    for k in range(int(headers["znodes"])):
        for j in range(int(headers["ynodes"])):
            for i in range(int(headers["xnodes"])):
                for coord in range(3): #Slowly populate, coordinate by coordinate
                    targetarray[i,j,k,coord] = decoder.unpack(filehandle.read(chunksize))[0] * valm
    return (targetarray, headers, extraCaptures)


def dirArray(inArray, dir, zSlice=0):
    dict0 = {'x': 0,'y': 1, 'z': 2}
    outArray = []
    for row in inArray:
        t = []
        [t.append(col[zSlice][dict0[dir]]) for col in row]
        outArray.append(t)
    return outArray
