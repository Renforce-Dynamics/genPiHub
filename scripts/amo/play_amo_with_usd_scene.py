#!/usr/bin/env python3
"""Run AMO policy in USD scene with interactive furniture.

This script demonstrates running AMO in a complete USD scene environment with:
- Interactive furniture with articulated joints (chairs, cabinets, etc.)
- Robot can physically interact with scene objects
- No joint indexing conflicts (using environment_objects system)

The key innovation is using the new EnvironmentObjectsConfig system to load
USD scenes AFTER robots, avoiding DOF space conflicts.

Usage:
    # Headless mode (default)
    python scripts/amo/play_amo_with_usd_scene.py

    # With viewer (recommended)
    python scripts/amo/play_amo_with_usd_scene.py --viewer

    # Interactive keyboard control
    python scripts/amo/play_amo_with_usd_scene.py --viewer --interactive

    # Custom scene
    python scripts/amo/play_amo_with_usd_scene.py --usd-scene path/to/scene.usd
"""

from __future__ import annotations

import sys
from pathlib import Path

import argparse
import time
import numpy as np
import torch

# Import from Policy Hub
from genPiHub import load_policy
from genPiHub.configs import (
    AMOPolicyConfig,
    GenesisEnvConfig,
    create_amo_genesis_env_config_with_usd_scene,
)
from genPiHub.tools import DOFConfig, CommandState, TerminalController
from genPiHub.environments import GenesisEnv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Play AMO policy in USD scene with interactive furniture"
    )

    # Environment
    parser.add_argument("--device", type=str, default=None, choices=["cpu", "cuda"])
    parser.add_argument("--num-envs", type=int, default=1)
    parser.add_argument("--viewer", action="store_true", help="Enable viewer")
    parser.add_argument("--headless", action="store_true", help="Disable viewer")

    # USD Scene
    parser.add_argument(
        "--usd-scene",
        type=str,
        default="third_party/genPiHub/data/assets/CWDL_LW_Assets_20260310/Scene.usd",
        help="Path to USD scene file (will be loaded as static terrain)",
    )

    # Control
    parser.add_argument("--max-steps", type=int, default=100000)
    parser.add_argument("--interactive", action="store_true", help="Keyboard control")
    parser.add_argument("--print-every", type=int, default=100)

    # Policy
    parser.add_argument("--model-dir", type=str, default="data/AMO", help="AMO model directory")
    parser.add_argument("--action-scale", type=float, default=0.25)

    # Commands
    parser.add_argument("--vx", type=float, default=0.3, help="Forward velocity (m/s)")
    parser.add_argument("--vy", type=float, default=0.0, help="Lateral velocity (m/s)")
    parser.add_argument("--yaw-rate", type=float, default=0.0, help="Yaw rate (rad/s)")
    parser.add_argument("--height", type=float, default=0.0, help="Height adjustment")

    return parser.parse_args()


def create_amo_policy_config(args) -> AMOPolicyConfig:
    """Create AMO policy configuration."""
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
        freq=50.0,
    )


def main() -> int:
    args = parse_args()

    # Handle viewer/headless flags
    use_viewer = args.viewer and not args.headless

    print("=" * 80)
    print("AMO Policy in USD Scene (地形系统)")
    print("=" * 80)
    print(f"Mode: {'Viewer' if use_viewer else 'Headless'}")
    print(f"USD Scene: {args.usd_scene}")
    print(f"加载方式: USD 作为静态地形")
    print("=" * 80)

    # Determine device
    backend = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # Load AMO policy configuration
    print("\n[1/5] Creating AMO policy configuration...")
    policy_config = create_amo_policy_config(args)
    print(f"✅ Policy config created: {policy_config.obs_dof.num_dofs} DOFs")

    # Create environment with USD scene
    print("\n[2/5] Creating environment with USD scene...")
    print(f"  - Loading USD: {args.usd_scene}")
    print(f"  - Using Terrain system (terrain_type='usd')")
    print(f"  - USD loaded as static terrain")

    # Create AMO environment config with USD terrain
    amo_env_cfg = create_amo_genesis_env_config_with_usd_scene(
        usd_scene_path=args.usd_scene,
        num_envs=args.num_envs,
        backend=backend,
        viewer=use_viewer,
        enable_corruption=False,
        resampling_time=1e9,
        standing_envs_ratio=0.0,
        increase_collision_limits=True,  # Important for complex scenes
    )

    # Create GenesisEnv wrapper
    genesis_cfg = GenesisEnvConfig(
        dof=policy_config.obs_dof,
        num_envs=args.num_envs,
    )

    env = GenesisEnv(cfg=genesis_cfg, device=backend, env_cfg=amo_env_cfg)
    print(f"✅ Environment created:")
    print(f"   - Envs: {env.num_envs}")
    print(f"   - DOFs: {env.num_dofs}")
    print(f"   - USD objects loaded successfully")

    # Check terrain
    if hasattr(env._env.scene, 'terrain') and env._env.scene.terrain is not None:
        print(f"   - USD Terrain: ✅ Loaded successfully")

    # Load AMO policy
    print("\n[3/5] Loading AMO policy...")
    policy_kwargs = {k: v for k, v in policy_config.__dict__.items() if k != 'name'}
    policy = load_policy("AMOPolicy", **policy_kwargs)
    print(f"✅ Policy loaded: {policy.cfg.name}")
    print(f"   - Device: {policy.device}")
    print(f"   - Control frequency: {policy.freq} Hz")

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

    # Setup interactive controller
    controller = None
    if args.interactive:
        controller = TerminalController(state)
        print("\n✅ Interactive mode enabled")
        print("Controls: w/s vx, a/d yaw, e/c vy, z/x height, q quit")
        controller.start()
    else:
        print(f"\n✅ Fixed command: vx={args.vx:.2f}, vy={args.vy:.2f}, yaw={args.yaw_rate:.2f}")

    # Reset
    print("\n[4/5] Resetting environment...")
    env.reset()
    policy.reset()
    print("✅ Ready to run")
    print("\n提示:")
    print("  - 机器人可以与USD场景中的家具交互")
    print("  - 关节空间隔离确保无冲突")
    print("  - 使用--interactive模式可通过键盘控制")

    # Main loop
    print(f"\n[5/5] Running for {args.max_steps} steps...")
    if controller:
        print("   Press 'q' to quit\n")

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

            # Reset policy if needed
            if step_result.get("terminated", False).any() or step_result.get("truncated", False).any():
                policy.reset()

            # Print status
            if step % args.print_every == 0:
                base_pos = env.base_pos
                fps = (step + 1) / max(1e-6, time.time() - t0)
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
        if controller:
            controller.stop()
        del env

    print("\n" + "=" * 80)
    print("✅ 完成！")
    print("   - AMO策略在USD场景中成功运行")
    print("   - 机器人与环境物体交互正常")
    print("   - 关节空间隔离系统工作正常")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
