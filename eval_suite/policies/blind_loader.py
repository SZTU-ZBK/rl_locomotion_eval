import torch


class BlindPolicy:
    def __init__(self, checkpoint_dir, policy_id, base_dim, history_len, update_every=2):
        self.prop_enc = torch.jit.load("%s/prop_encoder_%s.pt" % (checkpoint_dir, policy_id))
        self.mlp = torch.jit.load("%s/mlp_%s.pt" % (checkpoint_dir, policy_id))
        self.base_dim = base_dim
        self.history_len = history_len
        self.update_every = update_every
        self._latent = None
        self._step = 0

    def reset(self):
        self._latent = None
        self._step = 0

    def __call__(self, obs):
        obs_t = torch.from_numpy(obs).float()
        if self._step % self.update_every == 0:
            self._latent = self.prop_enc(obs_t[:, : self.base_dim * self.history_len])
        cur = obs_t[:, self.base_dim * self.history_len : self.base_dim * (self.history_len + 1)]
        action = self.mlp(torch.cat([cur, self._latent], dim=1))
        self._step += 1
        return action.detach().numpy()


def load_policy(config, repo_root_path):
    policy_cfg = config["policy"]
    if policy_cfg["type"] != "blind":
        raise NotImplementedError("Only blind policy is supported currently")
    ckpt_dir = policy_cfg["checkpoint_dir"]
    if not ckpt_dir.startswith("/"):
        ckpt_dir = repo_root_path + "/" + ckpt_dir
    return BlindPolicy(
        checkpoint_dir=ckpt_dir,
        policy_id=str(policy_cfg["policy_id"]),
        base_dim=int(policy_cfg["base_dim"]),
        history_len=int(policy_cfg["history_len"]),
        update_every=int(policy_cfg.get("prop_latent_update_every", 2)),
    )
