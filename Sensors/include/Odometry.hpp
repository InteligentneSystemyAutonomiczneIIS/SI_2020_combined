// // TeensyTimerTools: https://github.com/luni64/TeensyTimerTool.git

#pragma once

#include "TeensyTimerTool.h"
#include <Axle.hpp>
#include <chrono>
#include <ISAMobile.h>

class Odometry
{
private:
    Axle rearAxle; // initialize using default values - not always correct for all platforms
    float x = 0;
    float y = 0;
    float theta = 0;

    float leftWheelPreviousDistance = 0.0f;
    float rightWheelPreviousDistance = 0.0f;


    TeensyTimerTool::PeriodicTimer positionCalculationTimer; //can be programmed without timers
    std::chrono::milliseconds positionCheckInterval = 100ms;
public:
    Odometry()
    {


    }

    void Initialize()
    {
        rearAxle.Initialize();
        rearAxle.SetupEncoders(ENCODER_REAR_LEFT_1, ENCODER_REAR_LEFT_2, 
                               ENCODER_REAR_RIGHT_1, ENCODER_REAR_RIGHT_2);
        positionCalculationTimer = TeensyTimerTool::PeriodicTimer(TeensyTimerTool::TCK64);
        positionCalculationTimer.begin([this] {this->Update();}, positionCheckInterval);

    }

    void ResetPosition()
    {
        this->x = 0.0f;
        this->y = 0.0f;
        this->theta = 0.0f;
    }

    // returns x, y, theta
    std::tuple<float, float, float> GetPosition()
    {
        return std::make_tuple(this->x, this->y, this->theta);
    }

    float GetLinearSpeedSimplified()
    {
        return rearAxle.GetCurrentLinearSpeed();
    }

    float GetRPMSimplified()
    {
        return rearAxle.GetCurrentRotationalSpeed();
    }

    std::tuple<int32_t, int32_t> GetRawEncoderTicks()
    {
        return rearAxle.GetEncoderTicks();
    }

    
private:

    void Update()
    {
        float leftDistance = 0.0f;
        float rightDistance = 0.0f;

        std::tie(leftDistance, rightDistance) = rearAxle.GetCurrentWheelDistance();

        // Serial.println("Left: " + String(leftDistance) + " Right: " + String(rightDistance));

        float deltaLeftDistance = leftDistance - leftWheelPreviousDistance;
        float deltaRightDistance = rightDistance - rightWheelPreviousDistance;

        CalculateOdometry(deltaLeftDistance, deltaRightDistance);

        leftWheelPreviousDistance = leftDistance;
        rightWheelPreviousDistance = rightDistance;

    }

    void CalculateOdometry(float leftDistance, float rightDistance)
    {
        float centerDistance = (rightDistance + leftDistance) / 2;
        this->x = this->x + centerDistance * cos(this->theta);
        this->y = this->y + centerDistance * sin(this->theta);
        this->theta = fmodf(this->theta + (rightDistance - leftDistance) / this->rearAxle.GetAxleLength(), 2*PI );
        this->theta = this->theta < 0 ? 2 * M_PI + this->theta : this->theta;
    }



};