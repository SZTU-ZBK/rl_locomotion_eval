import numpy as np

from eval_suite.runners.rollout import run_rollout
from eval_suite.utils.timing import control_dt, steps_for_seconds


def _check_success(traj, vx_cmd, config):
    if traj["terminated_early"]:
        return False
    warmup_steps = steps_for_seconds(config["episode"]["warmup_s"], control_dt(config))
    steady_vx = np.asarray(traj["vx"][warmup_steps:], dtype=np.float64)
    if steady_vx.size == 0:
        return False
    threshold = float(config["speed_search"]["tracking_threshold"])
    return float(np.mean(np.abs(steady_vx - vx_cmd))) < threshold


def binary_search_vmax(env, policy, config):
    search = config["speed_search"]
    lo = float(search["v_min"])
    hi = float(search["v_max"])
    precision = float(search["precision"])
    ang_speed = float(search["ang_speed"])

    records = []
    best_vx_cmd = lo
    best_vx_meas = 0.0

    while hi - lo > precision:
        mid = (lo + hi) / 2.0
        traj = run_rollout(env, policy, config, vx_cmd=mid, wz_cmd=ang_speed)
        ok = _check_success(traj, mid, config)
        warmup_steps = steps_for_seconds(config["episode"]["warmup_s"], control_dt(config))
        steady_vx = traj["vx"][warmup_steps:]
        achieved = float(np.mean(steady_vx)) if steady_vx else 0.0
        records.append({
            "vx_cmd": mid,
            "success": ok,
            "achieved_vx_mean": achieved,
            "terminated_early": traj["terminated_early"],
            "episode_steps": traj["episode_steps"],
        })
        if ok:
            best_vx_cmd = mid
            best_vx_meas = achieved
            lo = mid
        else:
            hi = mid

    success_rate = float(np.mean([1.0 if r["success"] else 0.0 for r in records])) if records else 0.0
    return best_vx_meas, best_vx_cmd, success_rate, records
