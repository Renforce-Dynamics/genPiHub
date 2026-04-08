"""AMO-specific action configuration with correct offset ordering.

This is a Policy Hub copy of the AMO actions, eliminating the need
to import from the amo package.
"""

from __future__ import annotations

from genesislab.envs.mdp import actions as mdp
from genesislab.utils.configclass import configclass

# AMO default joint positions in AMO order (from amo_policy.py)
AMO_DEFAULT_JOINT_POS_DICT = {
    # Legs (0-11)
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
    # Waist (12-14)
    "waist_yaw_joint": 0.0,
    "waist_roll_joint": 0.0,
    "waist_pitch_joint": 0.0,
    # Arms (15-22)
    "left_shoulder_pitch_joint": 0.5,
    "left_shoulder_roll_joint": 0.0,
    "left_shoulder_yaw_joint": 0.2,
    "left_elbow_joint": 0.3,
    "right_shoulder_pitch_joint": 0.5,
    "right_shoulder_roll_joint": 0.0,
    "right_shoulder_yaw_joint": -0.2,
    "right_elbow_joint": 0.3,
}


@configclass
class AmoActionsCfg:
    """AMO-specific actions with correct default joint position offset.

    Genesis' default_joint_pos is in entity order, but actuator joints are in AMO order.
    We explicitly specify the offset in AMO order to avoid the ordering mismatch.
    """

    joint_pos: mdp.GenesisOriginalActionCfg = mdp.GenesisOriginalActionCfg(
        entity_name="robot",
        scale=0.25,  # AMO action_scale
        use_default_offset=False,  # Don't use entity's default (wrong order!)
        offset=AMO_DEFAULT_JOINT_POS_DICT,  # Explicitly specify in AMO order via dict
    )
