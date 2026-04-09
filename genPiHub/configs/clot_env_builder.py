"""CLOT environment configuration builder for genPiHub.

Provides factory functions to create CLOT-specific environment configurations
for Genesis-based simulation.
"""

from __future__ import annotations
from typing import Optional


def create_clot_genesis_env_config(
    num_envs: int = 1,
    backend: str = "cuda",
    viewer: bool = False,
    enable_corruption: bool = False,
    episode_length_s: float = 20.0,
    dt: float = 0.005,
    decimation: int = 4,
):
    """Create CLOT Genesis environment configuration.

    This function creates a CLOTGenesisEnvCfg instance with sensible defaults
    for motion tracking tasks.

    Args:
        num_envs: Number of parallel environments
        backend: Physics backend ("cuda" or "cpu")
        viewer: Enable Genesis viewer
        enable_corruption: Enable observation corruption/noise
        episode_length_s: Episode length in seconds
        dt: Physics timestep (seconds)
        decimation: Control decimation factor (4 = 50Hz control @ 200Hz physics)

    Returns:
        CLOTGenesisEnvCfg instance configured for genPiHub

    Example:
        >>> from genPiHub.configs import create_clot_genesis_env_config
        >>> env_cfg = create_clot_genesis_env_config(
        ...     num_envs=1,
        ...     backend="cuda",
        ...     viewer=True,
        ... )
        >>> env = GenesisEnv(cfg=genesis_cfg, device="cuda", env_cfg=env_cfg)
    """
    # Import from genPiHub CLOT env
    from genPiHub.envs.clot import CLOTGenesisEnvCfg

    # Create base config
    cfg = CLOTGenesisEnvCfg()

    # Configure scene
    cfg.scene.num_envs = num_envs
    cfg.scene.backend = backend
    cfg.scene.viewer = viewer
    cfg.scene.dt = dt

    # Configure observations
    cfg.observations.policy.enable_corruption = enable_corruption

    # Configure episode
    cfg.episode_length_s = episode_length_s
    cfg.decimation = decimation

    return cfg


def create_clot_genesis_env_config_with_options(
    num_envs: int = 1,
    backend: str = "cuda",
    viewer: bool = False,
    **kwargs,
):
    """Create CLOT Genesis environment configuration with additional options.

    This is a more flexible version that allows passing arbitrary config options.

    Args:
        num_envs: Number of parallel environments
        backend: Physics backend ("cuda" or "cpu")
        viewer: Enable Genesis viewer
        **kwargs: Additional configuration options to override

    Returns:
        CLOTGenesisEnvCfg instance

    Example:
        >>> env_cfg = create_clot_genesis_env_config_with_options(
        ...     num_envs=4,
        ...     backend="cuda",
        ...     viewer=True,
        ...     env_spacing=(3.0, 3.0),  # Custom spacing
        ... )
    """
    # Import from genPiHub CLOT env
    from genPiHub.envs.clot import CLOTGenesisEnvCfg

    cfg = CLOTGenesisEnvCfg()

    # Apply base settings
    cfg.scene.num_envs = num_envs
    cfg.scene.backend = backend
    cfg.scene.viewer = viewer

    # Apply custom overrides from kwargs
    for key, value in kwargs.items():
        if "." in key:
            # Nested attribute (e.g., "scene.env_spacing")
            parts = key.split(".")
            obj = cfg
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)
        else:
            # Top-level attribute
            if hasattr(cfg, key):
                setattr(cfg, key, value)

    return cfg
