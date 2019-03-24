import network, socket, time, machine

sockudp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sockudp.settimeout(0.02)
si = network.WLAN(network.STA_IF) 

# Connect to Blackview/S5 (Android) phone
def connectActivePhone(pled):
    si.active(True)
    ssids = [ l[0]  for l in si.scan() ]
    if b'BV6000' in ssids:
        wconn, wpass = b'BV6000', b'beckaaaa'
    elif b'ES_3041' in ssids:
        wconn, wpass = b'ES_3041', b'43900000'
    else:
        return False
    si.connect(wconn, wpass)
    while not si.isconnected():
        time.sleep_ms(100)
        pled.value(1-pled.value())
    return True

# udpaddr = ("192.168.43.1", 9019)  # ip default for android
secondaddr = None
def dwrite(mess, udpaddr):
    try:
        sockudp.sendto(mess, udpaddr)
    except OSError as e:
        print("dwrite", e)

