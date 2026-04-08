#!/usr/bin/env python3
"""Play AMO policy in GenesisLab environment.

This script runs the pre-trained AMO policy in the GenesisLab AMO task package.
Supports both headless and interactive (with viewer) modes.

Requires: pip install -e . (from project root)

Usage:
    # Headless mode (no viewer)
    python scripts/play_amo_genesislab.py

    # With viewer
    python scripts/play_amo_genesislab.py --viewer

    # Interactive keyboard control
    python scripts/play_amo_genesislab.py --viewer --interactive

    # Custom velocity
    python scripts/play_amo_genesislab.py --vx 0.5 --yaw-rate 0.2
"""

import argparse
from pathlib import Path

import numpy as np
import torch
import genesis as gs

from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnv

# Import from installed AMO package
from amo import AMOPolicy, CommandState, TerminalController, AmoGenesisEnvCfg, build_joint_index_map


def parse_args():
    parser = argparse.ArgumentParser(description="Play AMO policy in GenesisLab")
    parser.add_argument("--viewer", action="store_true", help="Enable viewer")
    parser.add_argument("--interactive", action="store_true", help="Enable keyboard control")
    parser.add_argument("--device", type=str, default="cuda", choices=["cpu", "cuda"])
    parser.add_argument("--max-steps", type=int, default=100000, help="Maximum steps")
    parser.add_argument("--print-every", type=int, default=100, help="Print status every N steps")

    # Velocity commands
    parser.add_argument("--vx", type=float, default=0.0, help="Forward velocity (m/s)")
    parser.add_argument("--vy", type=float, default=0.0, help="Lateral velocity (m/s)")
    parser.add_argument("--yaw-rate", type=float, default=0.0, help="Yaw rate (rad/s)")
    parser.add_argument("--height", type=float, default=0.0, help="Height adjustment")

    # Policy paths
    parser.add_argument("--model-dir", type=str, default=".reference/AMO", help="AMO model directory")

    return parser.parse_args()


def main():
    args = parse_args()

    print("="*60)
    print("AMO Policy in GenesisLab")
    print("="*60)

    # Initialize Genesis
    backend = gs.gpu if args.device == "cuda" else gs.cpu
    gs.init(backend=backend, logging_level="WARNING")

    if torch.cuda.is_available() and args.device == "cuda":
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # Create AMO environment
    cfg = AmoGenesisEnvCfg()
    cfg.scene.num_envs = 1
    cfg.scene.viewer = args.viewer
    env = ManagerBasedRlEnv(cfg=cfg, device=args.device)

    # Load AMO policy
    print(f"\n✅ Loading AMO policy from {args.model_dir}...")
    policy = AMOPolicy(
        model_dir=args.model_dir,
        device=args.device,
        action_scale=0.25,
    )

    # Get robot reference
    robot = env.entities["robot"]
    robot_joint_names = list(robot.joint_names)

    # Build joint mapping using utility function
    amo_to_robot, _ = build_joint_index_map(AMOPolicy.DOF_NAMES, robot_joint_names)

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
        print("Controls: w/s vx, a/d yaw, e/c vy, z/x height, q quit")
        controller.start()
    else:
        print(f"\n✅ Fixed command: vx={args.vx:.2f}, vy={args.vy:.2f}, yaw={args.yaw_rate:.2f}")

    # Reset
    print("\n✅ Resetting environment...")
    env.reset()
    policy.reset()

    # Print environment info
    print(f"   - Action dim: {env.action_manager.total_action_dim}")
    print(f"   - Num envs: {env.num_envs}")
    print(f"   - Physics dt: {env.physics_dt:.5f}s")
    print(f"   - Control dt: {env.step_dt:.5f}s")

    print(f"\n✅ Running AMO policy (max {args.max_steps} steps)...")
    if controller:
        print("   Press 'q' to quit\n")

    # Main loop
    try:
        for step in range(args.max_steps):
            # Read robot state (environment 0)
            joint_pos_robot = robot.data.joint_pos[0].detach().cpu().numpy()
            joint_vel_robot = robot.data.joint_vel[0].detach().cpu().numpy()
            quat_wxyz = robot.data.root_quat_w[0].detach().cpu().numpy()
            ang_vel_b = robot.data.root_ang_vel_b[0].detach().cpu().numpy()
            base_pos = robot.data.root_pos_w[0].detach().cpu().numpy()

            # Map to AMO joint order
            dof_pos_amo = joint_pos_robot[amo_to_robot].astype(np.float32)
            dof_vel_amo = joint_vel_robot[amo_to_robot].astype(np.float32)

            # Poll keyboard if interactive
            if controller:
                quit_now = controller.poll()
                if quit_now:
                    print("\n✅ User quit")
                    break
                commands = controller.state.as_array()
            else:
                commands = state.as_array()

            # Run AMO policy
            pd_target_amo = policy.act(
                dof_pos=dof_pos_amo,
                dof_vel=dof_vel_amo,
                quat=quat_wxyz.astype(np.float32),
                ang_vel=ang_vel_b.astype(np.float32),
                commands=commands,
                dt=float(env.step_dt),
            )

            # Convert to action (stays in AMO order)
            action_amo = (pd_target_amo - policy.DEFAULT_DOF_POS) / policy.action_scale

            # Send to environment
            actions = torch.zeros(
                (env.num_envs, env.action_manager.total_action_dim),
                dtype=torch.float32,
                device=env.device
            )
            actions[:, :len(action_amo)] = torch.from_numpy(action_amo).to(env.device)

            # Step
            obs, reward, term, trunc, info = env.step(actions)

            # Reset if needed
            done = term | trunc
            if done.any():
                reset_ids = done.nonzero(as_tuple=False).squeeze(-1)
                env.reset(env_ids=reset_ids)
                if (reset_ids == 0).any():
                    policy.reset()
                    print(f"   Episode reset at step {step}")

            # Print status
            if step % args.print_every == 0:
                print(
                    f"Step {step:06d}: "
                    f"pos=[{base_pos[0]:6.2f}, {base_pos[1]:6.2f}, {base_pos[2]:5.3f}], "
                    f"cmd=[vx={commands[0]:.2f}, vy={commands[2]:.2f}, yaw={commands[1]:.2f}]"
                )

    except KeyboardInterrupt:
        print("\n✅ Interrupted by user")
    finally:
        if controller:
            controller.stop()

    print("\n✅ Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
