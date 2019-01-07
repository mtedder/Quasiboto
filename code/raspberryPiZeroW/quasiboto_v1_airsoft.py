##Quasiboto firmware using Pimoroni Picon Zero
##Includes code to operate taigen airsoft module and wheel encoders
##By Maurice Tedder
##January 3, 2019

from bluedot.btcomm import BluetoothServer
from gpiozero import Button
from signal import pause
import piconzero as pz

#pi camera inports
import io
import picamera
import logging
import socketserver
import threading
from threading import Condition
from http import server
import queue

## gpio pins used: https://pinout.xyz/
##Picon Zero Motor A = Airsoft motor
##17 = Airsoft limitswith/button (BCM 17 - pin 11)
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
# exit 0

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

#initialize and clear settings
pz.init( )

ENCODER0_THRESHOLD = 500
ENCODER1_THRESHOLD = 500

VERSION_NUMBER = "B1.3"
#counter = 0
STOP = 90
LOW = 0 #sets digital outputs LOW
HIGH = 1 #sets digital outputs HIGH

#Output config options
DIGITAL_OUTPUT = 0
PWM_OUTPUT = 1
SERVO_OUTPUT = 2
NEOPIXEL_OUTPUT = 3

#init servo/digital outputs
#ch0
servoPort0 = 0
#ch1
servoPort1 = 1
#ch2
servoPort2 = 2
#ch3
digitalOutPort3 = 3
#ch 4
digitalOutPort4 = 4
#ch 5

# Set output modeS
pz.setOutputConfig(servoPort0, SERVO_OUTPUT) #set to output Servo (0 - 180)
#pz.setOutputConfig(servoPort0, PWM_OUTPUT)    # or set output 0 to PWM (100)
pz.setOutputConfig(servoPort1, SERVO_OUTPUT) #set to output Servo (0 - 180)
pz.setOutputConfig(servoPort2, SERVO_OUTPUT) #set to output Servo (0 - 180)
pz.setOutputConfig(digitalOutPort3, DIGITAL_OUTPUT) #set to digital output 3
pz.setOutputConfig(digitalOutPort4, DIGITAL_OUTPUT) #set to digital output 4
#initialize outputs
pz.setOutput(digitalOutPort3, LOW)
pz.setOutput(digitalOutPort4, LOW)

# Set motor ch. A & B outputs
motorB = 0 #(motor B, positive is forward if blk->left & red->right
motorA = 1 #(motor A, positive is forward if red->left & blk->right

#input config options
DIGITAL_INPUT = 0
ANALOG_INPUT = 1
DS18B20_INPUT = 2

#define input ports
analogPort0 = 0 #input port 0
analogPort1 = 1 #input port 1
digitalInPort2 = 2 #input port 2
digitalInPort3 = 3 #input port 2

# Set input mode
pz.setInputConfig(analogPort0, ANALOG_INPUT) # set input 0 to Analog
pz.setInputConfig(analogPort1, ANALOG_INPUT) # set input 1 to Analog
pz.setInputConfig(digitalInPort2, DIGITAL_INPUT) # set input 2 to Digital
pz.setInputConfig(digitalInPort3, DIGITAL_INPUT) # set input 3 to Digital

#airsoft gun limit switch
limitSwitch = Button(17)
                    
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

def checkLimitSwitch(device):   
    pz.setMotor(motorA, 0)

def motor(servoPort, speed):#activate servo motor
    pz.setOutput(servoPort, speed)    

class Encoder(threading.Thread):
    'Class for Analog encoder on continous rotation servo motors'
  
    def __init__(self, servo_port, analog_port, threshold):
        threading.Thread.__init__(self)
        self.q = queue.Queue() #q, command queue
        self.event = threading.Event()
        self.encoderLoop = True       
        self.servo_port = servo_port
        self.analog_port = analog_port        
        self.threshold = threshold #analog sensor encoder wheel signal threshold        

    def startEncoder(self):#start encoder loop
            self.encoderLoop = True
            
    def stopEncoder(self):#Stop encoder loop
            self.encoderLoop = False
        
    def addCmd(self, cmd):#function to add command tuple to the command queue        
        self.q.put(cmd)       
        
    def run(self):        
        tick = False
        tickp = False
        count = 0
        continueLoop = False #encoder tick counter loop flag
        while self.encoderLoop:       
            self.event.wait() #reduce threading cpu resource by only looping when neseccery
            if not self.q.empty():#Test for new commands in the queue
                count = 0                
                data = self.q.get() #get command tuple from queue and parse data
                pwm = data[0]
                cmd = data[1]                
                continueLoop = True
                motor(self.servo_port, pwm)               
            else:               
                self.event.clear()                
                    
            while continueLoop:#position control feedback loop                            
                val = pz.readInput(self.analog_port)
                if (val < self.threshold):
                    tick = True
                else:
                    tick = False
                    
                if (tick != tickp):
                    count = count + 1

                tickp = tick

                if((cmd - count) <= 0):#get next command after completion of previous command                    
                    count = 0
                    tick = False
                    tickp = False
                    continueLoop = False                    
     
