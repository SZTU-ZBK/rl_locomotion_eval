import numpy as np

from eval_suite.utils.timing import control_dt, steps_for_seconds


def run_rollout(env, policy, config, vx_cmd, wz_cmd=0.0):
    dt = control_dt(config)
    episode_steps = steps_for_seconds(config["episode"]["duration_s"], dt)

    env.wrapper.setSpeedCommand(float(vx_cmd), float(wz_cmd))
    env.reset()
    policy.reset()

    traj = {k: [] for k in ["vx", "vy", "vz", "roll", "pitch", "yaw", "power", "reward"]}
    telemetry = np.zeros((1, 8), dtype=np.float32)
    terminated_early = False

    for step_idx in range(episode_steps):
        obs = env.observe(False)
        action = policy(obs)
        reward, dones = env.step(action)
        env.wrapper.getTelemetry(telemetry)

        traj["vx"].append(float(telemetry[0, 0]))
        traj["vy"].append(float(telemetry[0, 1]))
        traj["vz"].append(float(telemetry[0, 2]))
        traj["roll"].append(float(telemetry[0, 3]))
        traj["pitch"].append(float(telemetry[0, 4]))
        traj["yaw"].append(float(telemetry[0, 5]))
        traj["power"].append(float(telemetry[0, 6]))
        traj["reward"].append(float(reward[0]))

        if dones[0]:
            terminated_early = step_idx < episode_steps - 1
            break

    traj["terminated_early"] = terminated_early
    traj["completed_full_episode"] = not terminated_early
    traj["episode_steps"] = len(traj["vx"])
    return traj
