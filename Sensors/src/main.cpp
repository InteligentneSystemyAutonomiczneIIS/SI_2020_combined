// // NewPing: https://bitbucket.org/teckel12/arduino-new-ping/wiki/Home
// // https://bitbucket.org/teckel12/arduino-new-ping/wiki/Help%20with%2015%20Sensors%20Example%20Sketch



#include <Arduino.h>
#include <NewPing.h>
#include <Encoder.h>
#include "ISAMobile.h"
#include <Axle.hpp>
#include <Odometry.hpp>
#include <elapsedMillis.h>



#define SONAR_NUM      3 // Number of sensors.
#define MAX_DISTANCE 200 // Maximum distance (in cm) to ping.
#define PING_INTERVAL 30 // Milliseconds between sensor pings (29ms is about the min to avoid cross-sensor echo).

unsigned long pingTimer[SONAR_NUM]; // Holds the times when the next ping should happen for each sensor.
unsigned int distances[SONAR_NUM];         // Where the ping distances are stored.
uint8_t currentSensor = 0;          // Keeps track of which sensor is active.
bool isObstacle[SONAR_NUM] = {false};

elapsedMillis elapsedTime;
unsigned int printingInterval = 200; //ms


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


Odometry odometry; // odometry using encoders on rear axle
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
  odometry.Initialize();
  
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


  float x, y, theta;
  std::tie(x, y, theta) = odometry.GetPosition();

  float speed = odometry.GetLinearSpeedSimplified();
  float rpm = odometry.GetRPMSimplified();

  int32_t leftWheelEncoderTicks, rightWheelEncoderTicks;
  std::tie(leftWheelEncoderTicks, rightWheelEncoderTicks) = odometry.GetRawEncoderTicks();

  if (elapsedTime > printingInterval)
  {
    Serial.println("X: " + String(x) + " ; Y: "+ String(y) + " ; theta: " + String(theta));
    Serial.println("RPM: " + String(rpm) + " ; Linear speed: " + String(speed));
    Serial.println("Raw encoder ticks L: " + String(leftWheelEncoderTicks) + "; Raw encoder ticks R: " + String(rightWheelEncoderTicks));
    Serial.println("****************************************");
    elapsedTime = 0;
  }

}

