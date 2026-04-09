"""G1 robot configuration for CLOT motion tracking.

This module provides the G1 robot configuration for CLOT, which uses
23 DOF (without hands) for motion tracking tasks.
"""

from genesislab.components.articulation import ArticulationCfg
from genesislab.components import sim_utils
from genesislab.utils.configclass import configclass

# Genesis asset paths
GENESIS_NUCLEUS_DIR = "{GENESIS_NUCLEUS_DIR}"


@configclass
class G1ActuatorCfg:
    """G1 actuator configuration for CLOT."""

    # Legs (high stiffness for motion tracking)
    legs_stiffness = 250.0
    legs_damping = 6.0
    legs_effort_limit = 300.0
    legs_velocity_limit = 100.0

    # Torso (high stiffness)
    torso_stiffness = 350.0
    torso_damping = 12.0
    torso_effort_limit = 300.0
    torso_velocity_limit = 100.0

    # Arms (moderate stiffness)
    arms_stiffness = 50.0
    arms_damping = 2.5
    arms_effort_limit = 100.0
    arms_velocity_limit = 100.0


def G1_CLOT_CFG() -> ArticulationCfg:
    """Create G1 articulation config for CLOT motion tracking.

    Uses 23 DOF configuration (legs + torso + arms, no hands).
    Higher PD gains than AMO for precise motion tracking.

    Returns:
        ArticulationCfg for G1 robot optimized for CLOT
    """
    actuator_cfg = G1ActuatorCfg()

    return ArticulationCfg(
        spawn=sim_utils.UsdFileCfg(
            usd_path=f"{GENESIS_NUCLEUS_DIR}/Robots/Unitree/G1/g1.usd",
            activate_contact_sensors=True,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.75),
            joint_pos={
                # Legs - slightly bent stance
                "left_hip_pitch_joint": -0.1,
                "left_hip_roll_joint": 0.0,
                "left_hip_yaw_joint": 0.0,
                "left_knee_joint": 0.3,
                "left_ankle_pitch_joint": -0.2,
                "left_ankle_roll_joint": 0.0,

                "right_hip_pitch_joint": -0.1,
                "right_hip_roll_joint": 0.0,
                "right_hip_yaw_joint": 0.0,
                "right_knee_joint": 0.3,
                "right_ankle_pitch_joint": -0.2,
                "right_ankle_roll_joint": 0.0,

                # Torso - upright
                "waist_yaw_joint": 0.0,
                "waist_roll_joint": 0.0,
                "waist_pitch_joint": 0.0,

                # Arms - neutral pose
                "left_shoulder_pitch_joint": 0.5,
                "left_shoulder_roll_joint": 0.0,
                "left_shoulder_yaw_joint": 0.2,
                "left_elbow_joint": 0.3,

                "right_shoulder_pitch_joint": 0.5,
                "right_shoulder_roll_joint": 0.0,
                "right_shoulder_yaw_joint": -0.2,
                "right_elbow_joint": 0.3,
            },
            joint_vel={".*": 0.0},
        ),
        actuators={
            "legs": sim_utils.ImplicitActuatorCfg(
                joint_names_expr=[".*_hip_.*", ".*_knee", ".*_ankle_.*"],
                stiffness=actuator_cfg.legs_stiffness,
                damping=actuator_cfg.legs_damping,
                effort_limit=actuator_cfg.legs_effort_limit,
                velocity_limit=actuator_cfg.legs_velocity_limit,
            ),
            "torso": sim_utils.ImplicitActuatorCfg(
                joint_names_expr=["waist_.*"],
                stiffness=actuator_cfg.torso_stiffness,
                damping=actuator_cfg.torso_damping,
                effort_limit=actuator_cfg.torso_effort_limit,
                velocity_limit=actuator_cfg.torso_velocity_limit,
            ),
            "arms": sim_utils.ImplicitActuatorCfg(
                joint_names_expr=[".*_shoulder_.*", ".*_elbow"],
                stiffness=actuator_cfg.arms_stiffness,
                damping=actuator_cfg.arms_damping,
                effort_limit=actuator_cfg.arms_effort_limit,
                velocity_limit=actuator_cfg.arms_velocity_limit,
            ),
        },
    )


# G1 23 DOF joint names (standard order)
G1_23DOF_NAMES = [
    # Left leg (6)
    "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
    "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",

    # Right leg (6)
    "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
    "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",

    # Torso (3)
    "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",

    # Left arm (4)
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint", "left_elbow_joint",

    # Right arm (4)
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint", "right_elbow_joint",
]

# G1 default joint positions for CLOT
G1_CLOT_DEFAULT_POS = [
    # Left leg
    -0.1, 0.0, 0.0, 0.3, -0.2, 0.0,
    # Right leg
    -0.1, 0.0, 0.0, 0.3, -0.2, 0.0,
    # Torso
    0.0, 0.0, 0.0,
    # Left arm
    0.5, 0.0, 0.2, 0.3,
    # Right arm
    0.5, 0.0, -0.2, 0.3,
]
