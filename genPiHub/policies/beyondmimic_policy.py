"""BeyondMimic policy wrapper.

BeyondMimic is a whole-body tracking policy that uses ONNX Runtime for inference.
It supports motion data embedded within the ONNX model.

Reference: whole_body_tracking project
"""

import numpy as np
import logging
from typing import Dict, Any, Tuple
from pathlib import Path

from genPiHub.policies.base_policy import Policy
from genPiHub.configs.policy_configs import BeyondMimicPolicyConfig

logger = logging.getLogger(__name__)


class BeyondMimicPolicy(Policy):
    """BeyondMimic policy wrapper for genPiHub.

    Uses ONNX Runtime for inference with optional model metadata configuration.
    Supports motion data embedded in ONNX model.

    Example:
        >>> from genPiHub import load_policy
        >>> policy = load_policy(
        ...     name="BeyondMimicPolicy",
        ...     policy_file="models/beyondmimic_dance.onnx",
        ...     device="cuda"
        ... )
        >>> policy.reset()
        >>> obs, extras = policy.get_observation(env_data, {})
        >>> action = policy.get_action(obs)
    """

    def __init__(self, cfg: BeyondMimicPolicyConfig, device: str = "cpu"):
        """Initialize BeyondMimic policy.

        Args:
            cfg: BeyondMimic policy configuration
            device: Device for inference (cpu/cuda/tensorrt)
        """
        # Check ONNX Runtime availability
        try:
            import onnxruntime as ort
            self.ort = ort
            self.onnx_available = True
        except ImportError:
            self.onnx_available = False
            logger.warning(
                "onnxruntime not available. Install: pip install onnxruntime-gpu"
            )

        self.cfg_bm: BeyondMimicPolicyConfig = cfg

        # Configure ONNX providers
        if device == "cpu":
            providers = ["CPUExecutionProvider"]
        elif device == "cuda":
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        elif device == "tensorrt":
            providers = ["TensorrtExecutionProvider", "CUDAExecutionProvider", "CPUExecutionProvider"]
        else:
            logger.warning(f"Unknown device {device}, using CPU")
            providers = ["CPUExecutionProvider"]

        # Load ONNX model
        self.session = None
        if cfg.policy_file and not cfg.disable_autoload and self.onnx_available:
            logger.info(f"Loading ONNX model from {cfg.policy_file}")
            sess_options = self.ort.SessionOptions()
            self.session = self.ort.InferenceSession(
                str(cfg.policy_file),
                sess_options,
                providers=providers
            )

            # Get input/output names
            self.input_names = [i.name for i in self.session.get_inputs()]
            self.output_names = [o.name for o in self.session.get_outputs()]

            # Load config from model metadata if enabled
            if cfg.use_model_meta_config:
                self._load_model_metadata()
        else:
            logger.warning("No ONNX model loaded")

        # Initialize base policy attributes (CUSTOM - don't use super().__init__())
        # BeyondMimic uses ONNX, not PyTorch JIT
        self._init_from_base(cfg, device)

        # BeyondMimic-specific parameters
        self.action_scales = np.array(cfg.action_scales) if cfg.action_scales else np.ones(self.num_actions)
        self.without_state_estimator = cfg.without_state_estimator
        self.use_motion_from_model = cfg.use_motion_from_model
        self.max_timestep = cfg.max_timestep
        self.timestep = cfg.start_timestep
        self.play_speed = 1.0
        self.flag_motion_done = False

        # Motion command buffer (for motion-from-model mode)
        self.command = None

        # Compute observation dimension
        # wose mode: command(29*2) + ori(6) + ang_vel(3) + joint_pos_rel(29) + joint_vel(29) + last_action(29) = 154
        # with SE: + lin_vel(3) + anchor_pos(3) = 160
        base_obs_dim = (self.num_actions * 2) + 6 + 3 + (self.num_actions * 3)
        if not self.without_state_estimator:
            base_obs_dim += 6  # lin_vel(3) + anchor_pos(3)
        self.num_obs = base_obs_dim

        logger.info(
            f"BeyondMimic policy initialized: "
            f"num_obs={self.num_obs}, num_actions={self.num_actions}, "
            f"wose={self.without_state_estimator}, "
            f"motion_from_model={self.use_motion_from_model}"
        )

    def _load_model_metadata(self):
        """Load configuration from ONNX model metadata."""
        if not self.session:
            return

        try:
            modelmeta = self.session.get_modelmeta()
            meta_dict = modelmeta.custom_metadata_map

            logger.info("Loading config from ONNX model metadata")

            # Helper functions
            def parse_floats(s):
                return [float(x) for x in s.split(",")]

            def parse_strings(s):
                return [x.strip() for x in s.split(",")]

            # Load joint configuration
            if "joint_names" in meta_dict:
                joint_names = parse_strings(meta_dict["joint_names"])
                default_pos = parse_floats(meta_dict.get("default_joint_pos", ""))
                stiffness = parse_floats(meta_dict.get("joint_stiffness", ""))
                damping = parse_floats(meta_dict.get("joint_damping", ""))

                logger.info(f"Loaded {len(joint_names)} joints from model metadata")

                # Update DOF config
                from genPiHub.tools import DOFConfig

                dof_cfg = DOFConfig(
                    joint_names=joint_names,
                    num_dofs=len(joint_names),
                    default_pos=default_pos if default_pos else None,
                    stiffness=stiffness if stiffness else None,
                    damping=damping if damping else None,
                )
                self.cfg_bm.obs_dof = dof_cfg
                self.cfg_bm.action_dof = dof_cfg

            # Load action scales
            if "action_scale" in meta_dict:
                self.cfg_bm.action_scales = parse_floats(meta_dict["action_scale"])
                logger.info(f"Loaded action scales from metadata")

        except Exception as e:
            logger.warning(f"Failed to load model metadata: {e}")

    def _init_from_base(self, cfg, device):
        """Initialize base policy attributes without loading PyTorch model.

        BeyondMimic uses ONNX Runtime, not PyTorch JIT, so we manually
        set the base attributes instead of calling super().__init__().
        """
        self.cfg = cfg
        self.device = device

        # Control parameters
        self.freq = cfg.freq
        self.dt = 1.0 / self.freq if self.freq > 0 else 0.02

        # DOF configuration
        self.cfg_obs_dof = cfg.obs_dof
        self.cfg_action_dof = cfg.action_dof

        self.num_dofs = cfg.obs_dof.num_dofs if cfg.obs_dof else cfg.action_dof.num_dofs
        self.num_actions = cfg.action_dof.num_dofs

        # Default positions
        if cfg.obs_dof and cfg.obs_dof.default_pos is not None:
            self.default_dof_pos = np.asarray(cfg.obs_dof.default_pos)
        else:
            self.default_dof_pos = np.zeros(self.num_dofs)

        if cfg.action_dof and cfg.action_dof.default_pos is not None:
            self.default_action_pos = np.asarray(cfg.action_dof.default_pos)
        else:
            self.default_action_pos = np.zeros(self.num_actions)

        # Action processing parameters
        self.action_scale = cfg.action_scale
        self.action_clip = cfg.action_clip
        self.action_beta = cfg.action_beta

        # State tracking
        self.last_action = np.zeros(self.num_actions)

        # Model is ONNX session, not PyTorch
        self.model = self.session

        # BeyondMimic-specific: yaw alignment
        self.init_to_world = None  # Transformation matrix for yaw alignment
        self.step_count = 0

    def reset(self):
        """Reset BeyondMimic policy state."""
        self.last_action = np.zeros(self.num_actions)
        self.timestep = self.cfg_bm.start_timestep
        self.play_speed = 1.0
        self.flag_motion_done = False
        self.command = None

        # Reset yaw alignment
        self.init_to_world = None
        self.step_count = 0

        # Warm up model if available
        if self.session:
            obs_shape = self.session.get_inputs()[0].shape
            if obs_shape and len(obs_shape) > 1:
                dummy_obs = np.zeros(obs_shape[1], dtype=np.float32)
                try:
                    self.get_action(dummy_obs)
                except:
                    pass  # Ignore warm-up errors

    @staticmethod
    def _quat_mul(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
        """Quaternion multiplication (Hamilton product).

        Args:
            q1, q2: Quaternions in [w, x, y, z] format

        Returns:
            Product quaternion [w, x, y, z]
        """
        w1, x1, y1, z1 = q1[0], q1[1], q1[2], q1[3]
        w2, x2, y2, z2 = q2[0], q2[1], q2[2], q2[3]

        ww = (z1 + x1) * (x2 + y2)
        yy = (w1 - y1) * (w2 + z2)
        zz = (w1 + y1) * (w2 - z2)
        xx = ww + yy + zz
        qq = 0.5 * (xx + (z1 - x1) * (x2 - y2))

        w = qq - ww + (z1 - y1) * (y2 - z2)
        x = qq - xx + (x1 + w1) * (x2 + w2)
        y = qq - yy + (w1 - x1) * (y2 + z2)
        z = qq - zz + (z1 + y1) * (w2 - x2)

        return np.array([w, x, y, z], dtype=np.float32)

    @staticmethod
    def _matrix_from_quat(q: np.ndarray) -> np.ndarray:
        """Convert quaternion to rotation matrix.

        Args:
            q: Quaternion in [w, x, y, z] format

        Returns:
            3x3 rotation matrix
        """
        w, x, y, z = q
        return np.array([
            [1 - 2 * (y**2 + z**2), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x**2 + z**2), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x**2 + y**2)]
        ], dtype=np.float32)

    @staticmethod
    def _yaw_quat(q: np.ndarray) -> np.ndarray:
        """Extract yaw component from quaternion.

        Args:
            q: Quaternion in [w, x, y, z] format

        Returns:
            Yaw-only quaternion [w, 0, 0, z]
        """
        w, x, y, z = q
        yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y**2 + z**2))
        return np.array([np.cos(yaw / 2), 0, 0, np.sin(yaw / 2)], dtype=np.float32)

    @staticmethod
    def _euler_to_quat(angle: float, axis: str) -> np.ndarray:
        """Convert single-axis Euler angle to quaternion.

        Args:
            angle: Rotation angle in radians
            axis: Rotation axis ('x', 'y', or 'z')

        Returns:
            Quaternion [w, x, y, z]
        """
        half_angle = angle * 0.5
        cos_half = np.cos(half_angle)
        sin_half = np.sin(half_angle)

        if axis == 'x':
            return np.array([cos_half, sin_half, 0.0, 0.0], dtype=np.float32)
        elif axis == 'y':
            return np.array([cos_half, 0.0, sin_half, 0.0], dtype=np.float32)
        elif axis == 'z':
            return np.array([cos_half, 0.0, 0.0, sin_half], dtype=np.float32)
        else:
            raise ValueError(f"Invalid axis: {axis}")

    def get_observation(
        self, env_data: Dict[str, Any], ctrl_data: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict]:
        """Get BeyondMimic observation from environment data.

        Args:
            env_data: Environment state
            ctrl_data: Controller data (motion commands)

        Returns:
            Tuple of (observation, extras)
        """
        # Get basic state
        dof_pos = env_data.get("dof_pos", np.zeros(self.num_actions, dtype=np.float32))
        dof_vel = env_data.get("dof_vel", np.zeros(self.num_actions, dtype=np.float32))
        ang_vel = env_data.get("base_ang_vel", np.zeros(3, dtype=np.float32))
        lin_vel = env_data.get("base_lin_vel", np.zeros(3, dtype=np.float32))
        base_quat = env_data.get("base_quat", np.array([1, 0, 0, 0], dtype=np.float32))  # [w,x,y,z]

        # Get motion command (joint positions and velocities from reference)
        if self.use_motion_from_model and self.command is not None:
            # Use motion from model
            ref_joint_pos = self.command.get("joint_pos", dof_pos)
            ref_joint_vel = self.command.get("joint_vel", dof_vel)
            command = np.concatenate([ref_joint_pos, ref_joint_vel])
        else:
            # Use external motion command
            command = ctrl_data.get("motion_command", np.concatenate([dof_pos, dof_vel]))
            ref_joint_pos = dof_pos
            ref_joint_vel = dof_vel

        # Compute relative joint positions (same as FSMDeployG1)
        joint_pos_rel = dof_pos - self.default_dof_pos

        # BeyondMimic uses TORSO orientation, not pelvis!
        # Convert pelvis quat to torso quat by adding waist joint rotations
        # Waist joints: [2]=waist_yaw, [5]=waist_roll, [8]=waist_pitch in BeyondMimic order
        waist_yaw = joint_pos_rel[2]     # waist_yaw_joint
        waist_roll = joint_pos_rel[5]    # waist_roll_joint
        waist_pitch = joint_pos_rel[8]   # waist_pitch_joint

        quat_yaw = self._euler_to_quat(waist_yaw, 'z')
        quat_roll = self._euler_to_quat(waist_roll, 'x')
        quat_pitch = self._euler_to_quat(waist_pitch, 'y')

        # Compose rotations: torso = pelvis * yaw * roll * pitch
        temp1 = self._quat_mul(quat_roll, quat_pitch)
        temp2 = self._quat_mul(quat_yaw, temp1)
        robot_quat = self._quat_mul(base_quat, temp2)

        # Get reference anchor orientation (body 7 is torso/pelvis in BeyondMimic)
        if self.use_motion_from_model and self.command is not None and "body_quat_w" in self.command:
            # body_quat_w shape is (14, 4) for 14 bodies
            ref_anchor_quat = self.command["body_quat_w"][7]  # Torso/anchor body
        else:
            ref_anchor_quat = np.array([1, 0, 0, 0], dtype=np.float32)

        # Yaw alignment: compute init_to_world on first step (same as FSMDeployG1)
        if self.step_count < 2:
            init_to_anchor = self._matrix_from_quat(self._yaw_quat(ref_anchor_quat))
            world_to_anchor = self._matrix_from_quat(self._yaw_quat(robot_quat))
            self.init_to_world = world_to_anchor @ init_to_anchor.T
            self.step_count += 1

            # Return zero observation on first frames (not ready yet)
            if self.step_count == 1:
                obs = np.zeros(self.num_obs, dtype=np.float32)
                extras = {
                    "timestep": self.timestep,
                    "motion_done": self.flag_motion_done,
                }
                return obs, extras

        # Compute motion_anchor_ori_b (relative orientation)
        robot_mat = self._matrix_from_quat(robot_quat)
        ref_anchor_mat = self._matrix_from_quat(ref_anchor_quat)
        motion_anchor_ori_b = robot_mat.T @ self.init_to_world @ ref_anchor_mat

        # Orientation observation: first two columns of rotation matrix flattened (6 dims)
        ori_obs = motion_anchor_ori_b[:, :2].flatten()

        # Build observation following FSMDeployG1 order
        # WOSE mode: ref_pos(29) + ref_vel(29) + ori(6) + ang_vel(3) + joint_pos_rel(29) + joint_vel(29) + last_action(29) = 154
        # With SE: add anchor_pos(3) + lin_vel(3) = 160
        obs_components = [
            ref_joint_pos,     # Reference joint positions (29)
            ref_joint_vel,     # Reference joint velocities (29)
        ]

        # Add anchor position if using state estimator
        if not self.without_state_estimator:
            # Placeholder for anchor position
            anchor_pos_b = np.zeros(3, dtype=np.float32)
            obs_components.append(anchor_pos_b)

        obs_components.extend([
            ori_obs,           # Motion anchor orientation (6)
        ])

        # Add linear velocity if using state estimator
        if not self.without_state_estimator:
            obs_components.append(lin_vel)  # Linear velocity (3)

        obs_components.extend([
            ang_vel,           # Angular velocity (3)
            joint_pos_rel,     # Relative joint positions (29)
            dof_vel,           # Joint velocities (29)
            self.last_action,  # Last action (29)
        ])

        obs = np.concatenate(obs_components).astype(np.float32)

        extras = {
            "timestep": self.timestep,
            "motion_done": self.flag_motion_done,
        }

        return obs, extras

    def get_action(self, obs: np.ndarray) -> np.ndarray:
        """Get action from BeyondMimic policy.

        Args:
            obs: Observation vector

        Returns:
            Scaled PD target positions
        """
        if self.session is None:
            logger.warning("No ONNX model loaded, returning zeros")
            return np.zeros(self.num_actions, dtype=np.float32)

        # Prepare ONNX inputs
        ort_inputs = {
            "obs": np.expand_dims(obs, axis=0).astype(np.float32),
            "time_step": np.expand_dims(np.array([int(self.timestep)]), axis=0).astype(np.float32),
        }

        # Run inference
        try:
            ort_outputs = self.session.run(None, ort_inputs)

            # Get actions (first output)
            actions = np.asarray(ort_outputs[0]).squeeze().astype(np.float32)

            # Apply EMA smoothing
            actions = (1 - self.action_beta) * self.last_action + self.action_beta * actions
            self.last_action = actions.copy()

            # Apply per-joint scaling
            scaled_actions = actions * self.action_scales

            # Update motion command if using motion from model
            if self.use_motion_from_model and len(ort_outputs) >= 5:
                self.command = {
                    "timestep": self.timestep,
                    "joint_pos": np.asarray(ort_outputs[1]).squeeze(),
                    "joint_vel": np.asarray(ort_outputs[2]).squeeze(),
                    "body_pos_w": np.asarray(ort_outputs[3]).squeeze(),
                    "body_quat_w": np.asarray(ort_outputs[4]).squeeze(),
                }

            return scaled_actions

        except Exception as e:
            logger.error(f"ONNX inference failed: {e}")
            return self.last_action

    def post_step_callback(self, commands: list[str] | None = None):
        """Post-step callback for timestep management.

        Args:
            commands: Optional command list
        """
        # Update timestep
        self.timestep += 1 * self.play_speed

        # Check if motion is done
        if 0 < self.max_timestep <= self.timestep:
            self.play_speed = 0.0
            self.flag_motion_done = True

        # Process commands
        for command in commands or []:
            if command == "[MOTION_RESET]":
                self.reset()
            elif command == "[MOTION_FADE_IN]":
                self.play_speed = 1.0
            elif command == "[MOTION_FADE_OUT]":
                self.play_speed = 0.0

    def get_init_dof_pos(self) -> np.ndarray:
        """Get initial DOF positions from motion (if available)."""
        if self.command and "joint_pos" in self.command:
            return self.command["joint_pos"].copy()
        return self.default_dof_pos.copy()


