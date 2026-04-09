"""BeyondMimic observation functions.

BeyondMimic observations depend on whether state estimator is used:
- With state estimator: includes anchor position and linear velocity
- Without state estimator (wose): only orientation, angular velocity, joint state
"""

import torch
from typing import TYPE_CHECKING

from genesislab.utils.torch_utils import quat_rotate_inverse

if TYPE_CHECKING:
    from genesislab.envs import ManagerBasedRlEnv


def base_lin_vel_b(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Linear velocity in base frame.

    Args:
        env: Environment instance

    Returns:
        Linear velocity (num_envs, 3)
    """
    lin_vel_w = env.scene["robot"].root_lin_vel_w[:, :3]
    base_quat = env.scene["robot"].root_quat_w
    return quat_rotate_inverse(base_quat, lin_vel_w)


def base_ang_vel_b(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Angular velocity in base frame.

    Args:
        env: Environment instance

    Returns:
        Angular velocity (num_envs, 3)
    """
    ang_vel_w = env.scene["robot"].root_lin_vel_w[:, 3:6]
    base_quat = env.scene["robot"].root_quat_w
    return quat_rotate_inverse(base_quat, ang_vel_w)


def joint_pos_rel(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Joint positions relative to default.

    Args:
        env: Environment instance

    Returns:
        Relative joint positions (num_envs, num_dofs)
    """
    return env.scene["robot"].data.joint_pos - env.scene["robot"].data.default_joint_pos


def joint_vel(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Joint velocities.

    Args:
        env: Environment instance

    Returns:
        Joint velocities (num_envs, num_dofs)
    """
    return env.scene["robot"].data.joint_vel


def last_action(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Last action taken.

    Args:
        env: Environment instance

    Returns:
        Last action (num_envs, num_actions)
    """
    return env.action_manager.prev_action
