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
    """Configuration for CLOT (Closed-Loop Motion Tracking) policy.

    CLOT uses AMP (Adversarial Motion Priors) for motion tracking.
    """

    name: str = "CLOTPolicy"

    # Motion library
    motion_lib_dir: Optional[Path | str] = None  # Directory containing motion files
    motion_files: list[str] = field(default_factory=list)  # Specific motion files to load

    # AMP parameters
    use_amp: bool = True  # Use AMP discriminator
    amp_obs_dim: int = 0  # AMP observation dimension (auto-computed)

    # Tracking parameters
    tracking_sigma: float = 0.5  # Position tracking tolerance
    tracking_sigma_vel: float = 0.1  # Velocity tracking tolerance

    # Action parameters (CLOT-specific)
    action_scale: float = 0.25  # Similar to AMO
    action_clip: Optional[float] = 10.0  # Clip actions to prevent extreme movements

    def __post_init__(self):
        """Post-initialization for CLOT-specific validation."""
        super().__post_init__()

        # Convert motion lib path
        if self.motion_lib_dir is not None and not isinstance(self.motion_lib_dir, Path):
            self.motion_lib_dir = Path(self.motion_lib_dir)


@dataclass
class BeyondMimicPolicyConfig(PolicyConfig):
    """Configuration for BeyondMimic policy (ONNX-based whole-body tracking)."""

    name: str = "BeyondMimicPolicy"

    # ONNX model
    model_format: str = "onnx"  # Force ONNX format
    use_model_meta_config: bool = True  # Load config from ONNX metadata

    # Motion data (embedded in ONNX model)
    use_motion_from_model: bool = True  # Motion data in model
    max_timestep: int = -1  # Max motion timesteps (-1 = auto from model)
    start_timestep: int = 0  # Starting timestep

    # State estimator mode
    without_state_estimator: bool = True  # wose mode (no position/velocity estimate)

    # Action processing
    action_scales: list[float] = field(default_factory=list)  # Per-joint scales
    action_beta: float = 1.0  # EMA smoothing

    # Robot anchor override
    override_robot_anchor_pos: bool = True  # Use motion anchor position


@dataclass
class ProtoMotionsPolicyConfig(PolicyConfig):
    """Configuration for ProtoMotions policy (placeholder)."""

    name: str = "ProtoMotionsPolicy"
    # TODO: Add ProtoMotions-specific parameters


@dataclass
class HoloMotionPolicyConfig(PolicyConfig):
    """Configuration for HorizonRobotics HoloMotion policy (ONNX).

    Supports two task types exported by HoloMotion v1.2:
      - ``velocity_tracking``: joystick-style command tracking (MLP, no KV cache)
      - ``motion_tracking``:   reference-motion imitation (Transformer-MoE + KV cache)

    The policy is distributed as a directory with ``config.yaml`` (training/env
    config used for the checkpoint) and ``exported/*.onnx`` (the deployable
    actor). The wrapper auto-reads DOF ordering, default angles and action
    scales from the ONNX metadata_props embedded at export time.
    """

    name: str = "HoloMotionPolicy"

    # Which model folder to load (preferred entry point). When set, overrides
    # ``policy_file`` / ``config_file`` with the canonical layout:
    #   <model_dir>/config.yaml
    #   <model_dir>/exported/*.onnx
    model_dir: Optional[Path | str] = None

    # Or specify files explicitly:
    config_file: Optional[Path | str] = None  # training config.yaml
    # policy_file inherited from PolicyConfig — points to the .onnx file

    # Task type — derived automatically from obs_groups config if omitted.
    # One of: "velocity_tracking", "motion_tracking", "auto"
    task_type: str = "auto"

    # Runtime device for onnxruntime:  "cpu" | "cuda" | "tensorrt"
    device: str = "cuda"

    # Control frequency (HoloMotion v1.2 policy runs at 50 Hz)
    freq: float = 50.0

    # Obs term naming — HoloMotion exported configs use the unified obs_groups
    # with the ``actor_`` prefix. Leave as-is unless you are using a fork.
    obs_group_name: str = "unified"
    actor_term_prefix: str = "actor_"

    # --- Velocity tracking command plumbing ---
    # The velocity command atomic obs is a 4-vector [is_moving, vx, vy, vyaw].
    # Threshold for setting the ``is_moving`` flag (matches ROS2 deployment).
    vel_cmd_is_moving_threshold: float = 0.1

    # --- Motion tracking plumbing (only used when task_type=="motion_tracking") ---
    # Path to a retargeted motion clip (.npz) to play during inference.
    motion_npz_path: Optional[Path | str] = None
    # Max transformer context length used at training/export time; the KV cache
    # tensor shape is [n_layers, 2, 1, max_ctx_len, n_kv_heads, head_dim] and is
    # read from the ONNX signature at load time.
    motion_max_ctx_len: int = 32

    # Action processing — HoloMotion uses per-joint action_scale embedded in
    # ONNX metadata, so the scalar ``action_scale`` inherited from PolicyConfig
    # stays at 1.0 and we apply the per-joint scale inside the wrapper.
    action_scale: float = 1.0
    action_clip: Optional[float] = 100.0  # matches env.config.normalization.clip_actions

    def __post_init__(self):
        super().__post_init__()
        if self.model_dir is not None and not isinstance(self.model_dir, Path):
            self.model_dir = Path(self.model_dir)
        if self.config_file is not None and not isinstance(self.config_file, Path):
            self.config_file = Path(self.config_file)
        if self.motion_npz_path is not None and not isinstance(self.motion_npz_path, Path):
            self.motion_npz_path = Path(self.motion_npz_path)
