"""Main logic for the Dalek."""

import logging
import os
import os.path
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from types import TracebackType
from typing import Self, override

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

_LEFT_WHEEL_PORT = OUTPUT_D
_RIGHT_WHEEL_PORT = OUTPUT_A
_HEAD_PORT = OUTPUT_B
_LED_PORT = OUTPUT_C
_PLUNGER_PORT = INPUT_2

_TICK_LENGTH = Seconds(0.1)

_log = logging.getLogger(__name__)


class _Leds:
    def __init__(self) -> None:
        port = _LED_PORT
        ev3.lego_port(port).mode = "led"

        # Give the system time to set up the changes
        time.sleep(1)

        super().__init__()

        self._led = ev3.led(port + "::brick-status")
        self.off()
        _log.info("created LEDs")

    def on(self) -> None:
        self._led.brightness = self._led.max_brightness

    def off(self) -> None:
        self._led.brightness = 0

    def toggle(self) -> None:
        if self._led.brightness > 0:
            self.off()
        else:
            self.on()


class _Actor(ABC):
    def __init__(
        self,
        *,
        preprocess: Callable[[], None] | None = None,
        postprocess: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self._queue = EventQueue(
            name=self.__class__.__name__,
            preprocess=preprocess,
            postprocess=postprocess,
        )

    def process(self) -> None:
        self._queue.process()

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError


class _Voice(_Actor):
    EXTERMINATE = "Exterminate"
    GUN = "Gun"
    COMMENCE_AWAKENING = "Commence awakening"
    STATUS_HIBERNATION = "Status hibernation"

    def __init__(
        self,
        sound_dir: str,
        text_to_speech_command: str,
        leds: _Leds,
    ) -> None:
        super().__init__()
        self._sound_dir = sound_dir
        self._text_to_speech_command = text_to_speech_command
        self._leds = leds
        self._lock = threading.Lock()
        self._subprocess: subprocess.Popen[bytes] | None = None
        _log.info("created voice")

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
                        tick_length=_TICK_LENGTH,
                        repeat=False,
                        start_action=lights_on_action,
                        end_action=lights_off_action,
                    ),
                )

            return action

        try:
            with open(path) as f:
                l = [Seconds(float(line.strip())) for line in f]

            if len(l) % 2 == 0:
                i = 0
                while i < len(l):
                    start = l[i]
                    end = l[i + 1]
                    self._queue.add(
                        RunAfterTime(
                            time=start,
                            tick_length=_TICK_LENGTH,
                            action=flash(start, end),
                        ),
                    )
                    i += 2
        except OSError as e:
            _log.error(f"failed to read light file for '{sound}': {e}")

    def speak(self, text: str) -> None:
        self.stop()

        # We first look for a sound file with the given name, otherwise we pass
        # the text to espeak
        filename = sound_filename(text)
        path = os.path.join(self._sound_dir, filename + ".wav")

        with self._lock:
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

    def stop(self) -> None:
        with self._lock:
            self._leds.off()
            self._queue.clear()
            if self._subprocess:
                self._subprocess.kill()
                self._subprocess.wait()
                self._subprocess = None

    def wait(self) -> None:
        with self._lock:
            if self._subprocess:
                self._subprocess.wait()
                self._subprocess = None

    @override
    def disconnect(self) -> None:
        self.wait()
        self.stop()


