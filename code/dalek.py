"""Main logic for the Dalek. Use one of the other scripts to actually control it."""

import threading
import time
from ev3.lego import LargeMotor, TouchSensor
from dalek_common import *

TICK_LENGTH_SECONDS = 0.1
DRIVE_SPEED = -700
TURN_SPEED = -500

DRIVE_STOP = 0
DRIVE_FORWARD = 1
DRIVE_REVERSE = 2
DRIVE_LEFT = 3
DRIVE_RIGHT = 4

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
        self.pre_process()
        i = 0
        while i < len(self.queue):
            if self.queue[i]():
                i += 1
            else:
                del self.queue[i]
        self.post_process()
        self.lock.release()

    def pre_process(self):
        pass

    def post_process(self):
        pass


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
        self.touch_sensor = TouchSensor(2)
        self.drive_state = DRIVE_STOP
        self.drive_factor = 0.0
        self.ticks_since_last = 0

    def drive_action(self, speed, state, factor):
        def action():
            self.drive_state = state
            self.drive_factor = factor
            self.left_wheel.pulses_per_second_sp = speed
            self.right_wheel.pulses_per_second_sp = speed
            self.left_wheel.start()
            self.right_wheel.start()
            self.ticks_since_last = 0
        return action

    def turn_action(self, left_speed, right_speed, state, factor):
        def action():
            self.drive_state = state
            self.drive_factor = factor
            self.left_wheel.pulses_per_second_sp = left_speed
            self.right_wheel.pulses_per_second_sp = right_speed
            self.left_wheel.start()
            self.right_wheel.start()
            self.ticks_since_last = 0
        return action

    def stop_action(self):
        def action():
            self.drive_state = DRIVE_STOP
            self.drive_factor = 0.0
            self.left_wheel.stop()
            self.right_wheel.stop()
            self.ticks_since_last = 0
        return action

    def conditional_stop_action(self, state):
        def action():
            if self.drive_state == state:
                self.ticks_since_last = 101
        return action

    def pre_process(self):
        if self.touch_sensor.is_pushed:
            self.shutdown()
        self.ticks_since_last += 1

    def post_process(self):
        if self.ticks_since_last > 100:
            self.shutdown()

    def forward(self, factor=1.0):
        self.replace(self.drive_action(clamp_percent(factor) * DRIVE_SPEED, DRIVE_FORWARD, clamp_percent(factor)))

    def reverse(self, factor=1.0):
        self.replace(self.drive_action(clamp_percent(factor) * -DRIVE_SPEED, DRIVE_REVERSE, clamp_percent(factor)))

    def turn_left(self, factor=1.0):
        factor = clamp_percent(factor)
        self.replace(self.turn_action(factor * -TURN_SPEED, factor * TURN_SPEED, DRIVE_LEFT, factor))

    def turn_right(self, factor=1.0):
        factor = clamp_percent(factor)
        self.replace(self.turn_action(factor * TURN_SPEED, factor * -TURN_SPEED, DRIVE_RIGHT, factor))

    def stop(self):
        self.replace(self.stop_action())

    def forward_stop(self):
        self.add(self.conditional_stop_action(DRIVE_FORWARD))

    def reverse_stop(self):
        self.add(self.conditional_stop_action(DRIVE_REVERSE))

    def left_stop(self):
        self.add(self.conditional_stop_action(DRIVE_LEFT))

    def right_stop(self):
        self.add(self.conditional_stop_action(DRIVE_RIGHT))

    def shutdown(self):
        self.clear()
        self.stop_action()()


class ControllerThread(threading.Thread):
    def __init__(self, parent):
        super(ControllerThread, self).__init__()
        self.parent = parent
        self.daemon = True

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
