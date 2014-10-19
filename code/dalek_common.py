
def clamp_control_range(value):
    value = float(value)
    if value < -1.0:
        return -1.0
    elif value > 1.0:
        return 1.0
    else:
        return value

def sign(x):
    if x > 0.0:
        return 1
    elif x < 0.0:
        return -1
    else:
        return 0
