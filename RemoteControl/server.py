from websocket_server import WebsocketServer
import serial
import json
import time

# for debgging purposes - set to False when testing (no commands to Teensy)
useSerial = True

# serial communication initialization
if useSerial:
	ser = serial.Serial(port='/dev/ttyACM1', baudrate=115200, timeout=0.05)
	time.sleep(2)

direction = 1
isStopped = True
servoPosYaw = 90 # yaw
servoPosPitch = 90 # pitch

motorDeadzone = 20
steeringDeadzone = 45

def stopMotors():
	print("Stopping motors")
	if useSerial:
		packet = '<motor, {}, {}>'.format(0, 0)
		packetBytes = bytes(packet, 'utf-8')
		ser.write(packetBytes)


# Called for every client connecting (after handshake)
def new_client(client, server):
	print("New client connected and was given id %d" % client['id'])
	server.send_message_to_all("Hey all, a new client has joined us")
	
	stopMotors()
	global isStopped
	isStopped = True


# Called for every client disconnecting
def client_left(client, server):
	print("Client(%d) disconnected" % client['id'], ".Stop motors")
	packet = '<motor, {}, {}>'.format(0, 0)
	packetBytes = bytes(packet, 'utf-8')
	if useSerial:
		ser.write(packetBytes)
	global isStopped
	isStopped = True

def calculateMotorValues(gas, brake, steering, direction):
			
	motorLeft = direction * min(255, max(0,(gas-brake))) #gas-brake -> single acceleration axis
	motorRight = direction * min(255, max(0,(gas-brake)))  #gas-brake -> single acceleration axis

	if steering < 0:
		modifier = - min(abs(steering), abs(motorLeft))
		motorLeft += direction*modifier
	else:
		modifier = min(abs(steering), abs(motorLeft))
		motorRight -= direction*modifier
	
	if -motorDeadzone <= motorRight <= motorDeadzone:
		motorRight = 0
	if -motorDeadzone <= motorLeft <= motorDeadzone:
		motorLeft = 0

	return motorLeft, motorRight


def parseControllerCommands(message):
	messageDict = json.loads(message)
	global direction
	global isStopped
	global servoPosYaw
	global servoPosPitch

	if messageDict['btn_2'] == 1:
		isStopped = False
	if messageDict['btn_1'] == 1:
		isStopped = True

	if not isStopped:
		steering = messageDict['steering']
		if -steeringDeadzone <= steering <= steeringDeadzone:
			steering = 0
		gas = messageDict['gas']
		brake = messageDict['brake']
		
		if messageDict['gear_up'] == 1:
			direction = 1
		elif messageDict['gear_down'] == 1:
			direction = -1

		motorLeft, motorRight = calculateMotorValues(gas, brake, steering, direction)
		
		packet = '<motor,{},{}>'.format(motorLeft, motorRight)
		packetBytes = bytes(packet, 'utf-8')
		print(packet)
		
		if useSerial:	
			ser.write(packetBytes)
	else:
		packet = '<motor,{},{}>'.format(0, 0)
		packetBytes = bytes(packet, 'utf-8')
		if useSerial:	
			ser.write(packetBytes)

	hat_x = messageDict["hat_x"]
	if hat_x != 0:		
		servoPosYaw = (servoPosYaw + 5*hat_x) if 0 <= (servoPosYaw + hat_x) <= 180 else servoPosYaw 
	
	hat_y = messageDict["hat_y"]
	if messageDict["hat_y"] != 0:
		servoPosPitch = (servoPosPitch + 5*hat_y) if 0 <= (servoPosPitch + hat_y) <= 180 else servoPosPitch 

	packet = '<servo,{},{}>'.format(servoPosYaw, servoPosPitch)
	packetBytes = bytes(packet, 'utf-8')
	print(packet)
	if useSerial:	
		ser.write(packetBytes)
	


# Called when a client sends a message
def message_received(client, server, message):
	if len(message) > 200:
		message = message[:200]+'..'
	# print("Client(%d) said: %s" % (client['id'], message))
	parseControllerCommands(message)


if __name__ == "__main__":
	PORT=8084

	stopMotors()
	server = WebsocketServer(host='10.24.224.216', port=PORT)
	# server = WebsocketServer(host='0.0.0.0', port=PORT)
	server.set_fn_new_client(new_client)
	server.set_fn_client_left(client_left)
	server.set_fn_message_received(message_received)
	server.run_forever()

