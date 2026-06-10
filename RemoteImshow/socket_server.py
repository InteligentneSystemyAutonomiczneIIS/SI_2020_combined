import json
import signal
import socket
import struct
import sys
import threading
import time

import cv2
import serial
from imutils.video import JetsonVideoStream


VIDEO_CLIENT_TIMEOUT_SECONDS = 5.0
SOCKET_TIMEOUT_SECONDS = 1.0
RECV_BUFFER_SIZE = 65536
VIDEO_TARGET_FPS = 30
VIDEO_JPEG_QUALITY = 80
MAX_VIDEO_PACKET_SIZE = 1300

VIDEO_HELLO_PACKET = b"h"
VIDEO_FRAME_PACKET_TYPE = b"v"
CONTROL_PACKET_TYPE = b"d"

VIDEO_HEADER_FORMAT = "!cIQIHH"
CONTROL_HEADER_FORMAT = "!cQQI"
VIDEO_HEADER_SIZE = struct.calcsize(VIDEO_HEADER_FORMAT)
CONTROL_HEADER_SIZE = struct.calcsize(CONTROL_HEADER_FORMAT)
MAX_VIDEO_CHUNK_SIZE = MAX_VIDEO_PACKET_SIZE - VIDEO_HEADER_SIZE


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
        return f"<{command};{data_length:02};{data};{checksum}>"

    def send_command(self, command_string, data_list):
        data_string = ",".join(map(str, data_list))
        packet = self._create_packet(command_string, data_string)
        self.ser.write(packet.encode())


class GamepadTeensyController:
    def __init__(self):
        self.gamepad_type = "Xbox 360"
        self.serial_communicator = SerialCommunicator("/dev/ttyACM0", 115200)

    def parse_data(self, axes, triggers, buttons):
        del buttons

        if len(axes) < 4 or len(triggers) < 2:
            return

        steering = round(float(axes[0]), 2)
        speed = round(float(triggers[1]) - float(triggers[0]), 2)
        pitch = -round(float(axes[3]), 2)
        yaw = round(float(axes[2]), 2)

        self.send_data(steering, speed, pitch, yaw)

    def send_data(self, steering, speed, pitch, yaw):
        self.serial_communicator.send_command("steering", [steering])
        self.serial_communicator.send_command("speed", [speed])
        self.serial_communicator.send_command("servos", [pitch, yaw])


