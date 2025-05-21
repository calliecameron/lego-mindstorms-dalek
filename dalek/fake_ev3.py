"""Fake versions of some ev3dev classes, for testing."""

import logging

_LOG = logging.getLogger(__name__)


class Motor:
    def __init__(self, address: str) -> None:
        super().__init__()
        self._address = address
        self.stop_action = "coast"
        self.position = 0.0
        self.speed_sp = 0.0
        self.ramp_up_sp = 0.0
        self.ramp_down_sp = 0.0

    def reset(self) -> None:
        self._msg("reset")

    def stop(self) -> None:
        self._msg("stop")

    def run_forever(self) -> None:
        self._msg("run_forever")

    def _msg(self, s: str) -> None:
        _LOG.info(f"[{self.__class__.__name__} {self._address}] {s}")


class LargeMotor(Motor):
    pass


class MediumMotor(Motor):
    pass


class TouchSensor:
    def __init__(self, address: str) -> None:
        super().__init__()
        self._address = address

    def is_pressed(self) -> bool:
        return False


class PowerSupply:
    def __init__(self) -> None:
        super().__init__()

    @property
    def measured_volts(self) -> float:
        return 8.0


class LegoPort:
    def __init__(self, address: str) -> None:
        super().__init__()
        self._address = address
        self.mode = "auto"


class Led:
    _MAX_BRIGHTNESS = 100

    def __init__(self, name_pattern: str) -> None:
        super().__init__()
        self._name_pattern = name_pattern
        self._brightness = 0

    @property
    def max_brightness(self) -> int:
        return self._MAX_BRIGHTNESS

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, b: int) -> None:
        self._brightness = min(max(0, b), self._MAX_BRIGHTNESS)
        _LOG.info(
            f"[LEDs {self._name_pattern}] brightness {self._brightness}",
        )
