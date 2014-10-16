
def clamp_percent(factor):
    factor = float(factor)
    if factor < 0.0:
        return 0.0
    elif factor > 1.0:
        return 1.0
    else:
        return factor