# Factory function
def create_beyondmimic_policy(
    model_file: str | Path,
    device: str = "cuda",
    **kwargs
) -> BeyondMimicPolicy:
    """Create BeyondMimic policy with default configuration.

    Args:
        model_file: Path to ONNX model file
        device: Device for inference
        **kwargs: Additional config overrides

    Returns:
        BeyondMimicPolicy instance
    """
    from pathlib import Path
    from genPiHub.tools import DOFConfig
    from genPiHub.envs.beyondmimic.robot_cfg import (
        G1_29DOF_BEYONDMIMIC_NAMES,
        G1_BEYONDMIMIC_DEFAULT_POS,
        G1_BEYONDMIMIC_ACTION_SCALES,
    )

    # Create DOF config
    dof_cfg = DOFConfig(
        joint_names=G1_29DOF_BEYONDMIMIC_NAMES,
        num_dofs=29,
        default_pos=G1_BEYONDMIMIC_DEFAULT_POS,
    )

    cfg = BeyondMimicPolicyConfig(
        policy_file=Path(model_file),
        device=device,
        obs_dof=dof_cfg,
        action_dof=dof_cfg,
        action_scales=G1_BEYONDMIMIC_ACTION_SCALES,
        use_model_meta_config=True,
        without_state_estimator=True,
        use_motion_from_model=True,
        **kwargs
    )

    return BeyondMimicPolicy(cfg, device)
