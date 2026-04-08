"""Run AMO policy in GenesisLab G1 humanoid environment.

Requires: pip install -e . (from project root)

Usage examples:
    python scripts/play_amo_genesis.py
    python scripts/play_amo_genesis.py --interactive
    python scripts/play_amo_genesis.py --vx 0.6 --yaw-rate 0.1
"""

from __future__ import annotations

import argparse
import importlib
import time
from pathlib import Path

import numpy as np
import torch

import genesis as gs
from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnv

# Import from installed AMO package
from amo import (
    AMOPolicy,
    CommandState,
    TerminalController,
    AMOModelConfig,
    AMODriverConfig,
    GenesisPlayEnvConfig,
    COMMAND_LAYOUT,
    OBS_LAYOUT,
    build_joint_index_map,
)


def _load_env_cfg_from_entry(entry: str):
    """Load and instantiate env cfg from 'module.path:ClassName'."""
    if ":" not in entry:
        raise ValueError(f"Invalid --env-cfg-entry '{entry}', expected 'module:ClassName'")
    module_name, class_name = entry.split(":", 1)
    module = importlib.import_module(module_name)
    cfg_cls = getattr(module, class_name)
    return cfg_cls()


def _print_amo_spec() -> None:
    print("\n=== AMO command input (8) ===")
    for i, name in enumerate(COMMAND_LAYOUT):
        print(f"  {i:2d}: {name}")

    print("\n=== AMO observation layout ===")
    for key, value in OBS_LAYOUT.items():
        print(f"  {key}: {value}")

    print("\n=== AMO joint output/order (23) ===")
    for i, name in enumerate(AMOPolicy.DOF_NAMES):
        print(f"  {i:2d}: {name}")


