"""Dalek control classes."""

from ev3.lego import LargeMotor, MediumMotor

class Dalek(object):
    """Main class for controlling the Dalek."""

    def __init__(self, sounds_dir):
        super(Dalek, self).__init__()
        self.sounds_dir = sounds_dir
        self.left_wheel = LargeMotor("D")
        self.right_wheel = LargeMotor("A")
        self.head_motor = MediumMotor("B")
