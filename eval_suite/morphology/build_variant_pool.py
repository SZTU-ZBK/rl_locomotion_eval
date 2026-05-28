"""Generate A1 morphology URDF variant pools for eval."""

from __future__ import division, print_function

import argparse
import json
import os
import sys

import numpy as np

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from eval_suite.config import load_config, repo_root
from eval_suite.morphology import urdf_scaler


def _sample_scales(rng, num_variants, scale_min, scale_max, mode):
    entries = []
    for i in range(num_variants):
        if mode == "symmetric":
            s = float(rng.uniform(scale_min, scale_max))
            leg_scales = urdf_scaler.symmetric_leg_scales(s)
            randomized_scale = s
        elif mode == "full_asym":
            leg_scales = {
                leg: float(rng.uniform(scale_min, scale_max))
                for leg in urdf_scaler.LEG_PREFIXES
            }
            randomized_scale = urdf_scaler.mean_leg_scale(leg_scales)
        else:
            raise ValueError("Unknown mode: %s" % mode)
        entries.append({
            "variant_index": i,
            "randomized_scale": randomized_scale,
            "leg_scales": leg_scales,
        })
    entries.sort(key=lambda e: e["randomized_scale"])
    for idx, entry in enumerate(entries):
        entry["variant_index"] = idx
    return entries


def build_pool(mode, num_variants, out_dir, seed, scale_min, scale_max, base_urdf):
    rng = np.random.RandomState(seed)
    urdf_dir = os.path.join(out_dir, "urdf")
    os.makedirs(urdf_dir, exist_ok=True)
    mesh_dir = os.path.join(os.path.dirname(os.path.dirname(base_urdf)), "meshes")

    entries = _sample_scales(rng, num_variants, scale_min, scale_max, mode)
    manifest = {
        "mode": mode,
        "seed": seed,
        "scale_min": scale_min,
        "scale_max": scale_max,
        "num_variants": num_variants,
        "variants": [],
    }

    for entry in entries:
        idx = entry["variant_index"]
        fname = "variant_%03d.urdf" % idx
        dst = os.path.join(urdf_dir, fname)
        urdf_scaler.scale_a1_urdf_file(base_urdf, dst, entry["leg_scales"], mesh_dir=mesh_dir)
        manifest["variants"].append({
            "variant_index": idx,
            "randomized_scale": entry["randomized_scale"],
            "leg_scales": entry["leg_scales"],
            "urdf_path": os.path.abspath(dst),
            "urdf_filename": fname,
        })

    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print("Wrote %d variants to %s" % (num_variants, manifest_path))
    return manifest_path


def main():
    parser = argparse.ArgumentParser(description="Build A1 morphology URDF pool")
    parser.add_argument("--mode", required=True, choices=["symmetric", "full_asym"])
    parser.add_argument("--num_variants", type=int, default=None)
    parser.add_argument("--out_dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--scale_min", type=float, default=None)
    parser.add_argument("--scale_max", type=float, default=None)
    parser.add_argument("--base_urdf", type=str, default=None)
    args = parser.parse_args()

    cfg = load_config()
    root = repo_root(cfg)
    morph = cfg["morphology"]
    paths = cfg["paths"]

    num_variants = args.num_variants or morph["pool_size"]
    seed = args.seed if args.seed is not None else morph["seed"]
    scale_min = args.scale_min if args.scale_min is not None else morph["scale_min"]
    scale_max = args.scale_max if args.scale_max is not None else morph["scale_max"]

    if args.out_dir:
        out_dir = args.out_dir
    elif args.mode == "symmetric":
        out_dir = paths["symmetric_assets"]
    else:
        out_dir = paths["full_asym_assets"]
    if not os.path.isabs(out_dir):
        out_dir = os.path.join(root, out_dir)

    base_urdf = args.base_urdf or paths["base_urdf"]
    if not os.path.isabs(base_urdf):
        base_urdf = os.path.join(root, base_urdf)

    build_pool(args.mode, num_variants, out_dir, seed, scale_min, scale_max, base_urdf)


if __name__ == "__main__":
    main()
