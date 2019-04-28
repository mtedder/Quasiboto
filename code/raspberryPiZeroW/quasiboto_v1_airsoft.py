##Quasiboto firmware using Pimoroni Picon Zero
##Includes code to operate taigen airsoft module and wheel encoders
##By Maurice Tedder
##January 3, 2019
##March 1, 2019 - Removed robot control code and placed it in its own class/module

from bluedot.btcomm import BluetoothServer
from signal import pause

#pi camera inports
import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
import QuasiBoto

## gpio pins used: https://pinout.xyz/
##Picon Zero Motor A = Airsoft motor
#(motor A, positive is forward if red->left & blk->right
#(motor B, positive is forward if blk->left & red->right
##17 = Airsoft limitswith/button (BCM 17 - pin 11 - G17) Connect red wire from Airsoft switch to this pin
#view camera streaming
#http://localhost:8000/index.html

#Ref:
#https://bluedot.readthedocs.io/en/latest/btcommapi.html
#https://gpiozero.readthedocs.io/en/stable/
#https://picamera.readthedocs.io/en/release-1.13/
#https://picamera.readthedocs.io/en/release-1.13/recipes2.html#web-streaming
#https://pinout.xyz/
#https://github.com/sparkfun/Pi_Servo_Hat
#https://projects.raspberrypi.org/en/projects/robotPID/3
#https://www.tutorialspoint.com/python/python_multithreading.htm
#http://4tronix.co.uk/blog/?p=1224 (picon)

#Clone project from GitHub repo and make the following modifications
#Modify the /etc/rc.local file to have this program run on startup in headless mode
#add the following lines to the rc.local file
#sudo python3 /home/pi/Quasiboto/code/raspberryPiZeroW/quasiboto_v1_airsoft.py &
#exit 0

PAGE="""\
<html>
<head>
<title>picamera MJPEG streaming demo</title>
</head>
<body>
<h1>PiCamera MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""
VERSION_NUMBER = "B1.3"
                    
class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def defaultFn(param1, param2):
    #print ("defaultFn:" + param1 + "," + param2)
    #do nothing
    pass

##Parse incoming data command
def parseData(data):
    # Step 1 strip first character
    cmd = data[0]
    data = data[1:]
    sep = data.find(",")
    
    #get first int
    param1 = data[:sep]
    data = data[sep+1:]

    #get second int    
    sep = data.find(",")
    param2 = data[:sep]    
    data = data[sep+1:]#consume previous substring and trailing delimiter

    return cmd, param1, param2, data

##Bluetooth data handler
def data_received(data):
    while (len(data) > 0):       
        cmd, param1, param2, data = parseData(data)        
        result = commands.get(str(cmd), defaultFn)(param1, param2)
        if(result is not None): #transmit data for functions that have a return value
            bt.send(result)
        #print(result)
print('started!!!')        
bot = QuasiBoto.Robot()

commands = {
            'e':bot.e,#servo 0
            'f':bot.f,#servo 1
            'g':bot.g,#servo 2
            'h':bot.h,#digital output 3
            'i':bot.i,#digital output 4
            'j':bot.j,#digital output 5
            'k':bot.k,#Not implemented
            'l':bot.l,#stop all motors emergency stop on all motors
            'm':bot.m,#return analog and digital read on all ports
            'n':bot.n,#return digital read on all ports
            'o':bot.o,#airsoft gun trigger
            'p':bot.p,#return digital input read on all ports
            'n':bot.n,#read analog sensor data
            's':bot.s,#return videostreaming url for this robots IP camera
            'z':bot.z #code version info
        }

        
bt = BluetoothServer(data_received)

with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
        

pause()
