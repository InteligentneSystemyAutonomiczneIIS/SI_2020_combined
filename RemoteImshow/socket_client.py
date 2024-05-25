import socket
import cv2
import numpy as np
import struct
import json
import threading
from Gamepad import GamepadState
import time

class VideoClient:
    def __init__(self, host, video_port, gamepad_port):
        self.usingJetson = True 
        self.host = host
        self.video_port = video_port
        self.gamepad_port = gamepad_port
        self.gamepad_state = GamepadState()

        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gamepad_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.connect_to_server()

        video_thread = threading.Thread(target=self.receive_video, daemon=True)
        gamepad_thread = threading.Thread(target=self.send_gamepad_data, daemon=True)
        video_thread.start()
        gamepad_thread.start()
        
        
        # Keep the main thread alive
        self.keep_alive()

    def keep_alive(self):
        while True:
            time.sleep(1)

    def connect_to_server(self):
        try:
            self.video_socket.connect((self.host, self.video_port))
            print(f"Connected to video server at {self.host}:{self.video_port}")
        except ConnectionRefusedError:
            print(f"Failed to connect to video server at {self.host}:{self.video_port}")

        try:
            self.gamepad_socket.connect((self.host, self.gamepad_port))
            print(f"Connected to gamepad server at {self.host}:{self.gamepad_port}")
        except ConnectionRefusedError:
            print(f"Failed to connect to gamepad server at {self.host}:{self.gamepad_port}")

    def receive_video(self):
        payload_size = struct.calcsize("!Q")
        while True:
            try:
                data_type = self.video_socket.recv(1)
                if not data_type:
                    break

                if data_type == b'v':
                    frame_size_data = self.video_socket.recv(payload_size)
                    if not frame_size_data:
                        break

                    frame_size = struct.unpack("!Q", frame_size_data)[0]
                    encoded_frame = b''
                    while len(encoded_frame) < frame_size:
                        packet = self.video_socket.recv(frame_size - len(encoded_frame))
                        if not packet:
                            break
                        encoded_frame += packet

                    if not encoded_frame:
                        break

                    frame = cv2.imdecode(np.frombuffer(encoded_frame, np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        cv2.imshow('Video Stream', frame)
                        cv2.waitKey(1)
            except (ConnectionResetError, BrokenPipeError):
                print("Video server disconnected. Reconnecting...")
                self.video_socket.close()
                self.connect_to_server()

    def send_gamepad_data(self):
        
        target_fps = 120  # Target frames per second
        target_delay = 1.0 / target_fps  # Delay between each iteration (in seconds)
        
        while True:
            start_time = time.perf_counter()  # Get the current time with high precision
            axes, triggers, buttons = self.gamepad_state.get_state()
            gamepad_data = {
                "axes": axes,
                "triggers": triggers,
                "buttons": buttons
            }
            encoded_data = json.dumps(gamepad_data).encode()
            data_type = b'd'
            data_length = struct.pack("!Q", len(encoded_data))
            packet = data_type + data_length + encoded_data
            try:
                self.gamepad_socket.sendall(packet)
            except (ConnectionResetError, BrokenPipeError):
                print("Gamepad server disconnected. Reconnecting...")
                self.gamepad_socket.close()
                self.connect_to_server()
            
            end_time = time.perf_counter()  # Get the current time after sending the data
            loop_time = end_time - start_time  # Calculate the time taken by the loop body

            # Delay to maintain the target frame rate
            remaining_delay = target_delay - loop_time
            if remaining_delay > 0:
                print("sleeping for : ", remaining_delay)
                time.sleep(remaining_delay)

# Example usage
# video_client = VideoClient('192.168.1.104', 8889, 8890)
video_client = VideoClient('192.168.1.23', 8889, 8890)
