"""BeyondMimic action configuration.

Actions are PD target positions with per-joint scaling.
BeyondMimic uses different action scales for each joint.
"""

from __future__ import annotations

from genesislab.envs.mdp import actions as mdp
from genesislab.utils.configclass import configclass

# BeyondMimic default joint positions in BeyondMimic order (29 DOF)
from .robot_cfg import G1_29DOF_BEYONDMIMIC_NAMES, G1_BEYONDMIMIC_DEFAULT_POS

BEYONDMIMIC_DEFAULT_JOINT_POS_DICT = dict(zip(
    G1_29DOF_BEYONDMIMIC_NAMES,
    G1_BEYONDMIMIC_DEFAULT_POS
))


@configclass
class BeyondMimicActionsCfg:
    """BeyondMimic-specific actions with per-joint scaling.

    BeyondMimic applies per-joint action scales in the policy itself,
    so we use scale=1.0 here and let the policy handle scaling.
    """

    joint_pos: mdp.GenesisOriginalActionCfg = mdp.GenesisOriginalActionCfg(
        entity_name="robot",
        scale=1.0,  # No additional scaling (policy already applies action_scales)
        use_default_offset=True,  # Add default positions as offset: target = default_pos + action
        offset=0.0,  # Use entity's default_joint_pos from MJCF
    )
