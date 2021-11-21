#include <Arduino.h>
#include "variables.h"
#include "functions.hpp"
#include "NERFTrigger.hpp"


// // Moduł przekaźników Iduino 2 kanały z optoizolacją - styki 10A/250VAC - cewka 5V
// // https://botland.com.pl/moduly-przekaznikow/14266-modul-przekaznikow-iduino-2-kanaly-z-optoizolacja-styki-10a250vac-cewka-5v-5903351242332.html
// // GND - IN1 - IN2 - VCC
// // Activated on LOW state !! - contrary to documentation
// // OR
// // // Moduł przekaźników 2 kanały - styki 10A/250VAC - cewka 5V
// // // https://botland.com.pl/przekazniki-przekazniki-arduino/2043-modul-przekaznikow-2-kanaly-styki-10a-250vac-cewka-5v-5904422302429.html
// // VCC - IN1 - IN2 - GND
// // Activated on LOW state 
// // Linear actuator - blue to IN1, green to IN2


const int relayIN1_pin = 6; //LEFT on module
const int relayIN2_pin = 7; //RIGHT on module
int defaultNotEnergized = HIGH;
bool canShoot = false;
NERFTrigger trigger;


void setup()
{
    // Use to check for any errors in using timers
    // TeensyTimerTool::attachErrFunc(TeensyTimerTool::ErrorHandler(Serial));

    initSerial(115200);
    delay(3000);
    Serial.println(" | Serial Done");

    trigger = NERFTrigger(relayIN1_pin, relayIN2_pin, std::chrono::milliseconds(3000));
    trigger.initialize();

    
}

void loop()
{
    trigger.shoot();
    // delay(50);
}






