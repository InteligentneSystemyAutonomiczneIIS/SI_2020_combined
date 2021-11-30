// #include <Arduino.h>
// #include <Ping.h>
// #include <Encoder.h>
// #include "NewPing.h"
// #include "ISAMobile.h"

// // NewPing: https://bitbucket.org/teckel12/arduino-new-ping/wiki/Home
// // https://bitbucket.org/teckel12/arduino-new-ping/wiki/Help%20with%2015%20Sensors%20Example%20Sketch
// // Encoder: https://www.pjrc.com/teensy/td_libs_Encoder.html


// const int maxDistance = 200;

// NewPing sonarMiddle(ultrasound_trigger_pin[(int)UltraSoundSensor::Front], 
//                      ultrasound_echo_pin[(int)UltraSoundSensor::Front], 
//                      maxDistance);

// unsigned int pingDelay = 30; // How frequently are we going to send out a ping (in milliseconds). 50ms would be 20 times a second.
// unsigned long pingTimer;     // Holds the next ping time.


// // ##########
// Encoder rightSide(ENCODER_REAR_RIGHT_1, ENCODER_REAR_RIGHT_2);
// Encoder leftSide(ENCODER_REAR_LEFT_1, ENCODER_REAR_LEFT_2);



// void echoCheck() { // Timer2 interrupt calls this function every 24uS where you can check the ping status.
//   // Don't do anything here!
//   if (sonarMiddle.check_timer()) { // This is how you check to see if the ping was received.
//     // Here's where you can add code.
//     Serial.print("Ping: ");
//     Serial.print(sonarMiddle.ping_result / US_ROUNDTRIP_CM); // Ping returned, uS result in ping_result, convert to cm with US_ROUNDTRIP_CM.
//     Serial.println("cm");
//   }
//   // Don't do anything here!
// }


// void setup() {
//    Serial.begin(115200); // Starting Serial Terminal
//    pingTimer = millis(); // Start now.
// }

// long positionLeft  = 0;
// long positionRight = 0;

// void loop() {
//    // Notice how there's no delays in this sketch to allow you to do other processing in-line while doing distance pings.
//    if (millis() >= pingTimer) {   // pingSpeed milliseconds since last ping, do another ping.
//       pingTimer += pingDelay;      // Set the next ping time.
//       sonarMiddle.ping_timer(echoCheck); // Send out the ping, calls "echoCheck" function every 24uS where you can check the ping status.
//       positionLeft = leftSide.read();
//       positionRight = rightSide.read();
//       Serial.println("Left = " + String(positionLeft) + "; Right = " + String(positionRight));

//    }
//    // Do other stuff here, really. Think of it as multi-tasking.
// }

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

// // ##########
// Encoder rightSide(ENCODER_REAR_RIGHT_1, ENCODER_REAR_RIGHT_2);
// Encoder leftSide(ENCODER_REAR_LEFT_1, ENCODER_REAR_LEFT_2);
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
    Serial.println("Left = " + String(positionLeft) + "; Right = " + String(positionRight));
  }
}

