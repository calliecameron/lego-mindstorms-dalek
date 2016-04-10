"""Run this script on the Dalek."""

import base64
from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import argparse
import sys
from dalek import Dalek


DALEK_PORT = 12346

EXIT = "exit"

BEGIN = "begin"
RELEASE = "release"

DRIVE = "drive"
TURN = "turn"
STOP = "stop"

HEAD_TURN = "headturn"

PLAY_SOUND = "playsound"
STOP_SOUND = "stopsound"

SNAPSHOT = "snapshot"

TOGGLE_LIGHTS = "togglelights"

BATTERY = "battery"


def print_error(data):
    print "Network received bad message: '%s'" % str(data)


parser = argparse.ArgumentParser(description="Run this on the Dalek so it can be controlled remotely.")
parser.add_argument("soundDir", help="Directory containing sound files")

args = parser.parse_args()


class Receiver(WebSocket):
    def handleConnected(self):
        self.d = Dalek(args.soundDir)

        def snapshot_handler(data):
            self.send_snapshot(data)
        self.d.camera.register_handler(snapshot_handler)

        def battery_handler(data):
            self.send_battery(data)
        self.d.battery.register_handler(battery_handler)

    def handleClose(self):
        print "Network: shutting down"
        self.d.shutdown()

    def handleMessage(self):
        msg = map(str, self.data.strip().split(":"))
        print "Network received: '%s'" % str(msg)
        if len(msg) >= 1:
            self.handle_recv(msg[0], msg[1:])
        else:
            print_error(msg)

    def send(self, *msg):
        self.sendMessage(u":".join(map(unicode, msg)))

    def send_snapshot(self, data):
        self.send(SNAPSHOT, base64.b64encode(data))

    def send_battery(self, data):
        self.send(BATTERY, data)

    def handle_recv(self, cmd, args):
        if cmd == BEGIN:
            if len(args) >= 2:
                self.begin_cmd(args[0], args[1])
            else:
                print_error([cmd] + args)
        elif cmd == RELEASE:
            if len(args) >= 2:
                self.release_cmd(args[0], args[1])
            else:
                print_error([cmd] + args)
        elif cmd == STOP:
            self.stop()
        elif cmd == PLAY_SOUND:
            if len(args) >= 1:
                self.play_sound(args[0])
            else:
                print_error([cmd] + args)
        elif cmd == STOP_SOUND:
            self.stop_sound()
        elif cmd == SNAPSHOT:
            self.snapshot()
        elif cmd == TOGGLE_LIGHTS:
            self.toggle_lights()
        elif cmd == EXIT:
            self.alive = False
        else:
            print_error([cmd] + args)

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

    def toggle_lights(self):
        self.d.voice.toggle_lights()

server = SimpleWebSocketServer("", 12346, Receiver)
print "Starting"
server.serveforever()
