"""AMO environment configuration builder for Policy Hub.

Provides factory functions to create AMO-specific environment configurations
without directly importing from the amo package in user scripts.
"""

from __future__ import annotations
from typing import Optional


def create_amo_genesis_env_config(
    num_envs: int = 1,
    backend: str = "cuda",
    viewer: bool = False,
    enable_corruption: bool = False,
    resampling_time: float = 1e9,
    standing_envs_ratio: float = 0.0,
):
    """Create AMO Genesis environment configuration.

    This function wraps the creation of AmoGenesisEnvCfg from the amo package,
    providing a Policy Hub interface for creating AMO-specific environment configs.

    Args:
        num_envs: Number of parallel environments
        backend: Physics backend ("cuda" or "cpu")
        viewer: Enable Genesis viewer
        enable_corruption: Enable observation corruption/noise
        resampling_time: Command resampling time (large value = no resampling)
        standing_envs_ratio: Ratio of environments with standing command

    Returns:
        AmoGenesisEnvCfg instance configured for Policy Hub

    Example:
        >>> from genPiHub.configs import create_amo_genesis_env_config
        >>> env_cfg = create_amo_genesis_env_config(
        ...     num_envs=1,
        ...     backend="cuda",
        ...     viewer=True,
        ... )
        >>> env = GenesisEnv(cfg=genesis_cfg, device="cuda", env_cfg=env_cfg)
    """
    # Import from Policy Hub (not from amo package!)
    from genPiHub.envs.amo import AmoGenesisEnvCfg

    # Create base config
    cfg = AmoGenesisEnvCfg()

    # Configure scene
    cfg.scene.num_envs = num_envs
    cfg.scene.backend = backend
    cfg.scene.viewer = viewer

    # Configure observations
    cfg.observations.policy.enable_corruption = enable_corruption

    # Configure commands
    cfg.commands.base_velocity.resampling_time_range = (resampling_time, resampling_time)
    cfg.commands.base_velocity.rel_standing_envs = standing_envs_ratio

    return cfg


def create_amo_genesis_env_config_with_options(
    num_envs: int = 1,
    backend: str = "cuda",
    viewer: bool = False,
    **kwargs,
):
    """Create AMO Genesis environment configuration with additional options.

    This is a more flexible version that allows passing arbitrary config options.

    Args:
        num_envs: Number of parallel environments
        backend: Physics backend ("cuda" or "cpu")
        viewer: Enable Genesis viewer
        **kwargs: Additional configuration options to override

    Returns:
        AmoGenesisEnvCfg instance

    Example:
        >>> env_cfg = create_amo_genesis_env_config_with_options(
        ...     num_envs=4,
        ...     backend="cuda",
        ...     viewer=True,
        ...     env_spacing=(3.0, 3.0),  # Custom spacing
        ... )
    """
    # Import from Policy Hub (not from amo package!)
    from genPiHub.envs.amo import AmoGenesisEnvCfg

    cfg = AmoGenesisEnvCfg()

    # Apply base settings
    cfg.scene.num_envs = num_envs
    cfg.scene.backend = backend
    cfg.scene.viewer = viewer

    # Default AMO settings for Policy Hub
    cfg.observations.policy.enable_corruption = False
    cfg.commands.base_velocity.resampling_time_range = (1e9, 1e9)
    cfg.commands.base_velocity.rel_standing_envs = 0.0

    # Apply additional kwargs
    for key, value in kwargs.items():
        if '.' in key:
            # Handle nested attributes like "scene.env_spacing"
            parts = key.split('.')
            obj = cfg
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)
        else:
            # Direct attribute
            if hasattr(cfg, key):
                setattr(cfg, key, value)

    return cfg


# Convenience aliases
build_amo_env_config = create_amo_genesis_env_config
amo_env_config = create_amo_genesis_env_config
