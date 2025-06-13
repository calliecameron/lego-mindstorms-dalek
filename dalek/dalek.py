"""Main logic for the Dalek."""

import asyncio
import logging
import os
import os.path
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from enum import StrEnum
from types import TracebackType
from typing import Self, override

import aiofiles
from ev3dev2.motor import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, Motor
from ev3dev2.sensor import INPUT_2

from dalek import ev3
from dalek.utils import (
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

_log = logging.getLogger(__name__)


class Sounds(StrEnum):
    BRING_HIM_TO_ME = "Bring him to me"
    CAN_I_BE_OF_ASSISTANCE = "Can I be of assistance?"
    CEASE_TALKING = "Cease talking"
    COMMENCE_AWAKENING = "Commence awakening"
    DALEKS_ARE_SUPREME = "Daleks are supreme"
    DALEKS_DO_NOT_QUESTION_ORDERS = "Daleks do not question orders"
    DALEKS_HAVE_NO_CONCEPT_OF_WORRY = "Daleks have no concept of worry"
    DOCTOR = "Doctor?"
    EXPLAIN = "Explain"
    EXTERMINATE = "Exterminate!"
    EXTERMINATE_3 = "Exterminate, exterminate, exterminate!"
    GUN = "Gun"
    IDENTIFY_YOURSELF = "Identify yourself"
    IT_IS_THE_DOCTOR = "It is the Doctor"
    I_BRING_YOU_THE_HUMAN = "I bring you the human"
    I_HAVE_DUTIES_TO_PERFORM = "I have duties to perform"
    PLEASE_EXCUSE_ME = "Please excuse me"
    REPORT = "Report"
    SOCIAL_INTERACTION_WILL_CEASE = "Social interaction will cease"
    STATUS_HIBERNATION = "Status hibernation"
    THAT_IS_INCORRECT = "That is incorrect"
    THEN_HEAR_ME_TALK_NOW = "Then hear me talk now"
    THE_DOCTOR = "The Doctor?"
    THE_DOCTOR_MUST_DIE = "The Doctor must die"
    THIS_HUMAN_IS_OUR_BEST_OPTION = "This human is our best option"
    WHICH_OF_YOU_IS_LEAST_IMPORTANT = "Which of you is least important?"
    WHY = "Why?"
    WOULD_YOU_CARE_FOR_SOME_TEA = "Would you care for some tea?"
    YOUR_LOYALTY_WILL_BE_REWARDED = "Your loyalty will be rewarded"
    YOU_WILL_BE_NECESSARY = "You will be necessary"
    YOU_WILL_FOLLOW = "You will follow"
    YOU_WILL_IDENTIFY = "You will identify"
    YOU_WOULD_MAKE_A_GOOD_DALEK = "You would make a good Dalek"


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
    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.disconnect()

    @abstractmethod
    async def disconnect(self) -> None:
        raise NotImplementedError


class _Voice(_Actor):
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
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None
        _log.info("created voice")

    async def _flash_lights(self, sound: str) -> None:
        path = os.path.join(self._sound_dir, sound + ".txt")

        try:
            async with aiofiles.open(path) as f:
                l = [float(line.strip()) async for line in f]
        except OSError as e:
            _log.error(f"failed to read light file for '{sound}': {e}")
            return

        if len(l) % 2 != 0:
            _log.error("sound file must have an even number of lines")
            return

        on = False
        last = 0.0
        for t in l:
            await asyncio.sleep(t - last)
            if on:
                self._leds.off()
            else:
                self._leds.on()
            on = not on
            last = t

    async def speak(self, text: str) -> None:
        async def task() -> None:
            self._leds.off()

            filename = sound_filename(text)
            path = os.path.join(self._sound_dir, filename + ".wav")

            if os.path.exists(path):
                p = await asyncio.create_subprocess_exec(
                    "aplay",
                    path,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await self._flash_lights(filename)
            else:
                p = await asyncio.create_subprocess_exec(
                    self._text_to_speech_command,
                    espeakify(text),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )

            if await p.wait() != 0:
                _log.error(
                    f"speech subprocess failed with exit code {p.returncode}",
                )

        async with self._lock:
            if self._task and not self._task.done():
                _log.warning(
                    "attempted to speak when another sound is in progress",
                )
                return

            self._task = asyncio.create_task(task())

    async def _stop(self) -> None:
        self._leds.off()
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _wait(self) -> None:
        if self._task:
            await self._task
            self._task = None

    async def stop(self) -> None:
        async with self._lock:
            await self._stop()

    async def wait(self) -> None:
        async with self._lock:
            await self._wait()

    @override
    async def disconnect(self) -> None:
        async with self._lock:
            await self._wait()
            await self._stop()


class _Camera(_Actor):
    def __init__(self, take_picture_command: str, output_file: str) -> None:
        super().__init__()
        self._take_picture_command = take_picture_command
        self._output_file = output_file
        self._lock = asyncio.Lock()
        self._handler: Callable[[bytes], Awaitable[None]] | None = None
        self._task: asyncio.Task[None] | None = None
        _log.info(f"created camera; camera found = {self._has_camera()}")

    def _has_camera(self) -> bool:
        return os.path.exists("/dev/video0")

    async def set_handler(self, h: Callable[[bytes], Awaitable[None]]) -> None:
        async with self._lock:
            if self._handler:
                _log.warning(
                    "attempted to set image handler when one already exists",
                )
                return
            self._handler = h

    async def take_picture(self) -> None:
        async def task() -> None:
            p = await asyncio.create_subprocess_exec(
                self._take_picture_command,
                self._output_file,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            if await p.wait() != 0:
                _log.error(
                    f"camera subprocess failed with exit code {p.returncode}",
                )
                return

            try:
                async with aiofiles.open(self._output_file, mode="rb") as f:
                    data = await f.read()
            except OSError as e:
                _log.error(f"failed to take picture: {e}")
                return

            async with self._lock:
                if self._handler:
                    await self._handler(data)

        async with self._lock:
            if not self._handler:
                _log.warning(
                    "attempted to take a picture when no handler exists",
                )
                return

            if self._task and not self._task.done():
                _log.warning(
                    "attempted to take a picture when another one is in "
                    "progress",
                )
                return

            if not self._has_camera():
                _log.info(
                    "no camera found",
                )
                return

            self._task = asyncio.create_task(task())

    @override
    async def disconnect(self) -> None:
        async with self._lock:
            if self._task:
                self._task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._task
                self._task = None
            self._handler = None


class _Battery(_Actor):
    def __init__(self) -> None:
        super().__init__()
        self._power_supply = ev3.power_supply()
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None
        _log.info("created battery")

    def status(self) -> str:
        return f"{self._power_supply.measured_volts:.2f}"

    async def set_handler(self, h: Callable[[str], Awaitable[None]]) -> None:
        async def task() -> None:
            while True:
                await h(self.status())
                await asyncio.sleep(10)

        async with self._lock:
            if self._task:
                _log.warning(
                    "attempted to set battery handler when one already exists",
                )
                return
            self._task = asyncio.create_task(task())

    @override
    async def disconnect(self) -> None:
        async with self._lock:
            if self._task:
                self._task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._task
                self._task = None


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
        super().__init__()

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
        self._ticks_since_last = 0
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None
        _log.info("created drive")

    async def _init_background_task(self) -> None:
        async def task() -> None:
            while True:
                self._ticks_since_last += 1
                if (
                    self._touch_sensor.is_pressed or self._ticks_since_last > 75  # noqa: PLR2004
                ):
                    self.stop()
                await asyncio.sleep(0.1)

        self._ticks_since_last = 0

        async with self._lock:
            if self._task:
                return
            self._task = asyncio.create_task(task())

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

    async def _control_press(
        self,
        control: _TwoWayControl,
        value: float,
    ) -> None:
        await self._init_background_task()
        control.press(value)
        self._update_wheel_speeds()

    async def _control_release(
        self,
        control: _TwoWayControl,
        value: float,
    ) -> None:
        await self._init_background_task()
        control.release(value)
        self._update_wheel_speeds()

    async def drive(self, value: float) -> None:
        await self._control_press(self._drive_control, value)

    async def drive_release(self, value: float) -> None:
        await self._control_release(self._drive_control, value)

    async def turn(self, value: float) -> None:
        await self._control_press(self._turn_control, value)

    async def turn_release(self, value: float) -> None:
        await self._control_release(self._turn_control, value)

    def stop(self) -> None:
        self._ticks_since_last = 0
        self._drive_control.off()
        self._turn_control.off()
        self._update_wheel_speeds()

    @override
    async def disconnect(self) -> None:
        async with self._lock:
            self.stop()
            if self._task:
                self._task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._task
                self._task = None


class Head(_Actor):
    _HEAD_LIMIT = 320
    _HEAD_SPEED = 300

    def __init__(self) -> None:
        super().__init__()
        self._motor = ev3.medium_motor(_HEAD_PORT)
        self._control = _TwoWayControl()
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None

        self._motor.reset()
        self._motor.position = 0
        self._motor.stop_action = Motor.STOP_ACTION_BRAKE
        self._motor.ramp_up_sp = 0
        self._motor.ramp_down_sp = 0

        _log.info("created head")

    async def _init_background_task(self) -> None:
        async def task() -> None:
            while True:
                if (
                    self._control.value > 0
                    and self._motor.position > self._HEAD_LIMIT
                ) or (
                    self._control.value < 0
                    and self._motor.position < -self._HEAD_LIMIT
                ):
                    self.stop()
                await asyncio.sleep(0.1)

        async with self._lock:
            if self._task:
                return
            self._task = asyncio.create_task(task())

    def _update_motor_speed(self) -> None:
        speed = self._control.value * self._HEAD_SPEED
        self._motor.speed_sp = speed
        if speed == 0:
            self._motor.stop()
        else:
            self._motor.run_forever()

    async def turn(self, value: float) -> None:
        await self._init_background_task()
        self._control.press(value)
        self._update_motor_speed()

    async def turn_release(self, value: float) -> None:
        await self._init_background_task()
        self._control.release(value)
        self._update_motor_speed()

    def stop(self) -> None:
        self._control.off()
        self._update_motor_speed()

    @override
    async def disconnect(self) -> None:
        async with self._lock:
            self.stop()
            if self._task:
                self._task.cancel()
                with suppress(asyncio.CancelledError):
                    await self._task
                self._task = None


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

    @asynccontextmanager
    async def run(self) -> AsyncGenerator[Self]:
        try:
            async with (
                self._voice,
                self._camera,
                self._battery,
                self._drive,
                self._head,
            ):
                await self._voice.speak(Sounds.COMMENCE_AWAKENING)
                await self._voice.wait()
                await asyncio.sleep(1)
                await self._voice.speak(Sounds.EXTERMINATE)
                await self._voice.wait()

                _log.info("ready")
                yield self
        finally:
            await self._voice.speak(Sounds.STATUS_HIBERNATION)
            await self._voice.disconnect()

    async def disconnect(self) -> None:
        await self._voice.disconnect()
        await self._camera.disconnect()
        await self._battery.disconnect()
        await self._drive.disconnect()
        await self._head.disconnect()

    async def drive(self, value: float) -> None:
        await self._drive.drive(value)

    async def drive_release(self, value: float) -> None:
        await self._drive.drive_release(value)

    async def turn(self, value: float) -> None:
        await self._drive.turn(value)

    async def turn_release(self, value: float) -> None:
        await self._drive.turn_release(value)

    async def head_turn(self, value: float) -> None:
        await self._head.turn(value)

    async def head_turn_release(self, value: float) -> None:
        await self._head.turn_release(value)

    def stop_moving(self) -> None:
        self._drive.stop()
        self._head.stop()

    def toggle_lights(self) -> None:
        self._leds.toggle()

    async def speak(self, text: str) -> None:
        await self._voice.speak(text)

    async def stop_speaking(self) -> None:
        await self._voice.stop()

    async def set_camera_handler(
        self,
        h: Callable[[bytes], Awaitable[None]],
    ) -> None:
        await self._camera.set_handler(h)

    async def take_picture(self) -> None:
        await self._camera.take_picture()

    def battery_status(self) -> str:
        return self._battery.status()

    async def set_battery_handler(
        self,
        h: Callable[[str], Awaitable[None]],
    ) -> None:
        await self._battery.set_handler(h)
