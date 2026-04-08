"""Policy configuration definitions."""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from genPiHub.tools import DOFConfig


@dataclass
class PolicyConfig:
    """Base configuration for all policies.

    Attributes:
        name: Policy name
        policy_file: Path to policy model file (.pt, .jit, etc.)
        device: Device for inference ("cpu" or "cuda")
        freq: Control frequency (Hz)

        # DOF configs
        obs_dof: Observation DOF configuration
        action_dof: Action DOF configuration

        # Action processing
        action_scale: Action scaling factor
        action_clip: Action clipping limit (optional)
        action_beta: EMA smoothing factor (1.0 = no smoothing)

        # History
        history_length: Number of history steps
        history_obs_size: Size of history observation

        # Loading
        disable_autoload: Disable automatic model loading
    """

    # Basic info
    name: str = "BasePolicy"
    policy_file: Optional[Path | str] = None
    device: str = "cpu"
    freq: float = 50.0  # Hz

    # DOF configurations
    obs_dof: DOFConfig = field(default_factory=DOFConfig)
    action_dof: DOFConfig = field(default_factory=DOFConfig)

    # Action processing
    action_scale: float = 1.0
    action_clip: Optional[float] = None
    action_beta: float = 1.0  # 1.0 = no EMA smoothing

    # History buffer
    history_length: int = 0
    history_obs_size: int = 0

    # Model loading
    disable_autoload: bool = False

    def __post_init__(self):
        """Post-initialization validation."""
        # Convert path to Path object
        if self.policy_file is not None and not isinstance(self.policy_file, Path):
            self.policy_file = Path(self.policy_file)

        # Validate frequencies
        assert self.freq > 0, "freq must be positive"

        # Validate action parameters
        assert 0.0 <= self.action_beta <= 1.0, "action_beta must be in [0, 1]"
        if self.action_clip is not None:
            assert self.action_clip > 0, "action_clip must be positive"


# ===== Policy-specific configs =====

@dataclass
class AMOPolicyConfig(PolicyConfig):
    """Configuration for AMO policy."""

    name: str = "AMOPolicy"

    # AMO-specific parameters
    scales_ang_vel: float = 0.25
    scales_dof_vel: float = 0.05
    gait_freq: float = 1.3

    # Adapter
    adapter_file: Optional[Path | str] = None
    norm_stats_file: Optional[Path | str] = None
    use_adapter: bool = True

    # History
    history_length: int = 35  # AMO uses 35 steps
    history_obs_size: int = 93  # AMO proprio size

    def __post_init__(self):
        """Post-initialization for AMO-specific validation."""
        super().__post_init__()

        # Convert adapter paths
        if self.adapter_file is not None and not isinstance(self.adapter_file, Path):
            self.adapter_file = Path(self.adapter_file)
        if self.norm_stats_file is not None and not isinstance(self.norm_stats_file, Path):
            self.norm_stats_file = Path(self.norm_stats_file)


@dataclass
class CLOTPolicyConfig(PolicyConfig):
    """Configuration for CLOT policy (placeholder)."""

    name: str = "CLOTPolicy"
    # TODO: Add CLOT-specific parameters


@dataclass
class ProtoMotionsPolicyConfig(PolicyConfig):
    """Configuration for ProtoMotions policy (placeholder)."""

    name: str = "ProtoMotionsPolicy"
    # TODO: Add ProtoMotions-specific parameters
