/*
 * Oprogramowanie testowe dla modeli autek
 * Blok obieralny: Inteligentne Systemy Autonomiczne (ISA)
 * Politechnika Łódzka, WEEIiA, IIS
 * Autor: Tomasz Jaworski, Paweł Kapusta, 2017-2020
 */


#pragma once


/*
 * Silniki, wejście enkoderowe
 *
 */
#define ENCODER_REAR_LEFT_1	14	// Enkoder lewej strony
#define ENCODER_REAR_LEFT_2	15	// Enkoder lewej strony
#define ENCODER_REAR_RIGHT_1	16	// Enkoder prawej strony	
#define ENCODER_REAR_RIGHT_2	17	// Enkoder prawej strony	
	
 
/*
 * Czujniki odległości
 * Moduł HC-SR04
*/

#define US_MIDDLE				0
#define US_MIDDLE_TRIGGER_PIN	11
#define US_MIDDLE_ECHO_PIN		10

#define US_LEFT					1
#define US_LEFT_TRIGGER_PIN		24
#define US_LEFT_ECHO_PIN		12

#define US_RIGHT				2
#define US_RIGHT_TRIGGER_PIN	9
#define US_RIGHT_ECHO_PIN		8
 
enum UltraSoundSensor {
	Front = 0,
	Left = 1,
	Right = 2,
	
	__first = Front,
	__last = Right,
	
	All,
};
 
int ultrasound_trigger_pin[] = {
	[UltraSoundSensor::Front]	= US_MIDDLE_TRIGGER_PIN,
	[UltraSoundSensor::Left]	= US_LEFT_TRIGGER_PIN,
	[UltraSoundSensor::Right]	= US_RIGHT_TRIGGER_PIN,
};

 
int ultrasound_echo_pin[] = {
	[UltraSoundSensor::Front]	= US_MIDDLE_ECHO_PIN,
	[UltraSoundSensor::Left]	= US_LEFT_ECHO_PIN,
	[UltraSoundSensor::Right]	= US_RIGHT_ECHO_PIN,
};
