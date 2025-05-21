"""Utilities."""

import logging
import os
import re
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum, auto
from typing import NewType, final, override

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


class Status(Enum):
    IN_PROGRESS = auto()
    DONE = auto()


class Event(ABC):
    @abstractmethod
    def process(self) -> Status:  # pragma: no cover
        raise NotImplementedError


@final
class EventQueue:
    def __init__(
        self,
        *,
        preprocess: Callable[[], None] | None = None,
        postprocess: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self._queue: list[Event] = []
        self._lock = threading.Condition(threading.RLock())
        self._preprocess_fn = preprocess
        self._postprocess_fn = postprocess

    def add(self, *events: Event) -> None:
        with self._lock:
            self._queue.extend(events)

    def add_if_empty(self, *events: Event) -> None:
        with self._lock:
            if not self._queue:
                self._queue.extend(events)

    def clear(self) -> None:
        with self._lock:
            self._queue = []
            self._lock.notify_all()

    def replace(self, *events: Event) -> None:
        with self._lock:
            self._queue = list(events)

    def wait_until_empty(self) -> None:
        with self._lock:
            while self._queue:
                self._lock.wait()

    def process(self) -> None:
        with self._lock:
            self._preprocess()
            if _VERBOSE and self._queue:  # pragma: no cover
                _LOG.info(f"{self._queue}")
            i = 0
            while i < len(self._queue):
                if self._queue[i].process() == Status.IN_PROGRESS:
                    i += 1
                else:
                    del self._queue[i]
            self._postprocess()
            if not self._queue:
                self._lock.notify_all()

    def _preprocess(self) -> None:
        if self._preprocess_fn:
            self._preprocess_fn()

    def _postprocess(self) -> None:
        if self._postprocess_fn:
            self._postprocess_fn()


Seconds = NewType("Seconds", float)


class Timer(Event):
    def __init__(
        self,
        *,
        time: Seconds,
        tick_length: Seconds,
        repeat: bool,
        start_action: Callable[[], None] | None,
        end_action: Callable[[], None],
    ) -> None:
        super().__init__()
        self._init_ticks = max(int(time / tick_length) - 1, 0)
        self._ticks = self._init_ticks
        self._repeat = repeat
        self._init_start_action = start_action
        self._start_action = self._init_start_action
        self._end_action = end_action

    @override
    def process(self) -> Status:
        if self._start_action:
            self._start_action()
            self._start_action = None

        if self._ticks == 0:
            self._end_action()
            if self._repeat:
                self._ticks = self._init_ticks
                return Status.IN_PROGRESS

        self._ticks -= 1

        if self._ticks < 0:
            return Status.DONE
        return Status.IN_PROGRESS

    @override
    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Timer: total {self._init_ticks}, remaining {self._ticks}, repeat "
            f"{self._repeat} [{self._init_start_action}, {self._end_action}]"
        )


class Immediate(Timer):
    def __init__(self, action: Callable[[], None]) -> None:
        super().__init__(
            time=Seconds(0),
            tick_length=Seconds(1),
            repeat=False,
            start_action=None,
            end_action=action,
        )


class RunAfterTime(Timer):
    def __init__(
        self,
        *,
        time: Seconds,
        tick_length: Seconds,
        action: Callable[[], None],
    ) -> None:
        super().__init__(
            time=time,
            tick_length=tick_length,
            repeat=False,
            start_action=None,
            end_action=action,
        )


class Repeat(Timer):
    def __init__(
        self,
        *,
        time: Seconds,
        tick_length: Seconds,
        action: Callable[[], None],
    ) -> None:
        super().__init__(
            time=time,
            tick_length=tick_length,
            repeat=True,
            start_action=None,
            end_action=action,
        )


class RunAfterCondition(Event):
    def __init__(
        self,
        *,
        condition: Callable[[], bool],
        action: Callable[[], None],
    ) -> None:
        super().__init__()
        self._condition = condition
        self._action: Callable[[], None] | None = action

    @override
    def process(self) -> Status:
        if self._condition():
            if self._action:
                self._action()
                self._action = None
            return Status.DONE
        return Status.IN_PROGRESS

    @override
    def __repr__(self) -> str:  # pragma: no cover
        return f"RunAfterCondition [{self._condition}, {self._action}]"
