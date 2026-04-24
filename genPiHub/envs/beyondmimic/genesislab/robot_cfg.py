"""G1 robot configuration for BeyondMimic (29 DOF with hands).

BeyondMimic uses the full 29 DOF G1 configuration including wrist joints.
Joint ordering is specific to BeyondMimic training.

This module provides only the configuration constants needed for BeyondMimic policy.
Full robot configuration should be handled by the environment builder.
"""

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

# PD controller gains (from RoboJuDo BeyondMimic configuration)
G1_BEYONDMIMIC_STIFFNESS = {
    # Legs
    ".*_hip_pitch_joint": 40.179,
    ".*_hip_roll_joint": 99.098,
    ".*_hip_yaw_joint": 40.179,
    ".*_knee_joint": 99.098,
    ".*_ankle_pitch_joint": 28.501,
    ".*_ankle_roll_joint": 28.501,
    # Torso
    "waist_yaw_joint": 40.179,
    "waist_roll_joint": 99.098,
    "waist_pitch_joint": 28.501,
    # Arms
    ".*_shoulder_pitch_joint": 14.251,
    ".*_shoulder_roll_joint": 14.251,
    ".*_shoulder_yaw_joint": 14.251,
    ".*_elbow_joint": 14.251,
    # Wrists
    ".*_wrist_roll_joint": 14.251,
    ".*_wrist_pitch_joint": 16.778,
    ".*_wrist_yaw_joint": 16.778,
}

G1_BEYONDMIMIC_DAMPING = {
    # Legs
    ".*_hip_pitch_joint": 2.558,
    ".*_hip_roll_joint": 6.309,
    ".*_hip_yaw_joint": 2.558,
    ".*_knee_joint": 6.309,
    ".*_ankle_pitch_joint": 1.814,
    ".*_ankle_roll_joint": 1.814,
    # Torso
    "waist_yaw_joint": 2.558,
    "waist_roll_joint": 6.309,
    "waist_pitch_joint": 1.814,
    # Arms
    ".*_shoulder_pitch_joint": 0.907,
    ".*_shoulder_roll_joint": 0.907,
    ".*_shoulder_yaw_joint": 0.907,
    ".*_elbow_joint": 0.907,
    # Wrists
    ".*_wrist_roll_joint": 0.907,
    ".*_wrist_pitch_joint": 1.068,
    ".*_wrist_yaw_joint": 1.068,
}

# Effort limits
G1_BEYONDMIMIC_EFFORT_LIMITS = {
    ".*_hip.*": 300.0,
    ".*_knee": 300.0,
    ".*_ankle.*": 300.0,
    "waist_.*": 300.0,
    ".*_shoulder.*": 100.0,
    ".*_elbow": 100.0,
    ".*_wrist.*": 50.0,
}

# Velocity limit (all joints)
G1_BEYONDMIMIC_VELOCITY_LIMIT = 100.0

# Initial base position
G1_BEYONDMIMIC_INITIAL_BASE_POS = [0.0, 0.0, 0.75]

# Initial base orientation (quaternion: w, x, y, z)
G1_BEYONDMIMIC_INITIAL_BASE_QUAT = [1.0, 0.0, 0.0, 0.0]
