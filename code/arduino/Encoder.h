/*
 * Header file for Analog encoder Class for continous rotation servo motor', that inherits from Thread.
 * Put the Encoder.cpp file and Encoder.h files to include this as library for your projects.
 * Author: Maurice Tedder December 29, 2018
 */
 
#ifndef Encoder_h
#define Encoder_h

#include "Arduino.h"
#include <Thread.h>
#include <Queue.h>
#include <Servo.h>

class Encoder: public Thread{

public:
  Encoder(Servo servo, int analogSensor, int threshold, int servoMin, int servoMax, int servoStop);

  /*
   * Add command string to command queue
   */
  void addCmd(String cmdStr);

private:
  Servo _servo; //servo controlled by this Encoder object
  int _analogSensor; //analog sensor port
  int _threshold; //analog sensor encoder wheel signal threshold
  Queue <String> _queue; //command queue
  bool _tick = false;
  bool _tickp = false;
  bool _continueLoop = true;
  int _count = 0;
  int _cmd = 0;
  int _servoMin; //Minimum allowed servo motor pwm value
  int _servoMax; //Maximum allowed servo motor pwm value
  int _servoStop; //Stop servo motor pwm value

  // No, "run" cannot be anything...
  // Because Thread uses the method "run" to run threads,
  // we MUST overload this method here. using anything other
  // than "run" will not work properly...
  void run();
};

#endif
