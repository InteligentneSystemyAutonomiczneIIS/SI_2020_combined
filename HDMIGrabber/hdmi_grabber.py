# Run this code on PC
import cv2
import sys
import time


# import the necessary packages
from threading import Thread
import cv2

class HDMIGrabberStream:
    def __init__(self, src=0, captureWidth=1920, captureHeight=1080, fps=60, name="HDMIGrabberStream"):
        # initialize the video camera stream 
        self.stream = cv2.VideoCapture(src)
        self.captureWidth = captureWidth

        # set camera capture resolution and FPS
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, captureWidth)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, captureHeight)
        self.stream.set(cv2.CAP_PROP_FPS, fps)

        # read the first frame from the stream
        (self.grabbed, self.frame) = self.stream.read()

        # initialize the thread name
        self.name = name

        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        t = Thread(target=self.update, name=self.name, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return

            # otherwise, read the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        # return the frame most recently read
        return self.frame

    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True



if __name__ == "__main__":

    captureWidth, captureHeight = (1920, 1080)
    fps = 60
    videoGrabberID = 0

    stream = HDMIGrabberStream(videoGrabberID, captureWidth, captureHeight, fps)
    stream.start()
    time.sleep(3)

    while True:
        # Capture frame-by-frame
        frame = stream.read()
        cv2.imshow("result", frame)

        # Press Q on keyboard to exit
        key = cv2.waitKey(1) & 0xFF 
        if key == ord('q'):
            break
    
    stream.stop()
    cv2.destroyAllWindows()
    