class _Camera(_Actor):
    def __init__(self, take_picture_command: str, output_file: str) -> None:
        super().__init__()
        self._take_picture_command = take_picture_command
        self._output_file = output_file
        self._lock = threading.Lock()
        self._handler: Callable[[bytes], None] | None = None
        self._subprocess: subprocess.Popen[bytes] | None = None
        _log.info(f"created camera; camera found = {self._has_camera()}")

    def _has_camera(self) -> bool:
        return os.path.exists("/dev/video0")

    def set_handler(self, h: Callable[[bytes], None]) -> None:
        with self._lock:
            self._handler = h

    def take_picture(self) -> None:
        def action() -> None:
            with self._lock:
                self._subprocess = subprocess.Popen(
                    [self._take_picture_command, self._output_file],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

        def is_idle() -> bool:
            with self._lock:
                if not self._subprocess:
                    return True

                if self._subprocess.poll() is not None:
                    self._subprocess.wait()
                    self._subprocess = None
                    return True

                return False

        def cleanup() -> None:
            with self._lock:
                if self._handler:
                    try:
                        with open(self._output_file, mode="rb") as f:
                            self._handler(f.read())
                    except OSError as e:
                        _log.error(f"failed to take picture: {e}")

        if self._has_camera():
            self._queue.add_if_empty(
                Immediate(action),
                RunAfterCondition(condition=is_idle, action=cleanup),
            )
        else:
            _log.info("no camera found")

    @override
    def disconnect(self) -> None:
        with self._lock:
            if self._subprocess:
                self._subprocess.kill()
                self._subprocess.wait()
                self._subprocess = None
            self._handler = None
        self._queue.clear()


class _Battery(_Actor):
    def __init__(self) -> None:
        super().__init__()
        self._power_supply = ev3.power_supply()
        self._lock = threading.Lock()
        self._handler: Callable[[str], None] | None = None
        _log.info("created battery")

    def status(self) -> str:
        return f"{self._power_supply.measured_volts:.2f}"

    def set_handler(self, h: Callable[[str], None]) -> None:
        with self._lock:
            self._handler = h

        def handle() -> None:
            with self._lock:
                if self._handler:
                    self._handler(self.status())

        self._queue.add(
            Repeat(
                time=Seconds(10),
                action=handle,
                tick_length=_TICK_LENGTH,
            ),
        )

    @override
    def disconnect(self) -> None:
        with self._lock:
            self._handler = None
        self._queue.clear()


class _TwoWayControl:
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


class _Drive(_Actor):
    _DRIVE_SPEED = -700
    _TURN_SPEED = -500

    def __init__(self) -> None:
        def preprocess() -> None:
            if self._touch_sensor.is_pressed():
                self.stop()
            else:
                with self._lock:
                    self._ticks_since_last += 1

        def postprocess() -> None:
            with self._lock:
                ticks_since_last = self._ticks_since_last
            if ticks_since_last > 75:  # noqa: PLR2004
                self.stop()

        super().__init__(preprocess=preprocess, postprocess=postprocess)

        def init_wheel(port: str) -> ev3.LargeMotor:
            wheel = ev3.large_motor(port)
            wheel.reset()
            wheel.stop_action = Motor.STOP_ACTION_COAST
            return wheel

        self._left_wheel = init_wheel(_LEFT_WHEEL_PORT)
        self._right_wheel = init_wheel(_RIGHT_WHEEL_PORT)
        self._touch_sensor = ev3.touch_sensor(_PLUNGER_PORT)
        self._drive_control = _TwoWayControl()
        self._turn_control = _TwoWayControl()
        self._lock = threading.Lock()
        self._ticks_since_last = 0
        _log.info("created drive")

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
        control: _TwoWayControl,
        value: float,
    ) -> Immediate:
        def action() -> None:
            control.press(value)
            self._update_wheel_speeds()
            with self._lock:
                self._ticks_since_last = 0

        return Immediate(action)

    def _control_release_action(
        self,
        control: _TwoWayControl,
        value: float,
    ) -> Immediate:
        def action() -> None:
            control.release(value)
            self._update_wheel_speeds()
            with self._lock:
                self._ticks_since_last = 0

        return Immediate(action)

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
        self._queue.clear()
        self._drive_control.off()
        self._turn_control.off()
        self._update_wheel_speeds()
        with self._lock:
            self._ticks_since_last = 0

    @override
    def disconnect(self) -> None:
        self.stop()


