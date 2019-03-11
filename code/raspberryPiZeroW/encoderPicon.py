import queue
import threading
import piconzero as pz

# Wheel encoder code for analog sensors attached to a continous rotation servo motor.
# Pomironi Picon Zero version
#By Maurice Tedder
#January 2, 2018
#Ref: https://www.tutorialspoint.com/python/python_multithreading.htm

##Setup to use I2C and smbus correctly:
#http://4tronix.co.uk/blog/?p=1224 (picon)
##sudo apt-get install python-smbus python3-smbus python-dev python3-dev
##Set enable i2c device in the Preferences->Raspberry Pi Configuration->Interfaces menu
#initialize and clear settings
pz.init( )

THRESHOLD = 500

#init servo outputs

#ch0
servoPort0 = 0
#ch1
servoPort1 = 1
#ch2
servoPort2 = 2

#define input ports
analogPort0 = 0 #input port 0
analogPort1 = 1 #input port 1

# Set output mode
pz.setOutputConfig(servoPort0, 2) #set to output Servo (0 - 180)
#pz.setOutputConfig(servoPort0, 1)    # set output 0 to PWM (100)

# Set input mode
pz.setInputConfig(analogPort0, 1)     # set input 0 to Analog

def motor(servoPort, speed):#activate servo hat servo motor           
    pz.setOutput (servoPort, speed)
        
        
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
        self.continueLoop = False

    def startEncoder(self):#start encoder loop
            self.encoderLoop = True
            
    def stopEncoder(self):#Stop encoder loop
        self.continueLoop = False
        self.encoderLoop = False        
        
    def addCmd(self, cmd):#function to add command tuple to the command queue        
        self.q.put(cmd)        
        
    def run(self):        
        tick = False
        tickp = False
        count = 0
        self.continueLoop = False #encoder tick counter loop flag
        while self.encoderLoop:
            self.event.wait() #reduce threading cpu resource by only looping when necessary            
            if not self.q.empty():#Test for new commands in the queue
                #self.continueLoop = True
                data = self.q.get() #get command tuple from queue and parse data
                pwm = data[0]
                cmd = data[1]
                self.continueLoop = True
                motor(self.servo_port, pwm)                
            else:
                self.event.clear()               
                    
            while self.continueLoop:#position control feedback loop
                #print(str(self.threshold))
                val = pz.readInput(self.analog_port)                
                if (val < self.threshold):
                    tick = True
                else:
                    tick = False
                    
                if (tick != tickp):
                    count = count + 1

                tickp = tick

                if((cmd - count) < 0):#get next command after completion of previous command                    
                    count = 0
                    tick = False
                    tickp = False
                    self.continueLoop = False                                                        
    
#create motor command list (CCW for 20 ticks, Stop, CW for 50 ticks, Stop)
cmds = [(180, 20), (90, 0),(50, 50), (90, 0)]
#CW for 50 ticks, Stop
#cmds = [(50, 50), (90, 0)]
#Stop
#cmds = [(90, 0)]

#Create encoder object
e0 = Encoder(servoPort0, analogPort0,THRESHOLD)

#add commands from command list to encoder command queue
for dat in cmds:
    e0.addCmd(dat)
    
e0.event.set()#send process command event to encoder thread

#start encoder thread
e0.start()


#Uncomment this section to use interactive servo command mode
#--- Start interactive mode servo command ---
##cmds = []
##doLoop = True
##while doLoop:
##    speed = int(input("Input Speed:"))
##    cmd = int(input("Input command ticks:"))
##    cmds.append((speed, cmd))
##    
##    user_input = input("Would you like send your commands? enter (y = yes):")
##    if user_input == 'y':
##        for dat in cmds:
##            e0.addCmd(dat)
##        cmds = [] #reset commands array
##        e0.event.set()#send process command event to encoder thread
##        
##    user_input = input("Would you like to continue? enter (y = yes):")
##    if user_input != 'y':
##        doLoop = False
#        
#---End interactive servo command mode code ---
#


#end encoder thread
user_input = input("Hit any key to end:")
e0.stopEncoder() #end encoder thread
    
#wait for thread to complete
#e0.join()

print("THE END")

#reset picon zero
pz.cleanup()
