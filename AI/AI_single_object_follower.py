# parts of the code are based on https://www.pyimagesearch.com/2016/01/04/unifying-picamera-and-cv2-videocapture-into-a-single-class-with-opencv/
# before running the code install imutils for python3 (from https://github.com/pawelplodzpl/imutils)

# in case of problems with camera image run:
# sudo systemctl restart nvargus-daemon


import cv2 
import numpy as np
from imutils.video import JetsonVideoStream
import jetson.inference
import jetson.utils
import time

import sys
import time
import imutils
from imutils.video import JetsonVideoStream
# from imutils.video import VideoStream
import serial



def translate(value, oldMin, oldMax, newMin=-100, newMax=100):
    # Figure out how 'wide' each range is
    oldRange = oldMax - oldMin
    newRange = newMax - newMin
    NewValue = (((value - oldMin) * newRange) / oldRange) + newMin
    return int(NewValue)

def getBoundingBoxes(net, image, className):
    boundingBoxes = []


    # convert to CUDA image
    img = image.copy()
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA).astype(np.float32)
    img = jetson.utils.cudaFromNumpy(frame)
    
    detections = net.Detect(img, width, height)
    
    for detection in detections:
        x,y,w,h = (int(detection.Left), int(detection.Top), int(detection.Width), int(detection.Height))
        classID = detection.ClassID
        if classID == classes[className]:
            boundingBoxes.append((x,y,w,h))

        print(detection)

    return boundingBoxes

classes = {'BACKGROUND': 0, "ducky": 1}

######## Main variables

# modelPath = 'AI/ssd-mobilenet.onnx'
# labelsPath = 'AI/labels.txt'

modelPath = 'ssd-mobilenet.onnx'
labelsPath = 'labels.txt'



runHeadless = False

# frameResolution = (960, 460)
# frameResolution = (848, 480)
frameResolution = (1280, 720)

HorizontalFOV = 62
VerticalFOV = 37

paused = False

######## Initialization

vs = JetsonVideoStream(outputResolution=frameResolution)

vs.start()

# # initialize serial communication
ser = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=0.05)

time.sleep(2.0)

net = jetson.inference.detectNet(argv=['--model={}'.format(modelPath),
                                       '--labels={}'.format(labelsPath),
                                       '--input-blob=input_0', '--output-cvg=scores', '--output-bbox=boxes'], #, '--input-flip=rotate-180'],
                                       threshold=0.5)



# pause camera movement

ser.write(bytes('<stop, 0, 0>', 'utf-8') )

######## Main loop

while True:
    loopStart = time.time()
    if not paused:

        frame = vs.read()     
        height, width = frame.shape[0:2]


        boundingBoxes = getBoundingBoxes(net, frame, 'ducky' )
        

        # draw bounding boxes
        for i, boundingBox in enumerate(boundingBoxes):
            
            x, y, w, h = boundingBox

            if i is 0:
                firstObjectMidPoint = ((x+ w//2), (y + h//2))
                cv2.rectangle(frame, (x, y), ((x+w), (y+h)), (0, 0, 255), thickness=3)

                screenMidPoint = width//2, height//2
                distanceVector = tuple(map(lambda x, y: x - y, firstObjectMidPoint, screenMidPoint))

                yaw = translate(distanceVector[0], -width//2, width//2, -HorizontalFOV//2, HorizontalFOV//2) # up-down
                yawError = yaw / (HorizontalFOV/2) 
                pitch = translate(distanceVector[1], -height//2, height//2, -VerticalFOV//2, VerticalFOV//2) # left-right
                pitchError = pitch / (VerticalFOV/2)

                print("Yaw error: {}, Pitch error: {}\n".format(yawError, pitchError))
                
                
                cv2.line(frame, screenMidPoint, firstObjectMidPoint, (0, 0, 255))
                packet = '<servo, {}, {}>'.format(yawError, pitchError)
                packetBytes = bytes(packet, 'utf-8')
                
                ser.write(packetBytes)
                
            else:
                cv2.rectangle(frame, (x, y), ((x+w), (y+h)), (255, 255, 0), thickness=2)
                 
        if not runHeadless:
            cv2.imshow("video", frame)


    # handle keys 
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

    elif key == ord('p'):
        paused = not paused
    elif key == ord('d'):
        # pause/unpause camera movement
        packet = '<stop, 0, 0>'
        packetBytes = bytes(packet, 'utf-8')  
        ser.write(packetBytes)
    elif key == ord('f'):
        # pause/unpause camera movement
        packet = '<start, 0, 0>'
        packetBytes = bytes(packet, 'utf-8')  
        ser.write(packetBytes)



    print(ser.read_all())

    loopEnd = time.time()
    print("loop execution took {:3.2f}ms".format((loopEnd - loopStart)*1000))
    

    
# cleanup

ser.close()
cv2.destroyAllWindows()

# to cleanly stop frame grabbing thread
vs.stop()
time.sleep(1.0)
sys.exit(0)

