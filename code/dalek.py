"""Dalek control classes."""

import time
from ev3.lego import LargeMotor, MediumMotor

DRIVE_SPEED = -700


class Dalek(object):
    """Main class for controlling the Dalek."""

    def __init__(self, sounds_dir):
        super(Dalek, self).__init__()
        self.sounds_dir = sounds_dir
        self.left_wheel = LargeMotor("D")
        self.right_wheel = LargeMotor("A")
        self.init_wheel(self.left_wheel)
        self.init_wheel(self.right_wheel)
        self.head = Head()

    def init_wheel(self, wheel):
        wheel.reset()
        wheel.regulation_mode = "on"
        wheel.stop_mode = "coast"

    def clamp_percent(self, factor):
        if factor < 0.0:
            return 0.0
        elif factor > 1.0:
            return 1.0
        else:
            return factor

    def forward(self, factor=1.0):
        factor = self.clamp_percent(factor)
        self.left_wheel.pulses_per_second_sp = factor * DRIVE_SPEED
        self.right_wheel.pulses_per_second_sp = factor * DRIVE_SPEED
        self.left_wheel.start()
        self.right_wheel.start()

    def reverse(self, factor=1.0):
        factor = self.clamp_percent(factor)
        self.left_wheel.pulses_per_second_sp = factor * -DRIVE_SPEED
        self.right_wheel.pulses_per_second_sp = factor * -DRIVE_SPEED
        self.left_wheel.start()
        self.right_wheel.start()

    def stop(self):
        self.left_wheel.stop()
        self.right_wheel.stop()

class Head(object):
    """Dalek's head."""

    def __init__(self):
        super(Head, self).__init__()
        self.head_motor = MediumMotor("B")

    def initialise(self):
        self.head_motor.reset()
        self.head_motor.regulation_mode = "off"
        self.head_motor.stop_mode = "coast"

        self.head_motor.duty_cycle_sp = 75
        self.head_motor.start()
        time.sleep(2)
        self.head_motor.stop()
        pos1 = self.head_motor.position

        self.head_motor.duty_cycle_sp = -75
        self.head_motor.start()
        time.sleep(2)
        self.head_motor.stop()
        pos2 = self.head_motor.position

        midpoint = (pos1 + pos2) / 2.0

        self.head_motor.regulation_mode = "on"
        self.head_motor.stop_mode = "hold"
        self.head_motor.ramp_up_sp = 500
        self.head_motor.ramp_down_sp = 200
        self.head_motor.run_position_limited(midpoint, 400)
        time.sleep(2)
        self.head_motor.stop()
        self.head_motor.position = 0
        self.head_motor.stop_mode = "brake"

    def rotate_to(self, pos):
        if pos > 135:
            pos = 135
        elif pos < -135:
            pos = -135

        self.head_motor.regulation_mode = "on"
        self.head_motor.stop_mode = "hold"
        self.head_motor.ramp_up_sp = 500
        self.head_motor.ramp_down_sp = 200
        self.head_motor.run_position_limited(pos, 400)
        time.sleep(2)
        self.head_motor.stop()
        self.head_motor.stop_mode = "brake"

    def rotate(self, deg):
        self.rotate_to(self.head_motor.position + deg)
