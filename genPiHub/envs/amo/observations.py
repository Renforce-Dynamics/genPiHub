"""AMO-specific observation helper terms for Genesis env configs.

This is a Policy Hub copy of the AMO observations, eliminating the need
to import from the amo package.
"""

from __future__ import annotations

import torch

from genesislab.managers import SceneEntityCfg


def _quat_wxyz_to_rpy(quat: torch.Tensor) -> torch.Tensor:
    """Convert quaternion [w,x,y,z] to roll/pitch/yaw."""
    w, x, y, z = quat[:, 0], quat[:, 1], quat[:, 2], quat[:, 3]
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = torch.atan2(sinr_cosp, cosr_cosp)

    sinp = 2 * (w * y - z * x)
    pitch = torch.asin(torch.clamp(sinp, -1.0, 1.0))

    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = torch.atan2(siny_cosp, cosy_cosp)
    return torch.stack([roll, pitch, yaw], dim=-1)


def amo_ang_vel_scaled(env, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"), scale: float = 0.25):
    """AMO angular velocity observation (scaled)."""
    return env.entities[asset_cfg.entity_name].data.root_ang_vel_b * scale


def amo_rpy_roll_pitch(env, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot")):
    """AMO roll/pitch observation."""
    quat = env.entities[asset_cfg.entity_name].data.root_quat_w
    rpy = _quat_wxyz_to_rpy(quat)
    return rpy[:, :2]


def amo_dyaw_sin_cos(
    env,
    command_name: str = "base_velocity",
    asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"),
):
    """AMO delta-yaw sin/cos observation."""
    quat = env.entities[asset_cfg.entity_name].data.root_quat_w
    yaw = _quat_wxyz_to_rpy(quat)[:, 2]
    cmd = env.command_manager.get_command(command_name)
    target_yaw_rate = cmd[:, 2]
    dyaw = yaw - target_yaw_rate
    return torch.stack([torch.sin(dyaw), torch.cos(dyaw)], dim=-1)


def amo_joint_vel_scaled(env, asset_cfg: SceneEntityCfg = SceneEntityCfg("robot"), scale: float = 0.05):
    """AMO joint velocity observation (scaled)."""
    return env.entities[asset_cfg.entity_name].data.joint_vel * scale


def zeros_like_command(env, command_name: str = "base_velocity", dim: int = 8):
    """Zeros placeholder matching command shape."""
    cmd = env.command_manager.get_command(command_name)
    return torch.zeros((cmd.shape[0], dim), dtype=cmd.dtype, device=cmd.device)
