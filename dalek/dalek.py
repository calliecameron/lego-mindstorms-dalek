"""Main logic for the Dalek."""

import os
import os.path
import subprocess
import threading
import time
from collections.abc import Callable

from ev3dev2.motor import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, Motor
from ev3dev2.sensor import INPUT_2

from dalek import ev3
from dalek.utils import (
    EventQueue,
    Immediate,
    Repeat,
    RunAfterCondition,
    RunAfterTime,
    Seconds,
    Timer,
    clamp_control_range,
    espeakify,
    sign,
    sound_filename,
)

LEFT_WHEEL_PORT = OUTPUT_D
RIGHT_WHEEL_PORT = OUTPUT_A
HEAD_PORT = OUTPUT_B
LED_PORT = OUTPUT_C
PLUNGER_PORT = INPUT_2

TICK_LENGTH = Seconds(0.1)


class Leds:
    def __init__(self) -> None:
        port = LED_PORT
        ev3.lego_port(port).mode = "led"

        # Give the system time to set up the changes
        time.sleep(1)

        super().__init__()

        self._led = ev3.led(port + "::brick-status")
        self.off()
        print("DALEK: created LEDs")

    def on(self) -> None:
        self._led.brightness = self._led.max_brightness

    def off(self) -> None:
        self._led.brightness = 0

    def toggle(self) -> None:
        if self._led.brightness > 0:
            self.off()
        else:
            self.on()


