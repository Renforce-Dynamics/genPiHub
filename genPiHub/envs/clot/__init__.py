"""CLOT (Closed-Loop Motion Tracking) environment configuration.

CLOT is from the humanoid_benchmark project and provides closed-loop
global motion tracking using AMP (Adversarial Motion Priors).

Reference: https://arxiv.org/abs/2602.15060
"""

from .env_cfg import CLOTGenesisEnvCfg, build_clot_env_config

__all__ = ["CLOTGenesisEnvCfg", "build_clot_env_config"]
