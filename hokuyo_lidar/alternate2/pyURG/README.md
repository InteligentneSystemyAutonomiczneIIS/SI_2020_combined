# pyURG
python program to use URG sensor (HOKUYO) which is connected through USB


## How to install

install python-serial
```
sudo pip install python-serial
```

## How to use
### Import  
```
from pyURG import serial_URG
URG1 = serial_URG("/dev/ttyACM0", 900000)
```

### Init timestamp (Optional)
matching timestamp precisely
```
URG1.init_timestamp2()
```

Simple one
```
URG1.init_timestamp()
```

### Single capture
```
xyz_GDGS, tm_GDGS = URG1.capture_GDGS(byte=3)
```
xyz_GDGS[n]: xyz value of a point. (z=0)  
tm_GDGS[n] : the time when xyz_GDGS[n] is captured.

### Multiple capture
```
xyz_MDMS, tm_MDMS = URG1.capture_MDMS(byte=3, interval = 4, num_scans = 10)
```
m: scan  
n: step  
xyz_MDMS[m][n]: xyz value of a point. (z=0)  
tm_MDMS[m][n] : the time when xyz_MDMS[m][n] is captured.

### Setting
```
MODE = 1
URG1.change_measure_mode(MODE)
```
MODE: 0 -> Normal sensitive mode  
MODE: 1 -> High sensitive mode  

---

```
SPEED_PARAM = 10
URG1.adjust_motor_speed(SPEED_PARAM)
```
SPEED_PARAM: 0       -> Default speed  
SPEED_PARAM: 1 to 10 -> Changes speed to different levels  
SPEED_PARAM: 99      -> Reset to initial speed
