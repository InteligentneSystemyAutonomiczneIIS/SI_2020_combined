# test application for Hokuyo UTM-30LX 2D lidar scanner (range finder)

# before using check following:
# - udev rules installed
# - chmod 777 /dev/ttyACM1 # or another ttyACM[0-9]
# 

import argparse
import pyurg
import time
import numpy as np
import sys


def showPlotGUI(plt, data):
    x, y = data
    axis = plt.gca()
    axis.clear()
    plt.plot(x,y)
    plt.draw()
    plt.autoscale()
    plt.pause(0.01)


def showPlotTerminal(data):
    x, y = data
    x = np.array(x)
    y = np.array(y)
    gp.plot( (x, y), _with = 'lines', terminal = 'dumb 80,40', unset = 'grid')
    # gp.plot( (x, y), _with = 'boxes', terminal = 'dumb 80,40', unset = 'grid')


if __name__ == "__main__":

    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--headless", default=False, action='store_true',
                    help="Run the application in terminal mode")
    ap.add_argument("-d", "--device", type=str, default='/dev/ttyACM1',
	                help="path to connected device (usually /dev/ttyACM1)")
    

    args = vars(ap.parse_args())

    isHeadless = args['headless']
    device = args['device']

    if isHeadless:
        import gnuplotlib as gp
    else:
        import matplotlib.pyplot as plt
        import time

    urg = pyurg.Urg()
    urg.set_urg(device)
    urg.reset_urg(device)

    if not isHeadless:
        plt.ion()
        plt.show()
        plt.autoscale(enable=True)
        axis = plt.gca()

    while True:
        try:   
            urg.check_status(urg.request_me(0, 1080, num = 1))
            dist, intensity, timestamp = urg.get_distance_and_intensity()
            x,y = urg.convert_to_x_y(dist)
            
            if isHeadless:
                showPlotTerminal((x,y))
            else:
                showPlotGUI(plt, (x,y))

        except KeyboardInterrupt:
            print("Stopping program")
            urg.reset_urg(device)
            urg.close_port()
            sys.exit()
            
