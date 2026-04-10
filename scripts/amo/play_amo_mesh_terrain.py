#!/usr/bin/env python3
"""Run AMO policy on mesh terrain (GLB/OBJ/STL/GLTF).

This script demonstrates deploying AMO policy on mesh terrain files.

Usage:
    python scripts/amo/play_amo_mesh_terrain.py --viewer
    python scripts/amo/play_amo_mesh_terrain.py --viewer --mesh-path data/assets/Barracks.glb
    python scripts/amo/play_amo_mesh_terrain.py --viewer --interactive
"""

from __future__ import annotations

import argparse
import os
import time
import numpy as np
import torch
from pathlib import Path

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
        description="Play AMO policy on mesh terrain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Environment
    parser.add_argument("--device", type=str, default=None, choices=["cpu", "cuda"])
    parser.add_argument("--num-envs", type=int, default=1, help="Number of environments")
    parser.add_argument("--viewer", action="store_true", help="Enable viewer (recommended!)")
    parser.add_argument("--headless", action="store_true", help="Disable viewer (explicit headless mode)")

    # Mesh Terrain
    parser.add_argument(
        "--mesh-path",
        type=str,
        default="data/assets/modern_apartment.glb",
        help="Path to mesh file (.obj, .stl, .glb, .gltf)",
    )
    parser.add_argument(
        "--env-spacing",
        type=float,
        default=4.0,
        help="Spacing between environments (meters)",
    )
    parser.add_argument(
        "--decompose-threshold",
        type=float,
        default=float("inf"),
        help="Convex decomposition error threshold (0.0=full, inf=none)",
    )
    parser.add_argument(
        "--sdf-cell-size",
        type=float,
        default=0.1,
        help="SDF cell size for collision detection",
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
        freq=50.0,  # 50 Hz control
    )


def create_amo_mesh_terrain_env_config(
    args,
    mesh_path: str,
    num_envs: int,
    env_spacing: float,
    backend: str,
    viewer: bool,
):
    """Create AMO environment configuration with mesh terrain.

    Args:
        args: Command line arguments
        mesh_path: Path to mesh file (.obj, .stl, .glb, .gltf)
        num_envs: Number of environments
        env_spacing: Environment spacing in meters
        backend: Physics backend
        viewer: Enable viewer

    Returns:
        AmoGenesisEnvCfg with mesh terrain
    """
    # Import AMO environment config
    from genPiHub.envs.amo import AmoGenesisEnvCfg

    # Create base AMO config
    cfg = AmoGenesisEnvCfg()

    # Set robot spawn position from args
    cfg.scene.robots["robot"].initial_pose.pos = [0, 0, 1]
    cfg.scene.sim_options.gravity = [0, 0, 0]

    # CRITICAL: Reduce timestep to avoid NaN in rigid body solver
    cfg.scene.dt = 0.001  # Reduce from 0.005 to 0.001
    cfg.scene.substeps = 5  # Increase substeps for stability

    # Configure scene
    cfg.scene.num_envs = num_envs
    cfg.scene.backend = backend
    cfg.scene.viewer = viewer

    # Replace plane terrain with mesh terrain
    cfg.scene.terrain = TerrainCfg(
        terrain_type="mesh",
        mesh_path=mesh_path,
        env_spacing=env_spacing,
        mesh_decompose_error_threshold=args.decompose_threshold,
        mesh_sdf_cell_size=args.sdf_cell_size,
    )

    # Configure observations (disable corruption for testing)
    cfg.observations.policy.enable_corruption = False

    # Configure commands (large resampling time = static command)
    cfg.commands.base_velocity.resampling_time_range = (1e9, 1e9)

    # Set initial command from args
    cfg.commands.base_velocity.ranges.lin_vel_x = (args.vx, args.vx)
    cfg.commands.base_velocity.ranges.lin_vel_y = (args.vy, args.vy)
    cfg.commands.base_velocity.ranges.ang_vel_z = (args.yaw_rate, args.yaw_rate)

    return cfg


