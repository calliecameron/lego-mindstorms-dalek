"""Utilities."""

import logging
import os
import re
from enum import Enum, auto

_LOG = logging.getLogger(__name__)
_VERBOSE = bool(os.getenv("EVENT_QUEUE_VERBOSE"))


def espeakify(text: str) -> str:
    # Espeak can't pronounce 'Dalek', so force it to say 'Dahlek'
    return re.sub(r"Dalek", "Dahlek", text, flags=re.IGNORECASE)


def sound_filename(text: str) -> str:
    text = text.lower().replace(" ", "-")
    return "".join(
        c if re.fullmatch(r"[a-z0-9-]", c) is not None else "" for c in text
    )


def clamp_control_range(value: float) -> float:
    if value < -1.0:
        return -1.0
    if value > 1.0:
        return 1.0
    return value


class Sign(Enum):
    POSITIVE = auto()
    NEGATIVE = auto()
    ZERO = auto()


def sign(x: float) -> Sign:
    if x > 0.0:
        return Sign.POSITIVE
    if x < 0.0:
        return Sign.NEGATIVE
    return Sign.ZERO
