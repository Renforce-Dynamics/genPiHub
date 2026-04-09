#!/usr/bin/env python3
"""Run AMO policy on USD terrain (Scene.usd).

This script demonstrates deploying AMO policy on a custom USD terrain,
allowing the humanoid to walk in realistic architectural environments.

Features:
- ✅ AMO policy via Policy Hub
- ✅ USD terrain support (Scene.usd)
- ✅ Multi-environment grid layout
- ✅ Interactive viewer controls
- ✅ Keyboard command control

Usage examples:
    # Basic: Run with viewer on USD terrain
    python scripts/amo/play_amo_usd_terrain.py --viewer

    # Interactive control
    python scripts/amo/play_amo_usd_terrain.py --viewer --interactive

    # Custom USD file
    python scripts/amo/play_amo_usd_terrain.py --viewer --usd-path path/to/your/scene.usd

    # Multiple environments
    python scripts/amo/play_amo_usd_terrain.py --viewer --num-envs 4 --env-spacing 12.0

    # Walk forward at 0.5 m/s
    python scripts/amo/play_amo_usd_terrain.py --viewer --vx 0.5

    # Headless test
    python scripts/amo/play_amo_usd_terrain.py --max-steps 500
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure we import genPiHub from the local third_party directory
# Use absolute path to avoid confusion with symlinks or relative paths
_genPiHub_dir = Path("/home/ununtu/code/glab/genesislab/third_party/genPiHub").resolve()
sys.path.insert(0, str(_genPiHub_dir))

import argparse
import time
import numpy as np
import torch

# Import from Policy Hub
from genPiHub import load_policy
from genPiHub.configs import (
    AMOPolicyConfig,
    GenesisEnvConfig,
)
from genPiHub.tools import DOFConfig, CommandState, TerminalController
from genPiHub.environments import GenesisEnv

# Import GenesisLab terrain config
from genesislab.components.terrains import TerrainCfg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Play AMO policy on USD terrain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Environment
    parser.add_argument("--device", type=str, default=None, choices=["cpu", "cuda"])
    parser.add_argument("--num-envs", type=int, default=1, help="Number of environments")
    parser.add_argument("--viewer", action="store_true", help="Enable viewer (recommended!)")
    parser.add_argument("--headless", action="store_true", help="Disable viewer (explicit headless mode)")

    # USD Terrain
    parser.add_argument(
        "--usd-path",
        type=str,
        default="third_party/genPiHub/data/assets/CWDL_LW_Assets_20260310/Scene.usd",
        help="Path to USD terrain file",
    )
    parser.add_argument(
        "--env-spacing",
        type=float,
        default=10.0,
        help="Spacing between environments (meters)",
    )

    # Control
    parser.add_argument("--max-steps", type=int, default=100000, help="Maximum steps to run")
    parser.add_argument("--interactive", action="store_true", help="Enable keyboard control")
    parser.add_argument("--print-every", type=int, default=100, help="Print stats every N steps")

    # Policy
    parser.add_argument("--model-dir", type=str, default="data/AMO", help="AMO model directory")
    parser.add_argument("--action-scale", type=float, default=0.25, help="Action scaling factor")

    # Commands
    parser.add_argument("--vx", type=float, default=0.3, help="Forward velocity (m/s)")
    parser.add_argument("--vy", type=float, default=0.0, help="Lateral velocity (m/s)")
    parser.add_argument("--yaw-rate", type=float, default=0.0, help="Yaw rate (rad/s)")
    parser.add_argument("--height", type=float, default=0.0, help="Height adjustment")

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
        "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
        "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
        "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
        "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
        "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
        "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint", "left_elbow_joint",
        "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint", "right_elbow_joint",
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


def create_amo_usd_terrain_env_config(
    args,
    usd_path: str,
    num_envs: int,
    env_spacing: float,
    backend: str,
    viewer: bool,
):
    """Create AMO environment configuration with USD terrain.

    Args:
        args: Command line arguments
        usd_path: Path to USD terrain file
        num_envs: Number of environments
        env_spacing: Environment spacing in meters
        backend: Physics backend
        viewer: Enable viewer

    Returns:
        AmoGenesisEnvCfg with USD terrain
    """
    # Import AMO environment config
    from genPiHub.envs.amo import AmoGenesisEnvCfg

    # Create base AMO config
    cfg = AmoGenesisEnvCfg()

    # Configure scene
    cfg.scene.num_envs = num_envs
    cfg.scene.backend = backend
    cfg.scene.viewer = viewer

    # ⭐ Replace plane terrain with USD terrain
    cfg.scene.terrain = TerrainCfg(
        terrain_type="usd",
        usd_path=usd_path,
        env_spacing=env_spacing,
    )

    # Configure observations (disable corruption for testing)
    cfg.observations.policy.enable_corruption = False

    # Configure commands (no resampling for manual control)
    cfg.commands.base_velocity.resampling_time_range = (1e9, 1e9)
    cfg.commands.base_velocity.rel_standing_envs = 0.0

    return cfg


def main() -> int:
    args = parse_args()

    # Handle viewer/headless flags
    use_viewer = args.viewer and not args.headless

    print("=" * 80)
    print("🏃 AMO Policy on USD Terrain")
    print("=" * 80)
    print(f"Mode: {'🎬 Viewer' if use_viewer else '⚙️  Headless'}")
    print(f"USD terrain: {args.usd_path}")
    print(f"Environments: {args.num_envs}")
    print(f"Env spacing: {args.env_spacing}m")
    print("=" * 80)

    # Validate USD file
    import os
    if not os.path.exists(args.usd_path):
        print(f"\n❌ ERROR: USD file not found: {args.usd_path}")
        print("\n💡 Please ensure the Scene.usd file exists at the specified location.")
        return 1

    print(f"\n✅ USD file found: {os.path.basename(args.usd_path)}")

    # Determine device
    backend = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"✅ Backend: {backend}")

    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # Load AMO policy configuration
    print("\n[1/4] Creating AMO policy configuration...")
    policy_config = create_amo_policy_config(args)
    print(f"✅ Policy config: {policy_config.obs_dof.num_dofs} DOFs, {policy_config.freq}Hz")

    # Create environment with USD terrain
    print(f"\n[2/4] Creating environment with USD terrain...")

    # Create AMO environment config with USD terrain
    amo_env_cfg = create_amo_usd_terrain_env_config(
        args=args,
        usd_path=args.usd_path,
        num_envs=args.num_envs,
        env_spacing=args.env_spacing,
        backend=backend,
        viewer=use_viewer,
    )

    # Create GenesisEnv wrapper
    genesis_cfg = GenesisEnvConfig(
        dof=policy_config.obs_dof,
        num_envs=args.num_envs,
    )

    env = GenesisEnv(cfg=genesis_cfg, device=backend, env_cfg=amo_env_cfg)
    print(f"✅ Environment: {env.num_envs} envs, {env.num_dofs} DOFs")
    print(f"   Terrain: USD (grid-based, {args.env_spacing}m spacing)")

    # Load AMO policy
    print("\n[3/4] Loading AMO policy...")
    policy_kwargs = {k: v for k, v in policy_config.__dict__.items() if k != 'name'}
    policy = load_policy("AMOPolicy", **policy_kwargs)
    print(f"✅ Policy loaded: {policy.cfg.name}")
    print(f"   Device: {policy.device}")
    print(f"   Action scale: {policy.action_scale}")

    # Setup command state
    state = CommandState(
        vx=args.vx,
        vy=args.vy,
        yaw_rate=args.yaw_rate,
        height=args.height,
        torso_yaw=0.0,
        torso_pitch=0.0,
        torso_roll=0.0,
        arm_enable=0.0,
    )

    # Setup interactive controller if requested
    controller = None
    if args.interactive:
        controller = TerminalController(state)
        print("\n✅ Interactive mode enabled")
        print("   Controls: w/s=vx, a/d=yaw, e/c=vy, z/x=height, q=quit")
        controller.start()
    else:
        print(f"\n✅ Fixed command: vx={args.vx:.2f} m/s, vy={args.vy:.2f} m/s, yaw={args.yaw_rate:.2f} rad/s")

    # Reset
    print("\n[4/4] Resetting environment...")
    env.reset()
    policy.reset()
    print("✅ Ready to run!")

    # Print info for viewer mode
    if use_viewer:
        print("\n" + "=" * 80)
        print("👁️  VIEWER CONTROLS:")
        print("   - Mouse drag: Rotate camera")
        print("   - Mouse wheel: Zoom in/out")
        print("   - Arrow keys: Pan camera")
        if controller:
            print("\n⌨️  KEYBOARD CONTROLS:")
            print("   - W/S: Forward/backward velocity")
            print("   - A/D: Yaw left/right")
            print("   - E/C: Lateral velocity left/right")
            print("   - Z/X: Height up/down")
            print("   - Q: Quit")
        print("   - Ctrl+C: Emergency stop")
        print("=" * 80)

    # Main loop
    print(f"\n▶️  Running for {args.max_steps} steps...\n")

    try:
        t0 = time.time()
        for step in range(args.max_steps):
            # Get environment state
            env_data = env.get_data()

            # Poll keyboard if interactive
            quit_now = False
            if controller:
                quit_now = controller.poll()
                if quit_now:
                    print("\n🛑 Quit command received")
                    break
                commands = controller.state.as_array()
            else:
                commands = state.as_array()

            # Add commands to environment data
            env_data["commands"] = commands

            # Get observation and action
            obs, extras = policy.get_observation(env_data, {})
            action = policy.get_action(obs)

            # Step environment
            step_result = env.step(action)

            # Policy reset if needed
            if step_result.get("terminated", False).any() or step_result.get("truncated", False).any():
                policy.reset()

            # Print status
            if step % args.print_every == 0:
                base_pos = env.base_pos
                fps = (step + 1) / max(1e-6, time.time() - t0)
                print(
                    f"Step {step:06d} | FPS {fps:6.1f} | "
                    f"Pos [{base_pos[0]:6.2f}, {base_pos[1]:6.2f}, {base_pos[2]:5.3f}] | "
                    f"Cmd [vx={commands[0]:.2f}, vy={commands[2]:.2f}, yaw={commands[1]:.2f}]"
                )

            # Post-step callback
            policy.post_step_callback()

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user (Ctrl+C)")
    finally:
        if controller:
            controller.stop()
        del env

    print("\n" + "=" * 80)
    print("✅ Done! AMO policy successfully deployed on USD terrain")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
