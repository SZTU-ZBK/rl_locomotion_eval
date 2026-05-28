import copy
import os

import numpy as np
from ruamel.yaml import YAML, dump, RoundTripDumper

from raisimGymTorch.env.RaisimGymVecEnv import RaisimGymVecEnv as VecEnv


def _import_env_module(name):
    if name == "dagger_a1":
        from raisimGymTorch.env.bin import dagger_a1 as mod
    elif name == "rsg_a1_task":
        from raisimGymTorch.env.bin import rsg_a1_task as mod
    else:
        raise ValueError("Unknown env module: %s" % name)
    return mod


def make_env(config, urdf_path, spawn_scale=1.0):
    repo_root_path = config["_repo_root"]
    sim_cfg = config["sim"]
    env_module = sim_cfg["env_module"]
    mod = _import_env_module(env_module)

    cfg_path = config["paths"]["dagger_cfg"]
    if not os.path.isabs(cfg_path):
        cfg_path = os.path.join(repo_root_path, cfg_path)
    cfg = YAML().load(open(cfg_path, "r"))

    overrides = copy.deepcopy(config.get("environment_override", {}))
    overrides["morphology_eval"] = True
    overrides["urdf_path"] = os.path.abspath(urdf_path)
    overrides["morphology_spawn_scale"] = float(spawn_scale)
    overrides["num_envs"] = 1
    overrides["num_threads"] = 1
    overrides["render"] = False
    overrides["eval"] = False
    overrides["test"] = False

    for key, value in overrides.items():
        cfg["environment"][key] = value

    home_path = os.path.abspath(os.path.join(repo_root_path, ".."))
    rsc_path = sim_cfg.get("home_path_rsc", home_path + "/rsc")
    env = VecEnv(
        mod.RaisimGymEnv(rsc_path, dump(cfg["environment"], Dumper=RoundTripDumper)),
        cfg["environment"],
    )

    policy_cfg = config["policy"]
    ckpt_dir = policy_cfg["checkpoint_dir"]
    if not os.path.isabs(ckpt_dir):
        ckpt_dir = os.path.join(repo_root_path, ckpt_dir)
    env.load_scaling(ckpt_dir, int(policy_cfg["policy_id"]))
    env.set_itr_number(30000)
    return env, cfg
