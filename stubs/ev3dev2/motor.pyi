OUTPUT_A: str
OUTPUT_B: str
OUTPUT_C: str
OUTPUT_D: str

class Motor:
    STOP_ACTION_COAST: str
    STOP_ACTION_BRAKE: str

    stop_action: str
    position: float
    speed_sp: float
    ramp_up_sp: float
    ramp_down_sp: float

    def __init__(self, address: str) -> None: ...
    def reset(self) -> None: ...
    def stop(self) -> None: ...
    def run_forever(self) -> None: ...

class LargeMotor(Motor): ...
class MediumMotor(Motor): ...
