def control_dt(config):
    return float(config["sim"]["control_dt"])


def steps_for_seconds(seconds, dt):
    return max(1, int(round(float(seconds) / float(dt))))
