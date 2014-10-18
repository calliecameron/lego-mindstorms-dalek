"""Main logic for the Dalek. Use one of the other scripts to actually control it."""

import threading
import time
import subprocess
import os.path
from ev3.lego import LargeMotor, MediumMotor, TouchSensor
from dalek_common import *

TICK_LENGTH_SECONDS = 0.1

DRIVE_SPEED = -700
TURN_SPEED = -500
DRIVE_STOP = 0
DRIVE_FORWARD = 1
DRIVE_REVERSE = 2
DRIVE_LEFT = 3
DRIVE_RIGHT = 4

HEAD_LIMIT = 135
HEAD_STOP = 0
HEAD_LEFT = 1
HEAD_RIGHT = 2


class RunAfterTime(object):
    def __init__(self, seconds, action):
        super(RunAfterTime, self).__init__()
        self.ticks = int(seconds / TICK_LENGTH_SECONDS)
        self.action = action

    def __call__(self):
        if self.ticks == 0:
            self.action()
            return False
        else:
            self.ticks -= 1
            return True

class RunAfterCondition(object):
    def __init__(self, cond, action):
        super(RunAfterCondition, self).__init__()
        self.cond = cond
        self.action = action

    def __call__(self):
        if self.cond():
            self.action()
            return False
        else:
            return True


class EventQueue(object):
    def __init__(self):
        super(EventQueue, self).__init__()
        self.queue = []
        self.lock = threading.Condition(threading.RLock())

    def add(self, *events):
        self.lock.acquire()
        for e in events:
            self.queue.append(e)
        self.lock.release()

    def clear(self):
        self.lock.acquire()
        self.queue = []
        self.lock.notifyAll()
        self.lock.release()

    def replace(self, *events):
        self.lock.acquire()
        self.queue = []
        for e in events:
            self.queue.append(e)
        self.lock.release()

    def wait_until_empty(self):
        self.lock.acquire()
        while self.queue:
            self.lock.wait()
        self.lock.release()

    def process(self):
        self.lock.acquire()
        self.pre_process()
        print str(self.queue)
        i = 0
        while i < len(self.queue):
            if self.queue[i]():
                i += 1
            else:
                del self.queue[i]
        self.post_process()
        if not self.queue:
            self.lock.notifyAll()
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


class Head(EventQueue):
    def __init__(self, parent):
        super(Head, self).__init__()

        self.parent = parent
        self.motor = MediumMotor("B")
        self.head_state = HEAD_STOP
        self.head_factor = 1.0
        self.camera_process = None

    def calibrate(self):
        def wait_for_stop():
            time.sleep(1)
            while self.motor.pulses_per_second != 0:
                time.sleep(0.1)

        self.parent.voice.exterminate()
        self.parent.voice.wait()

        self.motor.reset()
        self.motor.regulation_mode = "off"
        self.motor.stop_mode = "coast"

        self.motor.duty_cycle_sp = 65
        self.motor.start()
        wait_for_stop()
        self.motor.stop()
        pos1 = self.motor.position

        self.motor.duty_cycle_sp = -65
        self.motor.start()
        wait_for_stop()
        self.motor.stop()
        pos2 = self.motor.position

        midpoint = (pos1 + pos2) / 2.0

        self.motor.regulation_mode = "on"
        self.motor.stop_mode = "hold"
        self.motor.ramp_up_sp = 500
        self.motor.ramp_down_sp = 200
        self.motor.run_position_limited(midpoint, 400)
        wait_for_stop()
        self.motor.stop()
        self.motor.position = 0
        self.motor.stop_mode = "brake"

        self.parent.voice.exterminate()
        self.parent.voice.wait()


    def stop_action(self):
        def action():
            self.head_state = HEAD_STOP
            self.head_factor = 0.0
            self.motor.stop()
        return action

    def stopped_cond(self):
        def cond():
            return self.motor.pulses_per_second == 0
        return cond

    def pre_process(self):
        if ((self.head_state == HEAD_LEFT and self.motor.position < -HEAD_LIMIT)
            or (self.head_state == HEAD_RIGHT and self.motor.position > HEAD_LIMIT)):
            self.shutdown()

    def stop(self):
        self.replace(self.stop_action())

    def shutdown(self):
        self.clear()
        self.stop_action()()


class Voice(object):
    def __init__(self, sound_dir):
        super(Voice, self).__init__()
        self.sound_dir = sound_dir
        self.proc = None

    def stop(self):
        if self.proc:
            self.proc.kill()
            self.proc.wait()
            self.proc = None

    def wait(self):
        if self.proc:
            self.proc.wait()
            self.proc = None

    def speak(self, sound):
        self.stop()
        path = os.path.join(self.sound_dir, sound + ".wav")
        if os.path.exists(path):
            with open("/dev/null", "w") as devnull:
                self.proc = subprocess.Popen(["aplay", path], stdout=devnull, stderr=devnull)

    def exterminate(self):
        self.speak("exterminate")

    def fire_gun(self):
        self.speak("gun")

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
        self.drive = Drive()
        self.head = Head(self)
        self.voice = Voice(sound_dir)
        self.head.calibrate()
        self.thread = ControllerThread(self)
        self.thread.start()

    def shutdown(self):
        self.drive.shutdown()
        self.head.shutdown()
