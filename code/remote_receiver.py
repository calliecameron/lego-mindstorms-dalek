#!/usr/bin/env python

import sys
from dalek import Dalek, DALEK_PORT
from Mastermind import *

class Server(MastermindServerTCP):
    def __init__(self, d):
        super(Server, self).__init__()
        self.d = d
        self.connect("", DALEK_PORT)
        self.accepting_allow_wait_forever()

    def callback_client_handle(self, connection_object, data):
        cmd = str(data).strip().split(":")
        if cmd[0] == "forward":
            if len(cmd) > 1:
                factor = float(cmd[1])
            else:
                factor = 1.0
            self.d.drive.forward(factor)
        elif cmd[0] == "reverse":
            if len(cmd) > 1:
                factor = float(cmd[1])
            else:
                factor = 1.0
            self.d.drive.reverse(factor)
        elif cmd[0] == "stop":
            self.d.drive.stop()

        return super(Server, self).callback_client_handle(connection_object, data)

sound_dir = sys.argv[1]
d = Dalek(sound_dir)

try:
    Server(d)
finally:
    print "foo"
    d.shutdown()
    sys.exit(0)
    print "bar"
