"""Main entry point."""

import argparse
import asyncio
import logging
from contextlib import suppress

from websockets.asyncio.server import serve

from dalek.controller import handler as controller_handler
from dalek.dalek import Dalek
from dalek.websocket import handler as websocket_handler

_log = logging.getLogger(__name__)


PORT = 12346


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

    async with (
        Dalek(
            args.sound_dir,
            args.text_to_speech_command,
            args.take_picture_command,
            args.camera_output_file,
        ).run() as dalek,
        serve(websocket_handler(dalek), "", PORT) as server,
    ):
        _log.info("controller starting")
        controller_task: asyncio.Task[None] = asyncio.create_task(
            controller_handler(dalek),
        )
        _log.info("network starting")
        await server.start_serving()
        await server.wait_closed()
        _log.info("network stopped")
        controller_task.cancel()
        with suppress(asyncio.CancelledError):
            await controller_task
        _log.info("controller stopped")


if __name__ == "__main__":
    asyncio.run(main())
