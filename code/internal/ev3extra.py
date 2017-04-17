"""ev3dev's LEDs don't seem to work, so use a custom one instead."""

import os.path
import time


class Leds(object):
    def __init__(self, port):
        super(Leds, self).__init__()

        port_map = {"A": "4", "B": "5", "C": "6", "D": "7"}
        mode_path = (
            "/sys/devices/platform/legoev3-ports/lego-port/port%s/mode" %
            port_map[port])
        with open(mode_path, "w") as f:
            f.write("led\n")

        # Give the system time to set up the changes
        time.sleep(1)

        self.control_path = (
            "/sys/bus/lego/devices/out%s:rcx-led/leds/out%s::ev3dev/brightness"
            % (port, port))
        if not os.path.exists(self.control_path):
            raise Exception("Cannot find LEDs on port %s" % port)
        self.off()
        print "Created LEDs"

    def get_brightness(self):
        with open(self.control_path) as f:
            return int(f.read().strip())

    def set_brightness(self, brightness):
        brightness = int(brightness)
        if brightness < 0:
            brightness = 0
        elif brightness > 100:
            brightness = 100

        with open(self.control_path, "w") as f:
            f.write(str(brightness) + "\n")

    def on(self):
        self.set_brightness(100)

    def off(self):
        self.set_brightness(0)

    def toggle(self):
        if self.get_brightness() > 0:
            self.off()
        else:
            self.on()
