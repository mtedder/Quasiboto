
/*
 * Class for Analog encoder for continous rotation servo motor', that inherits from Thread.
 * Put the Encoder.cpp file and Encoder.h files to include this as library for your projects.
 * Author: Maurice Tedder December 29, 2018
 */

#include "Encoder.h"

Encoder::Encoder(Servo servo, int analogSensor, int threshold, int servoMin, int servoMax, int servoStop){
    _servo = servo;
    _analogSensor = analogSensor;
    _threshold = threshold; 
    _servoMin = servoMin;
    _servoMax = servoMax;
    _servoStop = servoStop;
  }

  /*
   * Add command string to command queue
   */
  void Encoder::addCmd(String cmdStr){
    _queue.enqueue (cmdStr);
  }

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

  // No, "run" cannot be anything...
  // Because Thread uses the method "run" to run threads,
  // we MUST overload this method here. using anything other
  // than "run" will not work properly...
  void Encoder::run(){
     // dequeue all the message's characters from the queue.
    while (!_queue.isEmpty()){
      _continueLoop = true;
      String data = _queue.dequeue();
      int delIndex = data.indexOf(',');
      //Serial.println (delIndex);
      int motorSpeed = (data.substring(0, delIndex)).toInt();//parse motor speed value
      _cmd = (data.substring(delIndex+1)).toInt();//parse position cmd value
      _servo.write(constrain(motorSpeed, _servoMin, _servoMax));
      
      while (_continueLoop) {//position control feedback loop
        int val = analogRead(_analogSensor); //get current value of wheel encoder  
        
        if (val < _threshold){//detect encoder wheel edge
          _tick = true;
        }else{
          _tick = false;
        }
                            
        if (_tick != _tickp){
          _count = _count + 1;
        }
      
        _tickp = _tick;
      
        if((_cmd - _count) < 0){//get next command after completion of previous command   
            _count = 0;
            _tick = false;
            _tickp = false;
            _continueLoop = false;
            _servo.write(constrain(_servoStop, _servoMin, _servoMax));
        }
                          
      }//end position control feedback loop
    }//end command queue read loop
  }//end run methods
