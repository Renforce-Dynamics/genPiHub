"""CLOT (Closed-Loop Motion Tracking) policy wrapper.

CLOT is from the humanoid_benchmark project and provides motion tracking
using AMP (Adversarial Motion Priors).

Reference: https://arxiv.org/abs/2602.15060
"""

import numpy as np
import torch
import logging
from typing import Dict, Any, Tuple
from pathlib import Path

from genPiHub.policies.base_policy import Policy
from genPiHub.configs.policy_configs import CLOTPolicyConfig

logger = logging.getLogger(__name__)


class CLOTPolicy(Policy):
    """CLOT policy wrapper for genPiHub.

    CLOT uses a trained tracking policy with optional motion library for
    reference motion tracking.

    Example:
        >>> from genPiHub import load_policy
        >>> policy = load_policy(
        ...     name="CLOTPolicy",
        ...     policy_file="models/clot_policy.pt",
        ...     motion_lib_dir="data/motions",
        ...     device="cuda"
        ... )
        >>> policy.reset()
        >>> obs, extras = policy.get_observation(env_data, {})
        >>> action = policy.get_action(obs)
    """

    def __init__(self, cfg: CLOTPolicyConfig, device: str = "cpu"):
        """Initialize CLOT policy.

        Args:
            cfg: CLOT policy configuration
            device: Device for inference
        """
        super().__init__(cfg, device)

        self.cfg_clot: CLOTPolicyConfig = cfg

        # Load policy model
        if cfg.policy_file is not None and not cfg.disable_autoload:
            logger.info(f"Loading CLOT policy from {cfg.policy_file}")
            self.model = torch.jit.load(
                str(cfg.policy_file),
                map_location=device
            )
            self.model.eval()
        else:
            logger.warning("No policy file provided, model not loaded")
            self.model = None

        # Load motion library if provided
        self.motion_lib = None
        if cfg.motion_lib_dir is not None:
            self._load_motion_library(cfg.motion_lib_dir, cfg.motion_files)

        # AMP observation buffer
        self.amp_obs_buffer = None

        # Compute observation dimension
        # Policy obs: gravity(3) + ang_vel(3) + lin_vel(3) + joint_pos(23) + joint_vel(23) + last_action(23) = 81
        self.num_obs = 3 + 3 + 3 + self.num_actions + self.num_actions + self.num_actions

        logger.info(
            f"CLOT policy initialized: "
            f"num_obs={self.num_obs}, num_actions={self.num_actions}, "
            f"has_motion_lib={self.motion_lib is not None}"
        )

    def _load_motion_library(self, motion_dir: Path, motion_files: list[str]):
        """Load motion library from directory.

        Args:
            motion_dir: Directory containing motion files
            motion_files: List of motion files to load (empty = load all .npy)
        """
        motion_dir = Path(motion_dir)
        if not motion_dir.exists():
            logger.warning(f"Motion library directory not found: {motion_dir}")
            return

        # Find motion files
        if motion_files:
            files = [motion_dir / f for f in motion_files]
        else:
            files = list(motion_dir.glob("*.npy"))

        if not files:
            logger.warning(f"No motion files found in {motion_dir}")
            return

        logger.info(f"Loading {len(files)} motion files from {motion_dir}")

        # Load motions (simple numpy-based motion lib for now)
        motions = []
        for f in files:
            try:
                motion_data = np.load(f)
                motions.append(motion_data)
                logger.debug(f"Loaded motion from {f.name}: shape={motion_data.shape}")
            except Exception as e:
                logger.warning(f"Failed to load motion from {f}: {e}")

        if motions:
            # Stack all motions
            self.motion_lib = {
                "motions": motions,
                "num_motions": len(motions),
                "files": [f.name for f in files],
            }
            logger.info(f"Motion library loaded: {len(motions)} motions")
        else:
            logger.warning("No valid motions loaded")

    def reset(self):
        """Reset CLOT policy state."""
        self.last_action = np.zeros(self.num_actions)
        self.amp_obs_buffer = None

        # Reset history buffer if used
        if self.history_buf is not None:
            default_history = np.zeros(self.history_obs_size)
            self._init_history(default_history)

    def get_observation(
        self, env_data: Dict[str, Any], ctrl_data: Dict[str, Any]
    ) -> Tuple[np.ndarray | Dict, Dict]:
        """Get CLOT observation from environment data.

        CLOT can work in two modes:
        1. Direct env_data pass-through (for genesis environment)
        2. Constructed observation vector

        Args:
            env_data: Environment state dict with keys:
                - dof_pos: Joint positions (num_dofs,)
                - dof_vel: Joint velocities (num_dofs,)
                - base_quat: Base orientation quaternion (4,) [x,y,z,w]
                - base_ang_vel: Angular velocity (3,)
                - base_lin_vel: Linear velocity (3,) [optional]
                - projected_gravity: Projected gravity (3,) [optional]
            ctrl_data: Controller data (unused for CLOT)

        Returns:
            Tuple of (observation, extras)
            - observation: Either dict (for genesis) or numpy array
            - extras: Dict with optional AMP observation
        """
        extras = {}

        # If running in genesis environment, pass through env_data
        # The observation will be constructed by the environment's observation manager
        if "obs" in env_data:
            # Genesis environment already constructed observation
            return env_data["obs"], extras

        # Otherwise, construct observation manually
        obs_components = []

        # Projected gravity (3,)
        if "projected_gravity" in env_data:
            obs_components.append(env_data["projected_gravity"])
        else:
            # Compute from base quaternion
            quat = env_data.get("base_quat", np.array([0, 0, 0, 1]))
            gravity = self._project_gravity(quat)
            obs_components.append(gravity)

        # Angular velocity in base frame (3,) - scaled
        base_ang_vel = env_data.get("base_ang_vel", np.zeros(3))
        obs_components.append(base_ang_vel * 0.25)  # CLOT scaling

        # Linear velocity in base frame (3,)
        if "base_lin_vel" in env_data:
            obs_components.append(env_data["base_lin_vel"])
        else:
            obs_components.append(np.zeros(3))

        # Joint positions relative to default (num_dofs,)
        dof_pos = env_data.get("dof_pos", np.zeros(self.num_actions))
        default_pos = getattr(self, "default_dof_pos", np.zeros_like(dof_pos))
        obs_components.append(dof_pos - default_pos)

        # Joint velocities - scaled (num_dofs,)
        dof_vel = env_data.get("dof_vel", np.zeros(self.num_actions))
        obs_components.append(dof_vel * 0.05)  # CLOT scaling

        # Last action (num_actions,)
        obs_components.append(self.last_action)

        # Concatenate observation
        obs = np.concatenate(obs_components)

        # Optionally compute AMP observation for extras
        if self.cfg_clot.use_amp:
            amp_obs = self._compute_amp_observation(env_data)
            extras["amp_obs"] = amp_obs

        return obs, extras

    def _project_gravity(self, quat: np.ndarray) -> np.ndarray:
        """Project gravity vector to base frame.

        Args:
            quat: Quaternion [x, y, z, w]

        Returns:
            Projected gravity vector (3,)
        """
        # Convert quaternion to rotation matrix and project [0, 0, -1]
        from scipy.spatial.transform import Rotation as R
        rot = R.from_quat(quat)  # scipy uses [x,y,z,w]
        gravity_world = np.array([0.0, 0.0, -1.0])
        gravity_base = rot.inv().apply(gravity_world)
        return gravity_base

    def _compute_amp_observation(self, env_data: Dict[str, Any]) -> np.ndarray:
        """Compute AMP observation for discriminator.

        AMP observation includes:
        - Root height (1,)
        - Root rotation quaternion (4,)
        - Root linear velocity (3,)
        - Root angular velocity (3,)
        - Joint positions (num_dofs,)
        - Joint velocities (num_dofs,)

        Args:
            env_data: Environment state

        Returns:
            AMP observation vector
        """
        amp_components = []

        # Root height
        root_pos = env_data.get("base_pos", np.array([0, 0, 0.75]))
        amp_components.append(root_pos[2:3])  # z-coordinate

        # Root rotation (quaternion)
        root_quat = env_data.get("base_quat", np.array([0, 0, 0, 1]))
        amp_components.append(root_quat)

        # Root linear velocity
        lin_vel = env_data.get("base_lin_vel", np.zeros(3))
        amp_components.append(lin_vel)

        # Root angular velocity (unscaled for AMP)
        ang_vel = env_data.get("base_ang_vel", np.zeros(3))
        amp_components.append(ang_vel)

        # Joint positions
        dof_pos = env_data.get("dof_pos", np.zeros(self.num_actions))
        amp_components.append(dof_pos)

        # Joint velocities
        dof_vel = env_data.get("dof_vel", np.zeros(self.num_actions))
        amp_components.append(dof_vel)

        amp_obs = np.concatenate(amp_components)
        return amp_obs

    def post_step_callback(self, commands: list[str] | None = None):
        """Post-step callback (CLOT doesn't need this)."""
        pass

    def get_init_dof_pos(self) -> np.ndarray:
        """Get CLOT default DOF positions.

        Returns:
            Default joint positions (23,)
        """
        # G1 CLOT default pose
        from genPiHub.envs.clot.robot_cfg import G1_CLOT_DEFAULT_POS
        return np.array(G1_CLOT_DEFAULT_POS, dtype=np.float32)


