#!/usr/bin/env python3
"""Run AMO policy with MuJoCo viewer using Policy Hub framework.

This script demonstrates using AMO through Policy Hub with MuJoCo backend.
Unlike the GenesisLab version, this directly uses MuJoCo + mujoco_viewer
for visualization and simulation.

✅ Policy Hub Integration:
   - AMOPolicy via load_policy()
   - CommandState/TerminalController via genPiHub.tools
   - Unified state management
   - Keyboard control support

🎮 Keyboard Controls:
   W/S: Forward/backward velocity (vx)
   A/D: Yaw rate left/right
   Q/E: Lateral velocity (vy) left/right
   Z/X: Height adjustment
   J/U: Torso yaw
   K/I: Torso pitch
   L/O: Torso roll
   T: Toggle arm control
   ESC: Quit

Usage:
    # Interactive mode (default)
    python scripts/amo/mujoco/play_amo.py

    # Custom commands
    python scripts/amo/mujoco/play_amo.py --vx 0.4 --yaw-rate 0.2

    # Specify model directory
    python scripts/amo/mujoco/play_amo.py --model-dir data/AMO
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
import argparse
import time

import numpy as np
import torch
import mujoco
import mujoco_viewer
import glfw

# Import from Policy Hub
from genPiHub import load_policy
from genPiHub.configs import AMOPolicyConfig
from genPiHub.tools import DOFConfig


def quat_to_euler(quat: np.ndarray) -> np.ndarray:
    """Convert quaternion to Euler angles (roll, pitch, yaw).

    Args:
        quat: Quaternion [w, x, y, z]

    Returns:
        Euler angles [roll, pitch, yaw]
    """
    euler = np.zeros(3)
    qw, qx, qy, qz = quat

    # Roll (x-axis)
    sinr_cosp = 2 * (qw * qx + qy * qz)
    cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
    euler[0] = np.arctan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis)
    sinp = 2 * (qw * qy - qz * qx)
    if np.abs(sinp) >= 1:
        euler[1] = np.copysign(np.pi / 2, sinp)
    else:
        euler[1] = np.arcsin(sinp)

    # Yaw (z-axis)
    siny_cosp = 2 * (qw * qz + qx * qy)
    cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
    euler[2] = np.arctan2(siny_cosp, cosy_cosp)

    return euler


def _key_callback(self, window, key, scancode, action, mods):
    """Keyboard callback for interactive control."""
    if action != glfw.PRESS:
        return

    if key == glfw.KEY_S:
        self.commands[0] -= 0.05
    elif key == glfw.KEY_W:
        self.commands[0] += 0.05
    elif key == glfw.KEY_A:
        self.commands[1] += 0.1
    elif key == glfw.KEY_D:
        self.commands[1] -= 0.1
    elif key == glfw.KEY_Q:
        self.commands[2] += 0.05
    elif key == glfw.KEY_E:
        self.commands[2] -= 0.05
    elif key == glfw.KEY_Z:
        self.commands[3] += 0.05
    elif key == glfw.KEY_X:
        self.commands[3] -= 0.05
    elif key == glfw.KEY_J:
        self.commands[4] += 0.1
    elif key == glfw.KEY_U:
        self.commands[4] -= 0.1
    elif key == glfw.KEY_K:
        self.commands[5] += 0.05
    elif key == glfw.KEY_I:
        self.commands[5] -= 0.05
    elif key == glfw.KEY_L:
        self.commands[6] += 0.05
    elif key == glfw.KEY_O:
        self.commands[6] -= 0.1
    elif key == glfw.KEY_T:
        self.commands[7] = not self.commands[7]
        print("Toggled arm control", "ON" if self.commands[7] else "OFF")
    elif key == glfw.KEY_ESCAPE:
        print("\nQuitting...")
        glfw.set_window_should_close(self.window, True)
        return

    print(
        f"vx: {self.commands[0]:<8.2f}"
        f"vy: {self.commands[2]:<8.2f}"
        f"yaw: {self.commands[1]:<8.2f}"
        f"height: {(0.75 + self.commands[3]):<8.2f}"
        f"torso yaw: {self.commands[4]:<8.2f}"
        f"torso pitch: {self.commands[5]:<8.2f}"
        f"torso roll: {self.commands[6]:<8.2f}"
    )


class MuJoCoG1Env:
    """MuJoCo environment wrapper for Unitree G1 with AMO policy.

    This class manages the MuJoCo simulation and provides state data
    in a format compatible with Policy Hub's AMOPolicy.
    """

    def __init__(
        self,
        model_path: str | Path = "g1.xml",
        sim_dt: float = 0.002,
        control_decimation: int = 10,
        viewer: bool = True,
        device: str = "cuda",
    ):
        """Initialize MuJoCo G1 environment.

        Args:
            model_path: Path to G1 MJCF file
            sim_dt: Simulation timestep
            control_decimation: Control decimation factor
            viewer: Enable viewer
            device: Device for policy
        """
        self.device = device
        self.sim_dt = sim_dt
        self.control_decimation = control_decimation
        self.control_dt = sim_dt * control_decimation

        # G1 robot parameters
        self.num_dofs = 23
        self.num_actions = 15  # Lower body control only

        # PD controller gains
        self.stiffness = np.array([
            150, 150, 150, 300, 80, 20,  # left leg
            150, 150, 150, 300, 80, 20,  # right leg
            400, 400, 400,                # waist
            80, 80, 40, 60,               # left arm
            80, 80, 40, 60,               # right arm
        ])

        self.damping = np.array([
            2, 2, 2, 4, 2, 1,
            2, 2, 2, 4, 2, 1,
            15, 15, 15,
            2, 2, 1, 1,
            2, 2, 1, 1,
        ])

        self.default_dof_pos = np.array([
            -0.1, 0.0, 0.0, 0.3, -0.2, 0.0,  # left leg
            -0.1, 0.0, 0.0, 0.3, -0.2, 0.0,  # right leg
            0.0, 0.0, 0.0,                    # waist
            0.5, 0.0, 0.2, 0.3,              # left arm
            0.5, 0.0, -0.2, 0.3,             # right arm
        ])

        self.torque_limits = np.array([
            88, 139, 88, 139, 50, 50,
            88, 139, 88, 139, 50, 50,
            88, 50, 50,
            25, 25, 25, 25,
            25, 25, 25, 25,
        ])

        # Arm control parameters
        self.arm_dof_lower = -0.4 * np.ones(8)
        self.arm_dof_upper = 0.4 * np.ones(8)
        self.arm_action = self.default_dof_pos[15:].copy()
        self.prev_arm_action = self.default_dof_pos[15:].copy()
        self.arm_blend = 0.0
        self.toggle_arm = False

        # Load MuJoCo model
        model_path = Path(model_path)
        if not model_path.exists():
            # Try in .reference/AMO
            alt_path = Path(".reference/AMO") / model_path
            if alt_path.exists():
                model_path = alt_path
            else:
                raise FileNotFoundError(f"Model file not found: {model_path}")

        print(f"Loading MuJoCo model: {model_path}")
        self.model = mujoco.MjModel.from_xml_path(str(model_path))
        self.model.opt.timestep = sim_dt
        self.data = mujoco.MjData(self.model)

        # Reset to default keyframe
        mujoco.mj_resetDataKeyframe(self.model, self.data, 0)
        mujoco.mj_step(self.model, self.data)

        # Setup viewer if requested
        self.viewer_enabled = viewer
        if viewer:
            self.viewer = mujoco_viewer.MujocoViewer(self.model, self.data)
            self.viewer.commands = np.zeros(8, dtype=np.float32)
            self.viewer.cam.distance = 2.5
            self.viewer.cam.elevation = 0.0

            # Bind keyboard callback
            self.viewer._key_callback = types.MethodType(_key_callback, self.viewer)
            glfw.set_key_callback(self.viewer.window, self.viewer._key_callback)
        else:
            self.viewer = None

        self.step_count = 0

    def get_state(self) -> dict:
        """Get current state in Policy Hub format.

        Returns:
            State dict with:
                - dof_pos: Joint positions [23]
                - dof_vel: Joint velocities [23]
                - base_quat: Base orientation quaternion [4]
                - base_ang_vel: Base angular velocity [3]
                - commands: User commands [8]
        """
        dof_pos = self.data.qpos[-self.num_dofs:].astype(np.float32)
        dof_vel = self.data.qvel[-self.num_dofs:].astype(np.float32)
        base_quat = self.data.sensor('orientation').data.astype(np.float32)
        base_ang_vel = self.data.sensor('angular-velocity').data.astype(np.float32)

        # Get commands from viewer if available
        if self.viewer is not None:
            commands = self.viewer.commands.copy()
        else:
            commands = np.zeros(8, dtype=np.float32)

        return {
            "dof_pos": dof_pos,
            "dof_vel": dof_vel,
            "base_quat": base_quat,
            "base_ang_vel": base_ang_vel,
            "commands": commands,
        }

    def step(self, action: np.ndarray):
        """Step simulation with action.

        Args:
            action: Action from policy (normalized joint targets for lower body)
        """
        # Handle arm control
        if self.viewer is not None and self.step_count % 300 == 0 and self.step_count > 0:
            if self.viewer.commands[7]:  # Arm control enabled
                self.arm_blend = 0
                self.prev_arm_action = self.data.qpos[-self.num_dofs:][15:].copy()
                self.arm_action = np.random.uniform(
                    0, 1, 8
                ) * (self.arm_dof_upper - self.arm_dof_lower) + self.arm_dof_lower
                self.toggle_arm = True
            elif self.toggle_arm:
                self.toggle_arm = False
                self.arm_blend = 0
                self.prev_arm_action = self.data.qpos[-self.num_dofs:][15:].copy()
                self.arm_action = self.default_dof_pos[15:]

        # Compute PD targets (lower body from policy, arms from controller)
        pd_target = np.zeros(self.num_dofs)
        pd_target[:15] = action[:15]  # Policy controls lower body
        pd_target[15:] = (1 - self.arm_blend) * self.prev_arm_action + self.arm_blend * self.arm_action
        self.arm_blend = min(1.0, self.arm_blend + 0.01)

        # Get current state
        dof_pos = self.data.qpos[-self.num_dofs:]
        dof_vel = self.data.qvel[-self.num_dofs:]

        # PD control
        torque = (pd_target - dof_pos) * self.stiffness - dof_vel * self.damping
        torque = np.clip(torque, -self.torque_limits, self.torque_limits)

        # Apply torque and step
        self.data.ctrl[:] = torque
        mujoco.mj_step(self.model, self.data)

        self.step_count += 1

    def render(self):
        """Render viewer if enabled."""
        if self.viewer is not None:
            # Update camera to follow robot
            self.viewer.cam.lookat = self.data.qpos[:3]
            self.viewer.render()

            # Check if window should close
            if glfw.window_should_close(self.viewer.window):
                return False
        return True

    def close(self):
        """Close viewer."""
        if self.viewer is not None:
            self.viewer.close()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Play AMO policy with MuJoCo viewer via Policy Hub"
    )

    # Environment
    parser.add_argument("--model-xml", type=str, default="g1.xml", help="MuJoCo model XML file")
    parser.add_argument("--device", type=str, default=None, choices=["cpu", "cuda"])
    parser.add_argument("--no-viewer", action="store_true", help="Disable viewer")
    parser.add_argument("--max-steps", type=int, default=100000)

    # Policy
    parser.add_argument("--model-dir", type=str, default="data/AMO", help="AMO model directory")
    parser.add_argument("--action-scale", type=float, default=0.25)

    # Initial commands (can be changed with keyboard)
    parser.add_argument("--vx", type=float, default=0.0, help="Forward velocity (m/s)")
    parser.add_argument("--vy", type=float, default=0.0, help="Lateral velocity (m/s)")
    parser.add_argument("--yaw-rate", type=float, default=0.0, help="Yaw rate (rad/s)")
    parser.add_argument("--height", type=float, default=0.0, help="Height adjustment")

    # Control
    parser.add_argument("--print-every", type=int, default=100)

    return parser.parse_args()


def create_amo_policy_config(args) -> AMOPolicyConfig:
    """Create AMO policy configuration.

    Args:
        args: Command line arguments

    Returns:
        AMOPolicyConfig instance
    """
    model_dir = Path(args.model_dir)

    # AMO DOF configuration (23 DOF G1)
    amo_dof_names = [
        "left_hip_pitch", "left_hip_roll", "left_hip_yaw",
        "left_knee", "left_ankle_pitch", "left_ankle_roll",
        "right_hip_pitch", "right_hip_roll", "right_hip_yaw",
        "right_knee", "right_ankle_pitch", "right_ankle_roll",
        "waist_yaw", "waist_roll", "waist_pitch",
        "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
        "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
    ]

    amo_default_pos = [
        -0.1, 0., 0., 0.3, -0.2, 0.,  # left leg
        -0.1, 0., 0., 0.3, -0.2, 0.,  # right leg
        0., 0., 0.,                    # waist
        0.5, 0., 0.2, 0.3,            # left arm
        0.5, 0., -0.2, 0.3,           # right arm
    ]

    dof_cfg = DOFConfig(
        joint_names=amo_dof_names,
        num_dofs=23,
        default_pos=amo_default_pos,
    )

    return AMOPolicyConfig(
        name="AMOPolicy",
        policy_file=model_dir / "amo_jit.pt",
        adapter_file=model_dir / "adapter_jit.pt",
        norm_stats_file=model_dir / "adapter_norm_stats.pt",
        device=args.device or ("cuda" if torch.cuda.is_available() else "cpu"),
        obs_dof=dof_cfg,
        action_dof=dof_cfg,
        action_scale=args.action_scale,
        freq=50.0,  # 50 Hz control
    )


def main() -> int:
    """Main entry point."""
    args = parse_args()

    print("=" * 60)
    print("AMO Policy with MuJoCo via Policy Hub")
    print("=" * 60)

    # Determine device
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # Create policy configuration
    print("\n[1] Creating AMO policy configuration...")
    policy_config = create_amo_policy_config(args)
    print(f"✅ Policy config created: {policy_config.obs_dof.num_dofs} DOFs")

    # Load AMO policy
    print("\n[2] Loading AMO policy via Policy Hub...")
    policy_kwargs = {k: v for k, v in policy_config.__dict__.items() if k != 'name'}
    policy = load_policy("AMOPolicy", **policy_kwargs)
    print(f"✅ Policy loaded: {policy.cfg.name}")
    print(f"   - Device: {policy.device}")
    print(f"   - Control frequency: {policy.freq} Hz")
    print(f"   - Action scale: {policy.action_scale}")

    # Create MuJoCo environment
    print("\n[3] Creating MuJoCo environment...")
    env = MuJoCoG1Env(
        model_path=args.model_xml,
        sim_dt=0.002,
        control_decimation=10,
        viewer=not args.no_viewer,
        device=device,
    )
    print(f"✅ Environment created: {env.num_dofs} DOFs")

    # Initialize commands if provided
    if not args.no_viewer and env.viewer is not None:
        env.viewer.commands[0] = args.vx
        env.viewer.commands[1] = args.yaw_rate
        env.viewer.commands[2] = args.vy
        env.viewer.commands[3] = args.height

    # Reset policy
    print("\n[4] Resetting policy...")
    policy.reset()
    print("✅ Ready to run")

    # Main loop
    print(f"\n[5] Running for {args.max_steps} steps...")
    if not args.no_viewer:
        print("   Use keyboard to control (W/S/A/D/Q/E/Z/X, ESC to quit)")
        print("   See script header for full control reference\n")

    try:
        t0 = time.time()
        for step in range(args.max_steps):
            # Get state from environment
            env_data = env.get_state()

            # Get action from policy (every control_decimation steps)
            if step % env.control_decimation == 0:
                obs, extras = policy.get_observation(env_data, {})
                action = policy.get_action(obs)

                # Convert action to PD targets
                pd_target = action * policy.action_scale + env.default_dof_pos

            # Step environment
            env.step(pd_target)

            # Render
            if not env.render():
                break

            # Print status
            if step % args.print_every == 0:
                base_pos = env.data.qpos[:3]
                fps = (step + 1) / max(1e-6, time.time() - t0)
                commands = env_data["commands"]
                print(
                    f"step={step:06d} fps={fps:6.1f} "
                    f"pos=[{base_pos[0]:6.2f}, {base_pos[1]:6.2f}, {base_pos[2]:5.3f}] "
                    f"cmd=[vx={commands[0]:.2f}, vy={commands[2]:.2f}, yaw={commands[1]:.2f}]"
                )

            # Post-step callback
            policy.post_step_callback()

    except KeyboardInterrupt:
        print("\n✅ Interrupted by user")
    finally:
        env.close()

    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
