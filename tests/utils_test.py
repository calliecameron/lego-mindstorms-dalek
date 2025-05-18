from threading import Thread
from time import sleep
from typing import override

from dalek.utils import (
    Event,
    EventQueue,
    Repeat,
    RunAfterCondition,
    RunAfterTime,
    Seconds,
    Sign,
    Status,
    Timer,
    clamp_control_range,
    espeakify,
    sign,
    sound_filename,
)

# ruff: noqa: PLR2004, S101, SLF001


class TestVoiceUtils:
    def test_espeakify(self) -> None:
        assert espeakify("Daleks are supreme") == "Dahleks are supreme"
        assert espeakify("You are a good dalek") == "You are a good Dahlek"
        assert espeakify("Test") == "Test"

    def test_sound_filename(self) -> None:
        assert sound_filename("A Dalek's voice") == "a-daleks-voice"
        assert sound_filename("test-text") == "test-text"


class TestNumericUtils:
    def test_clamp_control_range(self) -> None:
        assert clamp_control_range(-10.0) == -1.0
        assert clamp_control_range(-1.0) == -1.0
        assert clamp_control_range(-0.5) == -0.5
        assert clamp_control_range(0.5) == 0.5
        assert clamp_control_range(1.0) == 1.0
        assert clamp_control_range(10.0) == 1.0

    def test_sign(self) -> None:
        assert sign(-1.0) == Sign.NEGATIVE
        assert sign(0.0) == Sign.ZERO
        assert sign(1.0) == Sign.POSITIVE


class FakeEvent(Event):
    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name
        self._called = 0
        self._retval = Status.IN_PROGRESS

    @property
    def called(self) -> int:
        return self._called

    def set_retval(self, retval: Status) -> None:
        self._retval = retval

    @override
    def process(self) -> Status:
        self._called += 1
        return self._retval


class TestEventQueue:
    def test_event_queue(self) -> None:
        pre_processed = 0
        post_processed = 0

        class FakeEventQueue(EventQueue):
            @override
            def pre_process(self) -> None:
                nonlocal pre_processed
                pre_processed += 1

            @override
            def post_process(self) -> None:
                nonlocal post_processed
                post_processed += 1

        q = FakeEventQueue()
        a = FakeEvent("a")
        b = FakeEvent("b")

        assert q._queue == []

        q.add(a, b)
        assert q._queue == [a, b]

        q.add_if_empty(a)
        assert q._queue == [a, b]

        q.clear()
        assert q._queue == []

        q.add_if_empty(a)
        assert q._queue == [a]

        q.replace(a, b)
        assert q._queue == [a, b]

        assert pre_processed == 0
        assert post_processed == 0
        assert a.called == 0
        assert b.called == 0

        q.process()
        assert q._queue == [a, b]
        assert pre_processed == 1
        assert post_processed == 1
        assert a.called == 1
        assert b.called == 1

        a.set_retval(Status.DONE)
        q.process()
        assert q._queue == [b]
        assert pre_processed == 2
        assert post_processed == 2
        assert a.called == 2
        assert b.called == 2

        q.process()
        assert q._queue == [b]
        assert pre_processed == 3
        assert post_processed == 3
        assert a.called == 2
        assert b.called == 3

        b.set_retval(Status.DONE)
        q.process()
        assert q._queue == []
        assert pre_processed == 4
        assert post_processed == 4
        assert a.called == 2
        assert b.called == 4

        q.process()
        assert q._queue == []
        assert pre_processed == 5
        assert post_processed == 5
        assert a.called == 2
        assert b.called == 4

    def test_notify(self) -> None:
        q = EventQueue()
        a = FakeEvent("a")
        b = FakeEvent("b")

        class FakeThread(Thread):
            @override
            def run(self) -> None:
                q.wait_until_empty()

        t = FakeThread()
        t.start()
        sleep(0.1)
        t.join(timeout=10)
        assert not t.is_alive()
        assert q._queue == []

        q.add(a, b)
        t = FakeThread()
        t.start()
        sleep(0.1)
        q.clear()
        t.join(timeout=10)
        assert not t.is_alive()
        assert q._queue == []

        q.add(a, b)
        t = FakeThread()
        t.start()
        sleep(0.1)
        q.process()
        a.set_retval(Status.DONE)
        q.process()
        b.set_retval(Status.DONE)
        q.process()
        t.join(timeout=10)
        assert not t.is_alive()
        assert q._queue == []