class Head(_Actor):
    _HEAD_LIMIT = 320
    _HEAD_SPEED = 300

    def __init__(self) -> None:
        def preprocess() -> None:
            if self._position_out_of_bounds():
                self.stop()

        super().__init__(preprocess=preprocess)

        self._motor = ev3.medium_motor(_HEAD_PORT)
        self._control = _TwoWayControl()
        self._calibrate()
        _log.info("created head")

    def _calibrate(self) -> None:
        self._motor.reset()
        self._motor.position = 0
        self._motor.stop_action = Motor.STOP_ACTION_BRAKE
        self._motor.ramp_up_sp = 0
        self._motor.ramp_down_sp = 0

    def _position_out_of_bounds(self) -> bool:
        return (
            self._control.value > 0 and self._motor.position > self._HEAD_LIMIT
        ) or (
            self._control.value < 0 and self._motor.position < -self._HEAD_LIMIT
        )

    def _update_motor_speed(self) -> None:
        speed = self._control.value * self._HEAD_SPEED
        self._motor.speed_sp = speed
        if speed == 0:
            self._motor.stop()
        else:
            self._motor.run_forever()

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

    def turn(self, value: float) -> None:
        self._queue.add(self._control_press_action(value))

    def turn_release(self, value: float) -> None:
        self._queue.add(self._control_release_action(value))

    def stop(self) -> None:
        self._queue.clear()
        self._control.off()
        self._update_motor_speed()

    @override
    def disconnect(self) -> None:
        self.stop()


class ControllerThread(threading.Thread):
    def __init__(self, action: Callable[[], None]) -> None:
        super().__init__()
        self._action = action
        self._daemon = True
        self._alive = True
        self._lock = threading.Lock()
        _log.info("created controller thread")

    def is_alive(self) -> bool:
        with self._lock:
            return self._alive

    def stop(self) -> None:
        with self._lock:
            self._alive = False

    def run(self) -> None:
        while self.is_alive():
            self._action()
            time.sleep(_TICK_LENGTH)


class Dalek:
    """Main Dalek controller"""

    def __init__(
        self,
        sound_dir: str,
        text_to_speech_command: str,
        take_picture_command: str,
        camera_output_file: str,
    ) -> None:
        super().__init__()

        self._leds = _Leds()
        self._voice = _Voice(
            sound_dir,
            text_to_speech_command,
            self._leds,
        )
        self._camera = _Camera(
            take_picture_command,
            camera_output_file,
        )
        self._battery = _Battery()
        self._drive = _Drive()
        self._head = Head()

        self._actors = [
            self._voice,
            self._camera,
            self._battery,
            self._drive,
            self._head,
        ]

    def __enter__(self) -> Self:
        def process() -> None:
            for actor in self._actors:
                actor.process()

        self._thread = ControllerThread(process)
        self._thread.start()

        self._voice.speak(_Voice.COMMENCE_AWAKENING)
        self._voice.wait()
        time.sleep(1)
        self._voice.speak(_Voice.EXTERMINATE)
        self._voice.wait()

        _log.info("ready")
        return self

    def disconnect(self) -> None:
        for actor in self._actors:
            actor.disconnect()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.disconnect()
        self._voice.speak(_Voice.STATUS_HIBERNATION)
        self._voice.disconnect()
        self._thread.stop()
        self._thread.join()

    def drive(self, value: float) -> None:
        self._drive.drive(value)

    def drive_release(self, value: float) -> None:
        self._drive.drive_release(value)

    def turn(self, value: float) -> None:
        self._drive.turn(value)

    def turn_release(self, value: float) -> None:
        self._drive.turn_release(value)

    def head_turn(self, value: float) -> None:
        self._head.turn(value)

    def head_turn_release(self, value: float) -> None:
        self._head.turn_release(value)

    def stop_moving(self) -> None:
        self._drive.stop()
        self._head.stop()

    def toggle_lights(self) -> None:
        self._leds.toggle()

    def speak(self, text: str) -> None:
        self._voice.speak(text)

    def stop_speaking(self) -> None:
        self._voice.stop()

    def set_camera_handler(self, h: Callable[[bytes], None]) -> None:
        self._camera.set_handler(h)

    def take_picture(self) -> None:
        self._camera.take_picture()

    def battery_status(self) -> str:
        return self._battery.status()

    def set_battery_handler(self, h: Callable[[str], None]) -> None:
        self._battery.set_handler(h)
