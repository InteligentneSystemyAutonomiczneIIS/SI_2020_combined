// // Encoder: https://www.pjrc.com/teensy/td_libs_Encoder.html
// // TeensyTimerTools: https://github.com/luni64/TeensyTimerTool.git

#pragma once

#include "TeensyTimerTool.h"
#include <Encoder.h>
#include <memory>
#include <chrono>
#include <ISAMobile.h>

class Axle
{
private:
    // configurable params (defaults)
    int encoderTicksPerRevolution = 354; // 352 - 356; average, can be slightly different for left and right wheels
    float wheelDiameterInMM = 120.0; // 118.1 - 122.2 milimeters
    float wheelDiameterInMeters =  wheelDiameterInMM / 1000.0;
    float axleLengthInMeters = 0.277; //meters


    float currentRotationalSpeedLeftWheel = 0.0f;
    float currentRotationalSpeedRightWheel = 0.0f;
    float currentRotationalSpeed = 0.0f;


    float currentLinearSpeedLeftWheel = 0.0f;
    float currentLinearSpeedRightWheel = 0.0f;
    float currentLinearSpeed = 0.0f;

    float leftWheelDistance = 0.0f;
    float rightWheelDistance = 0.0f;


    std::unique_ptr<Encoder> leftWheelEncoder;
    std::unique_ptr<Encoder> rightWheelEncoder;
    int previousLeftEncoderTicks = 0;
    int previousRightEncoderTicks = 0;


    
    TeensyTimerTool::PeriodicTimer encoderCheckTimer;
    //Approximation of time passed - real time will be different ! (use millis() or micros() to calculate time passed)
    unsigned long prevTime = 0;
    std::chrono::milliseconds encoderCheckInterval = 50ms;


public:
    // use default values of parameters - can be wrong for some mobile platforms
    Axle()
    {

    }

    Axle(float wheelDiameterInMilimeters, float encoderTicksPerRevolution)
    {
        SetWheelsDiameter(wheelDiameterInMilimeters);
        SetEncoderTicksPerWheelRevolution(encoderTicksPerRevolution);
    }

    void SetWheelsDiameter(float wheelDiameterInMilimeters )
    {
        this->wheelDiameterInMM = wheelDiameterInMilimeters;
        this->wheelDiameterInMeters = wheelDiameterInMilimeters / 1000.0;
    }

    void SetEncoderTicksPerWheelRevolution(float encoderTicksPerRevolution)
    {
        this->encoderTicksPerRevolution = encoderTicksPerRevolution;
    }

    // default values are for rear axle
    void SetupEncoders(int pinLeft1 = ENCODER_REAR_LEFT_1, int pinLeft2 = ENCODER_REAR_LEFT_2, 
                       int pinRight1 = ENCODER_REAR_RIGHT_1, int pinRight2 = ENCODER_REAR_RIGHT_2)
    {
        leftWheelEncoder = std::make_unique<Encoder>(pinLeft1, pinLeft2);
        rightWheelEncoder = std::make_unique<Encoder>(pinRight1, pinRight2);
    }

    void Initialize()
    {
        this->currentRotationalSpeed = 0;
        this->currentLinearSpeed = 0;

        // initialize timers and set up callback functions
        encoderCheckTimer = TeensyTimerTool::PeriodicTimer(TeensyTimerTool::TCK32);
        encoderCheckTimer.begin([this] {this->Update();}, encoderCheckInterval);

        this->prevTime = millis();
    }

    float GetCurrentLinearSpeed()
    {
        return currentLinearSpeed;
    }

    float GetCurrentRotationalSpeed()
    {
        return currentRotationalSpeed;
    }

    std::tuple<float, float> GetCurrentWheelDistance()
    {
        return std::tuple<float, float> (this->leftWheelDistance, this->rightWheelDistance);
    }

    std::tuple<int32_t, int32_t> GetEncoderTicks()
    {
        return std::tuple<int32_t, int32_t>(previousLeftEncoderTicks, previousRightEncoderTicks);
    }

    float GetAxleLength()
    {
        return this->axleLengthInMeters;
    }

private:

    //make sure executon will not take longer than encoderCheckInterval, that might cause problems
    void Update()
    {
        unsigned long currentTime = millis();
        int leftEncoderTicks = leftWheelEncoder->read();
        int rightEncoderTicks = rightWheelEncoder->read();

        //actual time between executions - timers can be imprecise (though it is not really necessary here)
        auto timeDelta = std::chrono::milliseconds(currentTime - prevTime);

        // linear speed [m/s]
        this->currentLinearSpeedLeftWheel = CalculateLinearSpeedForWheel(leftEncoderTicks, this->previousLeftEncoderTicks, timeDelta);
        this->currentLinearSpeedRightWheel = CalculateLinearSpeedForWheel(rightEncoderTicks, this->previousRightEncoderTicks, timeDelta);
        this->currentLinearSpeed = (this->currentLinearSpeedLeftWheel + this->currentLinearSpeedRightWheel ) / 2.0f;

        // Rotational Speed [RPM]
        this->currentRotationalSpeedLeftWheel = CalculateRotationalSpeedForWheel(leftEncoderTicks, this->previousLeftEncoderTicks, timeDelta);
        this->currentRotationalSpeedLeftWheel = CalculateRotationalSpeedForWheel(rightEncoderTicks, this->previousRightEncoderTicks, timeDelta);
        this->currentRotationalSpeed = (this->currentRotationalSpeedLeftWheel + this->currentRotationalSpeedLeftWheel) / 2.0f;
        
        // wheel distance [m] (disregarding any form of slip, calculated based on rotations only) 
        this->leftWheelDistance += CalculateWheelDistance(leftEncoderTicks, previousLeftEncoderTicks, this->encoderTicksPerRevolution);
        this->rightWheelDistance += CalculateWheelDistance(rightEncoderTicks, previousRightEncoderTicks, this->encoderTicksPerRevolution);

        // rember values
        previousLeftEncoderTicks = leftEncoderTicks;
        previousRightEncoderTicks = rightEncoderTicks;
        this->prevTime = currentTime;

    }

    float CalculateLinearSpeedForWheel(int currentEncoderTicks, int previousEncoderTicks, std::chrono::milliseconds timeBetweenMeasurements)
    {

        float RPM = CalculateRotationalSpeedForWheel(currentEncoderTicks, previousEncoderTicks, timeBetweenMeasurements);
        float angularVelocity = (RPM/60) * 2*PI;
        float linearValocity = angularVelocity * (wheelDiameterInMeters/2);
        return linearValocity;
    }

    float CalculateRotationalSpeedForWheel(int currentEncoderTicks, int previousEncoderTicks, std::chrono::milliseconds timeBetweenMeasurements)
    {
        float timeBetweenInSeconds = float(timeBetweenMeasurements.count()) / 1000.0;
        float RPM = ((float(currentEncoderTicks - previousEncoderTicks) ) / float(this->encoderTicksPerRevolution)) / timeBetweenInSeconds * 60;
        return RPM;
    }

    float CalculateWheelDistance(int currentEncoderTicks, int previousEncoderTicks, int ticksPerFullRotation )
    {
        return PI*(this->wheelDiameterInMeters) * float(currentEncoderTicks - previousEncoderTicks) / float(ticksPerFullRotation);
    }
};