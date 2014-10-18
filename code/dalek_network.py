from Mastermind import MastermindClientTCP, MastermindServerTCP

DALEK_PORT = 12345

BEGIN = "begin"
RELEASE = "release"
DRIVE = "drive"
TURN = "turn"
STOP = "stop"


class Controller(object):
    def __init__(self, addr):
        super(Controller, self).__init__()
        self.sock = MastermindClientTCP()
        self.sock.connect(addr, DALEK_PORT)

    def send(self, msg):
        print "Network sending: '%s'" % msg
        self.sock.send(msg + "\n")

    def begin_cmd(self, cmd, value):
        self.send("%s:%s:%f" % (BEGIN, cmd, value))

    def release_cmd(self, cmd, value):
        self.send("%s:%s:%f" % (RELEASE, cmd, value))

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
            else:
                self.print_error(data)
        else:
            self.print_error(data)

        return super(Receiver, self).callback_client_handle(connection_object, data)

    def print_error(self, data):
        print "Network received bad message: '%s'" % str(data)

    def begin_cmd(self, cmd, value):
        raise NotImplementedError

    def release_cmd(self, cmd, value):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError
