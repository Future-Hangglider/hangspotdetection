
import struct
def skipto_b562(fin):
    b0 = ord(fin.read(1))
    for i in range(10000):
        b1 = ord(fin.read(1))
        if b0 == 0xb5 and b1 == 0x62:
            return i
        b0 = b1
    return -1

def checkchecksumUBX(header, payload, cca, ccb):
    ca, cb = 0, 0
    for c in header:
        ca = (ca + c) & 0xFF
        cb = (cb + ca) & 0xFF
    for c in payload:
        ca = (ca + c) & 0xFF
        cb = (cb + ca) & 0xFF
    return ca == cca and cb == ccb

def testubxcoherence(fubx):
    fin = open(fubx, "rb")
    try:
        for i in range(10000):
            gapbytes = skipto_b562(fin)
            header = fin.read(4)
            clsID, msgID, payloadlength = struct.unpack("<BBH", header)
            payload = fin.read(payloadlength)
            cca = ord(fin.read(1))
            ccb = ord(fin.read(1))
            checksumgood = checkchecksumUBX(header, payload, cca, ccb)
            if not checksumgood or gapbytes != 0:
                print(i, gapbytes, hex(clsID), hex(msgID), len(payload), checksumgood)
    except Exception as e:
        print(e)
    print("records", i, "byteposition", fin.tell())


    
import os, pandas, shutil, math, subprocess

# clone from https://github.com/tomojitakasu/RTKLIB
# git checkout origin/rtklib_2.4.3
# cd app; make


# clone from https://github.com/rtklibexplorer/RTKLIB; cd app; make
convbinexe = "/home/julian/extrepositories/RTKLIB-rtkexplorer/app/convbin/gcc/convbin"
rnx2rtkpexe = "/home/julian/extrepositories/RTKLIB-rtkexplorer/app/rnx2rtkp/gcc/rnx2rtkp"

def convbinfile(fubx):
    fobs = os.path.splitext(fubx)[0]+".obs"
    fnav = os.path.splitext(fubx)[0]+".nav"
    shutil.rmtree(fobs, ignore_errors=True)    
    shutil.rmtree(fnav, ignore_errors=True) 
    subprocess.check_output([convbinexe, "-od", "-os", "-oi", "-ot", "-v", "3.03", fubx])

def calcpossingle(fubx):
    fobs = os.path.splitext(fubx)[0]+".obs"
    fnav = os.path.splitext(fubx)[0]+".nav"
    fpos = os.path.splitext(fubx)[0]+".pos"
    shutil.rmtree(fpos, ignore_errors=True)    
    subprocess.check_output([rnx2rtkpexe, "-o", fpos, "-p", "0", fobs, fnav]) 
    return loadposfile(fpos)

def loadposfile(fpos):
    for percentrows, row in enumerate(open(fpos)):
        if row[0] != "%":
            break
    if percentrows != 0:
        return pandas.read_csv(fpos, skiprows=percentrows-1, sep="\s+")
    else:
        columnnames = "%  GPST                  latitude(deg) longitude(deg)  height(m)   Q  ns   sdn(m)   sde(m)   sdu(m)  sdne(m)  sdeu(m)  sdun(m) age(s)  ratio".split()
        return pandas.read_csv(fpos, header=None, names=columnnames, sep="\s+")

def calcavgposition(fubx):
    w = calcpossingle(fubx)
    return w["latitude(deg)"].mean(), w["longitude(deg)"].mean(), w["height(m)"].mean()

lng0, lat0 = None, None
GPS_UTC_SECONDS_DIFFERENCE = -18
def updatexytime(w):
    global lng0, lat0
    w["time"] = pandas.to_datetime(w["GPST"]) + pandas.Timedelta(seconds=GPS_UTC_SECONDS_DIFFERENCE)
    w.set_index("time", inplace=True)
    
    earthrad = 6378137
    nyfac = 2*math.pi*earthrad/360
    if lng0 is None:
        lng0, lat0 = w[["longitude(deg)", "latitude(deg)"]].iloc[0]
    exfac = nyfac*math.cos(math.radians(lat0))
    w["x"] = (w["longitude(deg)"] - lng0)*exfac  
    w["y"] = (w["latitude(deg)"] - lat0)*nyfac
    w["z"] = w["height(m)"]

def calcposrtk(fubxBase, llhBase, fubxRover):
    fobsBase = os.path.splitext(fubxBase)[0]+".obs"
    fnavBase = os.path.splitext(fubxBase)[0]+".nav"
    fconfBase = os.path.splitext(fubxBase)[0]+".conf"
    fobsRover = os.path.splitext(fubxRover)[0]+".obs"
    fposRover = os.path.splitext(fubxRover)[0]+".pos"
    shutil.rmtree(fposRover, ignore_errors=True)    

    # see https://rtklibexplorer.wordpress.com/2018/11/27/updated-guide-to-the-rtklib-configuration-file/
    with open(fconfBase, "w") as fc:
        fc.write("pos1-posmode=kinematic\n")
        fc.write("pos1-soltype=combined\n")
        fc.write("pos1-dynamics=on\n")
        fc.write("pos1-elmask=15\n")
        fc.write("pos2-armode=fix-and-hold\n")
        fc.write("pos2-gloarmode=on\n")
        fc.write("ant2-postype=llh\n")
        fc.write("ant2-pos1=%.9f\n"%llhBase[0])
        fc.write("ant2-pos2=%.9f\n"%llhBase[1])
        fc.write("ant2-pos3=%.9f\n"%llhBase[2])
        #fc.write("out-solformat=enu\n")  # will give positions relative to the base in metres


    rcmd = [rnx2rtkpexe, "-k", fconfBase, "-o", fposRover, fobsRover, fobsBase, fnavBase]
    print(" ".join(rcmd))
    subprocess.check_output(rcmd)
    w = loadposfile(fposRover)
    return w

