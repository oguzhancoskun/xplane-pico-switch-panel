# DIY switch panel: 7 ON-ON toggles + 1 ON-OFF-ON toggle, one indicator LED each.
# Every toggle's middle leg goes to GND; its outer leg(s) go to the pins below.
# Each LED: pin -> 330 ohm -> LED long leg; LED short leg -> GND.
#
# Each switch position briefly presses one or more joystick buttons, so X-Plane
# (one command per button) can map every position to its own commands.
import time

import board
import digitalio
import usb_hid

PULSE_S = 0.15
DEBOUNCE_S = 0.03

# (label, input pins, LED pin, buttons per position)
# An LED lights the wrong switch? Swap the LED pins here instead of rewiring.
# Positions: ON-ON = (on, off); ON-OFF-ON = (up, middle, down).
SWITCHES = [
    ("ENGINE", (board.GP0,), board.GP16, ((1,), (2,))),
    ("BATT", (board.GP1,), board.GP17, ((3,), (4,))),
    ("ALT", (board.GP2,), board.GP18, ((5,), (6,))),
    ("AVIONICS", (board.GP3,), board.GP19, ((7,), (8,))),
    ("FUEL PUMP", (board.GP4,), board.GP20, ((9,), (10,))),
    ("BEACON", (board.GP5,), board.GP21, ((11,), (12,))),
    ("NAV", (board.GP6,), board.GP22, ((13,), (14,))),
    # GP7 = up, GP8 = down. 15 landing on, 16 landing off, 17 taxi on, 18 taxi off.
    ("LAND/OFF/TAXI", (board.GP7, board.GP8), board.GP26, ((15, 18), (16, 18), (17, 16))),
]
OFF = 1  # position index meaning "off" for both switch types

joystick = next(d for d in usb_hid.devices if d.usage_page == 0x01 and d.usage == 0x04)
report = bytearray(4)  # 32 buttons


class Switch:
    def __init__(self, label, pins, led_pin, buttons):
        self.label = label
        self.buttons = buttons
        self.inputs = []
        for pin in pins:
            io = digitalio.DigitalInOut(pin)
            io.switch_to_input(pull=digitalio.Pull.UP)
            self.inputs.append(io)
        self.led = digitalio.DigitalInOut(led_pin)
        self.led.switch_to_output()
        self.position = self.read()
        self.led.value = self.position != OFF

    def read(self):
        if not self.inputs[0].value:  # closed contact reads LOW
            return 0
        if len(self.inputs) > 1 and not self.inputs[1].value:
            return 2
        return OFF


def send(mask):
    for i in range(4):
        report[i] = (mask >> (8 * i)) & 0xFF
    try:
        joystick.send_report(report)
    except OSError:
        pass  # host not ready yet (e.g. right after plugging in)


def pulse(buttons):
    mask = 0
    for b in buttons:
        mask |= 1 << (b - 1)
    send(mask)
    time.sleep(PULSE_S)
    send(0)


switches = [Switch(*cfg) for cfg in SWITCHES]

power_led = digitalio.DigitalInOut(board.LED)
power_led.switch_to_output(value=True)

while True:
    for sw in switches:
        position = sw.read()
        if position == sw.position:
            continue
        time.sleep(DEBOUNCE_S)
        position = sw.read()
        if position == sw.position:
            continue
        sw.position = position
        sw.led.value = position != OFF
        print(sw.label, "->", position, "buttons", sw.buttons[position])
        pulse(sw.buttons[position])
    time.sleep(0.005)
