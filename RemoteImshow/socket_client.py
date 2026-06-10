import json
import socket
import struct
import threading
import time

import cv2
import numpy as np

from Gamepad import GamepadState


SOCKET_TIMEOUT_SECONDS = 1.0
VIDEO_TARGET_FPS = 30
VIDEO_REGISTRATION_INTERVAL_SECONDS = 1.0
VIDEO_CLIENT_BUFFER_SIZE = 65536
RECONNECT_DELAY_SECONDS = 1.0
CONTROL_HEARTBEAT_HZ = 40

VIDEO_HELLO_PACKET = b"h"
VIDEO_FRAME_PACKET_TYPE = b"v"
CONTROL_PACKET_TYPE = b"d"

VIDEO_HEADER_FORMAT = "!cIQIHH"
CONTROL_HEADER_FORMAT = "!cQQI"
VIDEO_HEADER_SIZE = struct.calcsize(VIDEO_HEADER_FORMAT)


class VideoClient:
    def __init__(self, host, video_port, gamepad_port):
        self.host = host
        self.video_port = video_port
        self.gamepad_port = gamepad_port
        self.gamepad_state = GamepadState()
        self.shutdown_event = threading.Event()
        self.video_socket = None
        self.gamepad_socket = None
        self.video_socket_lock = threading.Lock()
        self.gamepad_socket_lock = threading.Lock()
        self.latest_frame_lock = threading.Lock()
        self.latest_frame_sequence = -1
        self.latest_frame_bytes = None
        self.control_sequence = 0

        self.connect_video_socket()
        self.connect_gamepad_socket()

        threading.Thread(target=self.video_registration_loop, daemon=True).start()
        threading.Thread(target=self.receive_video, daemon=True).start()
        threading.Thread(target=self.display_video, daemon=True).start()
        threading.Thread(target=self.send_gamepad_data, daemon=True).start()

        self.keep_alive()

    def keep_alive(self):
        while not self.shutdown_event.is_set():
            time.sleep(1)

    def connect_video_socket(self):
        with self.video_socket_lock:
            if self.video_socket is not None:
                self.video_socket.close()

            self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.video_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.video_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
            self.video_socket.bind(("", 0))

        self.send_video_registration()
        print(f"Video UDP socket ready for {self.host}:{self.video_port}")

    def connect_gamepad_socket(self):
        while not self.shutdown_event.is_set():
            try:
                gamepad_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                gamepad_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
                gamepad_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                gamepad_socket.connect((self.host, self.gamepad_port))
                with self.gamepad_socket_lock:
                    if self.gamepad_socket is not None:
                        self.gamepad_socket.close()
                    self.gamepad_socket = gamepad_socket
                print(f"Connected to gamepad server at {self.host}:{self.gamepad_port}")
                return
            except OSError:
                time.sleep(RECONNECT_DELAY_SECONDS)

    def send_video_registration(self):
        with self.video_socket_lock:
            if self.video_socket is None:
                return

            try:
                self.video_socket.sendto(VIDEO_HELLO_PACKET, (self.host, self.video_port))
            except OSError:
                pass

    def video_registration_loop(self):
        while not self.shutdown_event.is_set():
            self.send_video_registration()
            time.sleep(VIDEO_REGISTRATION_INTERVAL_SECONDS)

    def receive_video(self):
        assembling_frame = None

        while not self.shutdown_event.is_set():
            try:
                with self.video_socket_lock:
                    if self.video_socket is None:
                        raise OSError
                    packet, _addr = self.video_socket.recvfrom(VIDEO_CLIENT_BUFFER_SIZE)
            except socket.timeout:
                continue
            except OSError:
                time.sleep(RECONNECT_DELAY_SECONDS)
                self.connect_video_socket()
                assembling_frame = None
                continue

            if len(packet) < VIDEO_HEADER_SIZE:
                continue

            packet_type, frame_sequence, _timestamp_ns, frame_size, chunk_index, chunk_count = struct.unpack(
                VIDEO_HEADER_FORMAT,
                packet[:VIDEO_HEADER_SIZE],
            )
            if packet_type != VIDEO_FRAME_PACKET_TYPE:
                continue

            chunk_payload = packet[VIDEO_HEADER_SIZE:]

            if assembling_frame is None or frame_sequence > assembling_frame["sequence"]:
                assembling_frame = {
                    "sequence": frame_sequence,
                    "frame_size": frame_size,
                    "chunk_count": chunk_count,
                    "chunks": {},
                }

            if frame_sequence < assembling_frame["sequence"]:
                continue

            assembling_frame["chunks"][chunk_index] = chunk_payload
            if len(assembling_frame["chunks"]) != assembling_frame["chunk_count"]:
                continue

            frame_data = bytearray()
            for index in range(assembling_frame["chunk_count"]):
                chunk = assembling_frame["chunks"].get(index)
                if chunk is None:
                    frame_data = None
                    break
                frame_data.extend(chunk)

            if frame_data is None:
                continue

            complete_frame = bytes(frame_data[:assembling_frame["frame_size"]])
            with self.latest_frame_lock:
                if frame_sequence > self.latest_frame_sequence:
                    self.latest_frame_sequence = frame_sequence
                    self.latest_frame_bytes = complete_frame

            assembling_frame = None

    def display_video(self):
        last_displayed_sequence = -1

        while not self.shutdown_event.is_set():
            with self.latest_frame_lock:
                frame_sequence = self.latest_frame_sequence
                frame_bytes = self.latest_frame_bytes

            if frame_bytes is None or frame_sequence <= last_displayed_sequence:
                time.sleep(1.0 / VIDEO_TARGET_FPS)
                continue

            frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                time.sleep(0.01)
                continue

            cv2.imshow("Video Stream", frame)
            cv2.waitKey(1)
            last_displayed_sequence = frame_sequence

    def get_current_state(self):
        axes, triggers, buttons = self.gamepad_state.get_state()
        return {
            "axes": list(axes),
            "triggers": list(triggers),
            "buttons": list(buttons),
        }

    def send_gamepad_data(self):
        target_period = 1.0 / CONTROL_HEARTBEAT_HZ
        next_send_time = time.perf_counter()

        while not self.shutdown_event.is_set():
            next_send_time += target_period
            gamepad_data = self.get_current_state()
            payload = json.dumps(gamepad_data, separators=(",", ":")).encode("utf-8")
            self.control_sequence += 1
            header = struct.pack(
                CONTROL_HEADER_FORMAT,
                CONTROL_PACKET_TYPE,
                self.control_sequence,
                time.time_ns(),
                len(payload),
            )
            packet = header + payload

            try:
                with self.gamepad_socket_lock:
                    if self.gamepad_socket is None:
                        raise OSError
                    self.gamepad_socket.sendall(packet)
            except (ConnectionResetError, BrokenPipeError, OSError):
                self.connect_gamepad_socket()
                next_send_time = time.perf_counter()
                continue

            remaining_delay = next_send_time - time.perf_counter()
            if remaining_delay > 0:
                time.sleep(remaining_delay)
            else:
                next_send_time = time.perf_counter()


if __name__ == "__main__":
    VideoClient("10.24.224.110", 8889, 8890)
