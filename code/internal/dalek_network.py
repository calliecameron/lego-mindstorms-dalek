import base64
import socket
import threading
import sys

DALEK_PORT = 12345

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


class Buffer(object):
    def __init__(self):
        self.data = ""

    def add(self, data):
        self.data = self.data + str(data)

    def get(self):
        lines = self.data.split("\n")
        if len(lines) > 1:
            self.data = "\n".join(lines[1:])
            return lines[0]
        else:
            return None


class Controller(threading.Thread):
    def __init__(self, addr):
        super(Controller, self).__init__()
        self.verbose = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            self.sock.connect((addr, DALEK_PORT))
        except socket.error:
            print "Cannot connect to the Dalek - is the address correct?"
            sys.exit(1)
        self.start()

    def toggle_verbose(self):
        self.verbose = not self.verbose

    def send(self, *msg):
        data = ":".join(map(str, msg))
        if self.verbose:
            print "Network sending: '%s'" % data
        self.sock.send(data + "\n")

    def begin_cmd(self, cmd, value):
        self.send(BEGIN, cmd, value)

    def release_cmd(self, cmd, value):
        self.send(RELEASE, cmd, value)

    def stop(self):
        self.send(STOP)

    def play_sound(self, sound):
        self.send(PLAY_SOUND, sound)

    def stop_sound(self):
        self.send(STOP_SOUND)

    def snapshot(self):
        self.send(SNAPSHOT)

    def toggle_lights(self):
        self.send(TOGGLE_LIGHTS)

    def exit(self):
        self.send(EXIT)
        self.sock.close()

    def run(self):
        buf = Buffer()
        while True:
            data = self.sock.recv(4096)
            if not data:
                break

            buf.add(data)

            line = buf.get()
            while line:
                msg = line.strip().split(":")
                if self.verbose:
                    print "Network received: '%s'" % str(msg)
                if len(msg) >= 1:
                    self.handle_recv(msg[0], msg[1:])
                else:
                    print_error(msg)
                line = buf.get()

    def handle_recv(self, cmd, args):
        if cmd == SNAPSHOT:
            if len(args) >= 1:
                self.snapshot_received(base64.b64decode(args[0]))
            else:
                print_error([cmd] + args)
        elif cmd == BATTERY:
            if len(args) >= 1:
                self.battery_received(args[0])
            else:
                print_error([cmd] + args)

    def snapshot_received(self, data):
        raise NotImplementedError

    def battery_received(self, data):
        raise NotImplementedError

class Receiver(object):
    def __init__(self):
        super(Receiver, self).__init__()
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock = None
        self.buf = Buffer()
        self.alive = True

    def start(self):
        self.listen_sock.bind(("", DALEK_PORT))
        self.listen_sock.listen(1)
        (self.sock, _) = self.listen_sock.accept()
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        try:
            while self.alive:
                data = self.sock.recv(4096)
                if not data:
                    break

                self.buf.add(data)

                line = self.buf.get()
                while line:
                    msg = line.strip().split(":")
                    print "Network received: '%s'" % str(msg)
                    if len(msg) >= 1:
                        self.handle_recv(msg[0], msg[1:])
                    else:
                        print_error(msg)
                    line = self.buf.get()

        finally:
            print "Network: shutting down"
            self.sock.close()
            self.listen_sock.close()

    def send(self, *msg):
        if self.sock:
            data = ":".join(map(str, msg))
            self.sock.send(data + "\n")

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
        raise NotImplementedError

    def release_cmd(self, cmd, value):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def play_sound(self, sound):
        raise NotImplementedError

    def stop_sound(self):
        raise NotImplementedError

    def snapshot(self):
        raise NotImplementedError

    def toggle_lights(self):
        raise NotImplementedError
