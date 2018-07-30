
# This is the UDP socket setup in two threads that handles reconnections 
# and a heartbeat signal and hands the datastrings out through udpqueue

import queue, socket, threading

port = 9002

udpqueue = queue.Queue()  # data to be sent out on the socket
udpforgetconfirm = queue.Queue()

udprecstring = ""  # we can use this to set the request types

def udpincomingthread():
    global udprecstring
    while True:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("192.168.0.10", port))   # this is the Rpi itself
        s.settimeout(10)   # timeout for heartbeat
        print("waiting on port:", port)
        try:
            for i in range(100000):
                udprecstring, addr = s.recvfrom(1024)  # heartbeat
                print("udpincoming", udprecstring, addr)
                if i == 0:
                    udpqueue.put_nowait(s) # hand the socket over with first connection
                    udpqueue.put_nowait(addr)
        except socket.timeout:
            pass
        udpqueue.put_nowait("FORGETSOCKET")
        udpforgetconfirm.get()   # hang here until we get the socket back.  
        s.close()

def udpqueuethread():
    s, addr = None, None
    while True:
        X = udpqueue.get()
        if isinstance(X, socket.socket):
            s, addr = X, udpqueue.get()
        elif X is "FORGETSOCKET":
            s, addr = None, None
            udpforgetconfirm.put_nowait("FSCONFIRMED")
        elif s is not None:
            s.sendto(X, addr)

threading.Thread(target=udpincomingthread, daemon=True).start()
threading.Thread(target=udpqueuethread, daemon=True).start()

# This sets up a thread acquire and save frames from the camera
import time, math, numpy, queue
import picamera, picamera.array
 
camera = picamera.PiCamera()
camera.resolution = (640, 480)
camera.framerate = 30
rawCapture = picamera.array.PiRGBArray(camera, size=camera.resolution)
 
# allow the camera to warmup
time.sleep(0.1)

qframes = queue.Queue(2)
qspareframes = queue.Queue()

nframes = 0
def capturecamerathread():
    global nframes
    gcam = camera.capture_continuous(rawCapture, format="rgb", use_video_port=True) # this is a generator!
    while True:
        rawCapture.truncate(0)
        tstamp = time.time()
        nframes += 1
        next(gcam)  # (the above defined generator actually is called here)
        if qspareframes.qsize() != 0:
            blankframe = qspareframes.get()
            if blankframe is None:
                break
            numpy.copyto(blankframe, rawCapture.array)
        else:
            blankframe = rawCapture.array.copy()
        qframes.put((tstamp, blankframe)) 
    print("leaving capturethread")

threading.Thread(target=capturecamerathread, daemon=True).start()



# This is the main loop (which could respond to udprecstring)
import cv2, os
print("check deletetostop file", os.path.exists("/home/pi/deletetostophangspot"))
workingmask = None
n = 0
while True:
    n += 1
    tstamp, img = qframes.get()
    cv2.GaussianBlur(img, (11, 11), 0, dst=img)
    cv2.cvtColor(img, cv2.COLOR_RGB2HSV, dst=img)
    h = 89
    if workingmask is None:
        workingmask = cv2.inRange(img, (h-5, 0, 0), (h+5,255,255))
    else:
        cv2.inRange(img, (h-5, 0, 0), (h+5,255,255), dst=workingmask)
    cv2.erode(workingmask, None, iterations=2, dst=workingmask)
    cnts, hierarchy = cv2.findContours(workingmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1:]
    if cnts:
        cnt = max(cnts, key=lambda X:cv2.contourArea(X))
    else:
        cnt = [ ]
    if len(cnt) >= 5 and cv2.contourArea(cnt)>100:
        ellipse = cv2.fitEllipse(cnt)
        ex, ey = int(ellipse[0][0]), int(ellipse[0][1])
    else:
        ex, ey = 999, n%1000
    udpqueue.put(b"E%.04d %0.4d" % (ex, ey))
    qspareframes.put(img)
    if (n%100) == 0:
        print(n, ex, ey)
    time.sleep(0.01)
    
print("quitting hangstracking script")
    
