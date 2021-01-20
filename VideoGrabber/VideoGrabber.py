import sys
import time
import datetime
import imutils
from imutils.video import JetsonVideoStream

import argparse
import numpy as np
import cv2

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default='video.mp4',
	help="path to output video file (default video.mp4)")
ap.add_argument("-n", "--headless", type=bool, default=False,
	help="Run the application without showing the output")
ap.add_argument("-f", "--fps", type=int, default=30,
	help="FPS of output video (default 30)")
ap.add_argument("-c", "--codec", type=str, default="MP4V",
	help="codec of output video (default MP4V, available:DIVX, H264, avc1, MP4V, MJPG )")
ap.add_argument("-x", "--width", type=int, default=848,
	help="width of the output video (default 848)")
ap.add_argument("-y", "--height", type=int, default=480,
	help="height of the output video (default 480)")
ap.add_argument("-d", "--duration", type=int, default=60,
	help="maximum recording duration (in seconds) - default 60")

args = vars(ap.parse_args())



width = args['width']
height = args['height']
frameResolution = (width, height)


FPS = args['fps']
duration = args['duration'] # seconds
isHeadless = args['headless']

outputVideoPath = args['output']


vs = JetsonVideoStream(outputResolution=frameResolution).start()
# wait for camera initialization
time.sleep(2)


codec = cv2.VideoWriter_fourcc(*args['codec'])


writer= cv2.VideoWriter(outputVideoPath, codec, FPS, (width,height))


endTime = datetime.datetime.now() + datetime.timedelta(seconds=duration)

isRecording = False

if not isHeadless:
    print('\nPress R on the keyboard to start [R]ecording video')
    print('Press P on the keyboard to [P]ause recording video\n')
    print('Press S on the keyboard to [S]top the recording and save the video\n')
else:
    isRecording = True

while True:
    if datetime.datetime.now() >= endTime:
        break
  
    frame = vs.read() 
    
    if isHeadless is False:
        cv2.imshow('frame', frame)
    
    
    if isRecording is True:
        writer.write(frame)


    key = cv2.waitKey(1)
    if key & 0xFF == 27:
        break
    if key == ord('r') and isHeadless is False:
        isRecording = True
    if key == ord('p') and isRecording is True:
        isRecording = False
    if key == ord('s') :
        break

vs.stop()
writer.release()
cv2.destroyAllWindows()
