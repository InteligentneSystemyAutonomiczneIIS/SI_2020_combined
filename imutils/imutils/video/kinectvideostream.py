# import the necessary packages
from threading import Thread

import numpy as np
import cv2
import sys
from pylibfreenect2 import Freenect2, SyncMultiFrameListener
from pylibfreenect2 import FrameType, Registration, Frame
from pylibfreenect2 import createConsoleLogger, setGlobalLogger
from pylibfreenect2 import LoggerLevel

class KinectVideoStream:
	def __init__(self, src=0, name="KinectVideoStream", logKinectEvents = False):
		
		try:
			from pylibfreenect2 import OpenGLPacketPipeline
			pipeline = OpenGLPacketPipeline()
		except:
			try:
				from pylibfreenect2 import OpenCLPacketPipeline
				pipeline = OpenCLPacketPipeline()
			except:
				from pylibfreenect2 import CpuPacketPipeline
				pipeline = CpuPacketPipeline()
		
		
		print("Packet pipeline:", type(pipeline).__name__)
		
		if logKinectEvents:
		# Create and set logger
			logger = createConsoleLogger(LoggerLevel.Debug)
			setGlobalLogger(logger)

		self.fn = Freenect2()
		self.num_devices = self.fn.enumerateDevices()
		if self.num_devices == 0:
			print("No device connected!")
			sys.exit(1)
		self.serial = self.fn.getDeviceSerialNumber(src)
		self.device = self.fn.openDevice(self.serial, pipeline=pipeline)

		self.listener = SyncMultiFrameListener(
			FrameType.Color | FrameType.Ir | FrameType.Depth)

		# Register listeners
		self.device.setColorFrameListener(self.listener)
		self.device.setIrAndDepthFrameListener(self.listener)

		self.device.start()

		# NOTE: must be called after device.start()
		self.registration = Registration(self.device.getIrCameraParams(),
									self.device.getColorCameraParams())

		self.undistorted = Frame(512, 424, 4)
		self.registered = Frame(512, 424, 4)

		# Optinal parameters for registration
		# set True if you need
		self.need_bigdepth = False
		self.need_color_depth_map = False

		self.bigdepth = Frame(1920, 1082, 4) if self.need_bigdepth else None
		self.color_depth_map = np.zeros((424, 512),  np.int32).ravel() \
			if self.need_color_depth_map else None
		
		
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
			frames = self.listener.waitForNewFrame()

			color = frames["color"]
			ir = frames["ir"]
			depth = frames["depth"]

			self.registration.apply(color, depth, self.undistorted, self.registered,
							bigdepth=self.bigdepth,
							color_depth_map=self.color_depth_map)

			self.rawIr = ir
			self.rawColor = color
			self.rawDepth = depth

			self.ir = ir.asarray() / 65535.
			self.depth = depth.asarray() / 4500.
			self.color = cv2.cvtColor(color.asarray(), cv2.cv2.COLOR_RGB2BGR)
			if self.need_bigdepth:
				self.bigdepth = self.bigdepth.asarray(np.float32)
			
			if self.need_color_depth_map:
				self.color_depth_map = self.color_depth_map.reshape(424, 512)

			self.listener.release(frames)



	def read(self):
		# return the frame most recently read
		return self.color.copy(), self.ir.copy(), self.depth.copy()
	
	def readRaw(self):
		return self.rawColor, self.rawIr, self.rawDepth

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
		self.device.stop()
		self.device.close()


if __name__ == "__main__":
	import time
	vs = KinectVideoStream().start()
	time.sleep(5)

	while True:
		color, ir, depth = vs.read()

		cv2.imshow('color', color)
		cv2.imshow('ir', ir)
		cv2.imshow('depth', depth)
		key = cv2.waitKey(delay=1)
		if key == ord('q'):
			break
	
	vs.stop()
	sys.exit(0)
