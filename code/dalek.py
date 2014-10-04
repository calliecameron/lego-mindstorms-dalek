"""Dalek control classes."""

from ev3.lego import LargeMotor, MediumMotor

DRIVE_SPEED = -700


class Dalek(object):
    """Main class for controlling the Dalek."""

    def __init__(self, sounds_dir):
        super(Dalek, self).__init__()
        self.sounds_dir = sounds_dir
        self.left_wheel = LargeMotor("D")
        self.right_wheel = LargeMotor("A")
        self.head_motor = MediumMotor("B")
        self.init_wheel(self.left_wheel)
        self.init_wheel(self.right_wheel)

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

    def forward(self, factor):
        factor = self.clamp_percent(factor)
        self.left_wheel.pulses_per_second_sp = factor * DRIVE_SPEED
        self.right_wheel.pulses_per_second_sp = factor * DRIVE_SPEED
        self.left_wheel.start()
        self.right_wheel.start()

    def reverse(self, factor):
        factor = self.clamp_percent(factor)
        self.left_wheel.pulses_per_second_sp = factor * -DRIVE_SPEED
        self.right_wheel.pulses_per_second_sp = factor * -DRIVE_SPEED
        self.left_wheel.start()
        self.right_wheel.start()

    def stop(self):
        self.left_wheel.stop()
        self.right_wheel.stop()
