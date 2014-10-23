"""Run this script on the Dalek to receive control messages from
control_remote.py."""

import argparse
import sys
from dalek import Dalek
from dalek_network import Receiver, DRIVE, TURN, HEAD_TURN

parser = argparse.ArgumentParser(description="Run this on the Dalek so it can be controlled remotely.")
parser.add_argument("soundDir", help="Directory containing sound files")

args = parser.parse_args()


class DalekReceiver(Receiver):
    def __init__(self, d):
        super(DalekReceiver, self).__init__()
        self.d = d

        def snapshot_handler(data):
            self.send_snapshot(data)
        self.d.camera.register_handler(snapshot_handler)

        self.start()

    def begin_cmd(self, cmd, value):
        if cmd == DRIVE:
            self.d.drive.drive(value)
        elif cmd == TURN:
            self.d.drive.turn(value)
        elif cmd == HEAD_TURN:
            self.d.head.turn(value)

    def release_cmd(self, cmd, value):
        if cmd == DRIVE:
            self.d.drive.drive_release(value)
        elif cmd == TURN:
            self.d.drive.turn_release(value)
        elif cmd == HEAD_TURN:
            self.d.head.turn_release(value)

    def stop(self):
        self.d.drive.stop()

    def play_sound(self, sound):
        self.d.voice.speak(sound)

    def stop_sound(self):
        self.d.voice.stop()

    def snapshot(self):
        self.d.camera.take_snapshot()

dalek = Dalek(args.soundDir, False)

try:
    DalekReceiver(dalek)
finally:
    dalek.shutdown()
    sys.exit(0)
