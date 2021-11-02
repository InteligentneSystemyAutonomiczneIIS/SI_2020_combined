from websocket_server import WebsocketServer
import json
import cv2
import numpy as np
import base64


# Called for every client connecting (after handshake)
def new_client(client, server):
    print("New client connected and was given id %d" % client['id'])
    server.send_message_to_all("Hey all, a new client has joined us")


# Called for every client disconnecting
def client_left(client, server):
    print("Client(%d) disconnected" % client['id'])
    cv2.destroyAllWindows()

def decodeFrame(data):
    frame = json.loads(data)['imageData']
    buf = base64.b64decode(frame)
    buf2 = np.frombuffer(buf, dtype=np.uint8)
    image = cv2.imdecode(buf2, cv2.IMREAD_COLOR)
    return image

# Called when a client sends a message
def message_received(client, server, message):
    image = decodeFrame(message)
    cv2.imshow('Remote frame', image)
    cv2.waitKey(1)


if __name__ == "__main__":
    HOST = "0.0.0.0"
    PORT=8085

    server = WebsocketServer(host=HOST, port=PORT)
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    server.run_forever()
