"""BeyondMimic environment configuration builder for genPiHub.

Provides factory functions to create BeyondMimic-specific environment configurations.
"""

from __future__ import annotations


def create_beyondmimic_genesis_env_config(
    num_envs: int = 1,
    backend: str = "cuda",
    viewer: bool = False,
    enable_corruption: bool = False,
    episode_length_s: float = 20.0,
):
    """Create BeyondMimic Genesis environment configuration.

    Args:
        num_envs: Number of parallel environments
        backend: Physics backend
        viewer: Enable Genesis viewer
        enable_corruption: Enable observation corruption/noise
        episode_length_s: Episode length in seconds

    Returns:
        BeyondMimicGenesisEnvCfg instance

    Example:
        >>> from genPiHub.configs import create_beyondmimic_genesis_env_config
        >>> env_cfg = create_beyondmimic_genesis_env_config(
        ...     num_envs=1,
        ...     backend="cuda",
        ...     viewer=True,
        ... )
    """
    from genPiHub.envs.beyondmimic import BeyondMimicGenesisEnvCfg

    cfg = BeyondMimicGenesisEnvCfg()
    cfg.scene.num_envs = num_envs
    cfg.scene.backend = backend
    cfg.scene.viewer = viewer
    cfg.observations.policy.enable_corruption = enable_corruption
    cfg.episode_length_s = episode_length_s

    return cfg
