#!/usr/bin/env python3
"""Run BeyondMimic policy with MuJoCo backend.

Uses Policy Hub framework with MuJoCo environment for verification.
This script helps verify the ONNX model works correctly before debugging Genesis.

Usage:
    python scripts/beyondmimic/mujoco/play_beyondmimic.py \
        --model-file path/to/Dance_wose.onnx \
        --mjcf-file data/beyondmimic/g1_29dof_rev_1_0.xml
"""

import argparse
import time
import numpy as np
from pathlib import Path

import mujoco
import mujoco.viewer

from genPiHub import load_policy
from genPiHub.configs import BeyondMimicPolicyConfig
from genPiHub.tools import DOFConfig
from genPiHub.envs.beyondmimic.genesislab.robot_cfg import (
    G1_29DOF_BEYONDMIMIC_NAMES,
    G1_BEYONDMIMIC_DEFAULT_POS,
    G1_BEYONDMIMIC_ACTION_SCALES,
    G1_BEYONDMIMIC_STIFFNESS,
    G1_BEYONDMIMIC_DAMPING,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Play BeyondMimic with MuJoCo")
    parser.add_argument(
        "--model-file",
        type=str,
        required=True,
        help="Path to ONNX model file"
    )
    parser.add_argument(
        "--mjcf-file",
        type=str,
        default=".reference/RoboJuDo/assets/robots/g1/g1_29dof_rev_1_0.xml",
        help="Path to MJCF file"
    )
    parser.add_argument("--max-steps", type=int, default=100000)
    parser.add_argument("--print-every", type=int, default=100)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--without-state-estimator",
        action="store_true",
        help="Use WOSE mode"
    )
    parser.add_argument("--play-speed", type=float, default=1.0)
    parser.add_argument("--max-timestep", type=int, default=0)
    parser.add_argument("--loop", action="store_true")

    return parser.parse_args()


