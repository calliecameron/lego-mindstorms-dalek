from Mastermind import *
from dalek_common import *

DALEK_PORT = 12345

BEGIN = "begin"
RELEASE = "release"

FORWARD = "forward"
REVERSE = "reverse"
TURN_LEFT = "left"
TURN_RIGHT = "right"

STOP = "stop"


class Controller(object):
    def __init__(self, addr):
        super(Controller, self).__init__()
        self.sock = MastermindClientTCP()
        self.sock.connect(addr, DALEK_PORT)

    def send(self, msg):
        self.sock.send(msg + "\n")

    def begin_cmd(self, cmd, factor=1.0):
        self.send("%s:%s:%f" % (BEGIN, cmd, clamp_percent(factor)))

    def release_cmd(self, cmd):
        self.send("%s:%s" % (RELEASE, cmd))

    def stop(self):
        self.send(STOP)


class Receiver(MastermindServerTCP):
    def __init__(self):
        super(Receiver, self).__init__()

    def start(self):
        self.connect("", DALEK_PORT)
        self.accepting_allow_wait_forever()

    def callback_client_handle(self, connection_object, data):
        msg = str(data).strip().split(":")
        print "Network received: '%s'" % str(msg)
        if len(msg) >= 1:
            if msg[0] == BEGIN:
                if len(msg) >= 3:
                    self.begin_cmd(msg[1], clamp_percent(msg[2]))
                else:
                    self.print_error(data)
            elif msg[0] == RELEASE:
                if len(msg) >= 2:
                    self.release_cmd(msg[1])
                else:
                    self.print_error(data)
            elif msg[0] == STOP:
                self.stop()
            else:
                self.print_error(data)
        else:
            self.print_error(data)

        return super(Receiver, self).callback_client_handle(connection_object, data)

    def print_error(self, data):
        print "Network received bad message: '%s'" % str(data)

    def begin_cmd(self, cmd, factor):
        raise NotImplementedError

    def release_cmd(self, cmd):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError
