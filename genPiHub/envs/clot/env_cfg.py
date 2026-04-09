"""CLOT environment configuration for Genesis.

This provides a self-contained Genesis environment configuration for CLOT
(Closed-Loop Motion Tracking), eliminating dependencies on humanoid_benchmark.
"""

from __future__ import annotations

from genesislab.components.terrains import TerrainCfg
from genesislab.components.sensors.fake_sensors import FakeContactSensorCfg
from genesislab.engine.scene import SceneCfg
from genesislab.managers import SceneEntityCfg, EventTermCfg
from genesislab.managers.observation_manager import ObservationGroupCfg, ObservationTermCfg
from genesislab.utils.configclass import configclass

import genesis_tasks.locomotion.hvelocity.mdp as base_mdp
from genesis_tasks.locomotion.hvelocity.components import (
    CommandsCfg,
    CurriculumCfg,
    TerminationsCfg,
)
from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnvCfg
from genesislab.managers import RewardTermCfg

from . import observations as clot_obs
from .robot_cfg import G1_CLOT_CFG
from .actions import CLOTActionsCfg


@configclass
class CLOTSceneCfg(SceneCfg):
    """CLOT scene configuration."""

    num_envs: int = 1
    env_spacing: tuple = (2.5, 2.5)
    dt: float = 0.005  # 200 Hz
    substeps: int = 1
    backend: str = "cuda"
    viewer: bool = True
    terrain: TerrainCfg = TerrainCfg(terrain_type="plane")
    robots: dict = {"robot": G1_CLOT_CFG}
    sensors: dict = {
        "contact_forces": FakeContactSensorCfg(
            entity_name="robot",
            history_length=3,
            track_air_time=True,
        )
    }


@configclass
class CLOTObservationsCfg:
    """CLOT observation configuration.

    CLOT uses two observation groups:
    1. Policy observations: for the main tracking policy
    2. AMP observations: for the discriminator (motion quality)
    """

    @configclass
    class PolicyCfg(ObservationGroupCfg):
        """Policy observation group.

        Includes proprio state for tracking control.
        """
        # Base state
        base_ang_vel: ObservationTermCfg = ObservationTermCfg(
            func=clot_obs.base_ang_vel_scaled
        )
        projected_gravity: ObservationTermCfg = ObservationTermCfg(
            func=clot_obs.projected_gravity
        )
        base_lin_vel: ObservationTermCfg = ObservationTermCfg(
            func=clot_obs.base_lin_vel
        )

        # Joint state
        joint_pos_rel: ObservationTermCfg = ObservationTermCfg(
            func=clot_obs.joint_pos_rel
        )
        joint_vel: ObservationTermCfg = ObservationTermCfg(
            func=clot_obs.joint_vel_scaled
        )

        # Actions
        last_action: ObservationTermCfg = ObservationTermCfg(
            func=clot_obs.last_action
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    @configclass
    class AMPCfg(ObservationGroupCfg):
        """AMP observation group for discriminator."""

        amp_obs: ObservationTermCfg = ObservationTermCfg(
            func=clot_obs.amp_observation
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()
    amp: AMPCfg = AMPCfg()


@configclass
class CLOTEventsCfg:
    """CLOT reset events (uses 'pelvis' for G1)."""

    reset_base: EventTermCfg = EventTermCfg(
        func=base_mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "pose_range": {"x": (-0.1, 0.1), "y": (-0.1, 0.1), "yaw": (-0.2, 0.2)},
            "velocity_range": {
                "x": (-0.05, 0.05),
                "y": (-0.05, 0.05),
                "z": (-0.05, 0.05),
                "roll": (-0.05, 0.05),
                "pitch": (-0.05, 0.05),
                "yaw": (-0.05, 0.05),
            },
            "asset_cfg": SceneEntityCfg("robot", body_names="pelvis"),
        },
    )

    reset_robot_joints: EventTermCfg = EventTermCfg(
        func=base_mdp.reset_joints_by_scale,
        mode="reset",
        params={
            "position_range": (0.5, 1.5),
            "velocity_range": (0.0, 0.0),
            "asset_cfg": SceneEntityCfg("robot", joint_names=".*"),
        },
    )


@configclass
class CLOTRewardsCfg:
    """CLOT rewards for motion tracking.

    Note: These are placeholder rewards. CLOT mainly uses AMP-based
    rewards computed from the discriminator.
    """

    # Tracking reward (placeholder - actual tracking reward from motion lib)
    alive: RewardTermCfg = RewardTermCfg(func=base_mdp.is_alive, weight=1.0)


@configclass
class CLOTGenesisEnvCfg(ManagerBasedRlEnvCfg):
    """CLOT environment configuration for Genesis.

    This is a self-contained configuration for CLOT motion tracking,
    compatible with genPiHub and not dependent on humanoid_benchmark code.
    """

    scene: CLOTSceneCfg = CLOTSceneCfg()
    observations: CLOTObservationsCfg = CLOTObservationsCfg()
    actions: CLOTActionsCfg = CLOTActionsCfg()
    commands: CommandsCfg = CommandsCfg()
    rewards: CLOTRewardsCfg = CLOTRewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: CLOTEventsCfg = CLOTEventsCfg()
    curriculum: CurriculumCfg = CurriculumCfg()

    def __post_init__(self):
        self.decimation = 4  # 50 Hz control
        self.episode_length_s = 20.0
        # Use base velocity commands
        self.commands.base_velocity.ranges = self.commands.base_velocity.limit_ranges
        self.commands.base_velocity.rel_standing_envs = 0.0
        # Disable curriculum for now
        self.curriculum = None


def build_clot_env_config(
    num_envs: int = 1,
    viewer: bool = False,
    device: str = "cuda",
    **kwargs
) -> CLOTGenesisEnvCfg:
    """Build CLOT environment configuration.

    Args:
        num_envs: Number of parallel environments
        viewer: Whether to enable viewer
        device: Device for simulation (cuda/cpu)
        **kwargs: Additional overrides for config

    Returns:
        CLOTGenesisEnvCfg instance
    """
    cfg = CLOTGenesisEnvCfg()
    cfg.scene.num_envs = num_envs
    cfg.scene.viewer = viewer
    cfg.scene.backend = device

    # Apply additional overrides
    for key, value in kwargs.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)

    return cfg
