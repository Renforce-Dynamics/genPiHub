"""DOF (Degree of Freedom) configuration management."""

from dataclasses import dataclass, field
from typing import List
import numpy as np


@dataclass
class DOFConfig:
    """Configuration for robot degrees of freedom.

    Defines joint names, limits, gains, and default positions.
    """

    # Joint specification
    joint_names: List[str] = field(default_factory=list)
    num_dofs: int = 0

    # Default state
    default_pos: List[float] | np.ndarray = field(default_factory=list)

    # Physical limits
    position_limits: List[List[float]] | np.ndarray = field(default_factory=list)
    velocity_limits: List[float] | np.ndarray = field(default_factory=list)
    torque_limits: List[float] | np.ndarray = field(default_factory=list)

    # PD control gains
    stiffness: List[float] | np.ndarray = field(default_factory=list)
    damping: List[float] | np.ndarray = field(default_factory=list)

    def __post_init__(self):
        """Validate and normalize configuration."""
        # Infer num_dofs if not provided
        if self.num_dofs == 0 and len(self.joint_names) > 0:
            self.num_dofs = len(self.joint_names)

        # Convert to numpy arrays
        if isinstance(self.default_pos, list):
            self.default_pos = np.array(self.default_pos, dtype=np.float32)
        if isinstance(self.position_limits, list) and len(self.position_limits) > 0:
            self.position_limits = np.array(self.position_limits, dtype=np.float32)
        if isinstance(self.velocity_limits, list):
            self.velocity_limits = np.array(self.velocity_limits, dtype=np.float32)
        if isinstance(self.torque_limits, list):
            self.torque_limits = np.array(self.torque_limits, dtype=np.float32)
        if isinstance(self.stiffness, list):
            self.stiffness = np.array(self.stiffness, dtype=np.float32)
        if isinstance(self.damping, list):
            self.damping = np.array(self.damping, dtype=np.float32)

        # Validate dimensions
        if self.num_dofs > 0:
            if len(self.joint_names) > 0:
                assert len(self.joint_names) == self.num_dofs, \
                    f"joint_names length ({len(self.joint_names)}) != num_dofs ({self.num_dofs})"
            if len(self.default_pos) > 0:
                assert len(self.default_pos) == self.num_dofs, \
                    f"default_pos length ({len(self.default_pos)}) != num_dofs ({self.num_dofs})"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "joint_names": self.joint_names,
            "num_dofs": self.num_dofs,
            "default_pos": self.default_pos.tolist() if isinstance(self.default_pos, np.ndarray) else self.default_pos,
            "position_limits": self.position_limits.tolist() if isinstance(self.position_limits, np.ndarray) else self.position_limits,
            "velocity_limits": self.velocity_limits.tolist() if isinstance(self.velocity_limits, np.ndarray) else self.velocity_limits,
            "torque_limits": self.torque_limits.tolist() if isinstance(self.torque_limits, np.ndarray) else self.torque_limits,
            "stiffness": self.stiffness.tolist() if isinstance(self.stiffness, np.ndarray) else self.stiffness,
            "damping": self.damping.tolist() if isinstance(self.damping, np.ndarray) else self.damping,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DOFConfig":
        """Create from dictionary."""
        return cls(**data)


def merge_dof_configs(base: DOFConfig, override: DOFConfig) -> DOFConfig:
    """Merge two DOF configs, with override taking precedence.

    Args:
        base: Base configuration
        override: Override configuration

    Returns:
        Merged configuration
    """
    merged = DOFConfig()

    # Take joint names from override if available
    merged.joint_names = override.joint_names if len(override.joint_names) > 0 else base.joint_names
    merged.num_dofs = override.num_dofs if override.num_dofs > 0 else base.num_dofs

    # Merge arrays (override takes precedence)
    merged.default_pos = override.default_pos if len(override.default_pos) > 0 else base.default_pos
    merged.position_limits = override.position_limits if len(override.position_limits) > 0 else base.position_limits
    merged.velocity_limits = override.velocity_limits if len(override.velocity_limits) > 0 else base.velocity_limits
    merged.torque_limits = override.torque_limits if len(override.torque_limits) > 0 else base.torque_limits
    merged.stiffness = override.stiffness if len(override.stiffness) > 0 else base.stiffness
    merged.damping = override.damping if len(override.damping) > 0 else base.damping

    return merged
