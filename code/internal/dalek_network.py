
# import socket
# import threading
# import sys

# class Buffer(object):
#     def __init__(self):
#         self.data = ""

#     def add(self, data):
#         self.data = self.data + str(data)

#     def get(self):
#         lines = self.data.split("\n")
#         if len(lines) > 1:
#             self.data = "\n".join(lines[1:])
#             return lines[0]
#         else:
#             return None


# class RemoteController(threading.Thread):
#     def __init__(self, addr, snapshot_handler, battery_handler):
#         super(RemoteController, self).__init__()
#         self.snapshot_handler = snapshot_handler
#         self.battery_handler = battery_handler
#         self.verbose = False
#         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
#         try:
#             self.sock.connect((addr, DALEK_PORT))
#         except socket.error:
#             print "Cannot connect to the Dalek - is the address correct?"
#             sys.exit(1)
#         self.start()

#     def toggle_verbose(self):
#         self.verbose = not self.verbose

#     def send(self, *msg):
#         data = ":".join(map(str, msg))
#         if self.verbose:
#             print "Network sending: '%s'" % data
#         self.sock.send(data + "\n")

#     def begin_cmd(self, cmd, value):
#         self.send(BEGIN, cmd, value)

#     def release_cmd(self, cmd, value):
#         self.send(RELEASE, cmd, value)

#     def stop(self):
#         self.send(STOP)

#     def play_sound(self, sound):
#         self.send(PLAY_SOUND, sound)

#     def stop_sound(self):
#         self.send(STOP_SOUND)

#     def snapshot(self):
#         self.send(SNAPSHOT)

#     def toggle_lights(self):
#         self.send(TOGGLE_LIGHTS)

#     def exit(self):
#         self.send(EXIT)
#         self.sock.close()

#     def run(self):
#         buf = Buffer()
#         while True:
#             data = self.sock.recv(4096)
#             if not data:
#                 break

#             buf.add(data)

#             line = buf.get()
#             while line:
#                 msg = line.strip().split(":")
#                 if self.verbose:
#                     print "Network received: '%s'" % str(msg)
#                 if len(msg) >= 1:
#                     self.handle_recv(msg[0], msg[1:])
#                 else:
#                     print_error(msg)
#                 line = buf.get()

#     def handle_recv(self, cmd, args):
#         if cmd == SNAPSHOT:
#             if len(args) >= 1:
#                 self.snapshot_handler(base64.b64decode(args[0]))
#             else:
#                 print_error([cmd] + args)
#         elif cmd == BATTERY:
#             if len(args) >= 1:
#                 self.battery_handler(args[0])
#             else:
#                 print_error([cmd] + args)

