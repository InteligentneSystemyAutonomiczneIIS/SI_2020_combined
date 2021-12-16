# Run this code on PC
import cv2
import sys


captureWidth, captureHeight = (1920, 1080)
fps = 60
videoGrabberID = 1


##FOR NORMAL WEBCAMS
cap = cv2.VideoCapture(videoGrabberID)
if (cap.isOpened() == False):
    print("Error opening video stream or file")
    sys.exit(-1)

# set camera capture resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, captureWidth)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, captureHeight)
cap.set(cv2.CAP_PROP_FPS, fps)


while cap.isOpened():
    # Capture frame-by-frame
    ret, frame = cap.read()
    cv2.imshow("result", frame)

    # Press Q on keyboard to  exit
    key = cv2.waitKey(1) & 0xFF 
    if key == ord('q'):
        break


cv2.destroyAllWindows()


