"""AMO (Adaptive Motion Optimization) policy wrapper.

This wraps the existing AMO implementation from the `amo` package into the Policy Hub interface.
"""

import numpy as np
import logging
from typing import Dict, Any, Tuple

from genPiHub.policies.base_policy import Policy
from genPiHub.configs.policy_configs import AMOPolicyConfig

logger = logging.getLogger(__name__)


class AMOPolicy(Policy):
    """AMO policy wrapper for Policy Hub.

    This class adapts the existing AMO policy from `amo` package to the Policy Hub interface.

    Example:
        >>> from genPiHub import load_policy
        >>> policy = load_policy(
        ...     name="AMOPolicy",
        ...     model_dir=".reference/AMO",
        ...     device="cuda"
        ... )
        >>> policy.reset()
        >>> obs, extras = policy.get_observation(env_data, {})
        >>> action = policy.get_action(obs)
    """

    def __init__(self, cfg: AMOPolicyConfig, device: str = "cpu"):
        """Initialize AMO policy.

        Args:
            cfg: AMO policy configuration
            device: Device for inference
        """
        super().__init__(cfg, device)

        self.cfg_amo: AMOPolicyConfig = cfg

        # Import local AMO implementation (100% self-contained!)
        from genPiHub.policies.amo_policy_impl import AMOPolicyImpl
        self._amo_impl = AMOPolicyImpl

        # Create AMO policy instance
        logger.info(f"Loading AMO policy from {cfg.policy_file.parent if cfg.policy_file else 'default'}")
        self.amo_policy = self._amo_impl(
            model_dir=str(cfg.policy_file.parent) if cfg.policy_file else ".reference/AMO",
            device=device,
            policy_filename=cfg.policy_file.name if cfg.policy_file else "amo_jit.pt",
            adapter_filename=cfg.adapter_file.name if cfg.adapter_file else "adapter_jit.pt",
            norm_stats_filename=cfg.norm_stats_file.name if cfg.norm_stats_file else "adapter_norm_stats.pt",
            action_scale=cfg.action_scale,
            scales_ang_vel=cfg.scales_ang_vel,
            scales_dof_vel=cfg.scales_dof_vel,
            gait_freq=cfg.gait_freq,
        )

        # Override model reference
        self.model = self.amo_policy.policy_jit

        logger.info(f"AMO policy initialized with {self.num_actions} actions")

    def reset(self):
        """Reset AMO policy state."""
        self.amo_policy.reset()
        self.last_action = np.zeros(self.num_actions)

    def get_observation(self, env_data: Dict[str, Any], ctrl_data: Dict[str, Any]) -> Tuple[np.ndarray, Dict]:
        """Get AMO observation from environment data.

        AMO doesn't use a separate observation function - it takes raw state in act().
        This method returns the raw state for compatibility.

        Args:
            env_data: Environment state
            ctrl_data: Controller data (commands)

        Returns:
            Tuple of (observation, extras)
            - observation: Raw state dict (for AMO)
            - extras: Empty dict
        """
        # AMO takes state directly in act(), so we just pass through
        # The actual observation construction happens in act()
        return env_data, {}

    def get_action(self, obs: Dict[str, Any] | np.ndarray) -> np.ndarray:
        """Get action from AMO policy.

        Args:
            obs: Either dict with env_data or raw numpy observation

        Returns:
            PD target positions (joint space)
        """
        # If obs is dict (from get_observation), extract components
        if isinstance(obs, dict):
            dof_pos = obs.get("dof_pos")
            dof_vel = obs.get("dof_vel")
            quat = obs.get("base_quat")
            ang_vel = obs.get("base_ang_vel")
            commands = obs.get("commands", np.zeros(8, dtype=np.float32))

            # Call AMO policy
            pd_target = self.amo_policy.act(
                dof_pos=dof_pos,
                dof_vel=dof_vel,
                quat=quat,
                ang_vel=ang_vel,
                commands=commands,
                dt=self.dt,
            )

            # Convert to action (AMO returns PD targets directly)
            action = (pd_target - self.amo_policy.DEFAULT_DOF_POS) / self.amo_policy.action_scale
            return action

        # If obs is numpy array, use parent method
        return super().get_action(obs)

    def post_step_callback(self, commands: list[str] | None = None):
        """Post-step callback (AMO doesn't need this)."""
        pass

    def get_init_dof_pos(self) -> np.ndarray:
        """Get AMO default DOF positions."""
        return self.amo_policy.DEFAULT_DOF_POS.copy()


# Convenient factory function
def create_amo_policy(
    model_dir: str = ".reference/AMO",
    device: str = "cuda",
    **kwargs
) -> AMOPolicy:
    """Create AMO policy with default configuration.

    Args:
        model_dir: Directory containing AMO models
        device: Device for inference
        **kwargs: Additional config overrides

    Returns:
        AMOPolicy instance
    """
    from pathlib import Path
    from genPiHub.tools import DOFConfig

    # AMO DOF configuration (23 DOF G1)
    amo_dof_names = [
        "left_hip_pitch", "left_hip_roll", "left_hip_yaw",
        "left_knee", "left_ankle_pitch", "left_ankle_roll",
        "right_hip_pitch", "right_hip_roll", "right_hip_yaw",
        "right_knee", "right_ankle_pitch", "right_ankle_roll",
        "waist_yaw", "waist_roll", "waist_pitch",
        "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
        "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
    ]

    amo_default_pos = [
        -0.1, 0., 0., 0.3, -0.2, 0.,  # left leg
        -0.1, 0., 0., 0.3, -0.2, 0.,  # right leg
        0., 0., 0.,                    # waist
        0.5, 0., 0.2, 0.3,            # left arm
        0.5, 0., -0.2, 0.3,           # right arm
    ]

    dof_cfg = DOFConfig(
        joint_names=amo_dof_names,
        num_dofs=23,
        default_pos=amo_default_pos,
    )

    cfg = AMOPolicyConfig(
        policy_file=Path(model_dir) / "amo_jit.pt",
        adapter_file=Path(model_dir) / "adapter_jit.pt",
        norm_stats_file=Path(model_dir) / "adapter_norm_stats.pt",
        device=device,
        obs_dof=dof_cfg,
        action_dof=dof_cfg,
        action_scale=0.25,
        **kwargs
    )

    return AMOPolicy(cfg, device)
