"""Run all morphology eval conditions and aggregate summary_all.csv."""

from __future__ import division, print_function

import argparse
import csv
import json
import os
import sys
from datetime import datetime

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from eval_suite.config import load_config, repo_root
from eval_suite.runners.run_condition import SUMMARY_FIELDS, run_condition


def run_all(config=None, out_dir=None, visualize=False):
    config = config or load_config()
    config["_repo_root"] = repo_root(config)
    root = config["_repo_root"]

    if out_dir is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = os.path.join(root, "eval_suite/results", stamp)
    os.makedirs(out_dir, exist_ok=True)

    all_rows = []
    for condition in ("baseline", "symmetric", "full_asym"):
        cond_dir = os.path.join(out_dir, condition)
        rows = run_condition(condition, cond_dir, config=config, visualize=visualize)
        all_rows.extend(rows)

    summary_all = os.path.join(out_dir, "summary_all.csv")
    with open(summary_all, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for row in all_rows:
            writer.writerow({k: row.get(k, "") for k in SUMMARY_FIELDS})

    with open(os.path.join(out_dir, "summary_all.json"), "w") as f:
        json.dump(all_rows, f, indent=2)

    _write_combined_report(out_dir, all_rows)
    print("Wrote %s" % summary_all)
    return out_dir, all_rows


def _write_combined_report(out_dir, rows):
    lines = ["# Morphology Eval Report", ""]
    by_cond = {}
    for row in rows:
        by_cond.setdefault(row["condition"], []).append(row)

    for condition, cond_rows in by_cond.items():
        v_max = [r["v_max"] for r in cond_rows if r.get("v_max") == r.get("v_max")]
        yaw = [r["yaw_offset_mean"] for r in cond_rows if r.get("yaw_offset_mean") == r.get("yaw_offset_mean")]
        power = [r["mean_power"] for r in cond_rows if r.get("mean_power") == r.get("mean_power")]
        lines.append("## %s" % condition)
        if v_max:
            import numpy as np
            lines.append("- v_max mean±std: %.3f ± %.3f" % (np.mean(v_max), np.std(v_max)))
        if yaw:
            import numpy as np
            lines.append("- yaw_offset_mean mean±std: %.4f ± %.4f" % (np.mean(yaw), np.std(yaw)))
        if power:
            import numpy as np
            lines.append("- mean_power mean±std: %.2f ± %.2f" % (np.mean(power), np.std(power)))
        lines.append("")

    report_path = os.path.join(out_dir, "COMBINED_REPORT.md")
    with open(report_path, "w") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=None)
    parser.add_argument("--out_dir", default=None)
    parser.add_argument("--visualize", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    run_all(config=cfg, out_dir=args.out_dir, visualize=args.visualize)


if __name__ == "__main__":
    main()
