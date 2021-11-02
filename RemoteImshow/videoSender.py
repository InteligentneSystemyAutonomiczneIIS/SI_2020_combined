# in case of problems with camera image run:
# sudo systemctl restart nvargus-daemon

import cv2 
import websocket
import numpy as np
import json
import base64
from datetime import datetime
import time
from imutils.video import JetsonVideoStream

class RemoteVideoSender():
    
    def __init__(self, serverAddress = "127.0.0.1", port=8085):
        self.setConnectionDetails(serverAddress, port)
        self.startConnection()

    def setConnectionDetails(self, serverAddress = "127.0.0.1", port=8085):
        self.serverAddress = serverAddress
        self.port = port

    def startConnection(self):
        try:
            hostname = "ws://" + self.serverAddress + ":" + str(self.port)
            self.ws = websocket.create_connection(hostname)   
        except:
            raise Exception("Connection impossible")

    def encodeFrame(self, frame, scaleFactor = 2):
        height, width = frame.shape[0:2]
        frameResized = cv2.resize(frame, (width//scaleFactor, height//scaleFactor))
        timestamp = datetime.now().strftime("%S.%f")
        cv2.putText(frameResized, timestamp, (0,20), cv2.FONT_HERSHEY_COMPLEX, 0.5, color=(0,0,255))
        img_encoded = cv2.imencode('.jpg', frameResized)[1]
        img_b64 = base64.b64encode(img_encoded).decode()
        return  json.dumps({'imageData': img_b64})

    def sendData(self, message):
        self.ws.send(message)
    
    def remoteImShow(self, frame):
        try:
            jsonToSend = self.encodeFrame(frame)
            self.sendData(jsonToSend)
        except:
            raise Exception("Unable to send data")


if __name__ == "__main__":
    # set up camera and wait for initialization

    frameResolution = (848, 480)
    vs = JetsonVideoStream(outputResolution=frameResolution).start()
    time.sleep(3)

    host = "X.X.X.X"
    port = 8085
    rs = RemoteVideoSender(host, port)


    while(True):
        # Capture each frame of webcam video
        ret,frame = vs.read()
        # cv2.imshow("My cam video", frame)

        rs.remoteImShow(frame)

        if cv2.waitKey(1) &0XFF == ord('q'):
            break

    vs.stop()
    cv2.destroyAllWindows()