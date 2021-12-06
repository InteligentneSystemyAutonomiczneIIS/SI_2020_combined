#pragma once

#include "TeensyTimerTool.h"
#include <Encoder.h>
#include <memory>
#include <chrono>

class Axle
{
private:
    // configurable params (defaults)
    int encoderTicksPerRevolution = 354; // 352 - 356; average, can be slightly different for left and right wheels
    float wheelDiameterInMM = 120.0; // 118.1 - 122.2 milimeters

    float currentRotationalSpeed = 0;
    float currentLinearSpeed = 0;
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
        setWheelsDiameter(wheelDiameterInMilimeters);
        setEncoderTicksPerWheelRevolution(encoderTicksPerRevolution);
    }

    void setWheelsDiameter(float wheelDiameterInMilimeters )
    {
        this->wheelDiameterInMM = wheelDiameterInMilimeters;
    }

    void setEncoderTicksPerWheelRevolution(float encoderTicksPerRevolution)
    {
        this->encoderTicksPerRevolution = encoderTicksPerRevolution;
    }

    void setupEncoders(int pinLeft1, int pinLeft2,  int pinRight1, int pinRight2)
    {
        leftWheelEncoder = std::make_unique<Encoder>(pinLeft1, pinLeft2);
        rightWheelEncoder = std::make_unique<Encoder>(pinRight1, pinRight2);
    }

    void initialize()
    {
        this->currentRotationalSpeed = 0;
        this->currentLinearSpeed = 0;

        encoderCheckTimer = TeensyTimerTool::PeriodicTimer(TeensyTimerTool::TCK32);
        encoderCheckTimer.begin([this] {this->encoderCheck();}, encoderCheckInterval);

        this->prevTime = millis();
    }

    float getCurrentLinearSpeed()
    {
        return currentLinearSpeed;
    }

    float getCurrentRotationalSpeed()
    {
        return currentRotationalSpeed;
    }

    std::tuple<int32_t, int32_t> GetEncoderTicks()
    {
        return std::tuple<int32_t, int32_t>(previousLeftEncoderTicks, previousRightEncoderTicks);
    }

private:

    //make sure executon will not take longer than encoderCheckInterval, that might cause problems
    void encoderCheck()
    {
        unsigned long currentTime = millis();
        int leftEncoderTicks = leftWheelEncoder->read();
        int rightEncoderTicks = rightWheelEncoder->read();

        this->currentLinearSpeed = calculateAverageLinearSpeed(leftEncoderTicks, rightEncoderTicks, std::chrono::milliseconds(currentTime - prevTime));
        this->currentRotationalSpeed = calculateAverageRotationalSpeed(leftEncoderTicks, rightEncoderTicks, std::chrono::milliseconds(currentTime - prevTime));


        previousLeftEncoderTicks = leftEncoderTicks;
        previousRightEncoderTicks = rightEncoderTicks;
        this->prevTime = currentTime;

    }

    // Linear speed (m/s)
    float calculateAverageLinearSpeed(int leftEncoderTicks, int rightEncoderTicks, std::chrono::milliseconds timeBetweenMeasurements)
    {

        float leftWheelSpeed = calculateLinearSpeedForWheel(leftEncoderTicks, this->previousLeftEncoderTicks, timeBetweenMeasurements, this->encoderTicksPerRevolution, this->wheelDiameterInMM);
        float rightWheelSpeed = calculateLinearSpeedForWheel(rightEncoderTicks, this->previousRightEncoderTicks, timeBetweenMeasurements, this->encoderTicksPerRevolution, this->wheelDiameterInMM);

        return (leftWheelSpeed + rightWheelSpeed) / 2;

    }

    float calculateLinearSpeedForWheel(int currentEncoderTicks, int previousEncoderTicks, std::chrono::milliseconds timeBetweenMeasurements, int ticksPerFullRotation, float wheelDiameterInMM)
    {

        float RPM = calculateRotationalSpeedForWheel(currentEncoderTicks, previousEncoderTicks, timeBetweenMeasurements, ticksPerFullRotation);
        float angularVelocity = (RPM/60) * 2*PI;
        float linearValocity = angularVelocity * (wheelDiameterInMM/1000/2);
        return linearValocity;

    }

    // Rotational Speed (RPM)
    float calculateAverageRotationalSpeed(int leftEncoderTicks, int rightEncoderTicks, std::chrono::milliseconds timeBetweenMeasurements)
    {
        float leftWheelSpeed = calculateRotationalSpeedForWheel(leftEncoderTicks, this->previousLeftEncoderTicks, encoderCheckInterval, this->encoderTicksPerRevolution);
        float rightWheelSpeed = calculateRotationalSpeedForWheel(rightEncoderTicks, this->previousRightEncoderTicks, encoderCheckInterval, this->encoderTicksPerRevolution);

        return (leftWheelSpeed + rightWheelSpeed) / 2;

    }

    float calculateRotationalSpeedForWheel(int currentEncoderTicks, int previousEncoderTicks, std::chrono::milliseconds timeBetweenMeasurements, int ticksPerFullRotation)
    {

        float timeBetweenInSeconds = float(timeBetweenMeasurements.count()) / 1000.0;
        float RPM = ((float(currentEncoderTicks) - float(previousEncoderTicks) ) / float(ticksPerFullRotation)) / timeBetweenInSeconds * 60;
        return RPM;

    }
};