import network

from OLED_driver import i2c, fbuff, oledshow, doublepixels, fatntext, oledshowfattext

oledshowfattext(["Connect", "wifi", "hangspot"])

si = network.WLAN(network.STA_IF)
macaddress = "".join("{:02x}".format(x)  for x in si.config("mac"))
si.active(True)
print(macaddress)
oledshowfattext([macaddress[:8], macaddress[8:]])

si.connect("hangspot", "bubblino")
while not si.isconnected():
    pass
ipnumber = si.ifconfig()[0] 
print("Device has ipnumber", ipnumber)
oledshowfattext([ipnumber[:8], ipnumber[8:]])

import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(3)
port = 9002

import time
n = 0
t0 = 0
gx0 = 0
gy0 = 0
while True:
    if (n%10) == 0:
        s.sendto(b"hithere99", ("192.168.0.10", port))
    n += 1
    try:
        j, addr = s.recvfrom(10)
    except OSError:
        continue
    if j[0] == ord('E') and len(j) == 10:
        gx, gy = int(j[1:5]), int(j[6:10])
        dgx = gx-gx0
        gx0 = gx
    else:
        dgx = -1
        fbuff.text(j, 0, 0, 1)
        ne = j.find(b"E")
        if ne >= 0:
            s.recvfrom(10 - (len(j) - ne))
        continue
        
    t1 = time.ticks_ms()
    if (t1 - t0 < 20):
        continue
    dt = t1 - t0
    t0 = t1
    fbuff.fill(0)
    if gx != 999:
        rx, ry = int(gx/640*128), int((1-gy/480)*64)
        fbuff.fill_rect(rx-8, ry-8, 16, 16, 1)
        fbuff.text("dt %d"%dt, 0, 0, 1)
    else:
        fatntext(str(gy), 0, 0)
    oledshow()