def e(speed, ticks):#//Servo Ch 0
    #print ("e:" + str(speed) + "," + str(ticks))
    cmd = (int(speed),int(ticks))
    e0.addCmd(cmd)
    e0.event.set()#send process command event to encoder thread

def f(speed, ticks):#//Servo ch 1    
    cmd = (int(speed),int(ticks))
    e1.addCmd(cmd)
    e1.event.set() #send process command event to encoder thread

def g(speed, param2):#servo ch 2
    print ("g:" + speed + "," + param2)
    motor(servoPort2, int(speed));

def h(param1, param2):#digital output 3
    pz.setOutput(digitalOutPort3, int(param1))

def i(param1, param2):#digital output 4
    pz.setOutput(digitalOutPort4, int(param1))

def j(param1, param2):#output 5
    #automationhat.output[2].write(int(param1))
    pass

def k(param1, param2):
    print ("k:" + param1 + "," + param2)

def l(param1, param2):
    #print ("l:" + param1 + "," + param2)
    stopAllMotors()    

def m(param1, param2):#return analog and digital read on all ports
    vals = str(pz.readInput(analogPort0)) + "," + str(pz.readInput(analogPort1)) + "," + str(pz.readInput(digitalInPort2)) + ":" + str(pz.readInput(digitalInPort3)) + "\n"
    #print("m:" + vals)
    bt.send(vals) 
    
def n(param1, param2):#return digital input read on all ports
    vals = str(pz.readInput(digitalInPort2)) + "," + str(pz.readInput(digitalInPort3)) + "\n"
    #print ("n:" + vals)
    bt.send(vals)

def o(param1, param2):#//Airsoft gun trigger
    #print ("o:" + param1 + "," + param2)    
    pz.setMotor(motorA, int(param1))

def p(param1, param2):#return analog on all ports
    vals = str(pz.readInput(analogPort0)) + "," + str(pz.readInput(analogPort1)) + "\n"
    #print ("p:" + vals)
    bt.send(vals)
    
def z(param1, param2):#firmware version number
    print ("z:" + param1 + "," + param2)
    bt.send(VERSION_NUMBER)

def defaultFn(param1, param2):
    #print ("defaultFn:" + param1 + "," + param2)
    #do nothing
    pass

def stopAllMotors():
    pz.stop() #Stop DC motors
    #stop all servo motors
    motor(servoPort0, STOP)
    motor(servoPort1, STOP)
    motor(servoPort2, STOP)
    e(STOP, 0)
    f(STOP, 0)
               
    
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
        
    
def data_received(data):
    while (len(data) > 0):
    #print ("data_received:" + data)
        cmd, param1, param2, data = parseData(data)
        commands.get(str(cmd), defaultFn)(param1, param2)    

limitSwitch.when_released = checkLimitSwitch #airsoft limit switch function
#limitSwitch.when_pressed = checkLimitSwitch #airsoft limit switch function

commands = {
            'e':e,#servo 0
            'f':f,#servo 1
            'g':g,#servo 2
            'h':h,#digital output 3
            'i':i,#digital output 4
            'j':j,#digital output 5
            'k':k,#Not implemented
            'l':l,#Not implemented
            'm':m,#return analog and digital read on all ports
            'n':n,#return digital read on all ports
            'o':o,#airsoft gun trigger
            'p':p,#return analog on all ports
            'n':n,#read analog sensor data
            'z':z #code version info
        }

bt = BluetoothServer(data_received)

#Create encoder objects
e0 = Encoder(servoPort0, analogPort0,ENCODER0_THRESHOLD)
e1 = Encoder(servoPort1, analogPort1,ENCODER0_THRESHOLD)

#queueLock0.acquire()
#start encoder threads
e0.start()
e1.start()

stopAllMotors()

#wait for thread to complete
#e0.join()
#e1.join()

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