def parse_args() -> argparse.Namespace:
    default_model = AMOModelConfig()
    default_env = GenesisPlayEnvConfig()
    default_driver = AMODriverConfig()
    parser = argparse.ArgumentParser(description="Play AMO policy in GenesisLab.")
    parser.add_argument("--env-cfg-entry", type=str, default=default_env.env_cfg_entry)
    parser.add_argument("--model-dir", type=str, default=default_model.model_dir)
    parser.add_argument("--policy-file", type=str, default=default_model.policy_filename)
    parser.add_argument("--adapter-file", type=str, default=default_model.adapter_filename)
    parser.add_argument("--norm-file", type=str, default=default_model.norm_stats_filename)
    parser.add_argument("--device", type=str, default=None, choices=["cpu", "cuda"])
    parser.add_argument("--num-envs", type=int, default=default_env.num_envs)
    parser.add_argument("--max-steps", type=int, default=100000)
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--print-every", type=int, default=100)
    parser.add_argument("--print-spec", action="store_true")
    parser.add_argument("--action-scale", type=float, default=default_driver.action_scale)
    parser.add_argument("--ang-vel-scale", type=float, default=default_driver.scales_ang_vel)
    parser.add_argument("--dof-vel-scale", type=float, default=default_driver.scales_dof_vel)
    parser.add_argument("--gait-freq", type=float, default=default_driver.gait_freq)
    parser.add_argument("--vx", type=float, default=0.3)
    parser.add_argument("--vy", type=float, default=0.0)
    parser.add_argument("--yaw-rate", type=float, default=0.0)
    parser.add_argument("--height", type=float, default=0.0)
    parser.add_argument("--torso-yaw", type=float, default=0.0)
    parser.add_argument("--torso-pitch", type=float, default=0.0)
    parser.add_argument("--torso-roll", type=float, default=0.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backend = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    gs.init(backend=gs.gpu if backend == "cuda" else gs.cpu, logging_level="WARNING")
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        torch.backends.cudnn.deterministic = False
        torch.backends.cudnn.benchmark = False

    cfg = _load_env_cfg_from_entry(args.env_cfg_entry)
    cfg.scene.num_envs = args.num_envs
    cfg.scene.backend = backend
    cfg.scene.viewer = True
    cfg.observations.policy.enable_corruption = False
    cfg.commands.base_velocity.resampling_time_range = (1e9, 1e9)
    cfg.commands.base_velocity.rel_standing_envs = 0.0

    env = ManagerBasedRlEnv(cfg=cfg, device=backend)
    policy = AMOPolicy(
        model_dir=args.model_dir,
        device=backend,
        policy_filename=args.policy_file,
        adapter_filename=args.adapter_file,
        norm_stats_filename=args.norm_file,
        action_scale=args.action_scale,
        scales_ang_vel=args.ang_vel_scale,
        scales_dof_vel=args.dof_vel_scale,
        gait_freq=args.gait_freq,
    )

    robot = env.entities["robot"]
    robot_joint_names = list(robot.joint_names)
    amo_to_robot, robot_to_amo = build_joint_index_map(AMOPolicy.DOF_NAMES, robot_joint_names)
    action_dim = env.action_manager.total_action_dim

    state = CommandState(
        vx=args.vx,
        vy=args.vy,
        yaw_rate=args.yaw_rate,
        height=args.height,
        torso_yaw=args.torso_yaw,
        torso_pitch=args.torso_pitch,
        torso_roll=args.torso_roll,
        arm_enable=0.0,
    )
    controller = TerminalController(state)

    if args.print_spec:
        _print_amo_spec()
        print("\n=== Genesis joint order ===")
        for i, name in enumerate(robot_joint_names):
            print(f"  {i:2d}: {name}")
        print("\n=== Remap (AMO idx -> Genesis idx) ===")
        for i, j in enumerate(amo_to_robot):
            print(f"  {i:2d} ({AMOPolicy.DOF_NAMES[i]}) -> {j:2d} ({robot_joint_names[j]})")

    print("AMO Genesis play started.")
    if args.interactive:
        print("Controls: w/s vx, a/d yaw, e/c vy, z/x height, u/j yaw, i/k pitch, o/l roll, t arm, r reset, q quit")
        controller.start()

    env.reset()
    policy.reset()

    try:
        t0 = time.time()
        for step in range(args.max_steps):
            # Read latest robot state from env-0 and map to AMO joint order.
            joint_pos_robot = robot.data.joint_pos[0].detach().cpu().numpy()
            joint_vel_robot = robot.data.joint_vel[0].detach().cpu().numpy()
            quat_wxyz = robot.data.root_quat_w[0].detach().cpu().numpy()
            ang_vel_b = robot.data.root_ang_vel_b[0].detach().cpu().numpy()

            dof_pos_amo = joint_pos_robot[amo_to_robot].astype(np.float32)
            dof_vel_amo = joint_vel_robot[amo_to_robot].astype(np.float32)

            quit_now = controller.poll() if args.interactive else False
            if quit_now:
                break
            commands = controller.state.as_array() if args.interactive else state.as_array()

            pd_target_amo = policy.act(
                dof_pos=dof_pos_amo,
                dof_vel=dof_vel_amo,
                quat=quat_wxyz.astype(np.float32),
                ang_vel=ang_vel_b.astype(np.float32),
                commands=commands,
                dt=float(env.step_dt),
            )

            # Convert AMO target joint positions to Genesis action space.
            # The actuator is already in AMO order, so actions should be in AMO order too!
            # NO conversion to Genesis entity order needed!
            action_amo = (pd_target_amo - policy.DEFAULT_DOF_POS) / policy.action_scale

            actions = torch.zeros((env.num_envs, action_dim), dtype=torch.float32, device=env.device)
            usable = min(action_dim, action_amo.shape[0])
            actions[:, :usable] = torch.from_numpy(action_amo[:usable]).to(env.device)

            _, _, term, trunc, _ = env.step(actions)

            done = term | trunc
            if done.any():
                reset_ids = done.nonzero(as_tuple=False).squeeze(-1)
                env.reset(env_ids=reset_ids)
                if (reset_ids == 0).any():
                    policy.reset()

            if step % args.print_every == 0:
                fps = (step + 1) / max(1e-6, time.time() - t0)
                print(
                    f"step={step:06d} fps={fps:6.1f} "
                    f"cmd=[vx={commands[0]:.2f}, vy={commands[2]:.2f}, yaw={commands[1]:.2f}, h={0.75 + commands[3]:.2f}]"
                )
    finally:
        controller.stop()
        del env
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
