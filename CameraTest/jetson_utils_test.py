# parts of the code are based on https://www.pyimagesearch.com/2016/01/04/unifying-picamera-and-cv2-videocapture-into-a-single-class-with-opencv/
# before running the code install imutils for python3 (from https://github.com/pawelplodzpl/imutils)

# in case of problems with camera image run:
# sudo systemctl restart nvargus-daemon


import sys
import time
import cv2
import jetson.utils
import numpy as np


######## Main variables

inputWidth = 1280
inputHeight = 720
inputFrameRate = 60

rescaledWidth = 848
rescaledHeight = 480

# HorizontalFOV = 62
# VerticalFOV = 37

showImage = True

######## Initialization

# --input-flip=rotate-180 -> see gstCamera.cpp; the options are reversed (rotate-180 / none)
input = jetson.utils.videoSource("csi://0", argv=[ # "--input-flip=rotate-180", # currently error in library makes it impossible to use this option 
                                                  "--input-rate={}".format(inputFrameRate), # "--input-rtsp-latency=100", 
                                                  "--input-width={}".format(inputWidth), "--input-height={}".format(inputHeight)])


######## Main loop
frameTimes = []
for i in range(0, 500):
    loopStart = time.time()
    image = input.Capture(format='rgb8')
    imgcvt = jetson.utils.cudaAllocMapped(width=inputWidth, height=inputHeight, format='bgr8')
    jetson.utils.cudaConvertColor(image, imgcvt)

    imgOutput = jetson.utils.cudaAllocMapped(width=rescaledWidth, height=rescaledHeight, format='bgr8')
    jetson.utils.cudaResize(imgcvt, imgOutput)

    opencvImage = jetson.utils.cudaToNumpy(imgOutput)
    
    #final image in proper orientation
    imageRotated = cv2.rotate(opencvImage, cv2.ROTATE_180)

    if showImage:
        cv2.imshow("stream", opencvImage)

    # handle keys 
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

    # manual free memory - in theory can be skipped and handled by GarbageCollector
    del imgcvt 
    del image
    del opencvImage

    loopEnd = time.time()
    frameTime = (loopEnd - loopStart)*1000
    print("loop execution took {:3.2f}ms".format(frameTime))
    frameTimes.append(frameTime)
    

print("Average frametime: {}".format(np.average(frameTimes)))
    
# cleanup
cv2.destroyAllWindows()
time.sleep(1.0) #not strictly necessary, just in case, to give GStreamer some time to clean

