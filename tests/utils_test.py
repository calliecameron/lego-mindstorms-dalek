from dalek.utils import (
    Sign,
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
