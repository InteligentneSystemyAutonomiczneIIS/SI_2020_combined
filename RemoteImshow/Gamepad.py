import inputs
import threading
import time
import importlib


class GamepadState:
    def __init__(self):

        self.gamepad = None
        self.useRawValues = False
        
        self.axes = [0, 0, 0, 0]  # [left_x, left_y, right_x, right_y]
        self.triggers = [0, 0]  # [left_trigger, right_trigger]
        self.buttons = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # [X, Y, A, B, LB, RB, LS, RS, Back, Start]
        self.update_thread = threading.Thread(target=self.update_state_loop, daemon=True)
        self.update_thread.start()

        self.stickMaxValue = 32768
        self.triggersMaxValue = 255
        self.leftStickDeadzoneX = 0.15
        self.leftStickDeadzoneY = 0.15
        self.rightStickDeadzoneX = 0.15
        self.rightStickDeadzoneY = 0.15
        self.leftTriggerDeadzone = 0.00
        self.rightTriggerDeadzone = 0.00


    def reset_gamepad(self):
        # Gamepad is disconnected, reset state
        self.axes = [0, 0, 0, 0]
        self.triggers = [0, 0]
        self.buttons = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


    def normalize_axis_value(self, value, deadzone, maxValue):
        # Normalize the value of an axis to a range from -1 to 1
        if self.useRawValues:
            return value / maxValue
        else:
            if value > deadzone:
                # round to 4 digits after the decimal
                return round((value - deadzone) / (maxValue - deadzone), 4)
            elif value < -deadzone:
                # round to 4 digits after the decimal
                return round((value + deadzone) / (maxValue - deadzone), 4)
            else:
                return 0


    def update_state_loop(self):
        while True:
            try:
                self.gamepad = inputs.devices.gamepads[0]
            except IndexError:
                # the only way to detect gamepads connected after the program start is to reimport inputs lib
                self.gamepad = None
                self.reset_gamepad()
                time.sleep(5)
                importlib.reload(inputs)

            if self.gamepad is not None:
                try:
                    events = self.gamepad.read()
                    self.process_events(events)
                except:
                    self.gamepad = None
                    self.reset_gamepad()
            else:
                self.reset_gamepad()
                
    def process_events(self, events):
        for event in events:
            if event.ev_type == 'Absolute':
                if event.code == 'ABS_X':
                    if abs(event.state) < self.leftStickDeadzoneX * self.stickMaxValue:
                        self.axes[0] = 0
                    else:
                        if self.useRawValues:
                            self.axes[0] = event.state
                        else:
                            self.axes[0] = self.normalize_axis_value(event.state, self.leftStickDeadzoneX, self.stickMaxValue)
                elif event.code == 'ABS_Y':
                    if abs(event.state) < self.leftStickDeadzoneY * self.stickMaxValue:
                        self.axes[1] = 0
                    else:
                        if self.useRawValues:
                            self.axes[1] = event.state
                        else:
                            self.axes[1] = self.normalize_axis_value(event.state, self.leftStickDeadzoneY, self.stickMaxValue)
                elif event.code == 'ABS_RX':
                    if abs(event.state) < self.rightStickDeadzoneX * self.stickMaxValue:
                        self.axes[2] = 0
                    else:
                        if self.useRawValues:
                            self.axes[2] = event.state
                        else:
                            self.axes[2] = self.normalize_axis_value(event.state, self.rightStickDeadzoneX, self.stickMaxValue)
                elif event.code == 'ABS_RY':
                    if abs(event.state) < self.rightStickDeadzoneY * self.stickMaxValue:
                        self.axes[3] = 0
                    else:
                        if self.useRawValues:
                            self.axes[3] = event.state
                        else:
                            self.axes[3] = self.normalize_axis_value(event.state, self.rightStickDeadzoneY, self.stickMaxValue)
                elif event.code == 'ABS_Z':
                    if abs(event.state) < self.leftTriggerDeadzone * self.triggersMaxValue:
                        self.triggers[0] = 0
                    else:

                        if self.useRawValues:
                            self.triggers[0] = event.state
                        else:
                            self.triggers[0] = self.normalize_axis_value(event.state, self.leftTriggerDeadzone, self.triggersMaxValue)
                elif event.code == 'ABS_RZ':
                    if abs(event.state) < self.rightTriggerDeadzone * self.triggersMaxValue:
                        self.triggers[1] = 0
                    else:
                        if self.useRawValues:
                            self.triggers[1] = event.state
                        else:
                            self.triggers[1] = self.normalize_axis_value(event.state, self.rightTriggerDeadzone, self.triggersMaxValue)

            elif event.ev_type == 'Key':
                if event.code == 'BTN_SOUTH':
                    self.buttons[0] = event.state
                elif event.code == 'BTN_EAST':
                    self.buttons[1] = event.state
                elif event.code == 'BTN_WEST':
                    self.buttons[2] = event.state
                elif event.code == 'BTN_NORTH':
                    self.buttons[3] = event.state
                elif event.code == 'BTN_TL':  # Left Bumper
                    self.buttons[4] = event.state
                elif event.code == 'BTN_TR':  # Right Bumper
                    self.buttons[5] = event.state
                elif event.code == 'BTN_THUMBL':  # Left Thumbstick
                    self.buttons[6] = event.state
                elif event.code == 'BTN_THUMBR':  # Right Thumbstick
                    self.buttons[7] = event.state
                elif event.code == 'BTN_START':  # Back Button
                    self.buttons[8] = event.state
                elif event.code == 'BTN_SELECT':  # Start Button
                    self.buttons[9] = event.state

    
    def get_state(self):
        return self.axes, self.triggers, self.buttons


if __name__ == '__main__':
    gamepad_state = GamepadState()
    time_now = time.time()
    while True:
        time_from_start = time.time() - time_now
        axes, triggers, buttons = gamepad_state.get_state()
        print(f"Timestamp: {round(time_from_start, 2)}; Axes: {axes}, Triggers: {triggers}, Buttons: {buttons}")
        time.sleep(1/120)