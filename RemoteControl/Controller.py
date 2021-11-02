import inputs
from inputs import get_gamepad



buttonMappings = {
        #XBOX gamepad
        "ABS_Z": "brake",
        "ABS_RZ": "gas",
        "ABS_X": "steering",
        "BTN_TR": "gear_up",
        "BTN_TL": "gear_down",
        "ABS_HAT0X": "hat_x",
        # "ABS_RX": "hat_x",
        "ABS_HAT0Y":  "hat_y", 
        # "ABS_RY":  "hat_y", 
        "BTN_SOUTH": "btn_1", 
        "BTN_EAST": "btn_2", 
        "BTN_WEST": "btn_3", 
        "BTN_NORTH": "btn_4", 
        "BTN_THUMBL": "btn_5", 
        "BTN_THUMBR": "btn_6", 
        
        # wheel
        "BTN_GEAR_UP": "gear_down",
        "BTN_GEAR_DOWN" : "gear_up",
        "BTN_BASE" : "btn_1",
        "BTN_BASE2" : "btn_2",
        "BTN_BASE3" : "gear_down",
        "BTN_BASE4" : "gear_up",
        "BTN_BASE5" : "btn_3",
        "BTN_BASE6" : "btn_4",
        "ABS_GAS" : "gas",
        "ABS_WHEEL" : "steering",
        "ABS_BRAKE" : "brake"

}



class Controller():

    def __init__(self):
        self.controllerState = {
            "brake": 0,
            "gas": 0,
            "steering": 0,
            "gear_up" : 0,
            "gear_down": 0,
            "hat_x" : 0, 
            "hat_y" :0, 
            "btn_1" : 0,
            "btn_2" : 0,
            "btn_3" : 0,
            "btn_4" : 0,
            "btn_5" : 0,
            "btn_6" : 0,
        }

        self._get_gamepad()

    def setAxisLimiters(self):
        if "X-Box 360 pad" in self.gamepad.name:
            self.steeringAxisMin = -32768
            self.steeringAxisMax = 32768
            self.brakeAxisMin = 0
            self.brakeAxisMax = 255
            self.gasAxisMin = 0
            self.gasAxisMax = 255
            self.hatModifier = -1
        elif "wheel " in self.gamepad.name:
            self.steeringAxisMin = 0
            self.steeringAxisMax = 255
            self.brakeAxisMin = -2048
            self.brakeAxisMax = 2048
            self.gasAxisMin = 0
            self.gasAxisMax = 255
            self.hatModifier = 1

    def _get_gamepad(self):
        """Get a gamepad object."""
        try:
            self.gamepad = inputs.devices.gamepads[0]
            self.name = self.gamepad.name
            self.setAxisLimiters()

        except IndexError:
            self.controllerState = {}
            raise inputs.UnpluggedError("No controller found.")
    

    def mapRange(self, value, oldMin, oldMax, newMin=-255, newMax=255):
        # Figure out how 'wide' each range is
        oldRange = oldMax - oldMin
        newRange = newMax - newMin
        NewValue = (((value - oldMin) * newRange) / oldRange) + newMin
        return int(NewValue)

    def parseControllerEvent(self, event):
        if event.code in buttonMappings.keys():
                value = int(event.state)
                actionCode = buttonMappings[event.code]
                if actionCode == "steering":
                    value = self.mapRange(value, oldMin=self.steeringAxisMin, oldMax=self.steeringAxisMax, newMin=-255, newMax=255)
                if actionCode == "brake":
                    value = self.mapRange(value, oldMin=self.brakeAxisMin, oldMax=self.brakeAxisMax, newMin=0, newMax=255)
                if actionCode == "gas":
                    value = self.mapRange(value, oldMin=self.gasAxisMin, oldMax=self.gasAxisMax, newMin=0, newMax=255)
                if actionCode == "hat_y":
                    value *= self.hatModifier
                
                self.controllerState[actionCode] = value

    def getControllerState(self):

        events = get_gamepad()
        for event in events:
            self.parseControllerEvent(event)
        
        return self.controllerState
            


def main():
    import time
    controller = Controller()
    while True:
        startTime = time.time()
        state = controller.getControllerState()
        print(state)


if __name__ == "__main__":
    main()
