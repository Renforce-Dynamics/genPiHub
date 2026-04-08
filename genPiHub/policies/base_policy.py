"""Base policy interface.

All policies should inherit from this base class and implement the abstract methods.
"""

from abc import ABC, abstractmethod
from collections import deque
from typing import Any, Dict, Tuple
import numpy as np
import torch
import logging

from genPiHub.configs.policy_configs import PolicyConfig
from genPiHub.tools import DOFConfig

logger = logging.getLogger(__name__)


class Policy(ABC):
    """Base class for all policies.

    Attributes:
        cfg: Policy configuration
        device: Device for model inference ("cpu" or "cuda")
        freq: Control frequency (Hz)
        dt: Control timestep (seconds)
        num_dofs: Number of observation DOFs
        num_actions: Number of action DOFs
        model: Policy model (optional, loaded from file)
        last_action: Last action taken (for smoothing)
    """

    def __init__(self, cfg: PolicyConfig, device: str = "cpu"):
        """Initialize policy.

        Args:
            cfg: Policy configuration
            device: Device for inference
        """
        self.cfg = cfg
        self.device = device

        # Control parameters
        self.freq = cfg.freq
        self.dt = 1.0 / self.freq

        # DOF configuration
        self.cfg_obs_dof: DOFConfig = cfg.obs_dof
        self.cfg_action_dof: DOFConfig = cfg.action_dof

        self.num_dofs = self.cfg_obs_dof.num_dofs
        self.num_actions = self.cfg_action_dof.num_dofs

        # Default positions
        self.default_dof_pos = np.asarray(self.cfg_obs_dof.default_pos)
        self.default_action_pos = np.asarray(self.cfg_action_dof.default_pos)

        # Model loading
        self.model: torch.nn.Module | None = None
        if not cfg.disable_autoload:
            if cfg.policy_file:
                logger.info(f"Loading policy from {cfg.policy_file}")
                self.model = torch.jit.load(cfg.policy_file, map_location=self.device)
                self.model.eval()
            else:
                logger.warning("No policy_file specified, model not loaded")

        # Action processing parameters
        self.action_scale = cfg.action_scale
        self.action_clip = cfg.action_clip
        self.action_beta = cfg.action_beta  # For EMA smoothing

        # State tracking
        self.last_action = np.zeros(self.num_actions)

        # History buffer
        self.history_length = cfg.history_length
        self.history_obs_size = cfg.history_obs_size
        self.history_buf: deque | None = None

    def _init_history(self, default_history: np.ndarray | torch.Tensor | list):
        """Initialize history buffer.

        Args:
            default_history: Default history entry to fill buffer
        """
        logger.debug(f"Initializing history buffer: {self.history_length} x {len(default_history)}")
        self.history_buf = deque(maxlen=self.history_length)
        for _ in range(self.history_length):
            self.history_buf.append(default_history)

    @abstractmethod
    def reset(self):
        """Reset policy state.

        Should reset:
        - last_action
        - history_buf (if used)
        - Any policy-specific state
        """
        raise NotImplementedError

    @abstractmethod
    def get_observation(self, env_data: Dict[str, Any], ctrl_data: Dict[str, Any]) -> Tuple[np.ndarray, Dict]:
        """Compute policy observation from environment data.

        Args:
            env_data: Environment state (dof_pos, dof_vel, base_quat, etc.)
            ctrl_data: Controller data (commands, etc.)

        Returns:
            Tuple of (observation, extras)
            - observation: np.ndarray for policy input
            - extras: dict with additional information for debugging
        """
        raise NotImplementedError

    def get_action(self, obs: np.ndarray) -> np.ndarray:
        """Compute action from observation.

        Args:
            obs: Policy observation

        Returns:
            Processed action (scaled, clipped, smoothed)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded, cannot get action")

        # Model inference
        obs_tensor = torch.from_numpy(obs).unsqueeze(0).float().to(self.device)
        with torch.no_grad():
            actions_tensor = self.model(obs_tensor).cpu()

        actions = actions_tensor.numpy().squeeze()

        # EMA smoothing
        if self.action_beta < 1.0:
            actions = (1 - self.action_beta) * self.last_action + self.action_beta * actions

        self.last_action = actions.copy()

        # Clip if specified
        if self.action_clip is not None:
            actions = np.clip(actions, -self.action_clip, self.action_clip)

        # Scale
        actions = actions * self.action_scale

        return actions

    def get_init_dof_pos(self) -> np.ndarray:
        """Get initial DOF positions for robot preparation.

        For motion policies, this should return the first frame of reference motion.
        For other policies, return default standing pose.

        Returns:
            Initial joint positions
        """
        return self.default_action_pos.copy()

    @abstractmethod
    def post_step_callback(self, commands: list[str] | None = None):
        """Post-step callback for policy updates.

        Called after environment step. Used for:
        - Updating internal state
        - Processing commands
        - Logging/debugging

        Args:
            commands: Optional list of commands from user
        """
        raise NotImplementedError

    def reset_alignment(self):
        """Reset heading/spatial alignment.

        Override in policies that compute alignment at runtime (e.g., ProtoMotions trackers).
        Default no-op is correct for policies without alignment state.
        """
        pass

    def debug_viz(self, visualizer, env_data: Dict, ctrl_data: Dict, extras: Dict):
        """Optional debug visualization.

        Args:
            visualizer: Visualization interface
            env_data: Environment data
            ctrl_data: Controller data
            extras: Extra data from get_observation
        """
        pass
