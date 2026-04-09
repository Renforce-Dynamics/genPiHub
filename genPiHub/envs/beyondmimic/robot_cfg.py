"""G1 robot configuration for BeyondMimic (29 DOF with hands).

BeyondMimic uses the full 29 DOF G1 configuration including wrist joints.
Joint ordering is specific to BeyondMimic training.
"""

from genesislab.components.articulation import ArticulationCfg
from genesislab.components import sim_utils
from genesislab.utils.configclass import configclass

# Genesis asset paths
GENESIS_NUCLEUS_DIR = "{GENESIS_NUCLEUS_DIR}"


@configclass
class G1BeyondMimicActuatorCfg:
    """G1 actuator configuration for BeyondMimic.

    PD gains from RoboJuDo BeyondMimic configuration.
    """

    # Legs (grouped by DOF type)
    hip_pitch_stiffness = 40.179
    hip_pitch_damping = 2.558

    hip_roll_stiffness = 99.098
    hip_roll_damping = 6.309

    hip_yaw_stiffness = 40.179
    hip_yaw_damping = 2.558

    knee_stiffness = 99.098
    knee_damping = 6.309

    ankle_pitch_stiffness = 28.501
    ankle_pitch_damping = 1.814

    ankle_roll_stiffness = 28.501
    ankle_roll_damping = 1.814

    # Torso
    waist_stiffness = [40.179, 99.098, 28.501]  # yaw, roll, pitch
    waist_damping = [2.558, 6.309, 1.814]

    # Arms
    shoulder_pitch_stiffness = 14.251
    shoulder_pitch_damping = 0.907

    shoulder_roll_stiffness = 14.251
    shoulder_roll_damping = 0.907

    shoulder_yaw_stiffness = 14.251
    shoulder_yaw_damping = 0.907

    elbow_stiffness = 14.251
    elbow_damping = 0.907

    # Wrists
    wrist_roll_stiffness = 14.251
    wrist_roll_damping = 0.907

    wrist_pitch_stiffness = 16.778
    wrist_pitch_damping = 1.068

    wrist_yaw_stiffness = 16.778
    wrist_yaw_damping = 1.068

    # Effort limits
    legs_effort_limit = 300.0
    torso_effort_limit = 300.0
    arms_effort_limit = 100.0
    wrists_effort_limit = 50.0

    # Velocity limits
    velocity_limit = 100.0


