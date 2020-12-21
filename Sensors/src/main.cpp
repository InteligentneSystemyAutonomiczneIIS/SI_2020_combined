#include <Arduino.h>
#include <Ping.h>
#include <Encoder.h>
#include "NewPing.h"
#include "ISAMobile.h"

// NewPing: https://bitbucket.org/teckel12/arduino-new-ping/wiki/Home
// https://bitbucket.org/teckel12/arduino-new-ping/wiki/Help%20with%2015%20Sensors%20Example%20Sketch
// Encoder: https://www.pjrc.com/teensy/td_libs_Encoder.html


const int maxDistance = 200;

NewPing sonarMiddle(ultrasound_trigger_pin[(int)UltraSoundSensor::Front], 
                     ultrasound_echo_pin[(int)UltraSoundSensor::Front], 
                     maxDistance);

unsigned int pingDelay = 30; // How frequently are we going to send out a ping (in milliseconds). 50ms would be 20 times a second.
unsigned long pingTimer;     // Holds the next ping time.


// ##########
Encoder rightSide(ENCODER_REAR_RIGHT_1, ENCODER_REAR_RIGHT_2);
Encoder leftSide(ENCODER_REAR_LEFT_1, ENCODER_REAR_LEFT_2);



void echoCheck() { // Timer2 interrupt calls this function every 24uS where you can check the ping status.
  // Don't do anything here!
  if (sonarMiddle.check_timer()) { // This is how you check to see if the ping was received.
    // Here's where you can add code.
    Serial.print("Ping: ");
    Serial.print(sonarMiddle.ping_result / US_ROUNDTRIP_CM); // Ping returned, uS result in ping_result, convert to cm with US_ROUNDTRIP_CM.
    Serial.println("cm");
  }
  // Don't do anything here!
}


void setup() {
   Serial.begin(115200); // Starting Serial Terminal
   pingTimer = millis(); // Start now.
}

long positionLeft  = 0;
long positionRight = 0;

void loop() {
   // Notice how there's no delays in this sketch to allow you to do other processing in-line while doing distance pings.
   if (millis() >= pingTimer) {   // pingSpeed milliseconds since last ping, do another ping.
      pingTimer += pingDelay;      // Set the next ping time.
      sonarMiddle.ping_timer(echoCheck); // Send out the ping, calls "echoCheck" function every 24uS where you can check the ping status.
      positionLeft = leftSide.read();
      positionRight = rightSide.read();
      Serial.println("Left = " + String(positionLeft) + "; Right = " + String(positionRight));

   }
   // Do other stuff here, really. Think of it as multi-tasking.


}

