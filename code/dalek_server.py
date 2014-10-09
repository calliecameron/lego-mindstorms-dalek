#!/usr/bin/env python

import SocketServer

class CmdHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        print str(data)
        self.request.sendall(data.upper())

server = SocketServer.TCPServer(("", 12345), CmdHandler)
server.serve_forever()
