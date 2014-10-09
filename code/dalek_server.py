#!/usr/bin/env python

from Mastermind import *

class Server(MastermindServerTCP):
    def __init__(self):
        super(Server, self).__init__()
        self.connect("192.168.0.11", 12345)
        self.accepting_allow_wait_forever()

    def callback_client_handle(self, connection_object, data):
        print str(data)
        return super(Server, self).callback_client_handle(connection_object, data)

Server()
