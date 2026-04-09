"""CLOT observation functions.

CLOT uses AMP-style observations for motion tracking, including:
- Root orientation and angular velocity
- Joint positions and velocities
- Reference motion state
- Contact information
"""

import torch
from typing import TYPE_CHECKING

from genesislab.utils.torch_utils import quat_rotate_inverse, get_euler_xyz

if TYPE_CHECKING:
    from genesislab.envs import ManagerBasedRlEnv


def base_ang_vel_scaled(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Angular velocity in base frame, scaled for CLOT.

    Scale factor: 0.25 (less aggressive than AMO)

    Args:
        env: Environment instance

    Returns:
        Scaled angular velocity (num_envs, 3)
    """
    ang_vel_w = env.scene["robot"].root_lin_vel_w[:, 3:6]
    base_quat = env.scene["robot"].root_quat_w
    ang_vel_b = quat_rotate_inverse(base_quat, ang_vel_w)
    return ang_vel_b * 0.25


def projected_gravity(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Gravity vector projected to base frame.

    Args:
        env: Environment instance

    Returns:
        Projected gravity (num_envs, 3)
    """
    gravity_w = torch.tensor([0.0, 0.0, -1.0], device=env.device).repeat(env.num_envs, 1)
    base_quat = env.scene["robot"].root_quat_w
    return quat_rotate_inverse(base_quat, gravity_w)


def joint_pos_rel(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Joint positions relative to default.

    Args:
        env: Environment instance

    Returns:
        Relative joint positions (num_envs, num_dofs)
    """
    return env.scene["robot"].data.joint_pos - env.scene["robot"].data.default_joint_pos


def joint_vel_scaled(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Joint velocities scaled for CLOT.

    Scale factor: 0.05 (conservative)

    Args:
        env: Environment instance

    Returns:
        Scaled joint velocities (num_envs, num_dofs)
    """
    return env.scene["robot"].data.joint_vel * 0.05


def base_lin_vel(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Linear velocity in base frame.

    Args:
        env: Environment instance

    Returns:
        Linear velocity (num_envs, 3)
    """
    lin_vel_w = env.scene["robot"].root_lin_vel_w[:, :3]
    base_quat = env.scene["robot"].root_quat_w
    return quat_rotate_inverse(base_quat, lin_vel_w)


def base_height(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Base height above ground.

    Args:
        env: Environment instance

    Returns:
        Height (num_envs, 1)
    """
    return env.scene["robot"].root_pos_w[:, 2:3]


def base_rpy(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Base roll, pitch, yaw angles.

    Args:
        env: Environment instance

    Returns:
        RPY angles (num_envs, 3)
    """
    base_quat = env.scene["robot"].root_quat_w
    return get_euler_xyz(base_quat)


def last_action(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Last action taken.

    Args:
        env: Environment instance

    Returns:
        Last action (num_envs, num_actions)
    """
    return env.action_manager.prev_action


# AMP-specific observations for discriminator
def amp_observation(env: "ManagerBasedRlEnv") -> torch.Tensor:
    """Full AMP observation for discriminator.

    Includes:
    - Root height, rotation, linear velocity, angular velocity
    - Joint positions and velocities
    - Contact states

    Args:
        env: Environment instance

    Returns:
        AMP observation vector (num_envs, amp_obs_dim)
    """
    robot = env.scene["robot"]

    # Root state
    root_h = robot.root_pos_w[:, 2:3]  # (num_envs, 1)
    root_rot = robot.root_quat_w  # (num_envs, 4)
    root_lin_vel = base_lin_vel(env)  # (num_envs, 3)
    root_ang_vel = base_ang_vel_scaled(env) / 0.25  # Unscaled for AMP

    # Joint state
    joint_pos = robot.data.joint_pos  # (num_envs, num_dofs)
    joint_vel = robot.data.joint_vel  # (num_envs, num_dofs)

    # Concatenate all components
    amp_obs = torch.cat(
        [
            root_h,
            root_rot,
            root_lin_vel,
            root_ang_vel,
            joint_pos,
            joint_vel,
        ],
        dim=-1,
    )

    return amp_obs
