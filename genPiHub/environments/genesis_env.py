"""Genesis environment implementation for Policy Hub.

Wraps genesislab's ManagerBasedRlEnv to provide unified Policy Hub interface.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import numpy as np
import torch
import logging

import genesis as gs
from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnv

from genPiHub.environments.base_env import Environment
from genPiHub.configs.env_configs import GenesisEnvConfig
from genPiHub.tools import DOFConfig

logger = logging.getLogger(__name__)


class GenesisEnv(Environment):
    """Genesis physics environment wrapper.

    Wraps genesislab.envs.ManagerBasedRlEnv and provides:
    - Unified state access (dof_pos, dof_vel, base_quat, etc.)
    - PD control interface
    - Reset and step functionality

    Supports both single and vectorized environments.
    """

    def __init__(
        self,
        cfg: GenesisEnvConfig,
        device: str = "cuda",
        env_cfg: Any = None,
    ):
        """Initialize Genesis environment.

        Args:
            cfg: GenesisEnv configuration
            device: Device for computation
            env_cfg: Optional genesislab environment config (e.g., AmoGenesisEnvCfg)
        """
        super().__init__(cfg, device)

        # Initialize Genesis backend
        backend = gs.gpu if device == "cuda" else gs.cpu
        gs.init(backend=backend, logging_level="WARNING")

        # Create environment
        if env_cfg is None:
            raise ValueError("env_cfg must be provided to create Genesis environment")

        self.env = ManagerBasedRlEnv(cfg=env_cfg, device=device)
        self.num_envs = self.env.num_envs
        self.env_cfg = env_cfg

        # Get robot reference
        self.robot = self.env.entities["robot"]
        self.robot_joint_names = list(self.robot.joint_names)

        # Build joint index mapping (Policy Hub DOF order -> Robot order)
        self.policy_to_robot_idx = self._build_joint_mapping()

        # Initialize state
        self._update_state()

        logger.info(f"✅ GenesisEnv created: {self.num_envs} envs, device={device}")

    def _build_joint_mapping(self) -> np.ndarray:
        """Build mapping from policy DOF order to robot joint order.

        Returns:
            Index array for mapping policy_dof -> robot_joint
        """
        policy_to_robot = np.zeros(self.num_dofs, dtype=np.int32)

        for i, joint_name in enumerate(self.joint_names):
            if joint_name in self.robot_joint_names:
                policy_to_robot[i] = self.robot_joint_names.index(joint_name)
            else:
                raise ValueError(
                    f"Joint '{joint_name}' from DOF config not found in robot. "
                    f"Robot joints: {self.robot_joint_names}"
                )

        return policy_to_robot

    def _update_state(self, env_idx: int = 0):
        """Update internal state from Genesis backend.

        Args:
            env_idx: Environment index to read from (for vectorized envs)
        """
        # Read robot state (always from first env for now)
        joint_pos_robot = self.robot.data.joint_pos[env_idx].detach().cpu().numpy()
        joint_vel_robot = self.robot.data.joint_vel[env_idx].detach().cpu().numpy()

        # Map to policy DOF order
        self._dof_pos = joint_pos_robot[self.policy_to_robot_idx].astype(np.float32)
        self._dof_vel = joint_vel_robot[self.policy_to_robot_idx].astype(np.float32)

        # Base state
        # Note: Genesis stores quaternion as [w,x,y,z], keep it in this format
        # Policy Hub base class expects [x,y,z,w], but AMO policy expects [w,x,y,z]
        # For AMO compatibility, we store [w,x,y,z]
        quat_wxyz = self.robot.data.root_quat_w[env_idx].detach().cpu().numpy()
        self._base_quat = quat_wxyz.astype(np.float32)

        self._base_ang_vel = self.robot.data.root_ang_vel_b[env_idx].detach().cpu().numpy().astype(np.float32)
        self._base_pos = self.robot.data.root_pos_w[env_idx].detach().cpu().numpy().astype(np.float32)
        self._base_lin_vel = self.robot.data.root_lin_vel_w[env_idx].detach().cpu().numpy().astype(np.float32)

    def self_check(self):
        """Perform self-check."""
        assert self.env is not None, "Environment not initialized"
        assert self.robot is not None, "Robot not found in environment"
        assert len(self.policy_to_robot_idx) == self.num_dofs, "Joint mapping size mismatch"
        logger.info("✅ GenesisEnv self-check passed")

    def reset(self, env_ids: Optional[torch.Tensor] = None):
        """Reset environment.

        Args:
            env_ids: Optional tensor of environment indices to reset. If None, resets all.
        """
        self.env.reset(env_ids=env_ids)
        self._update_state()

    def update(self):
        """Update state from backend."""
        self._update_state()

    def step(self, pd_target: np.ndarray) -> Dict[str, Any]:
        """Execute one environment step.

        Args:
            pd_target: PD control targets in policy DOF order (num_dofs,)

        Returns:
            Dictionary with step results:
            - obs: Observation
            - reward: Reward
            - terminated: Termination flag
            - truncated: Truncation flag
            - info: Additional info
        """
        assert len(pd_target) == self.num_dofs, \
            f"pd_target length ({len(pd_target)}) must match num_dofs ({self.num_dofs})"

        # Convert to torch tensor and expand for all envs
        actions = torch.zeros(
            (self.num_envs, self.env.action_manager.total_action_dim),
            dtype=torch.float32,
            device=self.env.device
        )

        # Map policy DOF order to environment action order
        usable = min(self.env.action_manager.total_action_dim, len(pd_target))
        actions[:, :usable] = torch.from_numpy(pd_target[:usable]).to(self.env.device)

        # Step environment
        obs, reward, terminated, truncated, info = self.env.step(actions)

        # Handle resets
        done = terminated | truncated
        if done.any():
            reset_ids = done.nonzero(as_tuple=False).squeeze(-1)
            self.env.reset(env_ids=reset_ids)

        # Update state
        self._update_state()

        return {
            "obs": obs,
            "reward": reward,
            "terminated": terminated,
            "truncated": truncated,
            "info": info,
        }

    def shutdown(self):
        """Shutdown environment and release resources."""
        if hasattr(self, 'env') and self.env is not None:
            del self.env
        logger.info("✅ GenesisEnv shutdown")

    def set_gains(self, stiffness: np.ndarray, damping: np.ndarray):
        """Set PD control gains.

        Note: Genesis sets gains at initialization via robot config.
        This method is provided for interface compatibility but may not
        have runtime effect depending on the actuator configuration.

        Args:
            stiffness: Proportional gains (Kp)
            damping: Derivative gains (Kd)
        """
        self.stiffness = stiffness
        self.damping = damping
        logger.warning(
            "GenesisEnv.set_gains() called but Genesis sets gains at init. "
            "Gains stored but may not affect simulation."
        )

    def get_data(self, env_idx: int = 0) -> Dict[str, Any]:
        """Get current environment state.

        Args:
            env_idx: Environment index (for vectorized envs)

        Returns:
            Dictionary with state variables
        """
        self._update_state(env_idx=env_idx)
        return super().get_data()

    def __del__(self):
        """Cleanup on deletion."""
        self.shutdown()
