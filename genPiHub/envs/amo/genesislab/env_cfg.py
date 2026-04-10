"""AMO-specific Genesis environment config (robot + observations).

This is a Policy Hub copy of the AMO environment configuration, eliminating
the need to import from the amo package.
"""

from __future__ import annotations

from genesislab.components.terrains import TerrainCfg
from genesislab.components.sensors.fake_sensors import FakeContactSensorCfg
from genesislab.engine.scene import SceneCfg
from genesislab.managers import SceneEntityCfg, EventTermCfg
from genesislab.managers.observation_manager import ObservationGroupCfg, ObservationTermCfg
from genesislab.utils.configclass import configclass

import math
import genesis_tasks.locomotion.hvelocity.mdp as base_mdp
from genesis_tasks.locomotion.hvelocity.components import (
    CommandsCfg,
    CurriculumCfg,
    TerminationsCfg,
)
from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnvCfg
from genesislab.managers import RewardTermCfg

# Import from Policy Hub copies (not from amo package!)
from . import observations as amo_obs
from .robot_cfg import G1_AMO_CFG
from .actions import AmoActionsCfg


@configclass
class AmoSceneCfg(SceneCfg):
    """AMO scene configuration."""
    num_envs: int = 1
    env_spacing: tuple = (2.5, 2.5)
    dt: float = 0.005
    substeps: int = 1
    backend: str = "cuda"
    viewer: bool = True
    # Use Genesis plane terrain (AMO ground removed from g1.xml to avoid conflict)
    terrain: TerrainCfg = TerrainCfg(terrain_type="plane")
    robots: dict = {"robot": G1_AMO_CFG}
    sensors: dict = {
        "contact_forces": FakeContactSensorCfg(
            entity_name="robot",
            history_length=3,
            track_air_time=True,
        )
    }


@configclass
class AmoObservationsCfg:
    """AMO observation configuration."""

    @configclass
    class PolicyCfg(ObservationGroupCfg):
        """Policy observation group."""
        # AMO-like proprio block components
        ang_vel_scaled: ObservationTermCfg = ObservationTermCfg(func=amo_obs.amo_ang_vel_scaled)
        roll_pitch: ObservationTermCfg = ObservationTermCfg(func=amo_obs.amo_rpy_roll_pitch)
        dyaw_sin_cos: ObservationTermCfg = ObservationTermCfg(
            func=amo_obs.amo_dyaw_sin_cos, params={"command_name": "base_velocity"}
        )
        joint_pos_rel: ObservationTermCfg = ObservationTermCfg(func=base_mdp.joint_pos_rel)
        joint_vel_scaled: ObservationTermCfg = ObservationTermCfg(func=amo_obs.amo_joint_vel_scaled)
        last_action: ObservationTermCfg = ObservationTermCfg(func=base_mdp.last_action)
        velocity_command: ObservationTermCfg = ObservationTermCfg(
            func=base_mdp.generated_commands, params={"command_name": "base_velocity"}
        )
        zeros_arm_placeholder: ObservationTermCfg = ObservationTermCfg(
            func=amo_obs.zeros_like_command, params={"command_name": "base_velocity", "dim": 8}
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()


@configclass
class AmoEventsCfg:
    """G1-specific events (uses 'pelvis' instead of 'base')."""

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
class AmoRewardsCfg:
    """Minimal rewards for AMO play mode (not used during policy rollout)."""
    # For play mode, rewards are not needed but the manager requires some terms
    alive: RewardTermCfg = RewardTermCfg(func=base_mdp.is_alive, weight=1.0)


@configclass
class AmoGenesisEnvCfg(ManagerBasedRlEnvCfg):
    """Dedicated env cfg for AMO play in Genesis.

    This configuration is self-contained within Policy Hub and does not
    require importing from the amo package.
    """

    scene: AmoSceneCfg = AmoSceneCfg()
    observations: AmoObservationsCfg = AmoObservationsCfg()
    actions: AmoActionsCfg = AmoActionsCfg()  # Use AMO-specific actions with correct offset
    commands: CommandsCfg = CommandsCfg()
    rewards: AmoRewardsCfg = AmoRewardsCfg()  # Use AMO-specific rewards
    terminations: TerminationsCfg = None # TerminationsCfg()
    events: AmoEventsCfg = AmoEventsCfg()
    curriculum: CurriculumCfg = CurriculumCfg()

    def __post_init__(self):
        self.decimation = 4
        self.episode_length_s = 20.0
        self.commands.base_velocity.ranges = self.commands.base_velocity.limit_ranges
        self.commands.base_velocity.rel_standing_envs = 0.0
        # Disable curriculum manager for AMO demo (no terrain generator needed)
        self.curriculum = None
