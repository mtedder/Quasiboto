import queue
import threading
import automationhat
import smbus #I2C interface

# Wheel encoder code for analog sensors attached to a continous rotation servo motor.
#By Maurice Tedder
#December 25, 2018
#Ref: https://www.tutorialspoint.com/python/python_multithreading.htm

THRESHOLD = 2.5

bus = smbus.SMBus(1)
addr = 0x40

#init servo duty cycle
#bus.write_byte_data(addr, 0, 0x20) #200 Hz
#bus.write_byte_data(addr, 0xfe, 0x1e) #200 Hz
bus.write_byte_data(addr, 0, 0x20) #50 HZ
bus.write_byte_data(addr, 0xfe, 0x1e) #50 Hz
#ch0
servo0_start = 0x06
servo0_end = 0x08
#ch1
servo1_start = 0x0A
servo1_end = 0x0C
#ch2
servo2_start = 0x0E
servo2_end = 0x10

#create synchronization lock
queueLock = threading.Lock()

def motor(bus, addr, servo_start, servo_end, pwm):#activate servo hat servo motor       
    bus.write_word_data(addr, servo_start, 0)    
    bus.write_word_data(addr, servo_end, pwm)
        
        
class Encoder(threading.Thread):
    'Class for Analog encoder on continous rotation servo motors'
  
    def __init__(self, bus, addr, servo_start, servo_end, threshold):
        threading.Thread.__init__(self)
        self.q = queue.Queue() #q, command queue
        self.encoderLoop = True
        self.bus = bus
        self.addr = addr
        self.servo_start = servo_start
        self.servo_end = servo_end
        self.threshold = threshold #analog sensor encoder wheel signal threshold

    def startEncoder(self):#start encoder loop
            self.encoderLoop = True
            
    def stopEncoder(self):#Stop encoder loop
            self.encoderLoop = False
        
    def addCmd(self, cmd):#function to add command tuple to the command queue
        queueLock.acquire()
        self.q.put(cmd)
        queueLock.release()
        
    def run(self):        
        tick = False
        tickp = False
        count = 0
        continueLoop = False #encoder tick counter loop flag
        while self.encoderLoop:
            queueLock.acquire()            
            if not self.q.empty():#Test for new commands in the queue
                continueLoop = True
                data = self.q.get() #get command tuple from queue and parse data
                pwm = data[0]
                cmd = data[1]                       
                motor(self.bus, self.addr, self.servo_start, self.servo_end, pwm)
                queueLock.release()
            else:
                queueLock.release()                
                    
            while continueLoop:#position control feedback loop
                #print(str(self.threshold))
                val = automationhat.analog[0].read() #get current value of wheel encoder sensor                
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
                    continueLoop = False                                                        
    
#create motor command list
cmds = [(1639, 20), (1250, 0),(1000, 50), (1250, 0)]
#cmds = [(1639, 0)]

#Create encoder object
e1 = Encoder(bus, addr, servo0_start, servo0_end,THRESHOLD)

#add commands from command list to encoder command queue
for dat in cmds:
    e1.addCmd(dat)

#start encoder thread
e1.start()


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
##            e1.addCmd(dat)
##        cmds = [] #reset commands array
##        
##    user_input = input("Would you like to continue? enter (y = yes):")
##    if user_input != 'y':
##        doLoop = False
#        
#---End interactive servo command mode code ---
#

#wait for thread to complete
#e1.join()

#end encoder thread
user_input = input("Enter y to exit:")
if user_input == 'y':
    e1.stopEncoder() #end encoder thread
    
#wait for thread to complete
e1.join()

print("THE END")