class TestTimer:
    def test_immediate(self) -> None:
        start_calls = 0
        end_calls = 0

        def start() -> None:
            nonlocal start_calls
            start_calls += 1

        def end() -> None:
            nonlocal end_calls
            end_calls += 1

        t = Timer(
            time=Seconds(0),
            tick_length=Seconds(0.1),
            repeat=False,
            start_action=start,
            end_action=end,
        )

        assert start_calls == 0
        assert end_calls == 0

        assert t.process() == Status.DONE
        assert start_calls == 1
        assert end_calls == 1

    def test_no_repeat(self) -> None:
        start_calls = 0
        end_calls = 0

        def start() -> None:
            nonlocal start_calls
            start_calls += 1

        def end() -> None:
            nonlocal end_calls
            end_calls += 1

        t = Timer(
            time=Seconds(1.0),
            tick_length=Seconds(0.1),
            repeat=False,
            start_action=start,
            end_action=end,
        )

        assert start_calls == 0
        assert end_calls == 0

        for _ in range(9):
            assert t.process() == Status.IN_PROGRESS
            assert start_calls == 1
            assert end_calls == 0

        assert t.process() == Status.DONE
        assert start_calls == 1
        assert end_calls == 1

        assert t.process() == Status.DONE
        assert start_calls == 1
        assert end_calls == 1

    def test_repeat(self) -> None:
        start_calls = 0
        end_calls = 0

        def start() -> None:
            nonlocal start_calls
            start_calls += 1

        def end() -> None:
            nonlocal end_calls
            end_calls += 1

        t = Timer(
            time=Seconds(1.0),
            tick_length=Seconds(0.1),
            repeat=True,
            start_action=start,
            end_action=end,
        )

        assert start_calls == 0
        assert end_calls == 0

        for _ in range(9):
            assert t.process() == Status.IN_PROGRESS
            assert start_calls == 1
            assert end_calls == 0

        assert t.process() == Status.IN_PROGRESS
        assert start_calls == 1
        assert end_calls == 1

        for _ in range(9):
            assert t.process() == Status.IN_PROGRESS
            assert start_calls == 1
            assert end_calls == 1

        assert t.process() == Status.IN_PROGRESS
        assert start_calls == 1
        assert end_calls == 2


class TestRunAfterTime:
    def test_run_after_time(self) -> None:
        action_calls = 0

        def action() -> None:
            nonlocal action_calls
            action_calls += 1

        t = RunAfterTime(
            time=Seconds(1.0),
            tick_length=Seconds(0.1),
            action=action,
        )

        assert action_calls == 0

        for _ in range(9):
            assert t.process() == Status.IN_PROGRESS
            assert action_calls == 0

        assert t.process() == Status.DONE
        assert action_calls == 1

        assert t.process() == Status.DONE
        assert action_calls == 1


class TestRepeat:
    def test_repeat(self) -> None:
        action_calls = 0

        def action() -> None:
            nonlocal action_calls
            action_calls += 1

        t = Repeat(
            time=Seconds(1.0),
            tick_length=Seconds(0.1),
            action=action,
        )

        assert action_calls == 0

        for _ in range(9):
            assert t.process() == Status.IN_PROGRESS
            assert action_calls == 0

        assert t.process() == Status.IN_PROGRESS
        assert action_calls == 1

        for _ in range(9):
            assert t.process() == Status.IN_PROGRESS
            assert action_calls == 1

        assert t.process() == Status.IN_PROGRESS
        assert action_calls == 2


class TestRunAfterCondition:
    def test_run_after_condition(self) -> None:
        action_calls = 0
        cond = False

        def condition() -> bool:
            return cond

        def action() -> None:
            nonlocal action_calls
            action_calls += 1

        t = RunAfterCondition(
            condition=condition,
            action=action,
        )

        assert action_calls == 0

        assert t.process() == Status.IN_PROGRESS
        assert action_calls == 0

        assert t.process() == Status.IN_PROGRESS
        assert action_calls == 0

        cond = True

        assert t.process() == Status.DONE
        assert action_calls == 1

        assert t.process() == Status.DONE
        assert action_calls == 1
