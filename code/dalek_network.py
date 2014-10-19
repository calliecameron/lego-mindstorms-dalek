# from Mastermind import MastermindClientTCP, MastermindServerTCP
import socket

DALEK_PORT = 12345

BEGIN = "begin"
RELEASE = "release"

DRIVE = "drive"
TURN = "turn"
STOP = "stop"

PLAY_SOUND = "playsound"
STOP_SOUND = "stopsound"


class Controller(object):
    def __init__(self, addr):
        super(Controller, self).__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.connect((addr, DALEK_PORT))
        # self.sock = MastermindClientTCP()
        # self.sock.connect(addr, DALEK_PORT)

    def send(self, msg):
        print "Network sending: '%s'" % msg
        self.sock.send(msg + "\n")

    def begin_cmd(self, cmd, value):
        self.send("%s:%s:%f" % (BEGIN, cmd, value))

    def release_cmd(self, cmd, value):
        self.send("%s:%s:%f" % (RELEASE, cmd, value))

    def stop(self):
        self.send(STOP)

    def play_sound(self, sound):
        self.send("%s:%s" % (PLAY_SOUND, sound))

    def stop_sound(self):
        self.send(STOP_SOUND)


# class Receiver(MastermindServerTCP):
class Receiver(object):
    def __init__(self):
        super(Receiver, self).__init__()
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock = None

    def start(self):
        self.listen_sock.bind(("", DALEK_PORT))
        self.listen_sock.listen(1)
        (self.sock, _) = self.listen_sock.accept()
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        while True:
            data = self.sock.recv(4096)
            self.callback_client_handle(None, data)

        # self.connect("", DALEK_PORT)
        # self.accepting_allow_wait_forever()

    def callback_client_handle(self, connection_object, data):
        msg = str(data).strip().split(":")
        print "Network received: '%s'" % str(msg)
        if len(msg) >= 1:
            if msg[0] == BEGIN:
                if len(msg) >= 3:
                    self.begin_cmd(msg[1], msg[2])
                else:
                    self.print_error(data)
            elif msg[0] == RELEASE:
                if len(msg) >= 3:
                    self.release_cmd(msg[1], msg[2])
                else:
                    self.print_error(data)
            elif msg[0] == STOP:
                self.stop()
            elif msg[0] == PLAY_SOUND:
                if len(msg) >= 2:
                    self.play_sound(msg[1])
                else:
                    self.print_error(data)
            elif msg[0] == STOP_SOUND:
                self.stop_sound()
            else:
                self.print_error(data)
        else:
            self.print_error(data)

        # return super(Receiver, self).callback_client_handle(connection_object, data)

    def print_error(self, data):
        print "Network received bad message: '%s'" % str(data)

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
