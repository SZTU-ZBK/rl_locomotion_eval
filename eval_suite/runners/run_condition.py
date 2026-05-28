"""Run morphology eval for a single condition."""

from __future__ import division, print_function

import argparse
import csv
import json
import os
import sys
from datetime import datetime

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from eval_suite.config import load_config, repo_root
from eval_suite.metrics.compute import compute_metrics, merge_speed_search_metrics
from eval_suite.metrics.speed_search import binary_search_vmax
from eval_suite.policies.blind_loader import load_policy
from eval_suite.runners.env_factory import make_env
from eval_suite.runners.rollout import run_rollout
from eval_suite.utils.timing import control_dt, steps_for_seconds

SUMMARY_FIELDS = [
    "condition",
    "variant_index",
    "randomized_scale",
    "v_max",
    "v_max_success_rate",
    "yaw_offset_mean",
    "yaw_variance",
    "var_vx",
    "var_vy",
    "var_roll",
    "var_pitch",
    "base_variance_scalar",
    "mean_power",
    "cot",
    "urdf_path",
]


def _load_manifest(path):
    with open(path, "r") as f:
        return json.load(f)


def _baseline_variant(config):
    root = config["_repo_root"]
    urdf = config["paths"]["base_urdf"]
    if not os.path.isabs(urdf):
        urdf = os.path.join(root, urdf)
    return [{
        "variant_index": 0,
        "randomized_scale": 1.0,
        "urdf_path": os.path.abspath(urdf),
    }]


def _variants_for_condition(config, condition):
    morph = config["morphology"]
    num_eval = morph["num_variants"]
    paths = config["paths"]
    root = config["_repo_root"]

    if condition == "baseline":
        return _baseline_variant(config)

    if condition == "symmetric":
        manifest_path = os.path.join(root, paths["symmetric_assets"], "manifest.json")
    elif condition == "full_asym":
        manifest_path = os.path.join(root, paths["full_asym_assets"], "manifest.json")
    else:
        raise ValueError("Unknown condition: %s" % condition)

    if not os.path.isfile(manifest_path):
        raise FileNotFoundError("Missing manifest %s. Run build_variant_pool first." % manifest_path)

    manifest = _load_manifest(manifest_path)
    return manifest["variants"][:num_eval]


def _save_npz(path, trajectory, metrics):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez(
        path,
        vx=np.asarray(trajectory["vx"]),
        vy=np.asarray(trajectory["vy"]),
        roll=np.asarray(trajectory["roll"]),
        pitch=np.asarray(trajectory["pitch"]),
        yaw=np.asarray(trajectory["yaw"]),
        power=np.asarray(trajectory["power"]),
        reward=np.asarray(trajectory["reward"]),
        metrics=json.dumps(metrics),
    )


def run_condition(condition, out_dir, config=None, visualize=False):
    config = config or load_config()
    config["_repo_root"] = repo_root(config)

    os.makedirs(out_dir, exist_ok=True)
    config_copy = {k: v for k, v in config.items() if not k.startswith("_")}
    with open(os.path.join(out_dir, "config.json"), "w") as f:
        json.dump(config_copy, f, indent=2)

    dt = control_dt(config)
    ep = config["episode"]
    warmup_steps = steps_for_seconds(ep["warmup_s"], dt)
    base_var_steps = steps_for_seconds(ep["base_variance_window_s"], dt)
    robot_mass = config["robot"]["mass_kg"]
    gravity = config["metrics"]["gravity"]

    variants = _variants_for_condition(config, condition)
    manifest_out = {
        "condition": condition,
        "num_variants": len(variants),
        "variants": variants,
    }
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(manifest_out, f, indent=2)

    policy = load_policy(config, config["_repo_root"])
    straight_cmd = config["straight_line"]
    rows = []

    for variant in variants:
        idx = variant["variant_index"]
        urdf_path = variant["urdf_path"]
        print("[{}] variant {} scale={:.3f} urdf={}".format(
            condition, idx, variant.get("randomized_scale", 1.0), urdf_path))

        env, _ = make_env(config, urdf_path, spawn_scale=variant.get("randomized_scale", 1.0))
        if visualize:
            env.turn_on_visualization()

        if config["speed_search"].get("enabled", True):
            v_max, v_max_cmd, v_max_sr, speed_records = binary_search_vmax(env, policy, config)
        else:
            v_max, v_max_cmd, v_max_sr, speed_records = 0.0, 0.0, 0.0, []

        straight_traj = run_rollout(
            env,
            policy,
            config,
            vx_cmd=straight_cmd["command_max_speed"],
            wz_cmd=straight_cmd["command_ang_speed"],
        )
        straight_metrics = compute_metrics(
            straight_traj, warmup_steps, base_var_steps, robot_mass, gravity)
        metrics = merge_speed_search_metrics(straight_metrics, v_max, v_max_sr)

        ep_dir = os.path.join(out_dir, "episodes", "variant_%03d" % idx)
        os.makedirs(ep_dir, exist_ok=True)
        with open(os.path.join(ep_dir, "speed_limit.json"), "w") as f:
            json.dump({
                "records": speed_records,
                "v_max": v_max,
                "v_max_cmd": v_max_cmd,
                "v_max_success_rate": v_max_sr,
            }, f, indent=2)
        _save_npz(os.path.join(ep_dir, "straight_line.npz"), straight_traj, metrics)

        rows.append({
            "condition": condition,
            "variant_index": idx,
            "randomized_scale": variant.get("randomized_scale", 1.0),
            "urdf_path": urdf_path,
            **metrics,
        })

        env.close()

    summary_csv = os.path.join(out_dir, "summary.csv")
    with open(summary_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in SUMMARY_FIELDS})

    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(rows, f, indent=2)

    print("Wrote %s (%d variants)" % (summary_csv, len(rows)))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", required=True, choices=["baseline", "symmetric", "full_asym"])
    parser.add_argument("--out_dir", required=True)
    parser.add_argument("--config", default=None)
    parser.add_argument("--visualize", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    run_condition(args.condition, args.out_dir, config=cfg, visualize=args.visualize)


if __name__ == "__main__":
    main()
