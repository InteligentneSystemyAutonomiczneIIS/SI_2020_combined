# parts of the code are based on https://www.pyimagesearch.com/2016/01/04/unifying-picamera-and-cv2-videocapture-into-a-single-class-with-opencv/
# before running the code install imutils for python3 (from https://github.com/pawelplodzpl/imutils)

# in case of problems with camera image run:
# sudo systemctl restart nvargus-daemon



import sys
import time
from imutils.video import JetsonVideoStream, JetsonVideoStreamST
import numpy as np
import cv2
import jetson.utils




######## Main variables

# frameResolution = (960, 460)
inputWidth = 1280
inputHeight = 720
inputFrameRate = 28

rescaledWidth = 848
rescaledHeight = 480



singleThreaded = True

######## Initialization
if singleThreaded:
    vs = JetsonVideoStreamST(outputResolution=(rescaledWidth, rescaledHeight))
else:
    vs = JetsonVideoStream(outputResolution=(rescaledWidth, rescaledHeight))

vs.start()

time.sleep(2.0)


######## Main loop
frameTimes = []
for i in range(0, 100):
    loopStart = time.time()
        
    frame = vs.read()

    #convert to CUDA image (GPU memory)
    bgr_img  = jetson.utils.cudaFromNumpy(frame, isBGR=True) 
    # convert from BGR -> RGB
    rgb_img = jetson.utils.cudaAllocMapped(width=bgr_img .width, height=bgr_img .height, format='rgb8')

    jetson.utils.cudaConvertColor(bgr_img , rgb_img)


    # handle keys 
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break


    loopEnd = time.time()
    frameTime = (loopEnd - loopStart)*1000
    print("loop execution took {:3.2f}ms".format(frameTime))
    frameTimes.append(frameTime)
    

print("Average frametime: {}".format(np.average(frameTimes)))
    
# cleanup

cv2.destroyAllWindows()

# to cleanly stop frame grabbing
vs.stop()
time.sleep(1.0)
sys.exit(0)

