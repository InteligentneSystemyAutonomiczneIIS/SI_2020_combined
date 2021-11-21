#pragma once
#include "TeensyTimerTool.h"
#include <chrono>

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


class NERFTrigger
{
    private:
        int relayIN1_pin;
        int relayIN2_pin;
        int defaultNotEnergized = HIGH;
        int defaultEnergized;
        TeensyTimerTool::OneShotTimer retractTimer;
        TeensyTimerTool::OneShotTimer betweenShotDelayTimer;
        TeensyTimerTool::OneShotTimer releaseTimer;
        bool canShoot = true;

        std::chrono::milliseconds extendingTime = 100ms;
        std::chrono::milliseconds shotsCooldown = 1000ms;
        std::chrono::milliseconds retractionTime = 100ms;

    public:
        NERFTrigger() {}
        
        NERFTrigger(int relayIN1_PinNumber, int relayIN2_PinNumber, 
                    std::chrono::milliseconds timeBetweenShots = 1000ms,
                    int defaultRelayEnergizedState = LOW): 
                                        relayIN1_pin(relayIN1_PinNumber), relayIN2_pin(relayIN2_PinNumber),
                                        defaultNotEnergized(!defaultRelayEnergizedState), defaultEnergized(defaultRelayEnergizedState),
                                        shotsCooldown(timeBetweenShots)
        {

        }

        void initialize()
        {
            setupTimers();
            setupRelays();
        }

        void shoot()
        {
            if (canShoot)
            {
                canShoot = false;
                extend();
            }
            
        }

    protected:
        void setupTimers()
        {
            retractTimer = TeensyTimerTool::OneShotTimer(TeensyTimerTool::TCK32);
            betweenShotDelayTimer = TeensyTimerTool::OneShotTimer(TeensyTimerTool::TCK32);
            releaseTimer = TeensyTimerTool::OneShotTimer(TeensyTimerTool::TCK32);
            
            retractTimer.begin([this] {this->retract();});
            releaseTimer.begin([this] {this->releaseRelays();});
            betweenShotDelayTimer.begin([this] {this->resetCanShoot();});

            Serial.println("NERFTrigger timers setup finished");
        }

        void setupRelays()
        {
            //set pins to output + open drain (necessary for some boards)
            pinMode(relayIN1_pin, OUTPUT_OPENDRAIN);
            pinMode(relayIN2_pin, OUTPUT_OPENDRAIN);
            
            //retract
            digitalWriteFast(relayIN1_pin, defaultNotEnergized); 
            digitalWriteFast(relayIN2_pin, defaultEnergized);
            delay(retractionTime.count());

            //release
            digitalWriteFast(relayIN1_pin, defaultNotEnergized);   
            digitalWriteFast(relayIN2_pin, defaultNotEnergized); 

            delay(100);  
            canShoot = true;
            Serial.println("Setup relays finished");
        }

        void releaseRelays()
        {
            Serial.println("Release");
            //make sure, that the relay is turned OFF
            digitalWriteFast(relayIN1_pin, defaultNotEnergized);   
            digitalWriteFast(relayIN2_pin, defaultNotEnergized);
            betweenShotDelayTimer.trigger(shotsCooldown);
        }

        void resetCanShoot()
        {
            canShoot = true;
        }

        void extend() 
        {
            //extend (enegrize correct relays)
            Serial.println("Extending");
            digitalWriteFast(relayIN1_pin, defaultEnergized ); 
            digitalWriteFast(relayIN2_pin, defaultNotEnergized );
            retractTimer.trigger(extendingTime);
        }

        void retract()
        {
            //retract (enegrize correct relays)
            Serial.println("Retracting");
            digitalWriteFast(relayIN1_pin, defaultNotEnergized); 
            digitalWriteFast(relayIN2_pin, defaultEnergized );
            releaseTimer.trigger(retractionTime);
        }

};