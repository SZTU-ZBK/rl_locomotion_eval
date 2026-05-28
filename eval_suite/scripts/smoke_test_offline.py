#!/usr/bin/env python3
"""Offline smoke test for eval_suite morphology assets."""

import json
import os
import sys
import xml.etree.ElementTree as ET

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO_ROOT)

from eval_suite.config import load_config, repo_root


def main():
    cfg = load_config()
    root = repo_root(cfg)
    errors = []

    base_urdf = cfg["paths"]["base_urdf"]
    if not os.path.isfile(base_urdf):
        errors.append("Missing base URDF: %s" % base_urdf)
    else:
        ET.parse(base_urdf)
        print("OK base URDF:", base_urdf)

    for key in ("symmetric_assets", "full_asym_assets"):
        assets = cfg["paths"][key]
        if not os.path.isabs(assets):
            assets = os.path.join(root, assets)
        manifest_path = os.path.join(assets, "manifest.json")
        if not os.path.isfile(manifest_path):
            print("SKIP missing manifest:", manifest_path)
            continue
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        for variant in manifest["variants"][:3]:
            urdf = variant["urdf_path"]
            if not os.path.isfile(urdf):
                errors.append("Missing variant URDF: %s" % urdf)
            else:
                ET.parse(urdf)
        print("OK manifest:", manifest_path, "variants=", len(manifest["variants"]))

    if errors:
        for err in errors:
            print("ERROR:", err)
        sys.exit(1)
    print("smoke_test_offline passed")


if __name__ == "__main__":
    main()
