#include <ThreadController.h>
#include <StaticThreadController.h>
#include <Thread.h>

#include <Queue.h>
#include <Servo.h>

#include "Encoder.h"
/*
 * ref: 
 * https://github.com/EinarArnason/ArduinoQueue
 * https://github.com/ivanseidel/ArduinoThread
*/

/*
 * Class for Analog encoder for continous rotation servo motor', that inherits from Thread.
 * Put the Encoder.cpp file and Encoder.h files to include this as library for your projects.
 * Author: Maurice Tedder December 29, 2018
 * 
 * NOTE: This code is included as a reference to see how the encoder class is constructed. Use the Encoder.h and Encoder.cpp library files to include the Encoder in your projects.
 */
//class Encoder: public Thread
//{
//public:
//  Encoder(Servo servo, int analogSensor, int threshold, int servoMin, int servoMax, int servoStop){
//    _servo = servo;
//    _analogSensor = analogSensor;
//    _threshold = threshold; 
//    _servoMin = servoMin;
//    _servoMax = servoMax;
//    _servoStop = servoStop;
//  }
//
//  /*
//   * Add command string to command queue
//   */
//  void addCmd(String cmdStr){
//    _queue.enqueue (cmdStr);
//  }
//
//private:
//  Servo _servo; //servo controlled by this Encoder object
//  int _analogSensor; //analog sensor port
//  int _threshold; //analog sensor encoder wheel signal threshold
//  Queue <String> _queue; //command queue
//  bool _tick = false;
//  bool _tickp = false;
//  bool _continueLoop = true;
//  int _count = 0;
//  int _cmd = 0;
//  int _servoMin; //Minimum allowed servo motor pwm value
//  int _servoMax; //Maximum allowed servo motor pwm value
//  int _servoStop; //Stop servo motor pwm value
//
//  // No, "run" cannot be anything...
//  // Because Thread uses the method "run" to run threads,
//  // we MUST overload this method here. using anything other
//  // than "run" will not work properly...
//  void run(){
//     // dequeue all the message's characters from the queue.
//    while (!_queue.isEmpty()){
//      _continueLoop = true;
//      String data = _queue.dequeue();
//      int delIndex = data.indexOf(',');
//      //Serial.println (delIndex);
//      int motorSpeed = (data.substring(0, delIndex)).toInt();//parse motor speed value
//      _cmd = (data.substring(delIndex+1)).toInt();//parse position cmd value
//      _servo.write(constrain(motorSpeed, _servoMin, _servoMax));
//      
//      while (_continueLoop) {//position control feedback loop
//        int val = analogRead(_analogSensor); //get current value of wheel encoder  
//        
//        if (val < _threshold){//detect encoder wheel edge
//          _tick = true;
//        }else{
//          _tick = false;
//        }
//                            
//        if (_tick != _tickp){
//          _count = _count + 1;
//        }
//      
//        _tickp = _tick;
//      
//        if((_cmd - _count) < 0){//get next command after completion of previous command   
//            _count = 0;
//            _tick = false;
//            _tickp = false;
//            _continueLoop = false;
//            _servo.write(constrain(_servoStop, _servoMin, _servoMax));
//        }
//                          
//      }//end position control feedback loop
//    }//end command queue read loop
//  }//end run method
//};

// We need to use the 'raw' pin reading methods because timing is very important here
// and the digitalRead() procedure is slower!
#define AnalogInput_4 4 //Sensors on Analog pin 4
#define AnalogInput_5 5 //Sensors on Analog pin 5
#define THRESHOLD 560 //encoder sensor reading threshold
#define STOP 90 //servo motor stop value

//servo motors
Servo servo9;  // create servo object to control a servo
Servo servo10;  // create servo object to control a servo

//Create encoder object
Encoder e1 = Encoder(servo9, AnalogInput_4, THRESHOLD, 0, 180, STOP);

// Instantiate a new ThreadController
// StaticThreadController that will controll all threads
// All non-pointers go with '&', but pointers go without '&', 
StaticThreadController<1> encodersThread (&e1);
  
void setup() {
  // put your setup code here, to run once:

  //add closed loop motor position commands to encoder object queue
  e1.addCmd("180,20");//forward for 20 ticks
  e1.addCmd("90,0");//stop
  e1.addCmd("0,50");//reverse for 50 ticks
  e1.addCmd("90,0");//stop 

  servo9.attach(9);  // attaches the servo on pin 9 to the servo object
  servo10.attach(10);  // attaches the servo on pin 10 to the ser  

  // start serial communication.
  Serial.begin(115200);
}

void loop() {
// put your main code here, to run repeatedly:

  // run StaticThreadController
  // this will check every thread inside ThreadController,
  // if it should run. If yes, he will run it;
  encodersThread.run(); 

  //Serial.println("The End");
}
