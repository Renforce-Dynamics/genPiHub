#!/usr/bin/env python3
"""Run AMO policy with static Terrain USD.

This is a simplified version that uses static Terrain.usd (no articulated furniture)
to demonstrate the environment_objects system without collision complexity.

Recommended for initial testing before using full Scene.usd.

Usage:
    # Headless mode
    python scripts/amo/play_amo_with_terrain_usd.py

    # With viewer (recommended)
    python scripts/amo/play_amo_with_terrain_usd.py --viewer

    # Interactive control
    python scripts/amo/play_amo_with_terrain_usd.py --viewer --interactive --vx 0.4
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
    parser = argparse.ArgumentParser(description="Play AMO with static Terrain USD")

    # Environment
    parser.add_argument("--device", type=str, default=None, choices=["cpu", "cuda"])
    parser.add_argument("--num-envs", type=int, default=1)
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--headless", action="store_true")

    # Control
    parser.add_argument("--max-steps", type=int, default=100000)
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--print-every", type=int, default=100)

    # Policy
    parser.add_argument("--model-dir", type=str, default="third_party/genPiHub/data/AMO")
    parser.add_argument("--action-scale", type=float, default=0.25)

    # Commands
    parser.add_argument("--vx", type=float, default=0.3)
    parser.add_argument("--vy", type=float, default=0.0)
    parser.add_argument("--yaw-rate", type=float, default=0.0)
    parser.add_argument("--height", type=float, default=0.0)

    return parser.parse_args()


def create_amo_policy_config(args) -> AMOPolicyConfig:
    """Create AMO policy configuration."""
    model_dir = Path(args.model_dir)

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
        -0.1, 0., 0., 0.3, -0.2, 0.,
        -0.1, 0., 0., 0.3, -0.2, 0.,
        0., 0., 0.,
        0.5, 0., 0.2, 0.3,
        0.5, 0., -0.2, 0.3,
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
    use_viewer = args.viewer and not args.headless
    backend = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    print("=" * 80)
    print("AMO Policy with Static Terrain USD (简化版测试)")
    print("=" * 80)
    print(f"Mode: {'Viewer' if use_viewer else 'Headless'}")
    print(f"Using: Terrain.usd (static Floor/Wall/Ceiling)")
    print("=" * 80)

    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # Load policy config
    print("\n[1/5] Loading AMO policy config...")
    policy_config = create_amo_policy_config(args)
    print(f"✅ Policy: {policy_config.obs_dof.num_dofs} DOFs")



    # Create environment with static Terrain USD
    print("\n[2/5] Creating environment with Terrain USD...")
    amo_env_cfg = create_amo_genesis_env_config_with_usd_scene(
        usd_scene_path="data/assets/isaacsim_assets/Assets/Isaac/4.5/Isaac/Environments/Simple_Warehouse/warehouse.usd",
        num_envs=args.num_envs,
        backend=backend,
        viewer=use_viewer,
        enable_corruption=False,
        increase_collision_limits=True,  # Needed for complex scenes with many meshes
    )

    genesis_cfg = GenesisEnvConfig(
        dof=policy_config.obs_dof,
        num_envs=args.num_envs,
    )

    env = GenesisEnv(cfg=genesis_cfg, device=backend, env_cfg=amo_env_cfg)
    print(f"✅ Environment: {env.num_envs} envs, {env.num_dofs} DOFs")

    # Load policy
    print("\n[3/5] Loading AMO policy...")
    policy_kwargs = {k: v for k, v in policy_config.__dict__.items() if k != 'name'}
    policy = load_policy("AMOPolicy", **policy_kwargs)
    print(f"✅ Policy loaded")

    # Setup commands
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

    controller = None
    if args.interactive:
        controller = TerminalController(state)
        print("\n✅ Interactive mode: w/s vx, a/d yaw, e/c vy, z/x height, q quit")
        controller.start()
    else:
        print(f"\n✅ Command: vx={args.vx:.2f}")

    # Reset
    print("\n[4/5] Resetting...")
    env.reset()
    policy.reset()
    print("✅ Ready")

    # Main loop
    print(f"\n[5/5] Running ({args.max_steps} steps)...")

    try:
        t0 = time.time()
        for step in range(args.max_steps):
            env_data = env.get_data()

            quit_now = False
            if controller:
                quit_now = controller.poll()
                if quit_now:
                    break
                commands = controller.state.as_array()
            else:
                commands = state.as_array()

            env_data["commands"] = commands
            obs, extras = policy.get_observation(env_data, {})
            action = policy.get_action(obs)
            step_result = env.step(action)

            if step_result.get("terminated", False).any() or step_result.get("truncated", False).any():
                policy.reset()

            if step % args.print_every == 0:
                base_pos = env.base_pos
                fps = (step + 1) / max(1e-6, time.time() - t0)
                print(
                    f"step={step:06d} fps={fps:6.1f} "
                    f"pos=[{base_pos[0]:6.2f}, {base_pos[1]:6.2f}, {base_pos[2]:5.3f}]"
                )

            policy.post_step_callback()

    except KeyboardInterrupt:
        print("\n✅ Interrupted")
    finally:
        if controller:
            controller.stop()
        del env

    print("\n" + "=" * 80)
    print("✅ 完成！静态Terrain USD测试成功")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
