"""Main entry point."""

import argparse
import asyncio
import base64
import json
import logging
from collections.abc import Sequence
from enum import Enum, StrEnum, auto

from websockets import Data
from websockets.asyncio.server import ServerConnection, serve

from dalek.dalek import Dalek

_log = logging.getLogger(__name__)


class Result(Enum):
    KEEP_GOING = auto()
    SHUTDOWN = auto()


PORT = 12346


class Status(StrEnum):
    CONNECTED = "ready"
    SOMEONE_ELSE_CONNECTED = "busy"


class Command(StrEnum):
    BEGIN = "begin"
    RELEASE = "release"
    STOP = "stop"
    PLAY_SOUND = "playsound"
    STOP_SOUND = "stopsound"
    SNAPSHOT = "snapshot"
    TOGGLE_LIGHTS = "togglelights"
    EXIT = "exit"


class MovementControl(StrEnum):
    DRIVE = "drive"
    TURN = "turn"
    HEAD_TURN = "headturn"


class Response(StrEnum):
    BATTERY = "battery"
    SNAPSHOT = "snapshot"


class Controller:
    def __init__(self, websocket: ServerConnection, dalek: Dalek) -> None:
        super().__init__()
        self._websocket = websocket
        self._dalek = dalek

        async def image_handler(data: bytes) -> None:
            await self._send_image(data)

        self._dalek.set_camera_handler(image_handler)

        async def battery_handler(data: str) -> None:
            await self._send_battery(data)

        self._dalek.set_battery_handler(battery_handler)

    def _bad_args(
        self,
        command: str,
        args: Sequence[str],
        required: str,
    ) -> None:
        _log.warning(
            f"command '{command}' requires {required} arg(s); got {args}",
        )

    async def _send(self, response: Response, *args: str) -> None:
        _log.info(f"send {response} {list(args)}")
        await self._websocket.send(json.dumps([response, *args]) + "\n")

    async def _send_battery(self, data: str) -> None:
        await self._send(Response.BATTERY, data)

    async def _send_image(self, data: bytes) -> None:
        await self._send(Response.SNAPSHOT, base64.b64encode(data).decode())

    def _begin_command(self, control: MovementControl, value: float) -> None:
        if control == MovementControl.DRIVE:
            self._dalek.drive(value)
        elif control == MovementControl.TURN:
            self._dalek.turn(value)
        elif control == MovementControl.HEAD_TURN:
            self._dalek.head_turn(value)

    def _release_command(self, control: MovementControl, value: float) -> None:
        if control == MovementControl.DRIVE:
            self._dalek.drive_release(value)
        elif control == MovementControl.TURN:
            self._dalek.turn_release(value)
        elif control == MovementControl.HEAD_TURN:
            self._dalek.head_turn_release(value)

    async def handle(self, command: str, args: Sequence[str]) -> Result:
        _log.info(f"recv {command} {args}")
        if command == Command.BEGIN:
            if len(args) == 2:  # noqa: PLR2004
                self._begin_command(MovementControl(args[0]), float(args[1]))
            else:
                self._bad_args(command, args, "2")
        elif command == Command.RELEASE:
            if len(args) == 2:  # noqa: PLR2004
                self._release_command(MovementControl(args[0]), float(args[1]))
            else:
                self._bad_args(command, args, "2")
        elif command == Command.STOP:
            self._dalek.stop_moving()
        elif command == Command.TOGGLE_LIGHTS:
            self._dalek.toggle_lights()
        elif command == Command.PLAY_SOUND:
            if len(args) == 1:
                self._dalek.speak(args[0])
            else:
                self._bad_args(command, args, "1")
        elif command == Command.STOP_SOUND:
            await self._dalek.stop_speaking()
        elif command == Command.SNAPSHOT:
            self._dalek.take_picture()
        elif command == Command.EXIT:
            return Result.SHUTDOWN
        else:
            _log.warning(f"unknown command {command} {args}")

        return Result.KEEP_GOING


def parse_message(message: Data) -> tuple[str, list[str]] | None:
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


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description="Run this on the Dalek so it can be controlled remotely",
    )
    parser.add_argument("sound_dir", help="Directory containing sound files")
    parser.add_argument("text_to_speech_command", help="Text to speech command")
    parser.add_argument("take_picture_command", help="Take picture command")
    parser.add_argument("camera_output_file", help="File to save pictures to")
    args = parser.parse_args()

    connected = False

    async def _handler(websocket: ServerConnection) -> None:
        nonlocal connected

        if connected:
            await websocket.send(
                json.dumps([Status.SOMEONE_ELSE_CONNECTED]) + "\n",
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
                json.dumps([Status.CONNECTED, dalek.battery_status()]),
            )

            c = Controller(websocket, dalek)
            async for message in websocket:
                command = parse_message(message)
                if command and await c.handle(*command) == Result.SHUTDOWN:
                    websocket.server.close()
                    break
        finally:
            await dalek.disconnect()
            connected = False
            _log.info(f"disconnected from {websocket.remote_address}")

    async with (
        Dalek(
            args.sound_dir,
            args.text_to_speech_command,
            args.take_picture_command,
            args.camera_output_file,
        ) as dalek,
        serve(_handler, "", PORT) as server,
    ):
        _log.info("network starting")
        await server.start_serving()
        await server.wait_closed()
        _log.info("network stopped")


if __name__ == "__main__":
    asyncio.run(main())
