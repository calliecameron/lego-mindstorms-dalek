"""Use this script to control the Dalek from a shell on the Dalek
itself (i.e. through an SSH session). Controls are different from (and
less intuitive than) the pygame-based remote controller."""

import argparse
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

parser = argparse.ArgumentParser(description="Control the Dalek directly from the terminal")
parser.add_argument("soundDir", help="Directory containing sound files")

args = parser.parse_args()
d = Dalek(args.soundDir)

print "Dalek controller: press 'p' to exit (note that Ctrl-C doesn't work!)"

try:
    while True:
        cmd = getch()

        if cmd == "w":
            d.drive.drive(1.0)
        elif cmd == "W":
            d.drive.drive(0.5)
        elif cmd == "x":
            d.drive.drive(-1.0)
        elif cmd == "X":
            d.drive.drive(-0.5)
        elif cmd == "a":
            d.drive.turn(1.0)
        elif cmd == "A":
            d.drive.turn(0.5)
        elif cmd == "d":
            d.drive.turn(-1.0)
        elif cmd == "D":
            d.drive.turn(-0.5)
        elif cmd == "s" or cmd == "S":
            d.drive.stop()
        elif cmd == "p":
            break

finally:
    d.shutdown()
    sys.exit(0)
