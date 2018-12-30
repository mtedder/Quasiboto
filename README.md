# Quasiboto
Resource Files and demo code for Add an Encoder to Feetech Micro 360 Degree Continuous Rotation Servo FS90R Instructable.

Link to Instructable: https://www.instructables.com/id/Add-an-Encoder-to-Feetech-Micro-360-Degree-Continu/

It's very difficult or next to impossible to precisely control wheeled robot motion using open loop motor control. Many applications require accurately setting the pose or travel distance of a wheeled robot. Small continuous rotation micro servo motors are a great low cost solution to drive small robots but they lack the feedback control of larger servo motors.

The Feetech Micro 360 Degree Continuous Rotation Servos (FS90R) are great for robotics projects but sometimes you want the feedback control of larger servos.

Converting these little servos to use closed loop position feedback control is actually very easy once you add a Tamiya analog Encoder sensor and a simple closed loop feedback algorithm to an Arduino or Raspbery Pi controller.
