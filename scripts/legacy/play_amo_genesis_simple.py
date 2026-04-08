#!/usr/bin/env python3
"""Simplified AMO play script without curriculum manager issues.

This is a streamlined version that directly disables curriculum learning
to avoid terrain generator dependencies.

Usage:
    PYTHONPATH=src python scripts/play_amo_genesis_simple.py --interactive
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch
import genesis as gs

# Initialize Genesis
backend = "cuda" if torch.cuda.is_available() else "cpu"
gs.init(backend=gs.gpu if backend == "cuda" else gs.cpu, logging_level="WARNING")

from amo_genesis_env.amo_env_cfg import AmoGenesisEnvCfg
from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnv
from amo_policy import AMOPolicy, CommandState, TerminalController

# Create config
cfg = AmoGenesisEnvCfg()
cfg.scene.num_envs = 1
cfg.scene.backend = backend
cfg.scene.viewer = True
cfg.observations.policy.enable_corruption = False
cfg.commands.base_velocity.resampling_time_range = (1e9, 1e9)
cfg.commands.base_velocity.rel_standing_envs = 0.0

# ⭐ Fix: Disable curriculum manager to avoid terrain generator requirement
cfg.curriculum = None

print("Creating environment (curriculum disabled)...")
env = ManagerBasedRlEnv(cfg=cfg, device=backend)

# Load policy
policy = AMOPolicy(
    model_dir=".reference/AMO",
    device=backend,
)

# Setup
robot = env.entities["robot"]
robot_joint_names = list(robot.joint_names)

# Build joint mapping
from scripts.play_amo_genesis import _build_index_map
amo_to_robot, robot_to_amo = _build_index_map(AMOPolicy.DOF_NAMES, robot_joint_names)

# Command state
state = CommandState(vx=0.3)
controller = TerminalController(state)

print("\n✅ Setup complete!")
print("Controls: w/s vx, a/d yaw, e/c vy, z/x height, u/j/i/k/o/l torso, t arm, r reset, q quit")
print("Starting in 2 seconds...\n")

import time
time.sleep(2)

controller.start()
env.reset()
policy.reset()

import numpy as np

try:
    step = 0
    while True:
        # Poll keyboard
        quit_now = controller.poll()
        if quit_now:
            break

        # Get robot state
        joint_pos_robot = robot.data.joint_pos[0].detach().cpu().numpy()
        joint_vel_robot = robot.data.joint_vel[0].detach().cpu().numpy()
        quat_wxyz = robot.data.root_quat_w[0].detach().cpu().numpy()
        ang_vel_b = robot.data.root_ang_vel_b[0].detach().cpu().numpy()

        # Map to AMO order
        dof_pos_amo = joint_pos_robot[amo_to_robot].astype(np.float32)
        dof_vel_amo = joint_vel_robot[amo_to_robot].astype(np.float32)

        # Get commands
        commands = controller.state.as_array()

        # Run policy
        pd_target_amo = policy.act(
            dof_pos=dof_pos_amo,
            dof_vel=dof_vel_amo,
            quat=quat_wxyz.astype(np.float32),
            ang_vel=ang_vel_b.astype(np.float32),
            commands=commands,
            dt=float(env.step_dt),
        )

        # Convert to Genesis action
        action_amo = (pd_target_amo - policy.DEFAULT_DOF_POS) / policy.action_scale
        action_robot = np.zeros(len(robot_joint_names), dtype=np.float32)
        for ridx, aidx in enumerate(robot_to_amo):
            if aidx >= 0:
                action_robot[ridx] = action_amo[aidx]

        actions = torch.zeros((env.num_envs, env.action_manager.total_action_dim),
                             dtype=torch.float32, device=env.device)
        usable = min(env.action_manager.total_action_dim, action_robot.shape[0])
        actions[:, :usable] = torch.from_numpy(action_robot[:usable]).to(env.device)

        # Step environment
        _, _, term, trunc, _ = env.step(actions)

        # Handle resets
        done = term | trunc
        if done.any():
            reset_ids = done.nonzero(as_tuple=False).squeeze(-1)
            env.reset(env_ids=reset_ids)
            if (reset_ids == 0).any():
                policy.reset()

        # Print status
        if step % 100 == 0:
            print(f"step={step:06d} cmd=[vx={commands[0]:.2f}, vy={commands[2]:.2f}, "
                  f"yaw={commands[1]:.2f}, h={0.75+commands[3]:.2f}]")

        step += 1

finally:
    controller.stop()
    del env
    print("\nDone!")
