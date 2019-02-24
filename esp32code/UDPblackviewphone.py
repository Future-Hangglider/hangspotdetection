import network, socket, time, machine


udpaddr = ("192.168.43.1", 9019)  # ip default for android
sockudp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockudp.settimeout(0.1)

udpaddrUBX = ("192.168.43.1", 9020)  # ip default for android
sockudpUBX = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockudpUBX.settimeout(0.1)

si = network.WLAN(network.STA_IF) 

# Connect to Blackview (Android) phone
def connectBlackview(pled):
    wconn, wpass = b'BV6000', b'beckaaaa'
    si.active(True)
    bwconnexists = bool(l  for l in si.scan()  if l[0] == wconn)
    si.connect(wconn, wpass)
    while not si.isconnected():
        time.sleep_ms(100)
        pled.value(1-pled.value())

def dwrite(mess):
    try:
        sockudp.sendto(mess, udpaddr)
    except OSError as e:
        print("dwrite", e)

def dwriteUBX(mess):
    try:
        sockudpUBX.sendto(mess, udpaddrUBX)
    except OSError as e:
        print("dwrite", e)
