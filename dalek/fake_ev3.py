"""Fake versions of some ev3dev classes, so the networking code can be tested
without having the real ev3 to hand."""

import time
import subprocess


class Motor(object):
    def __init__(self, port, mtype):
        super(Motor, self).__init__()
        self.port = port
        self.mtype = mtype
        self.speed_regulation_enabled = "off"
        self.stop_command = "coast"
        self.speed_sp = 0
        self.position = 0
        self.ramp_up_sp = 0
        self.ramp_down_sp = 0

    def stop(self):
        self.msg("stop")

    def run_forever(self):
        self.msg("run_forever")

    def reset(self):
        self.msg("reset")

    def msg(self, s):
        print "[%sMotor %s] %s" % (self.mtype, self.port, s)


class LargeMotor(Motor):
    def __init__(self, port):
        super(LargeMotor, self).__init__(port, "Large")


class MediumMotor(Motor):
    def __init__(self, port):
        super(MediumMotor, self).__init__(port, "Medium")


class TouchSensor(object):
    def __init__(self, port):
        super(TouchSensor, self).__init__()
        self.port = port

    def value(self):
        return 0


class PowerSupply(object):
    def __init__(self):
        super(PowerSupply, self).__init__()
        self.measured_volts = 8


class Leds(object):
    def __init__(self, port):
        super(Leds, self).__init__()
        time.sleep(1)
        self.port = port
        self.brightness = 0
        self.off()
        print "Created LEDs"

    def get_brightness(self):
        return self.brightness

    def set_brightness(self, brightness):
        brightness = int(brightness)
        if brightness < 0:
            brightness = 0
        elif brightness > 100:
            brightness = 100
        self.brightness = brightness
        print "[LEDs %s] brightness %d" % (self.port, self.brightness)
        if self.brightness > 0:
            subprocess.call(["xset", "led", "named", "Scroll Lock"])
        else:
            subprocess.call(["xset", "-led", "named", "Scroll Lock"])

    def on(self):
        self.set_brightness(100)

    def off(self):
        self.set_brightness(0)

    def toggle(self):
        if self.get_brightness() > 0:
            self.off()
        else:
            self.on()