class MuJoCoEnv:
    """Simple MuJoCo environment wrapper for BeyondMimic."""

    def __init__(self, mjcf_path: str, sim_dt: float = 0.001, decimation: int = 20):
        self.model = mujoco.MjModel.from_xml_path(mjcf_path)
        self.data = mujoco.MjData(self.model)

        self.model.opt.timestep = sim_dt
        self.sim_decimation = decimation

        # Get joint info
        self.joint_names = []
        self.joint_ids = []
        for i in range(self.model.njnt):
            joint_name = self.model.joint(i).name
            if joint_name and joint_name != "root":  # Skip root joint
                self.joint_names.append(joint_name)
                # Get DOF index for this joint
                jnt_dofadr = self.model.jnt_dofadr[i]
                self.joint_ids.append(jnt_dofadr)

        print(f"Found {len(self.joint_names)} joints in MJCF")

        # Create mapping from BeyondMimic order to MuJoCo DOF indices
        self.policy_to_dof_idx = []
        for name in G1_29DOF_BEYONDMIMIC_NAMES:
            if name in self.joint_names:
                idx = self.joint_names.index(name)
                self.policy_to_dof_idx.append(self.joint_ids[idx])
            else:
                print(f"Warning: Joint {name} not found in MJCF")
                self.policy_to_dof_idx.append(-1)

        # Create mapping to actuator indices (assuming 1:1 with joints)
        self.policy_to_actuator_idx = []
        for name in G1_29DOF_BEYONDMIMIC_NAMES:
            # Find actuator with matching name
            act_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
            self.policy_to_actuator_idx.append(act_id)

        self.num_dofs = len(self.policy_to_dof_idx)

        # PD controller parameters (will be set later)
        self.stiffness = np.ones(self.num_dofs) * 40.0
        self.damping = np.ones(self.num_dofs) * 2.0
        self.torque_limits = np.ones(self.num_dofs) * 300.0

    def set_pd_gains(self, stiffness: np.ndarray, damping: np.ndarray, effort_limits: np.ndarray):
        """Set PD controller gains.

        Args:
            stiffness: Stiffness gains (29 DOF)
            damping: Damping gains (29 DOF)
            effort_limits: Torque limits (29 DOF)
        """
        self.stiffness = stiffness.copy()
        self.damping = damping.copy()
        self.torque_limits = effort_limits.copy()

    def reset(self):
        """Reset simulation."""
        mujoco.mj_resetData(self.model, self.data)

        # Set initial joint positions
        for i, name in enumerate(G1_29DOF_BEYONDMIMIC_NAMES):
            if self.policy_to_dof_idx[i] >= 0:
                self.data.qpos[self.policy_to_dof_idx[i]] = G1_BEYONDMIMIC_DEFAULT_POS[i]

        # Forward kinematics
        mujoco.mj_forward(self.model, self.data)

    def step(self, pd_target: np.ndarray):
        """Apply PD control and step simulation.

        Args:
            pd_target: Joint position targets in BeyondMimic order (29 DOF)
        """
        # PD control loop (same as RoboJuDo)
        for _ in range(self.sim_decimation):
            # Get current joint states
            dof_pos = np.zeros(self.num_dofs)
            dof_vel = np.zeros(self.num_dofs)
            for i in range(self.num_dofs):
                if self.policy_to_dof_idx[i] >= 0:
                    dof_pos[i] = self.data.qpos[self.policy_to_dof_idx[i]]
                    dof_vel[i] = self.data.qvel[self.policy_to_dof_idx[i]]

            # Compute PD torques
            torque = (pd_target - dof_pos) * self.stiffness - dof_vel * self.damping
            torque = np.clip(torque, -self.torque_limits, self.torque_limits)

            # Apply torques to actuators
            for i in range(self.num_dofs):
                if self.policy_to_actuator_idx[i] >= 0:
                    self.data.ctrl[self.policy_to_actuator_idx[i]] = torque[i]

            # Step simulation
            mujoco.mj_step(self.model, self.data)

    def get_data(self):
        """Get current state in Policy Hub format."""
        # Get joint positions and velocities in BeyondMimic order
        dof_pos = np.zeros(self.num_dofs, dtype=np.float32)
        dof_vel = np.zeros(self.num_dofs, dtype=np.float32)

        for i in range(self.num_dofs):
            if self.policy_to_dof_idx[i] >= 0:
                dof_pos[i] = self.data.qpos[self.policy_to_dof_idx[i]]
                dof_vel[i] = self.data.qvel[self.policy_to_dof_idx[i]]

        # Get base state (pelvis/root body)
        # Find pelvis body
        pelvis_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "pelvis")
        if pelvis_id < 0:
            pelvis_id = 1  # Fallback to first body after world

        base_pos = self.data.xpos[pelvis_id].copy()
        base_quat = self.data.xquat[pelvis_id].copy()  # MuJoCo uses [w,x,y,z]

        # Get velocities from root free joint (these are in WORLD frame)
        lin_vel_w = self.data.qvel[:3].copy()   # World frame
        ang_vel_w = self.data.qvel[3:6].copy()  # World frame

        # Convert linear velocity to BODY frame (like RoboJuDo)
        base_lin_vel = self._quat_rotate_inverse(base_quat, lin_vel_w)

        # Angular velocity stays in WORLD frame (RoboJuDo doesn't convert it!)
        base_ang_vel = ang_vel_w

        return {
            "dof_pos": dof_pos,
            "dof_vel": dof_vel,
            "base_pos": base_pos,
            "base_quat": base_quat,
            "base_lin_vel": base_lin_vel,
            "base_ang_vel": base_ang_vel,
        }

    @staticmethod
    def _quat_rotate_inverse(quat: np.ndarray, vec: np.ndarray) -> np.ndarray:
        """Rotate vector by inverse quaternion.

        Args:
            quat: Quaternion [w, x, y, z]
            vec: Vector to rotate [x, y, z]

        Returns:
            Rotated vector
        """
        from scipy.spatial.transform import Rotation as R
        # scipy expects [x, y, z, w]
        quat_xyzw = np.array([quat[1], quat[2], quat[3], quat[0]])
        rot = R.from_quat(quat_xyzw)
        return rot.inv().apply(vec).astype(np.float32)


