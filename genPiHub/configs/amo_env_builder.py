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


def create_amo_genesis_env_config_with_usd_scene(
    usd_scene_path: str,
    num_envs: int = 1,
    backend: str = "cuda",
    viewer: bool = False,
    enable_corruption: bool = False,
    resampling_time: float = 1e9,
    standing_envs_ratio: float = 0.0,
    env_spacing: float = 2.5,
    increase_collision_limits: bool = True,
    dt: float = 0.001,  # Smaller timestep for complex USD scenes (1ms for stability)
):
    """Create AMO Genesis environment configuration with USD terrain.

    This function creates an AMO environment with USD scene as terrain.
    The USD is loaded as static terrain geometry.

    Args:
        usd_scene_path: Path to USD scene file (e.g., Scene.usd or Terrain.usd)
        num_envs: Number of parallel environments
        backend: Physics backend ("cuda" or "cpu")
        viewer: Enable Genesis viewer
        enable_corruption: Enable observation corruption/noise
        resampling_time: Command resampling time (large value = no resampling)
        standing_envs_ratio: Ratio of environments with standing command
        env_spacing: Spacing between environments (for multi-env setup)
        increase_collision_limits: Increase collision parameters for complex scenes
        dt: Physics simulation timestep (default 0.002 for stability with complex USD)

    Returns:
        AmoGenesisEnvCfg instance with USD terrain configured

    Example:
        >>> from genPiHub.configs import create_amo_genesis_env_config_with_usd_scene
        >>> env_cfg = create_amo_genesis_env_config_with_usd_scene(
        ...     usd_scene_path="path/to/Terrain.usd",
        ...     num_envs=1,
        ...     backend="cuda",
        ...     viewer=True,
        ... )
        >>> env = GenesisEnv(cfg=genesis_cfg, device="cuda", env_cfg=env_cfg)
    """
    # Import from Policy Hub and GenesisLab
    from genPiHub.envs.amo import AmoGenesisEnvCfg
    from genesislab.components.terrains import TerrainCfg
    from genesislab.engine.sim import RigidOptionsCfg

    # Create base config
    cfg = AmoGenesisEnvCfg()

    # Configure scene
    cfg.scene.num_envs = num_envs
    cfg.scene.backend = backend
    cfg.scene.viewer = viewer
    cfg.scene.dt = dt  # Set smaller timestep for stability with complex geometry

    # Use USD as terrain (terrain system approach)
    cfg.scene.terrain = TerrainCfg(
        terrain_type="usd",
        usd_path=usd_scene_path,
        env_spacing=env_spacing,
    )

    # Increase collision limits and use more stable solver for complex scenes
    if increase_collision_limits:
        cfg.scene.rigid_options = RigidOptionsCfg(
            max_collision_pairs=1000000,  # Increase from default for complex scenes
            enable_collision=True,
            constraint_solver="GaussSeidel",  # More stable than Newton for complex geometry
        )

    # Configure observations
    cfg.observations.policy.enable_corruption = enable_corruption

    # Configure commands
    cfg.commands.base_velocity.resampling_time_range = (resampling_time, resampling_time)
    cfg.commands.base_velocity.rel_standing_envs = standing_envs_ratio

    return cfg


def create_amo_genesis_env_config_with_mesh_terrain(
    mesh_path: str,
    num_envs: int = 1,
    backend: str = "cuda",
    viewer: bool = False,
    enable_corruption: bool = False,
    resampling_time: float = 1e9,
    standing_envs_ratio: float = 0.0,
    env_spacing: float = 2.5,
    increase_collision_limits: bool = True,
):
    """Create AMO environment config with mesh terrain.

    Args:
        mesh_path: Path to mesh file (.obj, .stl, .glb, .gltf)
        num_envs: Number of parallel environments
        backend: Physics backend ("cuda" or "cpu")
        viewer: Enable Genesis viewer
        enable_corruption: Enable observation corruption/noise
        resampling_time: Command resampling time (large value = no resampling)
        standing_envs_ratio: Ratio of environments with standing command
        env_spacing: Grid spacing between environments
        increase_collision_limits: Increase collision pair limits for complex meshes

    Returns:
        AmoGenesisEnvCfg with mesh terrain configured

    Example:
        >>> cfg = create_amo_genesis_env_config_with_mesh_terrain(
        ...     mesh_path="data/assets/Barracks.glb",
        ...     num_envs=1,
        ...     viewer=True,
        ... )
        >>> env = GenesisEnv(cfg=genesis_cfg, device="cuda", env_cfg=env_cfg)
    """
    # Import from Policy Hub and GenesisLab
    from genPiHub.envs.amo import AmoGenesisEnvCfg
    from genesislab.components.terrains import TerrainCfg
    from genesislab.engine.sim import RigidOptionsCfg

    # Create base config
    cfg = AmoGenesisEnvCfg()

    # Configure scene
    cfg.scene.num_envs = num_envs
    cfg.scene.backend = backend
    cfg.scene.viewer = viewer

    # Use mesh as terrain (terrain system approach)
    cfg.scene.terrain = TerrainCfg(
        terrain_type="mesh",
        mesh_path=mesh_path,
        env_spacing=env_spacing,
    )

    # Increase collision limits for complex meshes if needed
    if increase_collision_limits:
        cfg.scene.rigid_options = RigidOptionsCfg(
            max_collision_pairs=1000000,  # Increase from default for complex scenes
            enable_collision=True,
        )

    # Configure observations
    cfg.observations.policy.enable_corruption = enable_corruption

    # Configure commands
    cfg.commands.base_velocity.resampling_time_range = (resampling_time, resampling_time)
    cfg.commands.base_velocity.rel_standing_envs = standing_envs_ratio

    return cfg


# Convenience aliases
build_amo_env_config = create_amo_genesis_env_config
amo_env_config = create_amo_genesis_env_config
