"""Shims for selecting between real and fake ev3 classes."""

from typing import Protocol

import ev3dev2.led
import ev3dev2.motor
import ev3dev2.port
import ev3dev2.power
import ev3dev2.sensor.lego

import dalek.fake_ev3


def is_real_ev3() -> bool:
    try:
        with open("/etc/os-release") as f:
            return "ev3dev" in f.read()
    except OSError:
        return False


class LegoPort(Protocol):
    mode: str


def lego_port(address: str) -> LegoPort:
    if is_real_ev3():
        return ev3dev2.port.LegoPort(address)
    return dalek.fake_ev3.LegoPort(address)


class Led(Protocol):
    brightness: int

    @property
    def max_brightness(self) -> int: ...


def led(name_pattern: str) -> Led:
    if is_real_ev3():
        return ev3dev2.led.Led(name_pattern)
    return dalek.fake_ev3.Led(name_pattern)


class PowerSupply(Protocol):
    @property
    def measured_volts(self) -> float: ...


def power_supply() -> PowerSupply:
    if is_real_ev3():
        return ev3dev2.power.PowerSupply()
    return dalek.fake_ev3.PowerSupply()


class Motor(Protocol):
    stop_action: str
    position: float
    speed_sp: float
    ramp_up_sp: float
    ramp_down_sp: float

    def reset(self) -> None: ...
    def stop(self) -> None: ...
    def run_forever(self) -> None: ...


class LargeMotor(Motor, Protocol): ...


def large_motor(address: str) -> LargeMotor:
    if is_real_ev3():
        return ev3dev2.motor.LargeMotor(address)
    return dalek.fake_ev3.LargeMotor(address)


class MediumMotor(Motor, Protocol): ...


def medium_motor(address: str) -> MediumMotor:
    if is_real_ev3():
        return ev3dev2.motor.MediumMotor(address)
    return dalek.fake_ev3.MediumMotor(address)


class TouchSensor(Protocol):
    def is_pressed(self) -> bool: ...


def touch_sensor(address: str) -> TouchSensor:
    if is_real_ev3():
        return ev3dev2.sensor.lego.TouchSensor(address)
    return dalek.fake_ev3.TouchSensor(address)
