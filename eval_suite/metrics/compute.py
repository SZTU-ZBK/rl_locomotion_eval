"""Compute morphology eval metrics from rollout trajectories."""

from __future__ import division, print_function

import math

import numpy as np


def _normalize_yaw(yaw):
    return (yaw + math.pi) % (2 * math.pi) - math.pi


def _yaw_delta(yaw, ref_yaw):
    return _normalize_yaw(yaw - ref_yaw)


def compute_metrics(trajectory, warmup_steps, base_variance_steps, robot_mass_kg, gravity=9.81):
    vx = np.asarray(trajectory["vx"], dtype=np.float64)
    vy = np.asarray(trajectory["vy"], dtype=np.float64)
    roll = np.asarray(trajectory["roll"], dtype=np.float64)
    pitch = np.asarray(trajectory["pitch"], dtype=np.float64)
    yaw = np.asarray(trajectory["yaw"], dtype=np.float64)
    power = np.asarray(trajectory["power"], dtype=np.float64)

    n = len(vx)
    if n == 0:
        return _empty_metrics()

    warmup_steps = min(warmup_steps, n - 1)
    steady_start = warmup_steps
    steady_end = n
    steady_slice = slice(steady_start, steady_end)

    ref_yaw = yaw[warmup_steps - 1] if warmup_steps > 0 else yaw[0]
    yaw_delta = np.array([_yaw_delta(y, ref_yaw) for y in yaw[steady_slice]])

    base_start = max(steady_start, n - base_variance_steps)
    base_slice = slice(base_start, n)
    if base_slice.stop > base_slice.start:
        var_vx_b = float(np.var(vx[base_slice]))
        var_vy_b = float(np.var(vy[base_slice]))
        var_roll_b = float(np.var(roll[base_slice]))
        var_pitch_b = float(np.var(pitch[base_slice]))
    else:
        var_vx_b = var_vy_b = var_roll_b = var_pitch_b = 0.0

    achieved_vx_mean = float(np.mean(vx[steady_slice])) if steady_end > steady_start else 0.0
    mean_power = float(np.mean(power[steady_slice])) if steady_end > steady_start else 0.0

    v_ref = max(abs(achieved_vx_mean), 1e-3)
    cot = mean_power / (robot_mass_kg * gravity * v_ref)

    completed = bool(trajectory.get("completed_full_episode", False))

    return {
        "v_max": achieved_vx_mean,
        "v_max_success_rate": 1.0 if completed else 0.0,
        "yaw_offset_mean": float(np.mean(np.abs(yaw_delta))) if len(yaw_delta) else 0.0,
        "yaw_variance": float(np.var(yaw[steady_slice])) if steady_end > steady_start else 0.0,
        "var_vx": var_vx_b,
        "var_vy": var_vy_b,
        "var_roll": var_roll_b,
        "var_pitch": var_pitch_b,
        "base_variance_scalar": float(np.mean([var_vx_b, var_vy_b, var_roll_b, var_pitch_b])),
        "mean_power": mean_power,
        "cot": float(cot),
        "episode_steps": n,
        "terminated_early": bool(trajectory.get("terminated_early", False)),
    }


def merge_speed_search_metrics(straight_metrics, v_max, v_max_success_rate):
    merged = dict(straight_metrics)
    merged["v_max"] = v_max
    merged["v_max_success_rate"] = v_max_success_rate
    return merged


def _empty_metrics():
    nan = float("nan")
    return {
        "v_max": nan,
        "v_max_success_rate": 0.0,
        "yaw_offset_mean": nan,
        "yaw_variance": nan,
        "var_vx": nan,
        "var_vy": nan,
        "var_roll": nan,
        "var_pitch": nan,
        "base_variance_scalar": nan,
        "mean_power": nan,
        "cot": nan,
        "episode_steps": 0,
        "terminated_early": True,
    }
