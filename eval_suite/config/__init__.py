import copy
import os

import yaml

_CONFIG_DIR = os.path.dirname(__file__)
_DEFAULT_PATH = os.path.join(_CONFIG_DIR, "eval_defaults.yaml")


def load_config(overrides_path=None, overrides_dict=None):
    with open(_DEFAULT_PATH, "r") as f:
        cfg = yaml.safe_load(f)
    if overrides_path:
        with open(overrides_path, "r") as f:
            extra = yaml.safe_load(f) or {}
        _deep_update(cfg, extra)
    if overrides_dict:
        _deep_update(cfg, overrides_dict)
    return cfg


def _deep_update(base, extra):
    for key, value in extra.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def repo_root(config):
    root = config.get("repo_root", ".")
    if os.path.isabs(root):
        return root
    return os.path.abspath(os.path.join(_CONFIG_DIR, "..", "..", root))
