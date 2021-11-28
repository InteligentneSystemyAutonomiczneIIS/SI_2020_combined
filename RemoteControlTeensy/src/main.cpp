#include <Arduino.h>
/*
This code is based on the examples at http://forum.arduino.cc/index.php?topic=396450
*/


// Example 5 - parsing text and numbers with start and end markers in the stream

#include "variables.h"
#include "functions.hpp"


float YawCalibrationCenter = 80.0f;
float PitchCalibrationCenter = 58.0f;

const byte numChars = 64;
char receivedChars[numChars];
char tempChars[numChars];        // temporary array for use when parsing

dataPacket packet;


boolean newData = false;


float leftSide = 0;
float rightSide = 0;

float yawPos = YawCalibrationCenter;
float pitchPos = PitchCalibrationCenter;


//============

//============

void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static byte ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;

    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();

        if (recvInProgress == true) {
            if (rc != endMarker) {
                receivedChars[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else {
                receivedChars[ndx] = '\0'; // terminate the string
                recvInProgress = false;
                ndx = 0;
                newData = true;
            }
        }

        else if (rc == startMarker) {
            recvInProgress = true;
        }
    }
}

//============

dataPacket parseData() {      // split the data into its parts

    dataPacket tmpPacket;

    char * strtokIndx; // this is used by strtok() as an index

    strtokIndx = strtok(tempChars,",");      // get the first part - the string
    strcpy(tmpPacket.message, strtokIndx); // copy it to messageFromPC

    strtokIndx = strtok(NULL, ","); // this continues where the previous call left off
    tmpPacket.first = atof(strtokIndx);

    strtokIndx = strtok(NULL, ",");
    tmpPacket.second = atof(strtokIndx);

    return tmpPacket;
}


void showParsedData(dataPacket packet) {
    Serial.print("Message ");
    Serial.println(packet.message);
    Serial.print("Yaw ");
    Serial.println(packet.first);
    Serial.print("Pitch ");
    Serial.println(packet.second);
}

void setup() {

    initSerial(115200);
    Serial.println("This demo expects 3 pieces of data - text, an integer and a floating point value");
    Serial.println("Enter data in this style <HelloWorld, 12, 24.7>  ");
    Serial.println();

    initMotors();

    // Each platform has to do this independently, checked manually
    calibrateServo(ServoSelector::Yaw, (int)YawCalibrationCenter);
    calibrateServo(ServoSelector::Pitch, (int)PitchCalibrationCenter);

    initServos();
    centerServos();

    Brake();
    delay(500);

    // Serial.println("Initalization ended");

}

//============

void loop() {
      
    // parse input data
    recvWithStartEndMarkers();

    if (newData == true) {
        strcpy(tempChars, receivedChars);
            // this temporary copy is necessary to protect the original data
            //   because strtok() used in parseData() replaces the commas with \0
        packet = parseData();
        // showParsedData(packet);
        
        if (strcmp(packet.message, "stop") == 0)
        {
            Brake();
            isStopped = true;
        }
        if (strcmp(packet.message, "start") == 0)
        {
            Brake();
            isStopped = false;
        }

        if (strcmp(packet.message, "motor") == 0)
        {
            if (isStopped == false)
            {
                leftSide = packet.first;
                rightSide = packet.second;

                SetPowerLevel(EngineSelector::Left, leftSide, 200);
                SetPowerLevel(EngineSelector::Right, rightSide, 200);
            }
        }

        if (strcmp(packet.message, "servo") == 0)
        {
            yawPos = packet.first;
            pitchPos = packet.second;

            moveServo(ServoSelector::Yaw, yawPos);
            moveServo(ServoSelector::Pitch, pitchPos);
        }

        newData = false;
    }
}

