# Send video from Jetson Nano to a UDP Server
# Partially based on code https://github.com/ancabilloni/udp_camera_streaming

#!!! WARNING - NOT FUNCTIONAL !!!
from __future__ import division

import sys
import time
import datetime
import imutils
from imutils.video import JetsonVideoStream

import argparse
import numpy as np
import cv2


import socket
import struct
import math


class FrameSegment(object):
    """ 
    Object to break down image frame segment
    if the size of image exceed maximum datagram size 
    """
    MAX_DGRAM = 2**16
    MAX_IMAGE_DGRAM = MAX_DGRAM - 64 # extract 64 bytes in case UDP frame overflown
    def __init__(self, sock, port, addr="127.0.0.1"):
        self.s = sock
        self.port = port
        self.addr = addr

    def udp_frame(self, img):
        """ 
        Compress image and Break down
        into data segments 
        """
        compress_img = cv2.imencode('.jpg', img)[1]
        dat = compress_img.tostring()
        size = len(dat)
        count = math.ceil(size/(self.MAX_IMAGE_DGRAM))
        array_pos_start = 0
        while count:
            array_pos_end = min(size, array_pos_start + self.MAX_IMAGE_DGRAM)
            self.s.sendto(struct.pack("B", count) +
                dat[array_pos_start:array_pos_end], 
                (self.addr, self.port)
                )
            array_pos_start = array_pos_end
            count -= 1


if __name__ == "__main__":

    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--server", type=str, default='10.24.224.253',
        help="address of the image server")
    ap.add_argument("-p", "--port", type=int, default=55567,
        help="address of the image server")
    ap.add_argument("-f", "--fps", type=int, default=30,
        help="FPS of output video (default 30)")
    ap.add_argument("-x", "--width", type=int, default=848,
        help="width of the output video (default 848)")
    ap.add_argument("-y", "--height", type=int, default=480,
        help="height of the output video (default 480)")
    ap.add_argument("-d", "--duration", type=int, default=0,
        help="maximum streaming duration (in seconds) - default 0")

    args = vars(ap.parse_args())

    width = args['width']
    height = args['height']
    frameResolution = (width, height)


    FPS = args['fps']
    duration = args['duration'] # seconds


    serverAddress = args['server']
    port = args['port']


    # set up camera and wait for initialization
    vs = JetsonVideoStream(outputResolution=frameResolution).start()
    time.sleep(2)

    # Set up UDP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    fs = FrameSegment(s, port, addr=serverAddress)


    #set up time limit for video sending
    endTime = None
    if duration > 0:
        endTime = datetime.datetime.now() + datetime.timedelta(seconds=duration)



    # Main loop
    while True:
        if endTime is not None:
            if datetime.datetime.now() >= endTime:
                break
        
        #read image from camera
        frame = vs.read() 
        #send image using UDP protocol to server
        fs.udp_frame(frame)
        print("frame sent")
              

    vs.stop()
    cv2.destroyAllWindows()