class VideoServer:
    def __init__(self, host, video_port, gamepad_port):
        self.using_jetson = True
        self.host = host
        self.video_port = video_port
        self.gamepad_port = gamepad_port
        self.video_socket = None
        self.gamepad_socket = None
        self.video_clients = {}
        self.video_clients_lock = threading.Lock()
        self.is_debug_video_show = False
        self.shutdown_event = threading.Event()
        self.video_sequence = 0
        self.last_control_sequence = -1
        self.last_control_sequence_lock = threading.Lock()

        self.teensy_controller = GamepadTeensyController()

        self.init_video_system()
        self.start_server()

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.keep_alive()

    def keep_alive(self):
        while not self.shutdown_event.is_set():
            time.sleep(1)

    def init_video_system(self):
        if self.using_jetson:
            frame_resolution = (848, 480)
            self.video_capture = JetsonVideoStream(outputResolution=frame_resolution).start()
            time.sleep(2)
        else:
            self.video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    def start_server(self):
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.video_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.video_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
        self.video_socket.bind((self.host, self.video_port))
        print(f"Video UDP server listening on {self.host}:{self.video_port}")

        self.gamepad_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.gamepad_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.gamepad_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
        self.gamepad_socket.bind((self.host, self.gamepad_port))
        self.gamepad_socket.listen(5)
        print(f"Gamepad TCP server listening on {self.host}:{self.gamepad_port}")

        threading.Thread(target=self.handle_video_clients, daemon=True).start()
        threading.Thread(target=self.video_streaming_loop, daemon=True).start()
        threading.Thread(target=self.handle_gamepad_clients, daemon=True).start()

    def handle_video_clients(self):
        while not self.shutdown_event.is_set():
            try:
                data, addr = self.video_socket.recvfrom(RECV_BUFFER_SIZE)
            except socket.timeout:
                self.prune_video_clients()
                continue
            except OSError:
                break

            if data != VIDEO_HELLO_PACKET:
                continue

            with self.video_clients_lock:
                is_new_client = addr not in self.video_clients
                self.video_clients[addr] = time.monotonic()

            if is_new_client:
                print(f"Video client registered from {addr}")

    def prune_video_clients(self):
        now = time.monotonic()
        with self.video_clients_lock:
            expired_clients = [
                addr
                for addr, last_seen in self.video_clients.items()
                if now - last_seen > VIDEO_CLIENT_TIMEOUT_SECONDS
            ]
            for addr in expired_clients:
                self.video_clients.pop(addr, None)

    def video_streaming_loop(self):
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, VIDEO_JPEG_QUALITY]
        target_period = 1.0 / VIDEO_TARGET_FPS
        next_send_time = time.perf_counter()

        while not self.shutdown_event.is_set():
            frame = self.video_capture.read()
            if frame is None:
                time.sleep(0.01)
                continue

            if self.is_debug_video_show:
                cv2.imshow("frame", frame)
                cv2.waitKey(1)

            success, encoded_frame = cv2.imencode(".jpg", frame, encode_params)
            if not success:
                continue

            self.send_video_frame(encoded_frame.tobytes())

            next_send_time += target_period
            remaining_delay = next_send_time - time.perf_counter()
            if remaining_delay > 0:
                time.sleep(remaining_delay)
            else:
                next_send_time = time.perf_counter()

    def send_video_frame(self, frame_bytes):
        with self.video_clients_lock:
            client_addresses = list(self.video_clients.keys())

        if not client_addresses or not frame_bytes:
            return

        self.video_sequence += 1
        frame_sequence = self.video_sequence
        send_timestamp_ns = time.time_ns()
        frame_size = len(frame_bytes)
        chunk_count = max(1, (frame_size + MAX_VIDEO_CHUNK_SIZE - 1) // MAX_VIDEO_CHUNK_SIZE)
        disconnected_clients = set()

        for chunk_index in range(chunk_count):
            start = chunk_index * MAX_VIDEO_CHUNK_SIZE
            end = min(start + MAX_VIDEO_CHUNK_SIZE, frame_size)
            payload = frame_bytes[start:end]
            header = struct.pack(
                VIDEO_HEADER_FORMAT,
                VIDEO_FRAME_PACKET_TYPE,
                frame_sequence,
                send_timestamp_ns,
                frame_size,
                chunk_index,
                chunk_count,
            )
            packet = header + payload

            for addr in client_addresses:
                if addr in disconnected_clients:
                    continue
                try:
                    self.video_socket.sendto(packet, addr)
                except OSError:
                    disconnected_clients.add(addr)

        if disconnected_clients:
            with self.video_clients_lock:
                for addr in disconnected_clients:
                    self.video_clients.pop(addr, None)

    def handle_gamepad_clients(self):
        while not self.shutdown_event.is_set():
            try:
                client_socket, addr = self.gamepad_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            client_socket.settimeout(SOCKET_TIMEOUT_SECONDS)
            client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"Gamepad client connected from {addr}")
            threading.Thread(
                target=self.gamepad_communication,
                args=(client_socket, addr),
                daemon=True,
            ).start()

    def recv_exactly(self, client_socket, size):
        chunks = bytearray()
        while len(chunks) < size and not self.shutdown_event.is_set():
            try:
                chunk = client_socket.recv(size - len(chunks))
            except socket.timeout:
                continue

            if not chunk:
                return None
            chunks.extend(chunk)

        if len(chunks) < size:
            return None
        return bytes(chunks)

    def should_accept_control_sequence(self, sequence):
        with self.last_control_sequence_lock:
            if sequence <= self.last_control_sequence:
                return False
            self.last_control_sequence = sequence
            return True

    def gamepad_communication(self, client_socket, addr):
        try:
            while not self.shutdown_event.is_set():
                header = self.recv_exactly(client_socket, CONTROL_HEADER_SIZE)
                if not header:
                    break

                packet_type, sequence, _timestamp_ns, payload_size = struct.unpack(
                    CONTROL_HEADER_FORMAT,
                    header,
                )
                if packet_type != CONTROL_PACKET_TYPE:
                    break

                payload = self.recv_exactly(client_socket, payload_size)
                if payload is None:
                    break

                if not self.should_accept_control_sequence(sequence):
                    continue

                gamepad_data = json.loads(payload.decode("utf-8"))
                axes = gamepad_data.get("axes", [])
                triggers = gamepad_data.get("triggers", [])
                buttons = gamepad_data.get("buttons", [])
                self.teensy_controller.parse_data(axes, triggers, buttons)
        except (ConnectionResetError, BrokenPipeError, json.JSONDecodeError, struct.error):
            pass
        finally:
            print(f"Gamepad client disconnected from {addr}")
            client_socket.close()

    def signal_handler(self, sig, frame):
        print(f"Received signal {sig}, cleaning up resources...")
        self.cleanup_resources()
        sys.exit(0)

    def cleanup_resources(self):
        self.shutdown_event.set()

        if self.using_jetson:
            self.video_capture.stop()
        else:
            self.video_capture.release()

        if self.video_socket is not None:
            self.video_socket.close()

        if self.gamepad_socket is not None:
            self.gamepad_socket.close()

        cv2.destroyAllWindows()
        print("Resources cleaned up successfully.")


if __name__ == "__main__":
    VideoServer("0.0.0.0", 8889, 8890)
