#pragma once

#include "TeensyTimerTool.h"
#include <Encoder.h>
#include <memory>

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
        return std::tuple<int32_t, int32_t>(leftWheelEncoder->read(), rightWheelEncoder->read());
    }

private:
    // Linear speed (m/s)
    float calculateAverageLinearSpeed()
    {

    }

    float calculateLinearSpeedForLeftWheel()
    {

    }

    float calculateLinearSpeedForRightWheel()
    {

    }

    // Rotational Speed (RPM)
    float calculateAverageRotationalSpeed()
    {

    }
    float calculateRotationalSpeedForLeftWheel()
    {

    }

    float calculateRotationalSpeedForRightWheel()
    {

    }
};