def main():
    args = parse_args()

    print("=" * 80)
    print("BeyondMimic Policy with MuJoCo Backend")
    print("=" * 80)

    # Check ONNX Runtime
    try:
        import onnxruntime as ort
        print(f"✅ ONNX Runtime: {ort.__version__}")
    except ImportError:
        print("❌ ONNX Runtime not available!")
        return 1

    # Load policy
    print("\n[1] Loading BeyondMimic policy...")
    model_file = Path(args.model_file)
    if not model_file.exists():
        print(f"❌ Model file not found: {model_file}")
        return 1

    dof_cfg = DOFConfig(
        joint_names=G1_29DOF_BEYONDMIMIC_NAMES,
        num_dofs=29,
        default_pos=G1_BEYONDMIMIC_DEFAULT_POS,
    )

    # Auto-detect WOSE mode
    without_se = args.without_state_estimator
    if "wose" in model_file.stem.lower():
        without_se = True
        print("   Auto-detected WOSE mode from filename")

    policy_config = BeyondMimicPolicyConfig(
        name="BeyondMimicPolicy",
        policy_file=model_file,
        device="cpu",  # MuJoCo runs on CPU
        obs_dof=dof_cfg,
        action_dof=dof_cfg,
        action_scales=G1_BEYONDMIMIC_ACTION_SCALES,
        freq=50.0,
        without_state_estimator=without_se,
        use_motion_from_model=True,
        start_timestep=0,
        max_timestep=args.max_timestep,
    )

    policy_kwargs = {k: v for k, v in policy_config.__dict__.items() if k != 'name'}
    policy = load_policy("BeyondMimicPolicy", **policy_kwargs)

    print(f"✅ Policy loaded")
    print(f"   - Observation dim: {policy.num_obs}")
    print(f"   - Action dim: {policy.num_actions}")
    print(f"   - Without SE: {policy.without_state_estimator}")

    if args.play_speed != 1.0:
        policy.play_speed = args.play_speed
        print(f"   - Play speed: {policy.play_speed}x")

    # Create MuJoCo environment
    print("\n[2] Creating MuJoCo environment...")
    mjcf_path = str(Path(args.mjcf_file).resolve())
    print(f"   Loading MJCF: {mjcf_path}")

    env = MuJoCoEnv(mjcf_path)
    print(f"✅ MuJoCo environment created: {env.num_dofs} DOFs")

    # Set PD gains
    print("\n[3] Configuring PD controller...")
    import re
    from genPiHub.envs.beyondmimic.genesislab.robot_cfg import G1_BEYONDMIMIC_EFFORT_LIMITS

    stiffness_array = np.zeros(29)
    damping_array = np.zeros(29)
    effort_limits_array = np.zeros(29)

    for i, name in enumerate(G1_29DOF_BEYONDMIMIC_NAMES):
        # Find matching gains
        stiffness = 40.0  # Default
        damping = 2.0
        effort_limit = 300.0

        for pattern, val in G1_BEYONDMIMIC_STIFFNESS.items():
            if re.match(pattern, name):
                stiffness = val
                break

        for pattern, val in G1_BEYONDMIMIC_DAMPING.items():
            if re.match(pattern, name):
                damping = val
                break

        for pattern, val in G1_BEYONDMIMIC_EFFORT_LIMITS.items():
            if re.match(pattern, name):
                effort_limit = val
                break

        stiffness_array[i] = stiffness
        damping_array[i] = damping
        effort_limits_array[i] = effort_limit

    env.set_pd_gains(stiffness_array, damping_array, effort_limits_array)
    print(f"✅ PD gains configured (kp: {stiffness_array[:3]}, kd: {damping_array[:3]})")

    # Reset
    print("\n[4] Resetting...")
    env.reset()
    policy.reset()
    print("✅ Ready to run")

    # Main loop
    print(f"\n[5] Running for {args.max_steps} steps...")
    if args.max_timestep > 0:
        print(f"   Motion will stop at timestep {args.max_timestep}")
    if args.loop:
        print("   Loop mode enabled")
    print()

    motion_resets = 0

    if args.headless:
        # Headless mode
        t0 = time.time()
        for step in range(args.max_steps):
            env_data = env.get_data()
            obs, extras = policy.get_observation(env_data, {})
            action = policy.get_action(obs)

            # Actions from policy are: target = default_pos + scaled_residual
            # We need to send absolute targets to MuJoCo
            pd_target = G1_BEYONDMIMIC_DEFAULT_POS + action
            env.step(pd_target)

            policy.post_step_callback()

            if args.loop and extras.get("motion_done", False):
                policy.reset()
                motion_resets += 1
                print(f"🔄 Motion completed, restarting (loop {motion_resets})...")

            if step % args.print_every == 0:
                base_pos = env_data["base_pos"]
                fps = (step + 1) / max(1e-6, time.time() - t0)
                timestep = extras.get("timestep", policy.timestep)
                motion_done = extras.get("motion_done", False)
                status = "DONE" if motion_done else f"t={timestep:.0f}"

                print(
                    f"step={step:06d} fps={fps:6.1f} "
                    f"pos=[{base_pos[0]:6.2f}, {base_pos[1]:6.2f}, {base_pos[2]:5.3f}] "
                    f"motion={status}"
                )

            if not args.loop and extras.get("motion_done", False):
                print(f"\n✅ Motion playback completed at step {step}")
                break
    else:
        # Interactive mode with viewer
        with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
            viewer.cam.distance = 3.0
            viewer.cam.azimuth = 90
            viewer.cam.elevation = -15

            t0 = time.time()
            for step in range(args.max_steps):
                env_data = env.get_data()
                obs, extras = policy.get_observation(env_data, {})
                action = policy.get_action(obs)

                pd_target = G1_BEYONDMIMIC_DEFAULT_POS + action
                env.step(pd_target)

                policy.post_step_callback()

                if args.loop and extras.get("motion_done", False):
                    policy.reset()
                    motion_resets += 1
                    print(f"🔄 Motion completed, restarting (loop {motion_resets})...")

                if step % args.print_every == 0:
                    base_pos = env_data["base_pos"]
                    fps = (step + 1) / max(1e-6, time.time() - t0)
                    timestep = extras.get("timestep", policy.timestep)
                    print(f"step={step:06d} fps={fps:6.1f} pos=[{base_pos[0]:6.2f}, {base_pos[1]:6.2f}, {base_pos[2]:5.3f}] t={timestep:.0f}")

                viewer.sync()

                if not args.loop and extras.get("motion_done", False):
                    print(f"\n✅ Motion playback completed")
                    break

                if not viewer.is_running():
                    break

    print("\n" + "=" * 80)
    print("✅ Done!")
    if args.loop and motion_resets > 0:
        print(f"   Total loops: {motion_resets}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