class Voice:
    EXTERMINATE = "Exterminate"
    GUN = "Gun"
    COMMENCE_AWAKENING = "Commence awakening"
    STATUS_HIBERNATION = "Status hibernation"

    def __init__(
        self,
        sound_dir: str,
        text_to_speech_command: str,
        leds: Leds,
    ) -> None:
        super().__init__()
        self._queue = EventQueue()
        self._sound_dir = sound_dir
        self._text_to_speech_command = text_to_speech_command
        self._leds = leds
        self._subprocess: subprocess.Popen[bytes] | None = None
        print("DALEK: created voice")

    def process(self) -> None:
        self._queue.process()

    def stop(self) -> None:
        if self._subprocess:
            self._leds.off()
            self._queue.clear()
            self._subprocess.kill()
            self._subprocess.wait()
            self._subprocess = None

    def wait(self) -> None:
        if self._subprocess:
            self._subprocess.wait()
            self._subprocess = None

    def wait_until_empty(self) -> None:
        self._queue.wait_until_empty()

    def _setup_lights_actions(self, sound: str) -> None:
        path = os.path.join(self._sound_dir, sound + ".txt")

        def lights_on_action() -> None:
            self._leds.on()

        def lights_off_action() -> None:
            self._leds.off()

        def flash(start: Seconds, end: Seconds) -> Callable[[], None]:
            def action() -> None:
                self._queue.add(
                    Timer(
                        time=Seconds(end - start),
                        tick_length=TICK_LENGTH,
                        repeat=False,
                        start_action=lights_on_action,
                        end_action=lights_off_action,
                    ),
                )

            return action

        if os.path.exists(path):
            l: list[Seconds] = []
            with open(path) as f:
                l.extend(Seconds(float(line.strip())) for line in f)

            if len(l) % 2 == 0:
                i = 0
                while i < len(l):
                    start = l[i]
                    end = l[i + 1]
                    self._queue.add(
                        RunAfterTime(
                            time=start,
                            tick_length=TICK_LENGTH,
                            action=flash(start, end),
                        ),
                    )
                    i += 2

    def speak(self, text: str) -> None:
        self.stop()

        # We first look for a sound file with the given name, otherwise we pass
        # the text to espeak
        filename = sound_filename(text)
        path = os.path.join(self._sound_dir, filename + ".wav")

        if os.path.exists(path):
            self._subprocess = subprocess.Popen(
                ["aplay", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._setup_lights_actions(filename)
        else:
            self._subprocess = subprocess.Popen(
                [self._text_to_speech_command, espeakify(text)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


class Camera:
    def __init__(self, snapshot_command: str, output_file: str) -> None:
        super().__init__()
        self._queue = EventQueue()
        self._snapshot_command = snapshot_command
        self._snapshot_handler: Callable[[str], None] | None = None
        self._output_file = output_file
        self._subprocess: subprocess.Popen[bytes] | None = None
        print("DALEK: created camera")

    def process(self) -> None:
        self._queue.process()

    def has_camera(self) -> bool:
        return os.path.exists("/dev/video0")

    def register_handler(self, h: Callable[[str], None]) -> None:
        self._snapshot_handler = h

    def clear_handler(self) -> None:
        self._snapshot_handler = None

    def take_snapshot(self) -> None:
        def action() -> None:
            self._subprocess = subprocess.Popen(
                [self._snapshot_command, self._output_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        def is_idle() -> bool:
            if not self._subprocess:
                return True

            if self._subprocess.poll() is not None:
                self._subprocess.wait()
                self._subprocess = None
                return True

            return False

        def cleanup() -> None:
            if self._snapshot_handler:
                with open(self._output_file) as f:
                    self._snapshot_handler(f.read())

        if self.has_camera():
            self._queue.add_if_empty(
                Immediate(action),
                RunAfterCondition(condition=is_idle, action=cleanup),
            )


class Battery:
    def __init__(self) -> None:
        super().__init__()
        self._queue = EventQueue()
        self._power_supply = ev3.power_supply()
        self._battery_handler: Callable[[str], None] | None = None

        def handle() -> None:
            if self._battery_handler:
                self._battery_handler(self._get_battery_status())

        self._queue.add(
            Repeat(time=Seconds(10), action=handle, tick_length=TICK_LENGTH),
        )
        print("DALEK: created battery")

    def process(self) -> None:
        self._queue.process()

    def _get_battery_status(self) -> str:
        return f"{self._power_supply.measured_volts:.2f}"

    def register_handler(self, h: Callable[[str], None]) -> None:
        self._battery_handler = h

    def clear_handler(self) -> None:
        self._battery_handler = None

    def shutdown(self) -> None:
        self._queue.clear()


class TwoWayControl:
    def __init__(self) -> None:
        super().__init__()
        self._value = 0.0

    @property
    def value(self) -> float:
        return self._value

    def off(self) -> None:
        self._value = 0.0

    def press(self, value: float) -> None:
        self._value = clamp_control_range(value)

    def release(self, direction: float) -> None:
        if sign(self._value) == sign(direction):
            self.off()


class Drive:
    _DRIVE_SPEED = -700
    _TURN_SPEED = -500

    def __init__(self) -> None:
        super().__init__()

        def preprocess() -> None:
            if self._touch_sensor.is_pressed():
                self.shutdown()
            self._ticks_since_last += 1

        def post_process() -> None:
            if self._ticks_since_last > 75:  # noqa: PLR2004
                self.shutdown()

        self._queue = EventQueue(
            preprocess=preprocess,
            postprocess=post_process,
        )

        def init_wheel(port: str) -> ev3.LargeMotor:
            wheel = ev3.large_motor(port)
            wheel.reset()
            wheel.stop_action = Motor.STOP_ACTION_COAST
            return wheel

        self._left_wheel = init_wheel(LEFT_WHEEL_PORT)
        self._right_wheel = init_wheel(RIGHT_WHEEL_PORT)
        self._touch_sensor = ev3.touch_sensor(PLUNGER_PORT)
        self._drive_control = TwoWayControl()
        self._turn_control = TwoWayControl()
        self._ticks_since_last = 0
        print("DALEK: created drive")

    def _update_wheel_speeds(self) -> None:
        def set_wheel_speed(wheel: ev3.LargeMotor, speed: float) -> None:
            wheel.speed_sp = speed
            if speed == 0.0:
                wheel.stop()
            else:
                wheel.run_forever()

        drive_part = self._DRIVE_SPEED * self._drive_control.value
        turn_part = self._TURN_SPEED * self._turn_control.value

        set_wheel_speed(self._left_wheel, drive_part + turn_part)
        set_wheel_speed(self._right_wheel, drive_part - turn_part)

    def _control_press_action(
        self,
        control: TwoWayControl,
        value: float,
    ) -> Immediate:
        def action() -> None:
            control.press(value)
            self._update_wheel_speeds()
            self._ticks_since_last = 0

        return Immediate(action)

    def _control_release_action(
        self,
        control: TwoWayControl,
        value: float,
    ) -> Immediate:
        def action() -> None:
            control.release(value)
            self._update_wheel_speeds()
            self._ticks_since_last = 0

        return Immediate(action)

    def _stop_action(self) -> Immediate:
        def action() -> None:
            self._drive_control.off()
            self._turn_control.off()
            self._update_wheel_speeds()
            self._ticks_since_last = 0

        return Immediate(action)

    def process(self) -> None:
        self._queue.process()

    def drive(self, value: float) -> None:
        self._queue.add(self._control_press_action(self._drive_control, value))

    def drive_release(self, value: float) -> None:
        self._queue.add(
            self._control_release_action(self._drive_control, value),
        )

    def turn(self, value: float) -> None:
        self._queue.add(self._control_press_action(self._turn_control, value))

    def turn_release(self, value: float) -> None:
        self._queue.add(self._control_release_action(self._turn_control, value))

    def stop(self) -> None:
        self._queue.add(self._stop_action())

    def shutdown(self) -> None:
        self._queue.clear()
        self._stop_action().process()


class Head:
    _HEAD_LIMIT = 320
    _HEAD_SPEED = 300

    def __init__(self, voice: Voice) -> None:
        super().__init__()

        def preprocess() -> None:
            if self._position_out_of_bounds():
                self.shutdown()

        self._queue = EventQueue(preprocess=preprocess)
        self._voice = voice
        self._motor = ev3.medium_motor(HEAD_PORT)
        self._control = TwoWayControl()
        print("DALEK: created head")

    def calibrate(self) -> None:
        try:
            self._voice.speak(Voice.COMMENCE_AWAKENING)
            self._voice.wait()

            self._motor.reset()

            self._motor.position = 0
            self._motor.stop_action = Motor.STOP_ACTION_BRAKE
            self._motor.ramp_up_sp = 0
            self._motor.ramp_down_sp = 0

            time.sleep(1)
            self._voice.speak(Voice.EXTERMINATE)
            self._voice.wait()

        except:
            self.shutdown()
            raise

    def _update_motor_speed(self) -> None:
        speed = self._control.value * self._HEAD_SPEED
        self._motor.speed_sp = speed
        if speed == 0:
            self._motor.stop()
        else:
            self._motor.run_forever()

    def _stop_action(self) -> Immediate:
        def action() -> None:
            self._control.off()
            self._update_motor_speed()

        return Immediate(action)

    def _control_press_action(self, value: float) -> Immediate:
        def action() -> None:
            self._control.press(value)
            self._update_motor_speed()

        return Immediate(action)

    def _control_release_action(self, value: float) -> Immediate:
        def action() -> None:
            self._control.release(value)
            self._update_motor_speed()

        return Immediate(action)

    def _position_out_of_bounds(self) -> bool:
        return (
            self._control.value > 0 and self._motor.position > self._HEAD_LIMIT
        ) or (
            self._control.value < 0 and self._motor.position < -self._HEAD_LIMIT
        )

    def process(self) -> None:
        self._queue.process()

    def stop(self) -> None:
        self._queue.replace(self._stop_action())

    def turn(self, value: float) -> None:
        self._queue.add(self._control_press_action(value))

    def turn_release(self, value: float) -> None:
        self._queue.add(self._control_release_action(value))

    def shutdown(self) -> None:
        self._queue.clear()
        self._stop_action().process()


class ControllerThread(threading.Thread):
    def __init__(self, parent: "Dalek") -> None:
        super().__init__()
        self._parent = parent
        self._daemon = True
        self._alive = True
        self._lock = threading.Lock()
        print("DALEK: created controller thread")

    def is_alive(self) -> bool:
        with self._lock:
            return self._alive

    def shutdown(self) -> None:
        with self._lock:
            self._alive = False

    def run(self) -> None:
        while self.is_alive():
            self._parent.drive.process()
            self._parent.head.process()
            self._parent.voice.process()
            self._parent.camera.process()
            self._parent.battery.process()
            time.sleep(TICK_LENGTH)


class Dalek:
    """Main Dalek controller"""

    def __init__(
        self,
        sound_dir: str,
        text_to_speech_command: str,
        snapshot_command: str,
        snapshot_file: str,
    ) -> None:
        super().__init__()
        self.leds = Leds()
        self.voice = Voice(sound_dir, text_to_speech_command, self.leds)
        self.camera = Camera(snapshot_command, snapshot_file)
        self.battery = Battery()
        self.drive = Drive()
        self.head = Head(self.voice)
        self.thread = ControllerThread(self)
        self.thread.start()
        self.head.calibrate()
        print("DALEK: ready")

    def shutdown(self) -> None:
        self.head.shutdown()
        self.drive.shutdown()
        self.battery.shutdown()
        self.voice.stop()
        self.voice.speak(Voice.STATUS_HIBERNATION)
        self.voice.wait()
        self.voice.wait_until_empty()
        self.voice.stop()
        self.thread.shutdown()
        self.thread.join()