def main():
    args = parse_args()

    # Handle viewer/headless logic
    use_viewer = args.viewer and not args.headless

    # Check mesh file exists
    import os
    if not os.path.exists(args.mesh_path):
        print(f"\n❌ ERROR: Mesh file not found: {args.mesh_path}")
        print("\n💡 Please ensure the mesh file exists at the specified location.")
        return 1

    print(f"\n✅ Mesh file found: {os.path.basename(args.mesh_path)}")

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

    # Create environment with mesh terrain
    print(f"\n[2/4] Creating environment with mesh terrain...")

    # Create AMO environment config with mesh terrain
    amo_env_cfg = create_amo_mesh_terrain_env_config(
        args=args,
        mesh_path=args.mesh_path,
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
    print(f"   Terrain: Mesh (grid-based, {args.env_spacing}m spacing)")
    print(f"   Collision: decompose_threshold={args.decompose_threshold:.2g}, sdf_cell_size={args.sdf_cell_size}")

    # Load AMO policy
    print("\n[3/4] Loading AMO policy...")
    policy_kwargs = {k: v for k, v in policy_config.__dict__.items() if k != 'name'}
    policy = load_policy("AMOPolicy", **policy_kwargs)
    print(f"✅ Policy loaded: {policy.cfg.name}")
    print(f"   Device: {policy.device}")

    # Deploy policy
    print("\n[4/4] Deploying policy...")
    print(f"✅ Running AMO on mesh terrain: {os.path.basename(args.mesh_path)}")
    print(f"   Command: vx={args.vx:.2f} m/s, vy={args.vy:.2f} m/s, yaw_rate={args.yaw_rate:.2f} rad/s")

    # Setup command state
    cmd_state = CommandState(vx=args.vx, vy=args.vy, yaw_rate=args.yaw_rate, height=args.height)

    # Interactive keyboard control
    terminal_ctrl = None
    if args.interactive:
        terminal_ctrl = TerminalController()
        print("\n⌨️  Interactive mode enabled")
        print("   w/s: forward/backward, a/d: left/right, q/e: turn left/right")
        print("   r/f: up/down, x: stop, Ctrl+C: quit")

    # Reset environment and policy
    env.reset()
    policy.reset()
    print(f"\n▶️  Starting deployment (max {args.max_steps} steps)...")

    # Main loop
    start_time = time.time()

    try:
        for step in range(args.max_steps):
            # Get environment data
            env_data = env.get_data()

            # Update command from keyboard if interactive
            if terminal_ctrl:
                cmd_state = terminal_ctrl.update_command(cmd_state)

            # Set commands in env_data
            env_data["commands"] = cmd_state.as_array()

            # Get observation and action from policy
            obs, extras = policy.get_observation(env_data, {})
            action = policy.get_action(obs)

            # Step environment
            step_result = env.step(action)

            # Handle episode termination
            if step_result.get("terminated", False).any() or step_result.get("truncated", False).any():
                policy.reset()

            # Print stats
            if step % args.print_every == 0:
                base_pos = env.base_pos
                elapsed = time.time() - start_time
                fps = (step + 1) / max(1e-6, elapsed)
                print(
                    f"step={step:06d} fps={fps:6.1f} "
                    f"pos=[{base_pos[0]:6.2f}, {base_pos[1]:6.2f}, {base_pos[2]:5.3f}] "
                    f"cmd: vx={cmd_state.vx:+.2f} vy={cmd_state.vy:+.2f} yaw={cmd_state.yaw_rate:+.2f}"
                )

            # Policy post-step callback
            policy.post_step_callback()

    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")

    print(f"\n✅ Done! Ran {args.max_steps} steps in {time.time() - start_time:.1f}s")
    return 0


if __name__ == "__main__":
    main()
