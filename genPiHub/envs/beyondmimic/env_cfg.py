"""BeyondMimic environment configuration for Genesis.

Self-contained configuration for BeyondMimic whole-body tracking.
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

from pathlib import Path

# BeyondMimic G1 29 DOF MJCF model path (ground removed for Genesis compatibility)
# Path from genPiHub/envs/beyondmimic/env_cfg.py -> data/beyondmimic
# env_cfg.py -> beyondmimic -> envs -> genPiHub -> genPiHub(project) -> data
BEYONDMIMIC_ASSET_DIR = Path(__file__).resolve().parents[3] / "data" / "beyondmimic"

from . import observations as bm_obs
from .actions import BeyondMimicActionsCfg
from .robot_cfg import (
    G1_29DOF_BEYONDMIMIC_NAMES,
    G1_BEYONDMIMIC_DEFAULT_POS,
    G1_BEYONDMIMIC_STIFFNESS,
    G1_BEYONDMIMIC_DAMPING,
    G1_BEYONDMIMIC_EFFORT_LIMITS,
    G1_BEYONDMIMIC_VELOCITY_LIMIT,
    G1_BEYONDMIMIC_INITIAL_BASE_POS,
    G1_BEYONDMIMIC_INITIAL_BASE_QUAT,
)


def create_g1_beyondmimic_robot_cfg():
    """Create G1 robot configuration for BeyondMimic (29 DOF).

    Uses MJCF model from RoboJuDo with BeyondMimic joint ordering and PD parameters.

    Returns:
        RobotCfg for 29 DOF G1 with BeyondMimic PD parameters
    """
    from genesislab.components.actuators.actuator_pd_cfg import ImplicitActuatorCfg
    from genesislab.engine.assets.robot import InitialPoseCfg, RobotCfg

    # Convert default positions to dict (for MJCF)
    default_pos_dict = dict(zip(G1_29DOF_BEYONDMIMIC_NAMES, G1_BEYONDMIMIC_DEFAULT_POS))

    # BeyondMimic G1 29 DOF configuration
    # Uses MJCF from RoboJuDo (29 DOF with wrists)
    return RobotCfg(
        morph_type="MJCF",
        morph_path=str(BEYONDMIMIC_ASSET_DIR / "g1_29dof_rev_1_0.xml"),
        initial_pose=InitialPoseCfg(
            pos=G1_BEYONDMIMIC_INITIAL_BASE_POS,
            quat=G1_BEYONDMIMIC_INITIAL_BASE_QUAT,
        ),
        fixed_base=False,
        control_dofs=None,
        default_joint_pos=default_pos_dict,
        actuators={
            "beyondmimic": ImplicitActuatorCfg(
                # CRITICAL: Genesis reorders joints when loading MJCF!
                # We MUST explicitly specify the order to match BeyondMimicPolicy joint order
                # Use exact joint names (not patterns) to force the BeyondMimic order
                joint_names_expr=G1_29DOF_BEYONDMIMIC_NAMES,  # Explicitly ordered list (29 DOF)
                effort_limit_sim={
                    # Legs
                    ".*_hip_.*_joint": 300.0,
                    ".*_knee_joint": 300.0,
                    ".*_ankle_.*_joint": 300.0,
                    # Torso
                    "waist_.*_joint": 300.0,
                    # Arms
                    ".*_shoulder_.*_joint": 100.0,
                    ".*_elbow_joint": 100.0,
                    # Wrists
                    ".*_wrist_.*_joint": 50.0,
                },
                stiffness=G1_BEYONDMIMIC_STIFFNESS,
                damping=G1_BEYONDMIMIC_DAMPING,
                velocity_limit_sim={
                    ".*_hip_.*_joint": 100.0,
                    ".*_knee_joint": 100.0,
                    ".*_ankle_.*_joint": 100.0,
                    "waist_.*_joint": 100.0,
                    ".*_shoulder_.*_joint": 100.0,
                    ".*_elbow_joint": 100.0,
                    ".*_wrist_.*_joint": 100.0,
                },
            ),
        },
    )


@configclass
class BeyondMimicSceneCfg(SceneCfg):
    """BeyondMimic scene configuration."""

    num_envs: int = 1
    env_spacing: tuple = (2.5, 2.5)
    dt: float = 0.005  # 200 Hz
    substeps: int = 1
    backend: str = "cuda"
    viewer: bool = True
    terrain: TerrainCfg = TerrainCfg(terrain_type="plane")

    def __post_init__(self):
        """Create robot config after initialization."""
        self.robots = {"robot": create_g1_beyondmimic_robot_cfg()}

    sensors: dict = {
        "contact_forces": FakeContactSensorCfg(
            entity_name="robot",
            history_length=3,
            track_air_time=True,
        )
    }


@configclass
class BeyondMimicObservationsCfg:
    """BeyondMimic observation configuration.

    Observations vary based on whether state estimator is used.
    """

    @configclass
    class PolicyCfg(ObservationGroupCfg):
        """Policy observation group."""

        # Angular velocity (always included)
        base_ang_vel: ObservationTermCfg = ObservationTermCfg(
            func=bm_obs.base_ang_vel_b
        )

        # Linear velocity (only with state estimator)
        base_lin_vel: ObservationTermCfg = ObservationTermCfg(
            func=bm_obs.base_lin_vel_b
        )

        # Joint state
        joint_pos_rel: ObservationTermCfg = ObservationTermCfg(
            func=bm_obs.joint_pos_rel
        )
        joint_vel: ObservationTermCfg = ObservationTermCfg(
            func=bm_obs.joint_vel
        )

        # Last action
        last_action: ObservationTermCfg = ObservationTermCfg(
            func=bm_obs.last_action
        )

        def __post_init__(self):
            self.enable_corruption = False
            self.concatenate_terms = True

    policy: PolicyCfg = PolicyCfg()


@configclass
class BeyondMimicEventsCfg:
    """BeyondMimic reset events."""

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
class BeyondMimicRewardsCfg:
    """BeyondMimic rewards (placeholder)."""

    alive: RewardTermCfg = RewardTermCfg(func=base_mdp.is_alive, weight=1.0)


@configclass
class BeyondMimicGenesisEnvCfg(ManagerBasedRlEnvCfg):
    """BeyondMimic environment configuration for Genesis.

    Self-contained configuration for BeyondMimic whole-body tracking.
    """

    scene: BeyondMimicSceneCfg = BeyondMimicSceneCfg()
    observations: BeyondMimicObservationsCfg = BeyondMimicObservationsCfg()
    actions: BeyondMimicActionsCfg = BeyondMimicActionsCfg()
    commands: CommandsCfg = CommandsCfg()
    rewards: BeyondMimicRewardsCfg = BeyondMimicRewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    events: BeyondMimicEventsCfg = BeyondMimicEventsCfg()
    curriculum: CurriculumCfg = CurriculumCfg()

    def __post_init__(self):
        self.decimation = 4  # 50 Hz control
        self.episode_length_s = 20.0
        self.commands.base_velocity.ranges = self.commands.base_velocity.limit_ranges
        self.commands.base_velocity.rel_standing_envs = 0.0
        self.curriculum = None


def build_beyondmimic_env_config(
    num_envs: int = 1,
    viewer: bool = False,
    device: str = "cuda",
    **kwargs
) -> BeyondMimicGenesisEnvCfg:
    """Build BeyondMimic environment configuration.

    Args:
        num_envs: Number of parallel environments
        viewer: Whether to enable viewer
        device: Device for simulation
        **kwargs: Additional overrides

    Returns:
        BeyondMimicGenesisEnvCfg instance
    """
    cfg = BeyondMimicGenesisEnvCfg()
    cfg.scene.num_envs = num_envs
    cfg.scene.viewer = viewer
    cfg.scene.backend = device

    for key, value in kwargs.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)

    return cfg
