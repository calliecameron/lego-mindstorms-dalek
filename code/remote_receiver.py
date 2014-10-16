#!/usr/bin/env python
"""Run this script on the Dalek to receive control messages from
control_remote.py."""

import sys
from dalek import *
from dalek_network import *

class DalekReceiver(Receiver):
    def __init__(self, d):
        super(DalekReceiver, self).__init__()
        self.d = d
        self.start()

    def begin_cmd(self, cmd, factor):
        if cmd == FORWARD:
            self.d.drive.forward(factor)
        elif cmd == REVERSE:
            self.d.drive.reverse(factor)
        elif cmd == TURN_LEFT:
            self.d.drive.turn_left(factor)
        elif cmd == TURN_RIGHT:
            self.d.drive.turn_right(factor)

    def release_cmd(self, cmd):
        if cmd == FORWARD:
            self.d.drive.forward_stop()
        elif cmd == REVERSE:
            self.d.drive.reverse_stop()
        elif cmd == TURN_LEFT:
            self.d.drive.left_stop()
        elif cmd == TURN_RIGHT:
            self.d.drive.right_stop()

    def stop(self):
        self.d.drive.stop()

sound_dir = sys.argv[1]
d = Dalek(sound_dir)

try:
    DalekReceiver(d)
finally:
    d.shutdown()
    sys.exit(0)
