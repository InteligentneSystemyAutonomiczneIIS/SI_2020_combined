# Receive video from Jetson Nano using UDP protocol
# Based on code: https://github.com/ancabilloni/udp_camera_streaming

#!!! WARNING - NOT FUNCTIONAL !!!


from __future__ import division
import cv2
import numpy as np
import socket
import struct
import argparse

MAX_DGRAM = 2**16

def dump_buffer(s):
    """ Emptying buffer frame """
    while True:
        seg, addr = s.recvfrom(MAX_DGRAM)
        print(seg[0])
        if struct.unpack("B", seg[0:1])[0] == 1:
            print("finish emptying buffer")
            break

def main(listenAddress='127.0.0.1', port=55567):
    """ Getting image udp frame &
    concate before decode and output image """
    
    # Set up socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((listenAddress, port))
    dat = b''
    dump_buffer(s)

    while True:
        seg, addr = s.recvfrom(MAX_DGRAM)
        if struct.unpack("B", seg[0:1])[0] > 1:
            dat += seg[1:]
        else:
            dat += seg[1:]
            img = cv2.imdecode(np.fromstring(dat, dtype=np.uint8), 1)
            cv2.imshow('frame', img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            dat = b''

    cv2.destroyAllWindows()
    s.close()

if __name__ == "__main__":

    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--server", type=str, default='10.24.224.253',
        help="listen address")
    ap.add_argument("-p", "--port", type=int, default=55567,
        help="listen port")
    
    args = vars(ap.parse_args())

    
    listenAddress = args['server']
    port = args['port']

    main(listenAddress, port)