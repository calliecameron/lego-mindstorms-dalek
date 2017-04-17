"""Run this script on the Dalek."""

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import argparse
import base64
import json
import sys
from dalek import Dalek


DALEK_PORT = 12346

# BUSY means that someone else is already connected to the Dalek
READY = "ready"
BUSY = "busy"

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


parser = argparse.ArgumentParser(
    description="Run this on the Dalek so it can be controlled remotely.")
parser.add_argument("soundDir", help="Directory containing sound files")
parser.add_argument("textToSpeech", help="Text to speech command")

args = parser.parse_args()


dalek = Dalek(args.soundDir, args.textToSpeech)
connected = False


class Receiver(WebSocket):
    def handleConnected(self):
        global connected
        try:
            if not connected:
                connected = True
                self.connected = True

                def snapshot_handler(data):
                    self.send_snapshot(data)
                dalek.camera.register_handler(snapshot_handler)

                def battery_handler(data):
                    self.send_battery(data)
                dalek.battery.register_handler(battery_handler)

                self.send_ready()
            else:
                self.connected = False
                self.send_busy()
        except Exception as e:
            print e

    def handleClose(self):
        global connected
        try:
            if self.connected:
                self.stop()
                dalek.camera.clear_handler()
                dalek.battery.clear_handler()
                connected = False
        except Exception as e:
            print e

    def handleMessage(self):
        try:
            if self.connected:
                msg = json.loads(self.data.strip())
                print "Network received: '%s'" % str(msg)
                if type(msg) == list and len(msg) >= 1:
                    self.handle_recv(unicode(msg[0]), map(unicode, msg[1:]))
                else:
                    print_error(msg)
        except Exception as e:
            print e

    def send(self, *msg):
        self.sendMessage(unicode(json.dumps(map(unicode, msg)) + "\n"))

    def send_ready(self):
        self.send(READY, dalek.battery.get_battery_status())

    def send_busy(self):
        self.send(BUSY)

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
            print "Network: shutting down"
            dalek.shutdown()
            sys.exit(0)
        else:
            print_error([cmd] + args)

    def begin_cmd(self, cmd, value):
        if cmd == DRIVE:
            dalek.drive.drive(value)
        elif cmd == TURN:
            dalek.drive.turn(value)
        elif cmd == HEAD_TURN:
            dalek.head.turn(value)

    def release_cmd(self, cmd, value):
        if cmd == DRIVE:
            dalek.drive.drive_release(value)
        elif cmd == TURN:
            dalek.drive.turn_release(value)
        elif cmd == HEAD_TURN:
            dalek.head.turn_release(value)

    def stop(self):
        dalek.drive.stop()

    def play_sound(self, sound):
        dalek.voice.speak(sound)

    def stop_sound(self):
        dalek.voice.stop()

    def snapshot(self):
        dalek.camera.take_snapshot()

    def toggle_lights(self):
        dalek.voice.toggle_lights()


server = SimpleWebSocketServer("", DALEK_PORT, Receiver)
print "Network: starting"
server.serveforever()
