"""AMO-specific G1 robot configuration with 23 DOFs (without wrists) and AMO PD parameters.

Uses the original g1.xml from AMO to ensure exact joint ordering and parameters.

This is a Policy Hub copy of the AMO robot configuration, eliminating the need
to import from the amo package.
"""

from __future__ import annotations
from pathlib import Path

from genesislab.components.actuators.actuator_pd_cfg import ImplicitActuatorCfg
from genesislab.engine.assets.robot import InitialPoseCfg, RobotCfg

# Use AMO's original g1.xml
# Path from genPiHub/envs/amo/robot_cfg.py -> data/amo_assets
AMO_ASSET_DIR = Path(__file__).resolve().parents[3] / "data" / "amo_assets"

# AMO PD parameters from play_amo.py
# G1 23DOF configuration
AMO_STIFFNESS = {
    # Legs (0-11)
    "left_hip_pitch_joint": 150.0,
    "left_hip_roll_joint": 150.0,
    "left_hip_yaw_joint": 150.0,
    "left_knee_joint": 300.0,
    "left_ankle_pitch_joint": 80.0,
    "left_ankle_roll_joint": 20.0,
    "right_hip_pitch_joint": 150.0,
    "right_hip_roll_joint": 150.0,
    "right_hip_yaw_joint": 150.0,
    "right_knee_joint": 300.0,
    "right_ankle_pitch_joint": 80.0,
    "right_ankle_roll_joint": 20.0,
    # Waist (12-14)
    "waist_yaw_joint": 400.0,
    "waist_roll_joint": 400.0,
    "waist_pitch_joint": 400.0,
    # Arms (15-22) - no wrists!
    ".*_shoulder_pitch_joint": 80.0,
    ".*_shoulder_roll_joint": 80.0,
    ".*_shoulder_yaw_joint": 40.0,
    ".*_elbow_joint": 60.0,
}

AMO_DAMPING = {
    # Legs (0-11)
    "left_hip_pitch_joint": 2.0,
    "left_hip_roll_joint": 2.0,
    "left_hip_yaw_joint": 2.0,
    "left_knee_joint": 4.0,
    "left_ankle_pitch_joint": 2.0,
    "left_ankle_roll_joint": 1.0,
    "right_hip_pitch_joint": 2.0,
    "right_hip_roll_joint": 2.0,
    "right_hip_yaw_joint": 2.0,
    "right_knee_joint": 4.0,
    "right_ankle_pitch_joint": 2.0,
    "right_ankle_roll_joint": 1.0,
    # Waist (12-14)
    "waist_yaw_joint": 15.0,
    "waist_roll_joint": 15.0,
    "waist_pitch_joint": 15.0,
    # Arms (15-22) - no wrists!
    ".*_shoulder_pitch_joint": 2.0,
    ".*_shoulder_roll_joint": 2.0,
    ".*_shoulder_yaw_joint": 1.0,
    ".*_elbow_joint": 1.0,
}

AMO_EFFORT_LIMITS = {
    # Legs
    "left_hip_pitch_joint": 88.0,
    "left_hip_roll_joint": 139.0,
    "left_hip_yaw_joint": 88.0,
    "left_knee_joint": 139.0,
    "left_ankle_pitch_joint": 50.0,
    "left_ankle_roll_joint": 50.0,
    "right_hip_pitch_joint": 88.0,
    "right_hip_roll_joint": 139.0,
    "right_hip_yaw_joint": 88.0,
    "right_knee_joint": 139.0,
    "right_ankle_pitch_joint": 50.0,
    "right_ankle_roll_joint": 50.0,
    # Waist
    "waist_yaw_joint": 88.0,
    "waist_roll_joint": 50.0,
    "waist_pitch_joint": 50.0,
    # Arms (no wrists)
    ".*_shoulder_pitch_joint": 25.0,
    ".*_shoulder_roll_joint": 25.0,
    ".*_shoulder_yaw_joint": 25.0,
    ".*_elbow_joint": 25.0,
}

# Default joint positions from AMO play_amo.py
AMO_DEFAULT_JOINT_POS = {
    # Legs
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
    # Waist
    "waist_yaw_joint": 0.0,
    "waist_roll_joint": 0.0,
    "waist_pitch_joint": 0.0,
    # Arms
    "left_shoulder_pitch_joint": 0.5,
    "left_shoulder_roll_joint": 0.0,
    "left_shoulder_yaw_joint": 0.2,
    "left_elbow_joint": 0.3,
    "right_shoulder_pitch_joint": 0.5,
    "right_shoulder_roll_joint": 0.0,
    "right_shoulder_yaw_joint": -0.2,
    "right_elbow_joint": 0.3,
}

# AMO G1 configuration - uses modified g1.xml (ground removed, pelvis at origin)
# - 23 DOF (no wrists)
# - Ground removed (use Genesis terrain instead)
# - Pelvis at origin in MJCF, spawn height controlled by initial_pose
G1_AMO_CFG = RobotCfg(
    morph_type="MJCF",
    morph_path=str(AMO_ASSET_DIR / "g1.xml"),
    initial_pose=InitialPoseCfg(
        pos=[0.0, 0.0, 0.793],  # Spawn at AMO training height
        quat=[0.0, 0.0, 0.0, 1.0],
    ),
    fixed_base=False,
    control_dofs=None,
    default_joint_pos=AMO_DEFAULT_JOINT_POS,
    actuators={
        "amo": ImplicitActuatorCfg(
            # CRITICAL: Genesis reorders joints when loading MJCF!
            # We MUST explicitly specify the order to match AMOPolicy.DOF_NAMES
            # Use exact joint names (not patterns) to force the order
            joint_names_expr=[
                # Legs (left first, then right) - AMO indices 0-11
                "left_hip_pitch_joint",      # AMO 0
                "left_hip_roll_joint",       # AMO 1
                "left_hip_yaw_joint",        # AMO 2
                "left_knee_joint",           # AMO 3
                "left_ankle_pitch_joint",    # AMO 4
                "left_ankle_roll_joint",     # AMO 5
                "right_hip_pitch_joint",     # AMO 6
                "right_hip_roll_joint",      # AMO 7
                "right_hip_yaw_joint",       # AMO 8
                "right_knee_joint",          # AMO 9
                "right_ankle_pitch_joint",   # AMO 10
                "right_ankle_roll_joint",    # AMO 11
                # Waist - AMO indices 12-14
                "waist_yaw_joint",           # AMO 12
                "waist_roll_joint",          # AMO 13
                "waist_pitch_joint",         # AMO 14
                # Arms - AMO indices 15-22
                "left_shoulder_pitch_joint", # AMO 15
                "left_shoulder_roll_joint",  # AMO 16
                "left_shoulder_yaw_joint",   # AMO 17
                "left_elbow_joint",          # AMO 18
                "right_shoulder_pitch_joint",# AMO 19
                "right_shoulder_roll_joint", # AMO 20
                "right_shoulder_yaw_joint",  # AMO 21
                "right_elbow_joint",         # AMO 22
            ],
            effort_limit_sim=AMO_EFFORT_LIMITS,
            stiffness=AMO_STIFFNESS,
            damping=AMO_DAMPING,
            velocity_limit_sim={
                ".*_hip_.*": 32.0,
                ".*_knee_joint": 20.0,
                ".*_ankle_.*": 37.0,
                "waist_.*": 32.0,
                ".*_shoulder_.*": 37.0,
                ".*_elbow_joint": 37.0,
            },
        ),
    },
)
