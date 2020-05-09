##Quasiboto Robot module using Pimoroni Picon Zero
##Includes code to operate taigen airsoft module and wheel encoders
##By Maurice Tedder
##February 13, 2019
##March 1, 2019 - corrected s() function return value and added missing self parameter
#to Robot class functions

from gpiozero import Button
from signal import pause
from subprocess import check_output
import piconzero as pz

#pi camera inports
import io
import logging
import threading
from threading import Condition
import queue

## gpio pins used: https://pinout.xyz/
##Picon Zero Motor A = Airsoft motor
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

#initialize and clear settings
#sudo i2cdetect -y 1 #To View i2c addresses
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

LIMIT_SWITCH_GPIO_PIN = 17

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


class Robot():
    'Class for Controlling a QuasiBoto Robot'

    def __init__(self):
        #Create encoder objects
        self.e0 = Encoder(servoPort0, analogPort0,ENCODER0_THRESHOLD, self.motor)
        self.e1 = Encoder(servoPort1, analogPort1,ENCODER0_THRESHOLD, self.motor)

        #queueLock0.acquire()
        #start encoder threads
        self.e0.start()
        self.e1.start()

        self.stopAllMotors()

        #airsoft gun limit switch
        self.limitSwitch = Button(LIMIT_SWITCH_GPIO_PIN)
        self.limitSwitch.when_released = self.checkLimitSwitch #airsoft limit switch function

    def checkLimitSwitch(self,device):
##        print('limit sw')
        pz.setMotor(motorA, 0)

    def motor(self, servoPort, speed):#activate servo motor
        pz.setOutput(servoPort, speed)

    def e(self, speed, ticks):#//Servo Ch 0
        #print ("e:" + str(speed) + "," + str(ticks))
        cmd = (int(speed),int(ticks))
        self.e0.addCmd(cmd)
        self.e0.event.set()#send process command event to encoder thread

    def f(self, speed, ticks):#//Servo ch 1
        #print ("f:" + str(speed) + "," + str(ticks))
        cmd = (int(speed),int(ticks))
        self.e1.addCmd(cmd)
        self.e1.event.set() #send process command event to encoder thread

    def g(self, speed, param2):#servo ch 2
        #print ("g:" + speed + "," + param2)
        self.motor(servoPort2, int(speed));

    def h(self, param1, param2):#digital output 3
        pz.setOutput(digitalOutPort3, int(param1))

    def i(self, param1, param2):#digital output 4
        pz.setOutput(digitalOutPort4, int(param1))

    def j(self, param1, param2):#output 5
        #automationhat.output[2].write(int(param1))
        pass

    def k(self, param1, param2):#Not implemented
        print ("k:" + param1 + "," + param2)

    def l(self, param1, param2):#stop all motors emergency stop on all motors
        #print ("l:" + param1 + "," + param2)
        stopAllMotors()

    def m(self, param1, param2):#return analog and digital read on all ports
        vals = str(pz.readInput(analogPort0)) + "," + str(pz.readInput(analogPort1)) + "," + str(pz.readInput(digitalInPort2)) + ":" + str(pz.readInput(digitalInPort3)) + "\n"
        #print("m:" + vals)
        return vals

    def n(self, param1, param2):#return digital input read on all ports
        vals = str(pz.readInput(digitalInPort2)) + "," + str(pz.readInput(digitalInPort3)) + "\n"
        #print ("n:" + vals)
        return vals

    def o(self, param1, param2):#Airsoft gun trigger (MotorA output). Closed loop controlled by limit switch
        #print ("o:" + param1 + "," + param2)
        pz.setMotor(motorA, int(param1))

    def p(self, param1, param2):#return analog on all ports
        vals = str(pz.readInput(analogPort0)) + "," + str(pz.readInput(analogPort1)) + "\n"
        #print ("p:" + vals)
        return vals

    def q(self, param1, param2):#MotorB output. Open loop control
        #print ("q:" + param1 + "," + param2)
        pz.setMotor(motorB, int(param1))

    def s(self, param1, param2):#return videostreaming url for this robots IP camera in json format
        #print ("s:" + param1 + "," + param2)
        ips = check_output(["hostname", "-I"])
        return "{'ipcamurl':'http://" + ips.decode('UTF-8').split()[0].strip() + ":8000/stream.mjpg'}\n"
        #print ("{'ipcamurl':'http://" + ips.decode().strip() + ":8000/stream.mjpg'}")

    def z(self, param1, param2):#firmware version number
        print ("z:" + param1 + "," + param2)
        return VERSION_NUMBER

    def stopAllMotors(self):
        pz.stop() #Stop DC motors
        #stop all servo motors
        self.motor(servoPort0, STOP)
        self.motor(servoPort1, STOP)
        self.motor(servoPort2, STOP)
        self.e(STOP, 0)
        self.f(STOP, 0)

class Encoder(threading.Thread):
    'Class for Analog encoder on continous rotation servo motors'

    def __init__(self, servo_port, analog_port, threshold, mtr):
        threading.Thread.__init__(self)
        self.q = queue.Queue() #q, command queue
        self.event = threading.Event()
        self.encoderLoop = True
        self.servo_port = servo_port
        self.analog_port = analog_port
        self.threshold = threshold #analog sensor encoder wheel signal threshold
        self.motor = mtr

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
                self.motor(self.servo_port, pwm)
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




#limitSwitch.when_pressed = checkLimitSwitch #airsoft limit switch function

#wait for thread to complete
#e0.join()
#e1.join()

#pause()
