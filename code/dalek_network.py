import socket

DALEK_PORT = 12345

EXIT = "exit"

BEGIN = "begin"
RELEASE = "release"

DRIVE = "drive"
TURN = "turn"
STOP = "stop"

PLAY_SOUND = "playsound"
STOP_SOUND = "stopsound"


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


class Controller(object):
    def __init__(self, addr):
        super(Controller, self).__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.connect((addr, DALEK_PORT))

    def send(self, *msg):
        data = ":".join(map(str, msg))
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

    def exit(self):
        self.send(EXIT)
        self.sock.close()


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
