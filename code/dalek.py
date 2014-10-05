"""Dalek control classes."""

import time
import os.path
import subprocess
from ev3.lego import LargeMotor, MediumMotor

DRIVE_SPEED = -700
TURN_SPEED = -500

def clamp_percent(factor):
    if factor < 0.0:
        return 0.0
    elif factor > 1.0:
        return 1.0
    else:
        return factor

def wait_for_stop(motor):
    time.sleep(0.5)
    while motor.pulses_per_second != 0:
        time.sleep(0.1)


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

    def forward(self, factor=1.0):
        factor = clamp_percent(factor)
        self.left_wheel.pulses_per_second_sp = factor * DRIVE_SPEED
        self.right_wheel.pulses_per_second_sp = factor * DRIVE_SPEED
        self.left_wheel.start()
        self.right_wheel.start()

    def reverse(self, factor=1.0):
        factor = clamp_percent(factor)
        self.left_wheel.pulses_per_second_sp = factor * -DRIVE_SPEED
        self.right_wheel.pulses_per_second_sp = factor * -DRIVE_SPEED
        self.left_wheel.start()
        self.right_wheel.start()

    def turn_left(self, factor=1.0):
        factor = clamp_percent(factor)
        self.left_wheel.pulses_per_second_sp = factor * -TURN_SPEED
        self.right_wheel.pulses_per_second_sp = factor * TURN_SPEED
        self.left_wheel.start()
        self.right_wheel.start()

    def turn_right(self, factor=1.0):
        factor = clamp_percent(factor)
        self.left_wheel.pulses_per_second_sp = factor * TURN_SPEED
        self.right_wheel.pulses_per_second_sp = factor * -TURN_SPEED
        self.left_wheel.start()
        self.right_wheel.start()

    def stop(self):
        self.left_wheel.stop()
        self.right_wheel.stop()

    def play_sound(self, sound):
        path = os.path.join(self.sounds_dir, sound + ".wav")
        if os.path.exists(path):
            subprocess.Popen(["aplay", path])

    def exterminate(self):
        self.play_sound("exterminate")


class Head(object):
    """Dalek's head."""

    def __init__(self):
        super(Head, self).__init__()
        self.head_motor = MediumMotor("B")
        self.initialise()

    def initialise(self):
        self.head_motor.reset()
        self.head_motor.regulation_mode = "off"
        self.head_motor.stop_mode = "coast"

        self.head_motor.duty_cycle_sp = 65
        self.head_motor.start()
        wait_for_stop(self.head_motor)
        self.head_motor.stop()
        pos1 = self.head_motor.position

        self.head_motor.duty_cycle_sp = -65
        self.head_motor.start()
        wait_for_stop(self.head_motor)
        self.head_motor.stop()
        pos2 = self.head_motor.position

        midpoint = (pos1 + pos2) / 2.0

        self.head_motor.regulation_mode = "on"
        self.head_motor.stop_mode = "hold"
        self.head_motor.ramp_up_sp = 500
        self.head_motor.ramp_down_sp = 200
        self.head_motor.run_position_limited(midpoint, 400)
        wait_for_stop(self.head_motor)
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
        wait_for_stop(self.head_motor)
        self.head_motor.stop()
        self.head_motor.stop_mode = "brake"

    def rotate(self, deg):
        self.rotate_to(self.head_motor.position + deg)
