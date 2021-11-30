// // NewPing: https://bitbucket.org/teckel12/arduino-new-ping/wiki/Home
// // https://bitbucket.org/teckel12/arduino-new-ping/wiki/Help%20with%2015%20Sensors%20Example%20Sketch
// // Encoder: https://www.pjrc.com/teensy/td_libs_Encoder.html
// // TeensyTimerTools: https://github.com/luni64/TeensyTimerTool.git


// #include <Ping.h>
// #include "NewPing.h"
#include <Arduino.h>
#include <NewPing.h>
#include <Encoder.h>
#include "ISAMobile.h"
#include <Axle.hpp>


#define SONAR_NUM      3 // Number of sensors.
#define MAX_DISTANCE 200 // Maximum distance (in cm) to ping.
#define PING_INTERVAL 30 // Milliseconds between sensor pings (29ms is about the min to avoid cross-sensor echo).

unsigned long pingTimer[SONAR_NUM]; // Holds the times when the next ping should happen for each sensor.
unsigned int distances[SONAR_NUM];         // Where the ping distances are stored.
uint8_t currentSensor = 0;          // Keeps track of which sensor is active.
bool isObstacle[SONAR_NUM] = {false};



NewPing sonar[SONAR_NUM] = {   // Sensor object array.
  NewPing(ultrasound_trigger_pin[(int)UltraSoundSensor::Left], 
                     ultrasound_echo_pin[(int)UltraSoundSensor::Left], 
                     MAX_DISTANCE), // Each sensor's trigger pin, echo pin, and max distance to ping.
  NewPing(ultrasound_trigger_pin[(int)UltraSoundSensor::Front], 
                     ultrasound_echo_pin[(int)UltraSoundSensor::Front], 
                     MAX_DISTANCE),
  NewPing(ultrasound_trigger_pin[(int)UltraSoundSensor::Right], 
                     ultrasound_echo_pin[(int)UltraSoundSensor::Right], 
                     MAX_DISTANCE)
};

Axle rearAxle;
long positionLeft  = 0;
long positionRight = 0;



void processPingResult(uint8_t sensor, int distanceInCm) {
  // The following code would be replaced with your code that does something with the ping result.
  if(distanceInCm < 30 && distanceInCm != 0)
  {
     isObstacle[sensor] = true;
     distances[sensor] = distanceInCm;
     Serial.println("Obstacle detected, stop motors!!!");
     Serial.println("Sensor: " + String(sensor) + "; Distance: " + String(distanceInCm));
  }
  else
  {
     isObstacle[sensor] = false;
  }
  
}

void echoCheck() {
  if (sonar[currentSensor].check_timer())
    processPingResult(currentSensor, sonar[currentSensor].ping_result / US_ROUNDTRIP_CM);
}


void setup() {
  Serial.begin(115200);
  rearAxle.setupEncoders(ENCODER_REAR_LEFT_1, ENCODER_REAR_LEFT_2, ENCODER_REAR_RIGHT_1, ENCODER_REAR_RIGHT_2);
  rearAxle.initialize();
  
  pingTimer[0] = millis() + 75;
 
  for (uint8_t i = 1; i < SONAR_NUM; i++)
    pingTimer[i] = pingTimer[i - 1] + PING_INTERVAL;
}

void loop() {
  for (uint8_t i = 0; i < SONAR_NUM; i++) {
    if (millis() >= pingTimer[i]) {
      pingTimer[i] += PING_INTERVAL * SONAR_NUM;
      sonar[currentSensor].timer_stop();
      currentSensor = i;
      sonar[currentSensor].ping_timer(echoCheck);
    }
  }
  // Other code that *DOESN'T* analyze ping results can go here.
  
  auto encoderPositions = rearAxle.GetEncoderTicks();
  int newLeft = std::get<0>(encoderPositions);
  int newRight = std::get<1>(encoderPositions);
  if (newLeft != positionLeft || newRight != positionRight)
  {
    positionLeft = newLeft;
    positionRight = newRight;
    // Serial.println("Left = " + String(positionLeft) + "; Right = " + String(positionRight));
    Serial.println("RPM = " + String(rearAxle.getCurrentRotationalSpeed() ) + "; Velocity [m/s] = " + String(rearAxle.getCurrentLinearSpeed()));
  }
}

