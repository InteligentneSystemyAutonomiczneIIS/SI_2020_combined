import socket
import cv2
import numpy as np
import struct
import json
import threading
from collections import deque
from imutils.video import JetsonVideoStream
import time

import signal
import sys

import serial 




class SerialCommunicator:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate

        self.ser = serial.Serial(self.port, self.baudrate, timeout=0.05)

    def _calculate_checksum(self, command, data_length, data):
        content = command + str(data_length).zfill(2) + data
        checksum = sum(ord(ch) for ch in content) % 256
        return f"{checksum:02X}".upper()

    def _create_packet(self, command, data):
        data_length = len(data)
        checksum = self._calculate_checksum(command, data_length, data)
        packet = f"<{command};{data_length:02};{data};{checksum}>"
        return packet
    

    def sendCommand(self, commandString, dataList):
        dataString = ','.join(map(str, dataList))  # Convert list to string with comma as delimiter
        packet = self._create_packet(commandString, dataString)
        binary_packet = packet.encode()

        self.ser.write(binary_packet)



class GamepadTeensyController:
    def __init__(self):
        self.gamepadType = "Xbox 360"
        self.ser = SerialCommunicator("/dev/ttyACM0", 115200)

    def parseData(self, axes, triggers, buttons):
        steering = round(float(axes[2]), 2)
        speed = round(float(triggers[1]) - float(triggers[0]), 2)
        pitch = round(float(axes[1]),2)
        yaw = round(float(axes[0]),2)

        self.sendData(steering, speed, pitch, yaw)

    def sendData(self, steering, speed, pitch, yaw ):
        self.ser.sendCommand("steering", [steering])
        self.ser.sendCommand("speed", [speed])
        self.ser.sendCommand("servos", [pitch, yaw])
        
        # test data:
        # <speed;04;0.75;3F>
        # <servos;08;0.5,-0.5;98>
        # <steering;05;-0.25;B8>



class VideoServer:
    def __init__(self, host, video_port, gamepad_port):
        self.usingJetson = True
        self.host = host
        self.video_port = video_port
        self.gamepad_port = gamepad_port
        self.video_socket = None
        self.gamepad_socket = None
        self.video_clients = []
        self.gamepad_clients = []
        self.received_data_queue = deque()
        self.isDebugVideoShow = False

        self.teensyController = GamepadTeensyController()

        self.init_video_system()
        
        self.start_server()

        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Keep the main thread alive
        self.keep_alive()

    def keep_alive(self):
        while True:
            time.sleep(1)


    def init_video_system(self):
        if self.usingJetson:
            width = 848
            height = 480
            frameResolution = (width, height)
            self.video_capture = JetsonVideoStream(outputResolution=frameResolution).start()
            time.sleep(2)
        else:
            self.video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)


    def start_server(self):
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_socket.bind((self.host, self.video_port))
        self.video_socket.listen(5)
        print(f"Video server listening on {self.host}:{self.video_port}")

        self.gamepad_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gamepad_socket.bind((self.host, self.gamepad_port))
        self.gamepad_socket.listen(5)
        print(f"Gamepad server listening on {self.host}:{self.gamepad_port}")

        video_thread = threading.Thread(target=self.handle_video_clients, daemon=True)
        gamepad_thread = threading.Thread(target=self.handle_gamepad_clients, daemon=True)
        video_thread.start()
        gamepad_thread.start()

    def handle_video_clients(self):
        while True:
            client_socket, addr = self.video_socket.accept()
            print(f"Video client connected from {addr}")
            client_thread = threading.Thread(target=self.video_streaming, args=(client_socket,), daemon=True)
            client_thread.start()
            self.video_clients.append(client_socket)

    def handle_gamepad_clients(self):
        while True:
            client_socket, addr = self.gamepad_socket.accept()
            print(f"Gamepad client connected from {addr}")
            client_thread = threading.Thread(target=self.gamepad_communication, args=(client_socket,), daemon=True)
            client_thread.start()
            self.gamepad_clients.append(client_socket)


    def video_streaming(self, client_socket):
        try:
            while True:
                # Capture frame from the camera
                frame = self.video_capture.read()

                if frame is None:
                    break

                # Encode the frame as JPEG
                _, encoded_frame = cv2.imencode('.jpg', frame)

                if self.isDebugVideoShow:
                    cv2.imshow('frame', frame)
                    cv2.waitKey(1)

                data_type = b'v'
                frame_size = len(encoded_frame)
                packet = data_type + struct.pack("!Q", frame_size) + encoded_frame.tobytes()
                client_socket.sendall(packet)
        # except (ConnectionResetError, BrokenPipeError):
        except:
            print(f"Video client disconnected")
            self.video_clients.remove(client_socket)
            client_socket.close()

    def gamepad_communication(self, client_socket):
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                data_type = data[0:1]
                if data_type == b'd':
                    data_length = struct.unpack("!Q", data[1:9])[0]
                    encoded_data = data[9:9 + data_length]
                    gamepad_data = json.loads(encoded_data.decode())
                    axes = gamepad_data.get("axes", [])
                    triggers = gamepad_data.get("triggers", [])
                    buttons = gamepad_data.get("buttons", [])
                    print(f"Received gamepad data: Axes={axes}, Triggers={triggers}, Buttons={buttons}")
                    self.teensyController.parseData(axes, triggers, buttons)
                    
                    # self.received_data_queue.append(gamepad_data)

                    
        # except (ConnectionResetError, BrokenPipeError):
        except:
            print(f"Gamepad client disconnected")
            self.gamepad_clients.remove(client_socket)
            client_socket.close()


    def signal_handler(self, sig, frame):
        print(f"Received signal {sig}, cleaning up resources...")
        self.cleanup_resources()
        sys.exit(0)

    def cleanup_resources(self):
        # Close video capture
        if self.usingJetson:
            self.video_capture.stop()
        else:
            self.video_capture.release()

        # Close sockets
        for client_socket in self.video_clients:
            client_socket.close()
        self.video_socket.close()

        for client_socket in self.gamepad_clients:
            client_socket.close()
        self.gamepad_socket.close()

        # Clean up any other resources here

        print("Resources cleaned up successfully.")


if __name__ == "__main__":



    # Example usage
    video_server = VideoServer('0.0.0.0', 8889, 8890)
