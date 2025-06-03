"""Game controller handlers."""

import asyncio
import logging
from collections.abc import Awaitable, Callable, Coroutine
from typing import Any

from evdev import (
    AbsEvent,
    InputDevice,
    KeyEvent,
    categorize,
    ecodes,
    list_devices,
)

from dalek.dalek import Dalek, Sounds

_log = logging.getLogger(__name__)

# Commented according to PS4 controller buttons
_SOUNDS = {
    ecodes.BTN_SOUTH: Sounds.EXTERMINATE,  # x
    ecodes.BTN_WEST: Sounds.GUN,  # square
    ecodes.BTN_EAST: Sounds.EXTERMINATE_3,  # circle
    ecodes.BTN_NORTH: Sounds.DALEKS_ARE_SUPREME,  # triangle
    ecodes.BTN_TL: Sounds.DOCTOR,  # L1
    ecodes.BTN_TR: Sounds.THE_DOCTOR,  # R1
    ecodes.BTN_TL2: Sounds.IT_IS_THE_DOCTOR,  # L2
    ecodes.BTN_TR2: Sounds.THE_DOCTOR_MUST_DIE,  # R2
    ecodes.BTN_THUMBL: Sounds.CAN_I_BE_OF_ASSISTANCE,  # left stick
    ecodes.BTN_THUMBR: Sounds.WOULD_YOU_CARE_FOR_SOME_TEA,  # right stick
    ecodes.BTN_SELECT: Sounds.YOU_WOULD_MAKE_A_GOOD_DALEK,  # share
    ecodes.BTN_START: Sounds.DALEKS_DO_NOT_QUESTION_ORDERS,  # options
    ecodes.BTN_MODE: Sounds.SOCIAL_INTERACTION_WILL_CEASE,  # PS button
    ecodes.BTN_DPAD_LEFT: Sounds.EXPLAIN,
    ecodes.BTN_DPAD_RIGHT: Sounds.REPORT,
    ecodes.BTN_DPAD_UP: Sounds.THAT_IS_INCORRECT,
    ecodes.BTN_DPAD_DOWN: Sounds.IDENTIFY_YOURSELF,
}


class _StickAxis:
    _MAX_VALUE = 255
    _DEAD_ZONE_SIZE = 10

    def __init__(
        self,
        fn: Callable[[float], Awaitable[None]],
        *,
        invert: bool = False,
    ) -> None:
        super().__init__()
        self._fn = fn
        self._multiplier = -1.0 if invert else 1.0
        self._middle = self._MAX_VALUE / 2.0
        self._dead_zone_min = self._middle - self._DEAD_ZONE_SIZE
        self._dead_zone_max = self._middle + self._DEAD_ZONE_SIZE
        self._last_value = 0.0

    def _convert_value(self, value: int) -> float:
        if value >= self._dead_zone_min and value <= self._dead_zone_max:
            return 0.0
        return ((value - self._middle) / self._middle) * self._multiplier

    async def handle(self, value: int) -> None:
        converted = self._convert_value(value)
        if converted != 0.0 or self._last_value != 0.0:
            self._last_value = converted
            await self._fn(converted)


async def _play_sound(dalek: Dalek, scancode: int) -> None:
    sound = _SOUNDS.get(scancode)
    if sound:
        await dalek.speak(sound)


class _DPadAxis:
    def __init__(self, dalek: Dalek, plus_btn: int, minus_btn: int) -> None:
        super().__init__()
        self._dalek = dalek
        self._plus_btn = plus_btn
        self._minus_btn = minus_btn
        self._current_value = 0

    async def handle(self, value: int) -> None:
        if value == 1 and self._current_value != 1:
            await _play_sound(self._dalek, self._plus_btn)
        elif value == -1 and self._current_value != -1:
            await _play_sound(self._dalek, self._minus_btn)
        self._current_value = value


async def _handle_controller(dalek: Dalek, device: InputDevice[str]) -> None:
    left_stick_x = _StickAxis(dalek.turn)
    left_stick_y = _StickAxis(dalek.drive, invert=True)
    right_stick_y = _StickAxis(dalek.head_turn)
    dpad_x = _DPadAxis(dalek, ecodes.BTN_DPAD_RIGHT, ecodes.BTN_DPAD_LEFT)
    dpad_y = _DPadAxis(dalek, ecodes.BTN_DPAD_DOWN, ecodes.BTN_DPAD_UP)

    async for raw_event in device.async_read_loop():
        event = categorize(raw_event)
        if isinstance(event, KeyEvent) and event.keystate == KeyEvent.key_down:
            await _play_sound(dalek, event.scancode)
        elif isinstance(event, AbsEvent):
            if event.event.code == ecodes.ABS_X:
                await left_stick_x.handle(event.event.value)
            elif event.event.code == ecodes.ABS_Y:
                await left_stick_y.handle(event.event.value)
            elif event.event.code == ecodes.ABS_RX:
                await right_stick_y.handle(event.event.value)
            elif event.event.code == ecodes.ABS_HAT0X:
                await dpad_x.handle(event.event.value)
            elif event.event.code == ecodes.ABS_HAT0Y:
                await dpad_y.handle(event.event.value)


def handler(dalek: Dalek) -> Coroutine[Any, Any, None]:
    async def _handler() -> None:
        while True:
            for device in [InputDevice(path) for path in list_devices()]:
                if device.name == "Wireless Controller":
                    _log.info(f"found controller on {device.path}")
                    with device.grab_context():
                        await _handle_controller(dalek, device)
                    break
            await asyncio.sleep(1)

    return _handler()
