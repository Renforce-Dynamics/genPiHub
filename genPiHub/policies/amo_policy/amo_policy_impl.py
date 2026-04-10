"""AMO (Adaptive Motion Optimization) policy implementation.

This is the core AMO policy that loads pre-trained JIT models and runs inference.
Replicated from src/amo/policy/policy.py to achieve 100% self-containment.

Original source: RSS 2025 AMO paper implementation
"""

import torch
import numpy as np
from collections import deque
from pathlib import Path


def quat_to_euler(quat: np.ndarray) -> np.ndarray:
    """Convert quaternion [w,x,y,z] to Euler angles [roll, pitch, yaw]."""
    w, x, y, z = quat[0], quat[1], quat[2], quat[3]
    # roll
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = np.arctan2(sinr_cosp, cosr_cosp)
    # pitch
    sinp = 2 * (w * y - z * x)
    pitch = np.copysign(np.pi / 2, sinp) if np.abs(sinp) >= 1 else np.arcsin(sinp)
    # yaw
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)
    return np.array([roll, pitch, yaw])


class AMOPolicyImpl:
    """AMO policy: loads JIT models and reproduces play_amo.py inference loop.

    Args:
        model_dir: Path to directory containing amo_jit.pt, adapter_jit.pt, adapter_norm_stats.pt
        device: torch device
    """

    # G1 robot constants (from play_amo.py)
    NUM_DOFS = 23
    NUM_ACTIONS = 15  # leg DOFs only
    DOF_NAMES = [
        "left_hip_pitch", "left_hip_roll", "left_hip_yaw", "left_knee", "left_ankle_pitch", "left_ankle_roll",
        "right_hip_pitch", "right_hip_roll", "right_hip_yaw", "right_knee", "right_ankle_pitch", "right_ankle_roll",
        "waist_yaw", "waist_roll", "waist_pitch",
        "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
        "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
    ]
    DEFAULT_DOF_POS = np.array([
        -0.1, 0.0, 0.0, 0.3, -0.2, 0.0,
        -0.1, 0.0, 0.0, 0.3, -0.2, 0.0,
        0.0, 0.0, 0.0,
        0.5, 0.0, 0.2, 0.3,
        0.5, 0.0, -0.2, 0.3,
    ], dtype=np.float32)
    STIFFNESS = np.array([
        150, 150, 150, 300, 80, 20,
        150, 150, 150, 300, 80, 20,
        400, 400, 400,
        80, 80, 40, 60,
        80, 80, 40, 60,
    ], dtype=np.float32)
    DAMPING = np.array([
        2, 2, 2, 4, 2, 1,
        2, 2, 2, 4, 2, 1,
        15, 15, 15,
        2, 2, 1, 1,
        2, 2, 1, 1,
    ], dtype=np.float32)
    TORQUE_LIMITS = np.array([
        88, 139, 88, 139, 50, 50,
        88, 139, 88, 139, 50, 50,
        88, 50, 50,
        25, 25, 25, 25,
        25, 25, 25, 25,
    ], dtype=np.float32)

    # Observation dimensions: 3 + 2 + 2 + 23*3 + 2 + 15 = 93
    N_PROPRIO = 93
    N_PRIV = 3
    N_DEMO_DOF = 8
    N_DEMO = 17  # 8 + 3 + 3 + 3
    HISTORY_LEN = 10
    EXTRA_HISTORY_LEN = 25

    def __init__(
        self,
        model_dir: str | Path,
        device: str = "cuda",
        policy_filename: str = "amo_jit.pt",
        adapter_filename: str = "adapter_jit.pt",
        norm_stats_filename: str = "adapter_norm_stats.pt",
        action_scale: float = 0.25,
        scales_ang_vel: float = 0.25,
        scales_dof_vel: float = 0.05,
        gait_freq: float = 1.3,
    ):
        self.device = device
        model_dir = Path(model_dir)

        # Load JIT models
        self.policy_jit = torch.jit.load(str(model_dir / policy_filename), map_location=device)
        self.policy_jit.eval()

        self.adapter = torch.jit.load(str(model_dir / adapter_filename), map_location=device)
        self.adapter.eval()
        for p in self.adapter.parameters():
            p.requires_grad = False

        # Load adapter normalization stats
        # Note: weights_only=False is safe here because we trust the AMO source
        norm_stats = torch.load(
            str(model_dir / norm_stats_filename), map_location=device, weights_only=False
        )
        # Convert numpy arrays to torch tensors if needed
        self.input_mean = torch.as_tensor(norm_stats["input_mean"], dtype=torch.float32, device=device)
        self.input_std = torch.as_tensor(norm_stats["input_std"], dtype=torch.float32, device=device)
        self.output_mean = torch.as_tensor(norm_stats["output_mean"], dtype=torch.float32, device=device)
        self.output_std = torch.as_tensor(norm_stats["output_std"], dtype=torch.float32, device=device)

        # Hyperparameters
        self.action_scale = action_scale
        self.scales_ang_vel = scales_ang_vel
        self.scales_dof_vel = scales_dof_vel
        self.gait_freq = gait_freq

        # Mutable state — call reset() before first use
        self.reset()

    def reset(self):
        """Reset all internal state (history buffers, gait, actions)."""
        self.proprio_history = deque(
            [np.zeros(self.N_PROPRIO, dtype=np.float32) for _ in range(self.HISTORY_LEN)],
            maxlen=self.HISTORY_LEN,
        )
        self.extra_history = deque(
            [np.zeros(self.N_PROPRIO, dtype=np.float32) for _ in range(self.EXTRA_HISTORY_LEN)],
            maxlen=self.EXTRA_HISTORY_LEN,
        )
        self.last_action = np.zeros(self.NUM_DOFS, dtype=np.float32)
        self.gait_cycle = np.array([0.25, 0.25])
        self.target_yaw = 0.0
        self._in_place_stand = True

        # Arm blending state
        self.arm_action = self.DEFAULT_DOF_POS[15:].copy()
        self.prev_arm_action = self.DEFAULT_DOF_POS[15:].copy()
        self.arm_blend = 0.0

        # Demo obs template
        self._demo_template = np.zeros(self.N_DEMO, dtype=np.float32)
        self._demo_template[:self.N_DEMO_DOF] = self.DEFAULT_DOF_POS[15:]
        self._demo_template[self.N_DEMO_DOF + 6 : self.N_DEMO_DOF + 9] = 0.75

    @torch.no_grad()
    def act(
        self,
        dof_pos: np.ndarray,
        dof_vel: np.ndarray,
        quat: np.ndarray,
        ang_vel: np.ndarray,
        commands: np.ndarray,
        dt: float = 0.02,
    ) -> np.ndarray:
        """Run one policy step: observation assembly → adapter → policy → action.

        Args:
            dof_pos: Joint positions (23,)
            dof_vel: Joint velocities (23,)
            quat: Base orientation quaternion [w,x,y,z] (4,)
            ang_vel: Base angular velocity in body frame (3,)
            commands: [vx, yaw_rate, vy, height, torso_yaw, torso_pitch, torso_roll, arm_enable] (8,)
            dt: Control timestep (default 0.02s = 50Hz)

        Returns:
            pd_target: Joint position targets for PD controller (23,)
        """
        # --- Observation assembly (mirrors play_amo.py get_observation) ---
        rpy = quat_to_euler(quat)

        self.target_yaw = commands[1]
        dyaw = rpy[2] - self.target_yaw
        dyaw = np.remainder(dyaw + np.pi, 2 * np.pi) - np.pi
        if self._in_place_stand:
            dyaw = 0.0

        obs_dof_vel = dof_vel.copy()
        obs_dof_vel[[4, 5, 10, 11, 13, 14]] = 0.0

        gait_obs = np.sin(self.gait_cycle * 2 * np.pi)

        # Adapter: input = [height, torso_yaw, torso_pitch, torso_roll, arm_joints(8)]
        adapter_in = np.concatenate([np.zeros(4), dof_pos[15:]]).astype(np.float32)
        adapter_in[0] = 0.75 + commands[3]
        adapter_in[1] = commands[4]
        adapter_in[2] = commands[5]
        adapter_in[3] = commands[6]

        adapter_tensor = torch.tensor(adapter_in, device=self.device, dtype=torch.float32).unsqueeze(0)
        adapter_tensor = (adapter_tensor - self.input_mean) / (self.input_std + 1e-8)
        adapter_out = self.adapter(adapter_tensor)
        adapter_out = adapter_out * self.output_std + self.output_mean
        adapter_np = adapter_out.cpu().numpy().squeeze()

        # Proprioceptive observation (93-dim)
        obs_prop = np.concatenate([
            ang_vel * self.scales_ang_vel,                      # 3
            rpy[:2],                                            # 2
            [np.sin(dyaw), np.cos(dyaw)],                      # 2
            dof_pos - self.DEFAULT_DOF_POS,                     # 23
            obs_dof_vel * self.scales_dof_vel,                  # 23
            self.last_action,                                   # 23
            gait_obs,                                           # 2
            adapter_np,                                         # 15
        ]).astype(np.float32)

        # Demo observation (17-dim)
        obs_demo = self._demo_template.copy()
        obs_demo[:self.N_DEMO_DOF] = dof_pos[15:]
        obs_demo[self.N_DEMO_DOF] = commands[0]       # vx
        obs_demo[self.N_DEMO_DOF + 1] = commands[2]   # vy
        self._in_place_stand = np.abs(commands[0]) < 0.1
        obs_demo[self.N_DEMO_DOF + 3] = commands[4]   # torso_yaw
        obs_demo[self.N_DEMO_DOF + 4] = commands[5]   # torso_pitch
        obs_demo[self.N_DEMO_DOF + 5] = commands[6]   # torso_roll
        obs_demo[self.N_DEMO_DOF + 6 : self.N_DEMO_DOF + 9] = 0.75 + commands[3]

        obs_priv = np.zeros(self.N_PRIV, dtype=np.float32)

        # Update history
        self.proprio_history.append(obs_prop)
        self.extra_history.append(obs_prop)

        obs_hist = np.array(self.proprio_history).flatten()

        # Main observation for policy
        obs = np.concatenate([obs_prop, obs_demo, obs_priv, obs_hist])
        obs_tensor = torch.from_numpy(obs).float().unsqueeze(0).to(self.device)

        extra_hist = torch.tensor(
            np.array(self.extra_history).flatten().copy(), dtype=torch.float32
        ).unsqueeze(0).to(self.device)

        # --- Policy inference ---
        raw_action = self.policy_jit(obs_tensor, extra_hist).cpu().numpy().squeeze()
        raw_action = np.clip(raw_action, -40.0, 40.0)

        # Update last_action: [15 leg actions, 8 arm relative positions]
        self.last_action = np.concatenate([
            raw_action.copy(),
            (dof_pos[15:] - self.DEFAULT_DOF_POS[15:]) / self.action_scale,
        ])

        # Compute PD targets
        scaled = raw_action * self.action_scale
        pd_target = np.concatenate([scaled, np.zeros(8)]) + self.DEFAULT_DOF_POS

        # Arm blending
        pd_target[15:] = (1 - self.arm_blend) * self.prev_arm_action + self.arm_blend * self.arm_action
        self.arm_blend = min(1.0, self.arm_blend + 0.01)

        # Gait cycle update
        self.gait_cycle = np.remainder(self.gait_cycle + dt * self.gait_freq, 1.0)
        if self._in_place_stand and (
            np.abs(self.gait_cycle[0] - 0.25) < 0.05 or np.abs(self.gait_cycle[1] - 0.25) < 0.05
        ):
            self.gait_cycle = np.array([0.25, 0.25])
        if (not self._in_place_stand) and (
            np.abs(self.gait_cycle[0] - 0.25) < 0.05 and np.abs(self.gait_cycle[1] - 0.25) < 0.05
        ):
            self.gait_cycle = np.array([0.25, 0.75])

        return pd_target

    def compute_torques(self, pd_target: np.ndarray, dof_pos: np.ndarray, dof_vel: np.ndarray) -> np.ndarray:
        """Compute PD torques (for simulators that don't have built-in PD).

        Args:
            pd_target: Target joint positions (23,)
            dof_pos: Current joint positions (23,)
            dof_vel: Current joint velocities (23,)

        Returns:
            torques: Clipped joint torques (23,)
        """
        torque = (pd_target - dof_pos) * self.STIFFNESS - dof_vel * self.DAMPING
        return np.clip(torque, -self.TORQUE_LIMITS, self.TORQUE_LIMITS)
