"""BeyondMimic action configuration.

Actions are PD target positions with per-joint scaling.
BeyondMimic uses different action scales for each joint.
"""

from genesislab.managers import ActionTermCfg, ActionsCfg
from genesislab.utils.configclass import configclass
import genesis_tasks.locomotion.hvelocity.mdp as base_mdp


@configclass
class BeyondMimicActionsCfg(ActionsCfg):
    """BeyondMimic action configuration.

    Uses joint position control with per-joint action scales.
    Scales are applied in the policy, not here.
    """

    joint_pos: ActionTermCfg = ActionTermCfg(
        class_type=base_mdp.JointPositionActionCfg,
        asset_name="robot",
        joint_names=[".*"],  # All 29 joints
        scale=1.0,  # Scaling done in policy with per-joint scales
        use_default_offset=True,
    )
