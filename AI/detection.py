#!/usr/bin/python3
#
# Copyright (c) 2020, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
import cv2 
import numpy as np
from imutils.video import JetsonVideoStream
import jetson.inference
import jetson.utils
import time


# frameResolution = (1280, 720)
frameResolution = (848, 480)
vs = JetsonVideoStream(outputResolution=frameResolution)
vs.start()
time.sleep(2.0)


modelPath = 'AI/ssd-mobilenet.onnx'
labelsPath = 'AI/labels.txt'


runHeadless = True


net = jetson.inference.detectNet(argv=['--model={}'.format(modelPath),
                                       '--labels={}'.format(labelsPath),
                                       '--input-blob=input_0', '--output-cvg=scores', '--output-bbox=boxes'], #, '--input-flip=rotate-180'],
                                       threshold=0.5)


# process frames until the user exits
while True:
	# capture the next image
	frame = vs.read()     
	height, width = frame.shape[0:2]

	# convert to CUDA image
	img = frame.copy()
	img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
	img = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA).astype(np.float32)
	img = jetson.utils.cudaFromNumpy(frame)


	detections = net.Detect(img, width, height)

	## convert back to OpenCV (numpy) image - normally not necessary
	# img = jetson.utils.cudaToNumpy(img, width, height, 4)
	# img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB).astype(np.uint8)
	# img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

	# print the detections
	print("detected {:d} objects in image".format(len(detections)))


	for detection in detections:
		x1,y1,x2,y2 = (int(detection.Left), int(detection.Top), int(detection.Right), int(detection.Bottom))
		classID = detection.ClassID
		cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), thickness=3)

		print(detection)


	# print out performance info
	net.PrintProfilerTimes()

	if runHeadless is False:
		cv2.imshow("video", frame)

	# handle keys 
	key = cv2.waitKey(1) & 0xFF
	if key == ord('q'):
		break



cv2.destroyAllWindows()

# to cleanly stop frame grabbing thread
vs.stop()

