"""Base environment interface.

All environments should inherit from this base class and implement the abstract methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy as np
import logging

from genPiHub.configs.env_configs import EnvConfig
from genPiHub.tools import DOFConfig

logger = logging.getLogger(__name__)


class Environment(ABC):
    """Base class for all environments.

    Provides unified interface for:
    - Robot state access (dof_pos, dof_vel, base_quat, base_ang_vel, etc.)
    - Action execution (PD control targets)
    - Environment stepping and resetting
    """

    def __init__(self, cfg: EnvConfig, device: str = "cpu"):
        """Initialize environment.

        Args:
            cfg: Environment configuration
            device: Device for computation
        """
        self.cfg = cfg
        self.device = device

        # DOF configuration
        self.dof_cfg: DOFConfig = cfg.dof
        self.joint_names = self.dof_cfg.joint_names
        self.num_dofs = self.dof_cfg.num_dofs
        self.default_pos = np.asarray(self.dof_cfg.default_pos)
        self.stiffness = np.asarray(self.dof_cfg.stiffness)
        self.damping = np.asarray(self.dof_cfg.damping)
        self.torque_limits = np.asarray(self.dof_cfg.torque_limits)
        self.position_limits = np.asarray(self.dof_cfg.position_limits)

        # State variables (all in radians)
        self._dof_pos = np.zeros(self.num_dofs)
        self._dof_vel = np.zeros(self.num_dofs)
        self._base_quat = np.array([0.0, 0.0, 0.0, 1.0])  # [x, y, z, w]
        self._base_ang_vel = np.zeros(3)

        # Optional state variables
        self._base_pos: np.ndarray | None = None
        self._base_lin_vel: np.ndarray | None = None
        self._base_lin_acc: np.ndarray | None = None

        # Visualization (optional)
        self.visualizer: Any | None = None

    def update_dof_cfg(self, override_cfg: DOFConfig | None = None):
        """Update DOF configuration.

        Args:
            override_cfg: Configuration to override current DOF config
        """
        from genPiHub.tools import merge_dof_configs

        if override_cfg is not None:
            self.dof_cfg = merge_dof_configs(self.cfg.dof, override_cfg)
        else:
            self.dof_cfg = self.cfg.dof

        # Update derived attributes
        self.joint_names = self.dof_cfg.joint_names
        self.num_dofs = self.dof_cfg.num_dofs
        self.default_pos = np.asarray(self.dof_cfg.default_pos)
        self.stiffness = np.asarray(self.dof_cfg.stiffness)
        self.damping = np.asarray(self.dof_cfg.damping)
        self.torque_limits = np.asarray(self.dof_cfg.torque_limits)
        self.position_limits = np.asarray(self.dof_cfg.position_limits)

        # Apply gains
        self.set_gains(self.stiffness, self.damping)

    @abstractmethod
    def self_check(self):
        """Perform self-check to ensure environment is ready."""
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        """Reset environment to initial state."""
        raise NotImplementedError

    @abstractmethod
    def update(self):
        """Update environment state from backend."""
        raise NotImplementedError

    @abstractmethod
    def step(self, pd_target: np.ndarray) -> Dict[str, Any]:
        """Execute one environment step.

        Args:
            pd_target: PD control targets (joint positions)

        Returns:
            Step result dictionary (optional)
        """
        assert len(pd_target) == self.num_dofs, \
            f"pd_target length ({len(pd_target)}) must match num_dofs ({self.num_dofs})"
        raise NotImplementedError

    @abstractmethod
    def shutdown(self):
        """Shutdown environment and release resources."""
        raise NotImplementedError

    @abstractmethod
    def set_gains(self, stiffness: np.ndarray, damping: np.ndarray):
        """Set PD control gains.

        Args:
            stiffness: Proportional gains (Kp)
            damping: Derivative gains (Kd)
        """
        raise NotImplementedError

    # === Properties (read-only state access) ===

    @property
    def dof_pos(self) -> np.ndarray:
        """Joint positions (radians)."""
        return self._dof_pos.copy()

    @property
    def dof_vel(self) -> np.ndarray:
        """Joint velocities (rad/s)."""
        return self._dof_vel.copy()

    @property
    def base_quat(self) -> np.ndarray:
        """Base orientation quaternion [x, y, z, w]."""
        return self._base_quat.copy()

    @property
    def base_ang_vel(self) -> np.ndarray:
        """Base angular velocity (rad/s) in world frame."""
        return self._base_ang_vel.copy()

    @property
    def base_pos(self) -> np.ndarray | None:
        """Base position (m) in world frame (optional)."""
        return self._base_pos.copy() if self._base_pos is not None else None

    @property
    def base_lin_vel(self) -> np.ndarray | None:
        """Base linear velocity (m/s) in world frame (optional)."""
        return self._base_lin_vel.copy() if self._base_lin_vel is not None else None

    @property
    def base_lin_acc(self) -> np.ndarray | None:
        """Base linear acceleration (m/s^2) in world frame (optional)."""
        return self._base_lin_acc.copy() if self._base_lin_acc is not None else None

    def get_data(self) -> Dict[str, Any]:
        """Get current environment state as dictionary.

        Returns:
            Dictionary with all available state variables:
            - dof_pos: Joint positions
            - dof_vel: Joint velocities
            - base_quat: Base quaternion
            - base_ang_vel: Base angular velocity
            - base_pos: Base position (if available)
            - base_lin_vel: Base linear velocity (if available)
            - base_lin_acc: Base linear acceleration (if available)
        """
        return {
            "dof_pos": self.dof_pos,
            "dof_vel": self.dof_vel,
            "base_quat": self.base_quat,
            "base_ang_vel": self.base_ang_vel,
            "base_pos": self.base_pos,
            "base_lin_vel": self.base_lin_vel,
            "base_lin_acc": self.base_lin_acc,
        }
