#Simple example showing how to get gamepad events and send them using websockets to platform
# WARNING! VEEERY janky, do not use in production!!!!!

import time
import json
import websocket
from Controller import Controller

preferredFPS = 60
refreshRate = 1./preferredFPS
host = "ws://10.24.224.217:8084"

def main():
    controller = Controller()

    # websocket.enableTrace(True)
    ws = websocket.create_connection(host)   


    deltaTime = 0
    while True:
        
        startTime = time.time()
        state = controller.getControllerState()
        
        if deltaTime > refreshRate:
            res = ws.send(json.dumps(state))
            deltaTime = 0
            # data = ws.recv()
            # print(data)
        endTime = time.time()

        deltaTime += endTime - startTime


if __name__ == "__main__":
    main()

    