# Factory function
def create_clot_policy(
    model_file: str | Path,
    motion_lib_dir: str | Path | None = None,
    device: str = "cuda",
    **kwargs
) -> CLOTPolicy:
    """Create CLOT policy with default configuration.

    Args:
        model_file: Path to CLOT model file (.pt or .jit)
        motion_lib_dir: Directory containing reference motions
        device: Device for inference
        **kwargs: Additional config overrides

    Returns:
        CLOTPolicy instance
    """
    from pathlib import Path
    from genPiHub.tools import DOFConfig
    from genPiHub.envs.clot.robot_cfg import G1_23DOF_NAMES, G1_CLOT_DEFAULT_POS

    # CLOT DOF configuration (same as AMO: 23 DOF G1)
    dof_cfg = DOFConfig(
        joint_names=G1_23DOF_NAMES,
        num_dofs=23,
        default_pos=G1_CLOT_DEFAULT_POS,
    )

    cfg = CLOTPolicyConfig(
        policy_file=Path(model_file),
        motion_lib_dir=Path(motion_lib_dir) if motion_lib_dir else None,
        device=device,
        obs_dof=dof_cfg,
        action_dof=dof_cfg,
        action_scale=0.25,
        action_clip=10.0,
        use_amp=True,
        **kwargs
    )

    return CLOTPolicy(cfg, device)
