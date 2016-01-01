"""Main logic for the Dalek. Use one of the other scripts to actually control it."""

from dalek_common import clamp_control_range, sign, EventQueue, DurationAction, RunAfterTime, RepeatingAction
from ev3dev.ev3 import LargeMotor, MediumMotor, TouchSensor, PowerSupply
import os.path
import subprocess
import tempfile
import time
import threading

TICK_LENGTH_SECONDS = 0.1

class TwoWayControl(object):
    def __init__(self):
        super(TwoWayControl, self).__init__()
        self.value = 0.0

    def off(self):
        self.value = 0.0

    def press(self, value):
        self.value = clamp_control_range(value)

    def release(self, direction):
        if sign(self.value) == sign(direction):
            self.off()

class Leds(object):
    def __init__(self, port):
        super(Leds, self).__init__()

        port_map = {"A": "4", "B": "5", "C": "6", "D": "7"}
        mode_path = "/sys/devices/platform/legoev3-ports/lego-port/port%s/mode" % port_map[port]
        with open(mode_path, "w") as f:
            f.write("led\n")

        # Give the system time to set up the changes
        time.sleep(1)

        self.control_path = "/sys/bus/lego/devices/out%s:rcx-led/leds/out%s::ev3dev/brightness" % (port, port)
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


class Drive(EventQueue):

    DRIVE_SPEED = -700
    TURN_SPEED = -500

    def __init__(self):
        super(Drive, self).__init__()

        def init_wheel(port):
            wheel = LargeMotor(port)
            wheel.reset()
            wheel.speed_regulation_enabled = "on"
            wheel.stop_command = "coast"
            return wheel

        self.left_wheel = init_wheel("D")
        self.right_wheel = init_wheel("A")
        self.touch_sensor = TouchSensor("2")
        self.drive_control = TwoWayControl()
        self.turn_control = TwoWayControl()
        self.ticks_since_last = 0
        print "Created drive"

    def update_wheel_speeds(self):
        def set_wheel_speed(wheel, speed):
            wheel.speed_sp = speed
            if speed == 0:
                wheel.stop()
            else:
                wheel.run_forever()

        drive_part = Drive.DRIVE_SPEED * self.drive_control.value
        turn_part = Drive.TURN_SPEED * self.turn_control.value

        set_wheel_speed(self.left_wheel, drive_part + turn_part)
        set_wheel_speed(self.right_wheel, drive_part - turn_part)

    def control_press_action(self, control, value):
        def action():
            control.press(value)
            self.update_wheel_speeds()
            self.ticks_since_last = 0
        return action

    def control_release_action(self, control, value):
        def action():
            control.release(value)
            self.update_wheel_speeds()
            self.ticks_since_last = 0
        return action

    def stop_action(self):
        def action():
            self.drive_control.off()
            self.turn_control.off()
            self.update_wheel_speeds()
            self.ticks_since_last = 0
        return action

    def pre_process(self):
        if self.touch_sensor.value() == 1:
            self.shutdown()
        self.ticks_since_last += 1

    def post_process(self):
        if self.ticks_since_last > 75:
            self.shutdown()

    def drive(self, value):
        self.add(self.control_press_action(self.drive_control, value))

    def drive_release(self, value):
        self.add(self.control_release_action(self.drive_control, value))

    def turn(self, value):
        self.add(self.control_press_action(self.turn_control, value))

    def turn_release(self, value):
        self.add(self.control_release_action(self.turn_control, value))

    def stop(self):
        self.add(self.stop_action())

    def shutdown(self):
        self.clear()
        self.stop_action()()


class Head(EventQueue):

    HEAD_LIMIT = 135
    HEAD_SPEED = 300

    def __init__(self, parent):
        super(Head, self).__init__()
        self.parent = parent
        self.motor = MediumMotor("B")
        self.control = TwoWayControl()
        print "Created head"

    def calibrate(self):
        try:
            self.parent.voice.speak("commence-awakening")
            self.parent.voice.wait()

            self.motor.reset()

            self.motor.speed_regulation_enabled = "on"
            self.motor.position = 0
            self.motor.stop_command = "brake"
            self.motor.ramp_up_sp = 0
            self.motor.ramp_down_sp = 0

            time.sleep(1)
            self.parent.voice.exterminate()
            self.parent.voice.wait()

        except:
            self.shutdown()
            raise

    def update_motor_speed(self):
        speed = self.control.value * Head.HEAD_SPEED
        self.motor.speed_sp = speed
        if speed == 0:
            self.motor.stop()
        else:
            self.motor.run_forever()

    def stop_action(self):
        def action():
            self.control.off()
            self.update_motor_speed()
        return action

    def control_press_action(self, value):
        def action():
            self.control.press(value)
            self.update_motor_speed()
        return action

    def control_release_action(self, value):
        def action():
            self.control.release(value)
            self.update_motor_speed()
        return action

    def pre_process(self):
        if ((self.control.value > 0 and self.motor.position > Head.HEAD_LIMIT)
            or (self.control.value < 0 and self.motor.position < -Head.HEAD_LIMIT)):
            self.shutdown()

    def stop(self):
        self.replace(self.stop_action())

    def turn(self, value):
        self.add(self.control_press_action(value))

    def turn_release(self, value):
        self.add(self.control_release_action(value))

    def shutdown(self):
        self.clear()
        self.stop_action()()


