#!/usr/bin/env python

import sys
import termios
import tty
from dalek import Dalek

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    except KeyboardInterrupt:
        raise
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

sound_dir = sys.argv[1]
d = Dalek(sound_dir)

try:
    while True:
        cmd = getch()

        if cmd == "w":
            d.drive.forward()
        elif cmd == "W":
            d.drive.forward(0.5)
        elif cmd == "x":
            d.drive.reverse()
        elif cmd == "X":
            d.drive.reverse(0.5)
        elif cmd == "a":
            d.drive.turn_left()
        elif cmd == "A":
            d.drive.turn_left(0.5)
        elif cmd == "d":
            d.drive.turn_right()
        elif cmd == "D":
            d.drive.turn_right(0.5)
        elif cmd == "s" or cmd == "S":
            d.drive.stop()
        # elif cmd == "q":
        #     d.head.rotate(-45)
        # elif cmd == "e":
        #     d.head.rotate(45)
        # elif cmd == "z":
        #     d.head.rotate_to(0)
        # elif cmd == "r":
        #     d.exterminate()
        # elif cmd == "f":
        #     d.fire()
        elif cmd == "p":
            break

finally:
    d.drive.shutdown()
    sys.exit(0)
    