def G1_BEYONDMIMIC_CFG() -> ArticulationCfg:
    """Create G1 articulation config for BeyondMimic (29 DOF).

    Uses full G1 configuration including wrist joints.
    PD gains optimized for motion tracking.

    Returns:
        ArticulationCfg for 29 DOF G1 robot
    """
    actuator_cfg = G1BeyondMimicActuatorCfg()

    return ArticulationCfg(
        spawn=sim_utils.UsdFileCfg(
            usd_path=f"{GENESIS_NUCLEUS_DIR}/Robots/Unitree/G1/g1.usd",
            activate_contact_sensors=True,
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.75),
            joint_pos={
                # Legs
                "left_hip_pitch_joint": -0.312,
                "left_hip_roll_joint": 0.0,
                "left_hip_yaw_joint": 0.0,
                "left_knee_joint": 0.669,
                "left_ankle_pitch_joint": -0.363,
                "left_ankle_roll_joint": 0.0,

                "right_hip_pitch_joint": -0.312,
                "right_hip_roll_joint": 0.0,
                "right_hip_yaw_joint": 0.0,
                "right_knee_joint": 0.669,
                "right_ankle_pitch_joint": -0.363,
                "right_ankle_roll_joint": 0.0,

                # Torso
                "waist_yaw_joint": 0.0,
                "waist_roll_joint": 0.0,
                "waist_pitch_joint": 0.0,

                # Arms
                "left_shoulder_pitch_joint": 0.2,
                "left_shoulder_roll_joint": 0.2,
                "left_shoulder_yaw_joint": 0.0,
                "left_elbow_joint": 0.6,

                "right_shoulder_pitch_joint": 0.2,
                "right_shoulder_roll_joint": -0.2,
                "right_shoulder_yaw_joint": 0.0,
                "right_elbow_joint": 0.6,

                # Wrists
                "left_wrist_roll_joint": 0.0,
                "left_wrist_pitch_joint": 0.0,
                "left_wrist_yaw_joint": 0.0,

                "right_wrist_roll_joint": 0.0,
                "right_wrist_pitch_joint": 0.0,
                "right_wrist_yaw_joint": 0.0,
            },
            joint_vel={".*": 0.0},
        ),
        actuators={
            "legs": sim_utils.ImplicitActuatorCfg(
                joint_names_expr=[".*_hip_.*", ".*_knee", ".*_ankle_.*"],
                stiffness={
                    ".*_hip_pitch": actuator_cfg.hip_pitch_stiffness,
                    ".*_hip_roll": actuator_cfg.hip_roll_stiffness,
                    ".*_hip_yaw": actuator_cfg.hip_yaw_stiffness,
                    ".*_knee": actuator_cfg.knee_stiffness,
                    ".*_ankle_pitch": actuator_cfg.ankle_pitch_stiffness,
                    ".*_ankle_roll": actuator_cfg.ankle_roll_stiffness,
                },
                damping={
                    ".*_hip_pitch": actuator_cfg.hip_pitch_damping,
                    ".*_hip_roll": actuator_cfg.hip_roll_damping,
                    ".*_hip_yaw": actuator_cfg.hip_yaw_damping,
                    ".*_knee": actuator_cfg.knee_damping,
                    ".*_ankle_pitch": actuator_cfg.ankle_pitch_damping,
                    ".*_ankle_roll": actuator_cfg.ankle_roll_damping,
                },
                effort_limit=actuator_cfg.legs_effort_limit,
                velocity_limit=actuator_cfg.velocity_limit,
            ),
            "torso": sim_utils.ImplicitActuatorCfg(
                joint_names_expr=["waist_.*"],
                stiffness={
                    "waist_yaw": actuator_cfg.waist_stiffness[0],
                    "waist_roll": actuator_cfg.waist_stiffness[1],
                    "waist_pitch": actuator_cfg.waist_stiffness[2],
                },
                damping={
                    "waist_yaw": actuator_cfg.waist_damping[0],
                    "waist_roll": actuator_cfg.waist_damping[1],
                    "waist_pitch": actuator_cfg.waist_damping[2],
                },
                effort_limit=actuator_cfg.torso_effort_limit,
                velocity_limit=actuator_cfg.velocity_limit,
            ),
            "arms": sim_utils.ImplicitActuatorCfg(
                joint_names_expr=[".*_shoulder_.*", ".*_elbow"],
                stiffness={
                    ".*_shoulder_pitch": actuator_cfg.shoulder_pitch_stiffness,
                    ".*_shoulder_roll": actuator_cfg.shoulder_roll_stiffness,
                    ".*_shoulder_yaw": actuator_cfg.shoulder_yaw_stiffness,
                    ".*_elbow": actuator_cfg.elbow_stiffness,
                },
                damping={
                    ".*_shoulder_pitch": actuator_cfg.shoulder_pitch_damping,
                    ".*_shoulder_roll": actuator_cfg.shoulder_roll_damping,
                    ".*_shoulder_yaw": actuator_cfg.shoulder_yaw_damping,
                    ".*_elbow": actuator_cfg.elbow_damping,
                },
                effort_limit=actuator_cfg.arms_effort_limit,
                velocity_limit=actuator_cfg.velocity_limit,
            ),
            "wrists": sim_utils.ImplicitActuatorCfg(
                joint_names_expr=[".*_wrist_.*"],
                stiffness={
                    ".*_wrist_roll": actuator_cfg.wrist_roll_stiffness,
                    ".*_wrist_pitch": actuator_cfg.wrist_pitch_stiffness,
                    ".*_wrist_yaw": actuator_cfg.wrist_yaw_stiffness,
                },
                damping={
                    ".*_wrist_roll": actuator_cfg.wrist_roll_damping,
                    ".*_wrist_pitch": actuator_cfg.wrist_pitch_damping,
                    ".*_wrist_yaw": actuator_cfg.wrist_yaw_damping,
                },
                effort_limit=actuator_cfg.wrists_effort_limit,
                velocity_limit=actuator_cfg.velocity_limit,
            ),
        },
    )


# G1 29 DOF joint names in BeyondMimic order
G1_29DOF_BEYONDMIMIC_NAMES = [
    # Legs (interleaved left-right-waist pattern)
    "left_hip_pitch_joint",
    "right_hip_pitch_joint",
    "waist_yaw_joint",
    "left_hip_roll_joint",
    "right_hip_roll_joint",
    "waist_roll_joint",
    "left_hip_yaw_joint",
    "right_hip_yaw_joint",
    "waist_pitch_joint",
    "left_knee_joint",
    "right_knee_joint",
    # Arms
    "left_shoulder_pitch_joint",
    "right_shoulder_pitch_joint",
    "left_ankle_pitch_joint",
    "right_ankle_pitch_joint",
    "left_shoulder_roll_joint",
    "right_shoulder_roll_joint",
    "left_ankle_roll_joint",
    "right_ankle_roll_joint",
    "left_shoulder_yaw_joint",
    "right_shoulder_yaw_joint",
    # Wrists
    "left_elbow_joint",
    "right_elbow_joint",
    "left_wrist_roll_joint",
    "right_wrist_roll_joint",
    "left_wrist_pitch_joint",
    "right_wrist_pitch_joint",
    "left_wrist_yaw_joint",
    "right_wrist_yaw_joint",
]

# Default positions from RoboJuDo BeyondMimic config
G1_BEYONDMIMIC_DEFAULT_POS = [
    -0.312, -0.312, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.669, 0.669,
    0.200, 0.200, -0.363, -0.363, 0.200, -0.200, 0.000, 0.000, 0.000, 0.000,
    0.600, 0.600, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
]

# Per-joint action scales from RoboJuDo
G1_BEYONDMIMIC_ACTION_SCALES = [
    0.548, 0.548, 0.548, 0.351, 0.351, 0.439, 0.548, 0.548, 0.439, 0.351, 0.351,
    0.439, 0.439, 0.439, 0.439, 0.439, 0.439, 0.439, 0.439, 0.439, 0.439,
    0.439, 0.439, 0.439, 0.439, 0.075, 0.075, 0.075, 0.075,
]
