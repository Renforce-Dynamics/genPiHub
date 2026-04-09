"""CLOT action configuration.

Actions for CLOT are PD target positions in joint space,
similar to AMO but with different scaling.
"""

from genesislab.managers import ActionTermCfg, ActionsCfg
from genesislab.utils.configclass import configclass
import genesis_tasks.locomotion.hvelocity.mdp as base_mdp


@configclass
class CLOTActionsCfg(ActionsCfg):
    """CLOT action configuration.

    Uses joint position control with PD controller.
    Action scale is typically 0.25 for CLOT.
    """

    joint_pos: ActionTermCfg = ActionTermCfg(
        class_type=base_mdp.JointPositionActionCfg,
        asset_name="robot",
        joint_names=[".*"],  # All 23 joints
        scale=0.25,  # Action scaling factor
        use_default_offset=True,  # Use default joint positions as offset
    )
