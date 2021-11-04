# https://github.com/mtaki91/pyURG

import serial
import time
import numpy as np

class serial_URG(serial.Serial):
  def __init__(self, port = '/dev/ttyACM0', baudrate = 900000, timeout = 1):
    super(serial.Serial, self).__init__()
    self.port = port
    self.baudrate = baudrate
    self.timeout = timeout

    self.latest_timestamp = 0
    self.timestamp_param = np.array([0, 1/1000.])
    self.connect()
    self.set_scip2()
    self.get_version()
    print "Connect to " + self.version['PROD'] + " No."+ self.version["SERI"]
    self.get_parameter()
    self.set_capture_range(self.parameter["AMIN"], self.parameter["AMAX"])
    self.reset()
    self.adjust_motor_speed(99)
    self.laser_on()
    self.get_status()

    
  def connect(self):
    if not self.isOpen():
      self.open()

      
  def set_scip2(self):
    self.write("SCIP2.0\n")
    self.receive_data()

    
  def buffer_clear(self):   
    self.flushInput()

    
  def receive_data(self):
    data = []
    tmp = 't' # temp data 
    while tmp != "\n" and tmp != "":
      tmp = self.readline()
      data.append(tmp)
    return data

  
  def get_version(self):
    self.buffer_clear()
    self.write("VV\n")
    dat = self.receive_data()
    info = {}
    for l in dat[3:-1]:
      pos_colon = l.find(":")
      info[l[:pos_colon]] = l[pos_colon+1:-3]
    self.version = info
    return info

  
  def get_parameter(self):
    self.buffer_clear()
    self.write("PP\n")
    dat = self.receive_data()
    info = {}
    for l in dat[3:-1]:
      pos_colon = l.find(":")
      info[l[:pos_colon]] = l[pos_colon+1:-3]
    self.parameter = info
    return info

  
  def get_status(self):
    self.buffer_clear()
    self.write("II\n")
    dat = self.receive_data()
    info = {}
    for l in dat[3:-1]:
      pos_colon = l.find(":")
      info[l[:pos_colon]] = l[pos_colon+1:-3]
    self.status = info
    return info


  def init_timestamp2(self, n = 100):
    self.write("TM0\n")
    self.receive_data()
    A = []
    b = []
    for i in range(n):
      self.write("TM1\n")
      tm_pc = time.time()
      received = self.receive_data()
      tm_urg = decode(received[2][:-2])[0]
      A.append([1, tm_urg])
      b.append(tm_pc)
      time.sleep(0.01)
    self.write("TM2\n")
    self.receive_data()
    A_T = np.linalg.pinv(A)
    self.timestamp_param = np.dot(A_T, b).reshape(2)

   
  def init_timestamp(self):
    self.write("TM0\n")
    self.receive_data()
    self.write("TM1\n")
    tm_pc = time.time()
    received = self.receive_data()
    self.write("TM2\n")
    self.receive_data()
    tm_urg = decode(received[2][:-2])[0]
    self.timestamp_param[0] = tm_pc - tm_urg * self.timestamp_param[1]

    
  def decode_timestamp(self, encode_str):
    time = decode(encode_str)[0]
    if time < self.latest_timestamp:
      self.timestamp_param[0] += (2 ** 24) * self.timestamp_param[1]
    self.latest_timestamp = time
    return time * self.timestamp_param[1] + self.timestamp_param[0]

  
  def get_scantime_table(self):
    scsp_str = self.get_status()["SCSP"]
    scsp = float(scsp_str[scsp_str.find("(")+1:scsp_str.find("[rpm]")])
    ares = float(self.parameter["ARES"])
    time_1scan = 60. / scsp
    self.scantime_table = np.linspace(0, time_1scan, ares+1)[int(self.start_step): int(self.end_step)+1]
    return self.scantime_table

  
  def get_scanangle_table(self):
    ares = float(self.parameter["ARES"])
    angle_list = np.linspace(0, 2*np.pi, ares+1)
    angle_list = angle_list - angle_list[int(self.parameter["AFRT"])]
    self.scanangle_table = angle_list[int(self.start_step): int(self.end_step)+1]
    self.cvt_xyz = np.array([np.cos(self.scanangle_table),
                             np.sin(self.scanangle_table),
                             np.zeros_like(self.scanangle_table)])

    return self.scanangle_table

  
  def laser_on(self):
    self.write("BM\n")
    dat = self.receive_data()

    
  def laser_off(self):
    self.write("QT\n")
    dat = self.receive_data()

    
  def reset(self):
    self.write("RS\n")
    dat = self.receive_data()
    self.latest_timestamp = 0
    self.init_timestamp()
    self.get_scantime_table()

    
  def reset2(self):
    self.write("RT\n")
    dat = self.receive_data()
    self.latest_timestamp = 0
    self.init_timestamp()
    self.get_scantime_table()

    
  def change_measure_mode(self, mode):
    """
    mode:0 -> normal sensitive mode
    mode:1 -> high sensitive mode
    """
    self.write("HS"+str(mode)+"\n")
    dat = self.receive_data()

    
  def adjust_motor_speed(self, speed_param):
    speed_param = str(speed_param).zfill(2)
    self.write("CR"+speed_param+"\n")
    dat = self.receive_data()
    self.get_scantime_table()

    
  def change_bitrate(self, bitrate):
    """
    When sensor is connected USB, bit rate change will not have any effect on the communication speed.
    """
    bitrate = str(bitrate).zfill(6)
    self.write("SS"+bitrate+"\n")
    self.baudrate = int(bitrate)
    dat = self.receive_data()

    
  def set_capture_range(self, start, end):
    #checking value
    if int(start) < int(self.parameter["AMIN"]):
      print "start must be larger than", self.parameter["AMIN"]
      raise ValueError
    if int(start) > int(self.parameter["AMAX"]):
      print "start must be smaller than", self.parameter["AMAX"]
      raise ValueError
    if int(end) <= int(start):
      print "end step must be larger than start step"
      raise ValueError
    if int(end) > int(self.parameter["AMAX"]):
      print "end step must be smaller than", self.parameter["AMAX"]
      raise ValueError

    self.start_step = str(start).zfill(4)
    self.end_step = str(end).zfill(4)
    self.get_scantime_table()
    self.get_scanangle_table()

    
  def capture_GDGS(self, byte=3):
    if byte ==3:
      command = "GD"
    elif byte ==2:
      command = "GS"
    else:
      print "byte: 2 or 3"
      raise ValueError
    self.buffer_clear()
    self.write(command
               + self.start_step
               + self.end_step
               + "01" #cluster_count
               + "\n")
    
    received = self.receive_data()

    if received[1] == "10Q\n":
      #When laser is off; laser_on -> try again
      self.laser_on()
      return self.capture_GDGS(byte)
    
    elif received[1] != "00P\n":
      print "Status: ", received[1][:-2]
      raise EnvironmentError
    
    data = ""
    for db in received[3:-1]:
      data = data + db[:-2]

    ## decoding data
    tm = self.decode_timestamp(received[2][:-2]) + self.scantime_table
    dist = np.array(decode(data, byte), np.float)
    dist[np.where(dist<20)] *= np.nan
    xyz = (dist * self.cvt_xyz).T
    return xyz, tm

  
  def capture_MDMS(self, byte=3, interval = 0, num_scans = 1):
    #set decoding byte
    if byte ==3:
      command = "MD"
    elif byte ==2:
      command = "MS"
    else:
      print "byte: 2 or 3"
      raise ValueError

    if interval > 9:
      print "interval should be 0~9"
      raise ValueError
    interval = str(interval)
    
    if num_scans < 100:
      str_num_scans = str(num_scans).zfill(2)
    else:
      str_num_scans = "00"

    self.buffer_clear()
    self.write(command
               + self.start_step
               + self.end_step
               + "01"
               + interval
               + str_num_scans
               + "\n")
    
    received = self.receive_data()
    if received[1] != "00P\n":
      print "Status: ", received[1][:-2]
      raise EnvironmentError

    xyz = []
    tm = []
    for n in range(num_scans):
      received = self.receive_data()
      data = ""
      for db in received[3:-1]:
        data = data + db[:-2]
      tm.append(self.decode_timestamp(received[2][:-2]) + self.scantime_table)
      dist = np.array(decode(data, byte), np.float)
      dist[np.where(dist<20)] *= np.nan
      xyz.append((dist * self.cvt_xyz).T)

    if str_num_scans == "00":
      self.laser_off() # laser_off in order to stop receiving data.

    self.laser_on() 
    return np.array(xyz), np.array(tm)

    
## Decoding Function
def decode(encode_str, byte = None):
  _len = len(encode_str)  
  if byte == None:
    byte = len(encode_str)
  shift6bit = np.array([2**((byte-1-i)*6) for i in range(byte)])
  dec = np.array([ord(c) for c in encode_str]) - 0x30
  dec = dec.reshape(_len/byte, byte) * shift6bit
  return np.sum(dec, axis=1)
