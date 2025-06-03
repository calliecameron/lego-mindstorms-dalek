"""Websocket handlers."""

import base64
import json
import logging
from collections.abc import Awaitable, Callable, Sequence
from enum import Enum, StrEnum, auto
from types import TracebackType
from typing import Self

from websockets import Data
from websockets.asyncio.server import ServerConnection

from dalek.dalek import Dalek

_log = logging.getLogger(__name__)


class _Result(Enum):
    KEEP_GOING = auto()
    SHUTDOWN = auto()


class _Status(StrEnum):
    CONNECTED = "ready"
    SOMEONE_ELSE_CONNECTED = "busy"


class _Command(StrEnum):
    BEGIN = "begin"
    RELEASE = "release"
    STOP = "stop"
    PLAY_SOUND = "playsound"
    STOP_SOUND = "stopsound"
    SNAPSHOT = "snapshot"
    TOGGLE_LIGHTS = "togglelights"
    EXIT = "exit"


class _MovementControl(StrEnum):
    DRIVE = "drive"
    TURN = "turn"
    HEAD_TURN = "headturn"


class _Response(StrEnum):
    BATTERY = "battery"
    SNAPSHOT = "snapshot"


class _Controller:
    def __init__(self, websocket: ServerConnection, dalek: Dalek) -> None:
        super().__init__()
        self._websocket = websocket
        self._dalek = dalek

    async def __aenter__(self) -> Self:
        async def image_handler(data: bytes) -> None:
            await self._send_image(data)

        await self._dalek.set_camera_handler(image_handler)

        async def battery_handler(data: str) -> None:
            await self._send_battery(data)

        await self._dalek.set_battery_handler(battery_handler)

        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self._dalek.disconnect()

    def _bad_args(
        self,
        command: str,
        args: Sequence[str],
        required: str,
    ) -> None:
        _log.warning(
            f"command '{command}' requires {required} arg(s); got {args}",
        )

    async def _send(self, response: _Response, *args: str) -> None:
        _log.info(f"send {response} {list(args)}")
        await self._websocket.send(json.dumps([response, *args]) + "\n")

    async def _send_battery(self, data: str) -> None:
        await self._send(_Response.BATTERY, data)

    async def _send_image(self, data: bytes) -> None:
        await self._send(_Response.SNAPSHOT, base64.b64encode(data).decode())

    async def _begin_command(
        self,
        control: _MovementControl,
        value: float,
    ) -> None:
        if control == _MovementControl.DRIVE:
            await self._dalek.drive(value)
        elif control == _MovementControl.TURN:
            await self._dalek.turn(value)
        elif control == _MovementControl.HEAD_TURN:
            await self._dalek.head_turn(value)

    async def _release_command(
        self,
        control: _MovementControl,
        value: float,
    ) -> None:
        if control == _MovementControl.DRIVE:
            await self._dalek.drive_release(value)
        elif control == _MovementControl.TURN:
            await self._dalek.turn_release(value)
        elif control == _MovementControl.HEAD_TURN:
            await self._dalek.head_turn_release(value)

    async def handle(self, command: str, args: Sequence[str]) -> _Result:
        _log.info(f"recv {command} {args}")
        if command == _Command.BEGIN:
            if len(args) == 2:  # noqa: PLR2004
                await self._begin_command(
                    _MovementControl(args[0]),
                    float(args[1]),
                )
            else:
                self._bad_args(command, args, "2")
        elif command == _Command.RELEASE:
            if len(args) == 2:  # noqa: PLR2004
                await self._release_command(
                    _MovementControl(args[0]),
                    float(args[1]),
                )
            else:
                self._bad_args(command, args, "2")
        elif command == _Command.STOP:
            self._dalek.stop_moving()
        elif command == _Command.TOGGLE_LIGHTS:
            self._dalek.toggle_lights()
        elif command == _Command.PLAY_SOUND:
            if len(args) == 1:
                await self._dalek.speak(args[0])
            else:
                self._bad_args(command, args, "1")
        elif command == _Command.STOP_SOUND:
            await self._dalek.stop_speaking()
        elif command == _Command.SNAPSHOT:
            await self._dalek.take_picture()
        elif command == _Command.EXIT:
            return _Result.SHUTDOWN
        else:
            _log.warning(f"unknown command {command} {args}")

        return _Result.KEEP_GOING


def _parse_message(message: Data) -> tuple[str, list[str]] | None:
    if isinstance(message, bytes):
        try:
            message = message.decode("utf-8")
        except UnicodeDecodeError:
            _log.warning(f"command does not parse as utf-8: {message!r}")
            return None

    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        _log.warning(f"command does not parse as json: {message}")
        return None

    if not isinstance(data, list):
        _log.warning(f"command is not a list: {data}")
        return None

    if not data:
        _log.warning("command is empty")
        return None

    data = [str(item) for item in data]
    return (data[0], data[1:])


def handler(dalek: Dalek) -> Callable[[ServerConnection], Awaitable[None]]:
    connected = False

    async def _handler(websocket: ServerConnection) -> None:
        nonlocal connected

        if connected:
            await websocket.send(
                json.dumps([_Status.SOMEONE_ELSE_CONNECTED]) + "\n",
            )
            _log.info(
                (
                    f"attempted to connect from {websocket.remote_address}, "
                    "but someone else is already connected",
                ),
            )
            return

        connected = True
        _log.info(f"connected from {websocket.remote_address}")

        try:
            await websocket.send(
                json.dumps([_Status.CONNECTED, dalek.battery_status()]),
            )

            async with _Controller(websocket, dalek) as c:
                async for message in websocket:
                    command = _parse_message(message)
                    if command and await c.handle(*command) == _Result.SHUTDOWN:
                        websocket.server.close()
                        break
        finally:
            connected = False
            _log.info(f"disconnected from {websocket.remote_address}")

    return _handler
