"""HoloMotion (Horizon Robotics) ONNX policy wrapper for genPiHub.

Loads an exported HoloMotion v1.2 checkpoint (``config.yaml`` + ``exported/*.onnx``)
and runs inference inside the genPiHub Policy protocol.

Supported task types
--------------------

``velocity_tracking``
    MLP actor, no KV cache. Observation = 8-step history of
    ``[velocity_command(4), projected_gravity(3), rel_root_angvel(3), dof_pos(29),
    dof_vel(29), last_action(29)]`` → 776-d input, 29-d action.

    Environment feeds the current base state + joystick command
    ``[vx, vy, vyaw]`` each step; wrapper maintains history and action buffers
    internally.

``motion_tracking``
    Transformer-MoE actor with a KV cache. Observation is a 522-d vector built
    from 10 current-frame terms + 5 future-frame terms (10 frames lookahead).
    Requires a reference motion (retargeted ``.npz``) to be loaded.

    **Not implemented in this wrapper yet** — the ONNX + KV-cache plumbing is
    stubbed out. Velocity tracking covers end-to-end inference in genesislab
    without motion retargeting infrastructure; motion tracking will be added
    once the motion loader / FK path is ported.

DOF ordering
------------

HoloMotion's exported ONNX uses a custom interleaved joint order
(``left_hip_pitch, right_hip_pitch, waist_yaw, left_hip_roll, ...``) that
differs from the URDF order. The wrapper maintains two permutations:

* ``urdf_to_onnx[i]`` — source index in URDF order that should be placed at
  position ``i`` of the ONNX vector. Applied to DoF-valued observations.
* ``onnx_to_urdf[i]`` — source index in ONNX order that should be placed at
  position ``i`` of the URDF vector. Applied to the scaled action before
  handing it back to the environment.

The URDF joint order is taken from ``policy_cfg.action_dof.joint_names`` if
provided by the caller; otherwise it falls back to the ONNX order (identity
mapping).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import yaml

from genPiHub.configs.policy_configs import HoloMotionPolicyConfig
from genPiHub.policies.base_policy import Policy
from genPiHub.tools import DOFConfig

from .obs_builder import HoloMotionObsBuilder, resolve_actor_atomic_obs_list
from .obs_terms import gravity_orientation_from_quat_wxyz

logger = logging.getLogger(__name__)


class HoloMotionPolicy(Policy):
    """genPiHub wrapper around a HoloMotion v1.2 ONNX checkpoint."""

    # ------------------------------------------------------------------
    # Construction / loading
    # ------------------------------------------------------------------

    def __init__(self, cfg: HoloMotionPolicyConfig, device: str = "cuda") -> None:
        self.cfg_hm: HoloMotionPolicyConfig = cfg
        self._resolve_paths()

        try:
            import onnxruntime as ort
        except ImportError as e:  # pragma: no cover — surfaced as a runtime hint
            raise ImportError(
                "onnxruntime is required for HoloMotionPolicy. "
                "Install: pip install onnxruntime-gpu"
            ) from e
        self.ort = ort

        self.train_config: Dict[str, Any] = self._load_train_config()
        self.task_type: str = self._resolve_task_type()

        # ONNX session + metadata (joint_names, default_pos, action_scale).
        self.session = self._create_session(device)
        self._load_onnx_metadata()

        # URDF <-> ONNX permutations. Must come after ONNX metadata is loaded.
        self._build_joint_permutations()

        # Populate base Policy attributes manually because we load ONNX, not a
        # PyTorch JIT module — super().__init__ expects the latter.
        self._init_from_base(cfg, device)

        # Per-term obs builder, driven by the training config's atomic_obs_list.
        self.obs_builder = HoloMotionObsBuilder(
            atomic_obs_list=resolve_actor_atomic_obs_list(
                self.train_config,
                group_name=cfg.obs_group_name,
                actor_prefix=cfg.actor_term_prefix,
            ),
            evaluator=self,
        )

        # Ephemeral state read by _get_obs_* — updated each call to
        # get_observation(). In ONNX joint order.
        self._env_dof_pos_onnx = np.zeros(self.num_actions, dtype=np.float32)
        self._env_dof_vel_onnx = np.zeros(self.num_actions, dtype=np.float32)
        self._base_quat_wxyz = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        self._base_ang_vel_body = np.zeros(3, dtype=np.float32)
        self._velocity_cmd = np.zeros(4, dtype=np.float32)  # [flag, vx, vy, vyaw]

        # Last raw (pre-scale, pre-permute) action from the policy, ONNX order.
        self._last_action_onnx = np.zeros(self.num_actions, dtype=np.float32)

        # KV cache state (motion tracking only).
        self._kv_cache: Optional[np.ndarray] = None
        self._step_idx: int = 0

        # Motion tracking not supported yet — fail loudly if someone picks it.
        if self.task_type == "motion_tracking":
            raise NotImplementedError(
                "HoloMotion motion_tracking inference requires the motion loader "
                "and reference-FK path, which are not ported yet. Use the "
                "velocity_tracking checkpoint for now, or track the TODO in "
                "docs/policies/holomotion.md."
            )

        logger.info(
            "HoloMotionPolicy loaded: task=%s, obs_dim=%d, action_dim=%d, "
            "onnx=%s",
            self.task_type,
            self.session.get_inputs()[0].shape[-1],
            self.num_actions,
            self.onnx_path,
        )

    def _resolve_paths(self) -> None:
        cfg = self.cfg_hm
        if cfg.model_dir is not None:
            mdir = Path(cfg.model_dir)
            if cfg.config_file is None:
                cfg.config_file = mdir / "config.yaml"
            if cfg.policy_file is None:
                onnxs = sorted((mdir / "exported").glob("*.onnx"))
                if not onnxs:
                    raise FileNotFoundError(
                        f"No .onnx found under {mdir / 'exported'}"
                    )
                cfg.policy_file = onnxs[0]
        if cfg.policy_file is None:
            raise ValueError("HoloMotionPolicy: model_dir or policy_file required")
        if cfg.config_file is None:
            raise ValueError("HoloMotionPolicy: config_file required (training yaml)")
        self.onnx_path = Path(cfg.policy_file)
        self.config_path = Path(cfg.config_file)

    def _load_train_config(self) -> Dict[str, Any]:
        """Load HoloMotion's training YAML with Hydra/OmegaConf interpolations resolved.

        HoloMotion's configs use ``${obs.context_length}`` style references that
        must be resolved before we can read numeric fields like ``history_length``.
        We try OmegaConf first (handles interpolation) and fall back to plain YAML
        only if OmegaConf is unavailable — in which case unresolved strings will
        surface later as ValueError, signaling the user to install omegaconf.
        """
        try:
            from omegaconf import OmegaConf

            # HoloMotion configs reference Hydra runtime resolvers like ${now:...}
            # and ${hydra:...}. Register harmless stubs so OmegaConf can finish
            # resolving the variables we actually care about (obs.context_length,
            # obs.n_fut_frames, etc.).
            for name in ("now", "hydra"):
                if not OmegaConf.has_resolver(name):
                    OmegaConf.register_new_resolver(name, lambda *args, **kwargs: "")

            cfg = OmegaConf.load(str(self.config_path))
            return OmegaConf.to_container(cfg, resolve=True)  # type: ignore[return-value]
        except ImportError:
            logger.warning(
                "omegaconf not installed; HoloMotion config interpolations will "
                "NOT be resolved. Install: pip install omegaconf"
            )
            with open(self.config_path, "r") as f:
                return yaml.unsafe_load(f) or {}

    def _resolve_task_type(self) -> str:
        cfg = self.cfg_hm
        if cfg.task_type != "auto":
            return cfg.task_type
        # Heuristic: velocity_tracking config contains actor_velocity_command.
        obs_groups = (self.train_config.get("obs") or {}).get("obs_groups") or {}
        unified = obs_groups.get(cfg.obs_group_name) or {}
        atomic = unified.get("atomic_obs_list") or []
        names = {next(iter(d.keys())) for d in atomic}
        if "actor_velocity_command" in names:
            return "velocity_tracking"
        if "actor_ref_dof_pos_cur" in names:
            return "motion_tracking"
        raise ValueError(
            "Could not infer task_type from config. Set cfg.task_type explicitly."
        )

    def _create_session(self, device: str):
        providers: List[str]
        if device == "cpu":
            providers = ["CPUExecutionProvider"]
        elif device == "cuda":
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        elif device == "tensorrt":
            providers = [
                "TensorrtExecutionProvider",
                "CUDAExecutionProvider",
                "CPUExecutionProvider",
            ]
        else:
            logger.warning("Unknown device %s, falling back to CPU", device)
            providers = ["CPUExecutionProvider"]
        return self.ort.InferenceSession(
            str(self.onnx_path),
            sess_options=self.ort.SessionOptions(),
            providers=providers,
        )

    def _load_onnx_metadata(self) -> None:
        meta = self.session.get_modelmeta().custom_metadata_map

        def parse_floats(s: str) -> np.ndarray:
            return np.array([float(x) for x in s.split(",")], dtype=np.float32)

        def parse_strings(s: str) -> List[str]:
            return [x.strip() for x in s.split(",")]

        if "joint_names" not in meta:
            raise ValueError(
                f"ONNX at {self.onnx_path} missing 'joint_names' metadata."
            )
        self.joint_names_onnx: List[str] = parse_strings(meta["joint_names"])
        self.num_actions: int = len(self.joint_names_onnx)

        self.default_angles_onnx: np.ndarray = parse_floats(meta["default_joint_pos"])
        self.joint_stiffness_onnx: np.ndarray = parse_floats(meta["joint_stiffness"])
        self.joint_damping_onnx: np.ndarray = parse_floats(meta["joint_damping"])
        self.action_scales_onnx: np.ndarray = parse_floats(meta["action_scale"])

        for name, arr in [
            ("default_joint_pos", self.default_angles_onnx),
            ("joint_stiffness", self.joint_stiffness_onnx),
            ("joint_damping", self.joint_damping_onnx),
            ("action_scale", self.action_scales_onnx),
        ]:
            if arr.shape[0] != self.num_actions:
                raise ValueError(
                    f"ONNX metadata '{name}' length {arr.shape[0]} != "
                    f"num_actions {self.num_actions}"
                )

        self.input_names = [i.name for i in self.session.get_inputs()]
        self.output_names = [o.name for o in self.session.get_outputs()]

    def _build_joint_permutations(self) -> None:
        """Build urdf<->onnx permutations against ``cfg.action_dof.joint_names``."""
        cfg = self.cfg_hm
        urdf_names: List[str] = list(cfg.action_dof.joint_names) if cfg.action_dof else []
        if not urdf_names:
            # No URDF order supplied: caller is already in ONNX order.
            self.urdf_joint_names = list(self.joint_names_onnx)
            self.urdf_to_onnx = np.arange(self.num_actions, dtype=np.int64)
            self.onnx_to_urdf = np.arange(self.num_actions, dtype=np.int64)
            return

        if len(urdf_names) != self.num_actions:
            raise ValueError(
                f"action_dof.joint_names has {len(urdf_names)} joints but ONNX "
                f"expects {self.num_actions}."
            )

        urdf_idx = {n: i for i, n in enumerate(urdf_names)}
        try:
            # urdf_to_onnx[i] = index in URDF that should be placed at ONNX pos i
            self.urdf_to_onnx = np.array(
                [urdf_idx[n] for n in self.joint_names_onnx], dtype=np.int64
            )
        except KeyError as e:
            missing = [n for n in self.joint_names_onnx if n not in urdf_idx]
            raise ValueError(
                f"URDF joint list missing ONNX joints: {missing}"
            ) from e
        onnx_idx = {n: i for i, n in enumerate(self.joint_names_onnx)}
        self.onnx_to_urdf = np.array(
            [onnx_idx[n] for n in urdf_names], dtype=np.int64
        )
        self.urdf_joint_names = urdf_names

    def _init_from_base(self, cfg: HoloMotionPolicyConfig, device: str) -> None:
        """Populate :class:`Policy` attributes without triggering torch.jit.load.

        We mirror BeyondMimicPolicy's pattern: HoloMotion ships ONNX, so we
        cannot let ``Policy.__init__`` call ``torch.jit.load``.
        """
        self.cfg = cfg
        self.device = device
        self.freq = cfg.freq
        self.dt = 1.0 / self.freq if self.freq > 0 else 0.02

        # If caller didn't populate DoF configs, synthesize from ONNX metadata
        # (URDF order == ONNX order fallback).
        def _ensure_dof_cfg(orig: DOFConfig) -> DOFConfig:
            if orig and len(orig.joint_names) == self.num_actions:
                filled = DOFConfig.from_dict(orig.to_dict())
                if len(filled.default_pos) == 0:
                    # Reorder ONNX defaults into URDF order if possible.
                    try:
                        onnx_to_urdf_defaults = np.zeros(self.num_actions, dtype=np.float32)
                        for i, name in enumerate(orig.joint_names):
                            onnx_to_urdf_defaults[i] = self.default_angles_onnx[
                                self.joint_names_onnx.index(name)
                            ]
                        filled.default_pos = onnx_to_urdf_defaults
                    except ValueError:
                        filled.default_pos = self.default_angles_onnx.copy()
                return filled
            return DOFConfig(
                joint_names=list(self.joint_names_onnx),
                num_dofs=self.num_actions,
                default_pos=self.default_angles_onnx.copy(),
                stiffness=self.joint_stiffness_onnx.copy(),
                damping=self.joint_damping_onnx.copy(),
            )

        self.cfg_obs_dof = _ensure_dof_cfg(cfg.obs_dof)
        self.cfg_action_dof = _ensure_dof_cfg(cfg.action_dof)
        # Keep the config in sync so downstream consumers see the enriched DOF.
        cfg.obs_dof = self.cfg_obs_dof
        cfg.action_dof = self.cfg_action_dof

        self.num_dofs = self.cfg_obs_dof.num_dofs
        self.default_dof_pos = np.asarray(self.cfg_obs_dof.default_pos, dtype=np.float32)
        self.default_action_pos = np.asarray(
            self.cfg_action_dof.default_pos, dtype=np.float32
        )

        self.action_scale = cfg.action_scale
        self.action_clip = cfg.action_clip
        self.action_beta = cfg.action_beta
        self.last_action = np.zeros(self.num_actions, dtype=np.float32)

        self.history_length = cfg.history_length
        self.history_obs_size = cfg.history_obs_size
        self.history_buf = None
        self.model = self.session

    # ------------------------------------------------------------------
    # Policy protocol
    # ------------------------------------------------------------------

    def reset(self) -> None:
        self._last_action_onnx.fill(0.0)
        self.last_action.fill(0.0)
        self._step_idx = 0
        self._kv_cache = None
        self.obs_builder.reset()

    def get_observation(
        self,
        env_data: Dict[str, Any],
        ctrl_data: Dict[str, Any],
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        # --- Update cached env state (convert to ONNX order where needed). ---
        dof_pos_urdf = np.asarray(
            env_data.get("dof_pos", np.zeros(self.num_actions)), dtype=np.float32
        )
        dof_vel_urdf = np.asarray(
            env_data.get("dof_vel", np.zeros(self.num_actions)), dtype=np.float32
        )
        self._env_dof_pos_onnx[:] = dof_pos_urdf[self.urdf_to_onnx]
        self._env_dof_vel_onnx[:] = dof_vel_urdf[self.urdf_to_onnx]

        base_quat = np.asarray(
            env_data.get("base_quat", np.array([1.0, 0.0, 0.0, 0.0])),
            dtype=np.float32,
        )
        # Accept [w,x,y,z] directly; if someone passes [x,y,z,w], reject early.
        if base_quat.shape != (4,):
            raise ValueError("env_data['base_quat'] must be a length-4 quaternion.")
        self._base_quat_wxyz[:] = base_quat

        self._base_ang_vel_body[:] = np.asarray(
            env_data.get("base_ang_vel", np.zeros(3)), dtype=np.float32
        )

        # --- Update velocity command (velocity_tracking only). ---
        if self.task_type == "velocity_tracking":
            cmd = ctrl_data.get("commands", None)
            if cmd is None:
                cmd = env_data.get("commands", np.zeros(3, dtype=np.float32))
            cmd = np.asarray(cmd, dtype=np.float32).reshape(-1)
            if cmd.shape[0] < 3:
                raise ValueError(
                    "velocity command must provide at least [vx, vy, vyaw]."
                )
            vx, vy, vyaw = float(cmd[0]), float(cmd[1]), float(cmd[2])
            moving = float(np.linalg.norm([vx, vy, vyaw]) > self.cfg_hm.vel_cmd_is_moving_threshold)
            self._velocity_cmd[0] = moving
            self._velocity_cmd[1] = vx
            self._velocity_cmd[2] = vy
            self._velocity_cmd[3] = vyaw

        obs = self.obs_builder.build()
        extras = {
            "task_type": self.task_type,
            "step_idx": self._step_idx,
            "velocity_command": self._velocity_cmd.copy()
            if self.task_type == "velocity_tracking"
            else None,
        }
        return obs, extras

    def get_action(self, obs: np.ndarray) -> np.ndarray:
        if self.session is None:
            raise RuntimeError("HoloMotionPolicy: ONNX session not initialized")

        obs_batched = obs.astype(np.float32).reshape(1, -1)
        inputs = {"obs": obs_batched}

        if self.task_type == "motion_tracking":
            if self._kv_cache is None:
                self._kv_cache = self._zero_kv_cache()
            inputs["past_key_values"] = self._kv_cache
            inputs["step_idx"] = np.array(
                [self._step_idx % self.cfg_hm.motion_max_ctx_len],
                dtype=np.int64,
            )

        outputs = self.session.run(self.output_names, inputs)
        out_map = dict(zip(self.output_names, outputs))

        raw_action = out_map["actions"].reshape(-1).astype(np.float32)

        if "present_key_values" in out_map:
            self._kv_cache = out_map["present_key_values"]

        # EMA smoothing on raw (pre-scale) action.
        if self.action_beta < 1.0:
            raw_action = (
                (1.0 - self.action_beta) * self._last_action_onnx
                + self.action_beta * raw_action
            )
        self._last_action_onnx[:] = raw_action

        # Clip, scale per-joint, then convert ONNX -> URDF for the env.
        if self.action_clip is not None:
            raw_action = np.clip(raw_action, -self.action_clip, self.action_clip)
        scaled_onnx = raw_action * self.action_scales_onnx
        scaled_urdf = scaled_onnx[self.onnx_to_urdf]
        self.last_action[:] = scaled_urdf
        return scaled_urdf

    def post_step_callback(self, commands: Optional[List[str]] = None) -> None:
        self._step_idx += 1
        for cmd in commands or []:
            if cmd == "[MOTION_RESET]":
                self.reset()

    def get_init_dof_pos(self) -> np.ndarray:
        """Initial standing pose in URDF order."""
        return self.default_action_pos.copy()

    # ------------------------------------------------------------------
    # _get_obs_<term> methods dispatched by HoloMotionObsBuilder.
    # All return vectors in ONNX joint order.
    # ------------------------------------------------------------------

    def _get_obs_actor_projected_gravity(self) -> np.ndarray:
        return gravity_orientation_from_quat_wxyz(self._base_quat_wxyz)

    def _get_obs_actor_rel_robot_root_ang_vel(self) -> np.ndarray:
        return self._base_ang_vel_body.copy()

    def _get_obs_actor_dof_pos(self) -> np.ndarray:
        return (self._env_dof_pos_onnx - self.default_angles_onnx).astype(np.float32)

    def _get_obs_actor_dof_vel(self) -> np.ndarray:
        return self._env_dof_vel_onnx.copy()

    def _get_obs_actor_last_action(self) -> np.ndarray:
        return self._last_action_onnx.copy()

    def _get_obs_actor_velocity_command(self) -> np.ndarray:
        return self._velocity_cmd.copy()

    # ------------------------------------------------------------------
    # Motion-tracking specific obs terms — stubbed, will be implemented
    # alongside the motion loader port. Raising here keeps the failure
    # localized instead of producing silently-wrong obs.
    # ------------------------------------------------------------------

    def _motion_tracking_not_implemented(self, term: str):
        raise NotImplementedError(
            f"HoloMotion motion_tracking obs term '{term}' requires the "
            "reference-motion loader which is not ported to genPiHub yet."
        )

    def _get_obs_actor_ref_gravity_projection_cur(self):
        self._motion_tracking_not_implemented("actor_ref_gravity_projection_cur")

    def _get_obs_actor_ref_gravity_projection_fut(self):
        self._motion_tracking_not_implemented("actor_ref_gravity_projection_fut")

    def _get_obs_actor_ref_base_linvel_cur(self):
        self._motion_tracking_not_implemented("actor_ref_base_linvel_cur")

    def _get_obs_actor_ref_base_linvel_fut(self):
        self._motion_tracking_not_implemented("actor_ref_base_linvel_fut")

    def _get_obs_actor_ref_base_angvel_cur(self):
        self._motion_tracking_not_implemented("actor_ref_base_angvel_cur")

    def _get_obs_actor_ref_base_angvel_fut(self):
        self._motion_tracking_not_implemented("actor_ref_base_angvel_fut")

    def _get_obs_actor_ref_dof_pos_cur(self):
        self._motion_tracking_not_implemented("actor_ref_dof_pos_cur")

    def _get_obs_actor_ref_dof_pos_fut(self):
        self._motion_tracking_not_implemented("actor_ref_dof_pos_fut")

    def _get_obs_actor_ref_root_height_cur(self):
        self._motion_tracking_not_implemented("actor_ref_root_height_cur")

    def _get_obs_actor_ref_root_height_fut(self):
        self._motion_tracking_not_implemented("actor_ref_root_height_fut")

    def _get_obs_actor_ref_keybody_rel_pos_cur(self):
        self._motion_tracking_not_implemented("actor_ref_keybody_rel_pos_cur")

    def _get_obs_actor_ref_keybody_rel_pos_fut(self):
        self._motion_tracking_not_implemented("actor_ref_keybody_rel_pos_fut")

    def _get_obs_actor_ref_motion_filter_cutoff_hz(self):
        # This term is a 1-d scalar in the config but only used when online
        # filtering is enabled. Returning 0.0 matches the fallback in
        # HoloMotion's deployment when motion filtering is disabled.
        return np.zeros(1, dtype=np.float32)

    def _zero_kv_cache(self) -> np.ndarray:
        """Allocate a zeroed KV cache matching the ONNX input shape."""
        kv_input = next(
            (i for i in self.session.get_inputs() if i.name == "past_key_values"),
            None,
        )
        if kv_input is None:
            raise RuntimeError(
                "ONNX model has no 'past_key_values' input but task is motion_tracking."
            )
        shape = [int(d) if isinstance(d, int) else 1 for d in kv_input.shape]
        return np.zeros(shape, dtype=np.float32)