class Voice(EventQueue):
    def __init__(self, sound_dir):
        super(Voice, self).__init__()
        self.sound_dir = sound_dir
        self.proc = None
        self.leds = Leds("C")
        print "Created voice"

    def stop(self):
        if self.proc:
            self.leds.off()
            self.clear()
            self.proc.kill()
            self.proc.wait()
            self.proc = None

    def toggle_lights(self):
        self.leds.toggle()

    def wait(self):
        if self.proc:
            self.proc.wait()
            self.proc = None

    def setup_lights_actions(self, sound):
        path = os.path.join(self.sound_dir, sound + ".txt")
        if os.path.exists(path):
            def lights_on_action():
                self.leds.on()

            def lights_off_action():
                self.leds.off()

            def flash(start, end):
                def action():
                    self.add(DurationAction(end - start,
                                            lights_on_action,
                                            lights_off_action,
                                            TICK_LENGTH_SECONDS))
                return action

            l = []
            with open(path) as f:
                for line in f:
                    l.append(float(line.strip()))

            if len(l) % 2 == 0:
                i = 0
                while i < len(l):
                    start = l[i]
                    end = l[i + 1]
                    self.add(RunAfterTime(start,
                                          flash(start, end),
                                          TICK_LENGTH_SECONDS))
                    i += 2

    def speak(self, sound):
        self.stop()
        path = os.path.join(self.sound_dir, sound + ".wav")
        if os.path.exists(path):
            with open("/dev/null", "w") as devnull:
                self.proc = subprocess.Popen(["aplay", path], stdout=devnull, stderr=devnull)
            self.setup_lights_actions(sound)

    def is_speaking(self):
        if self.proc:
            if self.proc.poll() is not None:
                self.proc.wait()
                self.proc = None
                return False
            else:
                return True
        else:
            return False

    def exterminate(self):
        self.speak("exterminate")

    def fire_gun(self):
        self.speak("gun")

class Camera(EventQueue):
    def __init__(self):
        super(Camera, self).__init__()
        self.snapshot_handler = None
        self.output_file = tempfile.mktemp(suffix=".jpeg")
        self.proc = None
        print "Created camera"

    def register_handler(self, h):
        self.snapshot_handler = h

    def take_snapshot(self):
        def action():
            with open("/dev/null", "w") as devnull:
                self.proc = subprocess.Popen(["streamer", "-s", "800x600", "-o", self.output_file], stdout=devnull, stderr=devnull)

        def cleanup():
            if self.is_busy():
                return True
            elif self.snapshot_handler:
                with open(self.output_file) as f:
                    self.snapshot_handler(f.read())

        if os.path.exists("/dev/video0"):
            self.add_if_empty(action, cleanup)

    def is_busy(self):
        if self.proc:
            if self.proc.poll() is not None:
                self.proc.wait()
                self.proc = None
                return False
            else:
                return True
        else:
            return False

class Battery(EventQueue):
    def __init__(self):
        super(Battery, self).__init__()
        self.power_supply = PowerSupply()
        self.battery_handler = None
        def handle():
            if self.battery_handler:
                self.battery_handler("%.2f" % self.power_supply.measured_volts)
        self.add(RepeatingAction(10, handle, TICK_LENGTH_SECONDS))
        print "Created battery"

    def register_handler(self, h):
        self.battery_handler = h

    def shutdown(self):
        self.clear()

class ControllerThread(threading.Thread):
    def __init__(self, parent):
        super(ControllerThread, self).__init__()
        self.parent = parent
        self.daemon = True
        self.alive = True
        self.lock = threading.Lock()
        print "Created controller thread"

    def is_alive(self):
        self.lock.acquire()
        a = self.alive
        self.lock.release()
        return a

    def shutdown(self):
        self.lock.acquire()
        self.alive = False
        self.lock.release()

    def run(self):
        while self.is_alive():
            self.parent.drive.process()
            self.parent.head.process()
            self.parent.voice.process()
            self.parent.camera.process()
            self.parent.battery.process()
            time.sleep(TICK_LENGTH_SECONDS)

class Dalek(object):
    """Main Dalek controller"""

    def __init__(self, sound_dir):
        super(Dalek, self).__init__()
        self.drive = Drive()
        self.head = Head(self)
        self.voice = Voice(sound_dir)
        self.camera = Camera()
        self.battery = Battery()
        self.thread = ControllerThread(self)
        self.thread.start()
        self.head.calibrate()
        print "Ready"

    def shutdown(self):
        self.drive.shutdown()
        self.head.shutdown()
        self.battery.shutdown()
        self.voice.stop()
        self.voice.speak("status-hibernation")
        self.voice.wait()
        self.voice.wait_until_empty()
        self.voice.stop()
        self.thread.shutdown()
        self.thread.join()
