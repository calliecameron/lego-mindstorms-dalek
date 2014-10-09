import threading
import time
from ev3.lego import LargeMotor, MediumMotor

TICK_LENGTH_SECONDS = 0.1
DRIVE_SPEED = -700
TURN_SPEED = -500
DALEK_PORT = 12345

def clamp_percent(factor):
    factor = float(factor)
    if factor < 0.0:
        return 0.0
    elif factor > 1.0:
        return 1.0
    else:
        return factor

class RunAfter(object):
    def __init__(self, seconds, action):
        super(RunAfter, self).__init__()
        self.ticks = int(seconds / TICK_LENGTH_SECONDS)
        self.action = action

    def __call__(self):
        if self.ticks == 0:
            self.action()
            return False
        else:
            self.ticks -= 1
            return True


class EventQueue(object):
    def __init__(self):
        super(EventQueue, self).__init__()
        self.queue = []
        self.lock = threading.RLock()

    def add(self, *events):
        self.lock.acquire()
        for e in events:
            self.queue.append(e)
        self.lock.release()

    def clear(self):
        self.lock.acquire()
        self.queue = []
        self.lock.release()

    def replace(self, *events):
        self.lock.acquire()
        self.queue = []
        for e in events:
            self.queue.append(e)
        self.lock.release()

    def process(self):
        self.lock.acquire()
        i = 0
        while i < len(self.queue):
            if self.queue[i]():
                i += 1
            else:
                del self.queue[i]
        self.lock.release()


class Drive(EventQueue):
    def __init__(self):
        super(Drive, self).__init__()

        def init_wheel(port):
            wheel = LargeMotor(port)
            wheel.reset()
            wheel.regulation_mode = "on"
            wheel.stop_mode = "coast"
            return wheel

        self.left_wheel = init_wheel("D")
        self.right_wheel = init_wheel("A")

    def drive_action(self, speed):
        def action():
            self.left_wheel.pulses_per_second_sp = speed
            self.right_wheel.pulses_per_second_sp = speed
            self.left_wheel.start()
            self.right_wheel.start()
        return action

    def turn_action(self, left_speed, right_speed):
        def action():
            self.left_wheel.pulses_per_second_sp = left_speed
            self.right_wheel.pulses_per_second_sp = right_speed
            self.left_wheel.start()
            self.right_wheel.start()
        return action

    def stop_action(self):
        def action():
            self.left_wheel.stop()
            self.right_wheel.stop()
        return action

    def forward(self, factor=1.0):
        self.replace(self.drive_action(clamp_percent(factor) * DRIVE_SPEED))

    def reverse(self, factor=1.0):
        self.replace(self.drive_action(clamp_percent(factor) * -DRIVE_SPEED))

    def turn_left(self, factor=1.0):
        factor = clamp_percent(factor)
        self.replace(self.turn_action(factor * -TURN_SPEED, factor * TURN_SPEED))

    def turn_right(self, factor=1.0):
        factor = clamp_percent(factor)
        self.replace(self.turn_action(factor * TURN_SPEED, factor * -TURN_SPEED))

    def stop(self):
        self.replace(self.stop_action())

    def shutdown(self):
        self.clear()
        self.stop_action()()

class ControllerThread(threading.Thread):
    def __init__(self, parent):
        super(ControllerThread, self).__init__()
        self.parent = parent

    def run(self):
        while True:
            self.parent.drive.process()
            time.sleep(TICK_LENGTH_SECONDS)

class Dalek(object):
    """Main Dalek controller"""

    def __init__(self, sound_dir):
        super(Dalek, self).__init__()
        self.sound_dir = sound_dir
        self.drive = Drive()
        self.thread = ControllerThread(self)
        self.thread.start()

    def shutdown(self):
        self.drive.shutdown()
