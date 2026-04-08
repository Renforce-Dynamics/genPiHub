"""Test AMO policy in headless mode to verify integration."""

import sys
from pathlib import Path
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import genesis as gs
from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnv
from amo_genesis_env import AmoGenesisEnvCfg
from amo_policy import AMOPolicy

def main():
    print("="*60)
    print("AMO Headless Test - Checking if robot can stand")
    print("="*60)

    # Initialize
    gs.init(backend=gs.gpu, logging_level="WARNING")

    # Create environment (no viewer)
    cfg = AmoGenesisEnvCfg()
    cfg.scene.num_envs = 1
    cfg.scene.backend = "cuda"
    cfg.scene.viewer = False  # Headless!
    env = ManagerBasedRlEnv(cfg=cfg, device="cuda")

    # Load policy
    policy = AMOPolicy(model_dir=".reference/AMO", device="cuda")

    robot = env.entities["robot"]
    robot_joint_names = list(robot.joint_names)

    print(f"\nRobot has {len(robot_joint_names)} joints:")
    for i, name in enumerate(robot_joint_names):
        print(f"  {i:2d}: {name}")

    # Build joint mapping
    robot_norm = {name.lower().replace("_joint", ""): i for i, name in enumerate(robot_joint_names)}
    amo_to_robot = []
    for name in AMOPolicy.DOF_NAMES:
        key = name.lower()
        if key not in robot_norm:
            raise ValueError(f"AMO joint '{name}' not found! Available: {list(robot_norm.keys())}")
        amo_to_robot.append(robot_norm[key])

    robot_to_amo = [-1] * len(robot_joint_names)
    for amo_i, robot_i in enumerate(amo_to_robot):
        robot_to_amo[robot_i] = amo_i

    print(f"\nAction dimension: {env.action_manager.total_action_dim}")
    print(f"Expected: {AMOPolicy.NUM_DOFS}")

    # Test
    env.reset()
    policy.reset()

    commands = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)

    print("\n" + "="*60)
    print("Running 100 steps with zero velocity command...")
    print("="*60)

    heights = []
    for step in range(100):
        # Read state
        joint_pos_robot = robot.data.joint_pos[0].detach().cpu().numpy()
        joint_vel_robot = robot.data.joint_vel[0].detach().cpu().numpy()
        quat_wxyz = robot.data.root_quat_w[0].detach().cpu().numpy()
        ang_vel_b = robot.data.root_ang_vel_b[0].detach().cpu().numpy()
        base_pos = robot.data.root_pos_w[0].detach().cpu().numpy()

        # Map to AMO order
        dof_pos_amo = joint_pos_robot[amo_to_robot].astype(np.float32)
        dof_vel_amo = joint_vel_robot[amo_to_robot].astype(np.float32)

        # Policy inference
        pd_target_amo = policy.act(
            dof_pos=dof_pos_amo,
            dof_vel=dof_vel_amo,
            quat=quat_wxyz.astype(np.float32),
            ang_vel=ang_vel_b.astype(np.float32),
            commands=commands,
            dt=float(env.step_dt),
        )

        # Convert to robot action
        action_amo = (pd_target_amo - policy.DEFAULT_DOF_POS) / policy.action_scale
        action_robot = np.zeros(len(robot_joint_names), dtype=np.float32)
        for ridx, aidx in enumerate(robot_to_amo):
            if aidx >= 0:
                action_robot[ridx] = action_amo[aidx]

        actions = torch.zeros((env.num_envs, env.action_manager.total_action_dim), dtype=torch.float32, device=env.device)
        actions[:, :len(action_robot)] = torch.from_numpy(action_robot).to(env.device)

        # Step
        _, _, term, trunc, _ = env.step(actions)

        heights.append(base_pos[2])

        if step % 20 == 0:
            print(f"Step {step:3d}: height={base_pos[2]:.3f}m, "
                  f"quat={quat_wxyz}, "
                  f"term={term[0].item()}, trunc={trunc[0].item()}")

        if term[0] or trunc[0]:
            print(f"\n⚠️  Robot fell at step {step}!")
            break

    print("\n" + "="*60)
    print("Test Results:")
    print("="*60)
    print(f"Final height: {heights[-1]:.3f}m")
    print(f"Min height: {min(heights):.3f}m")
    print(f"Max height: {max(heights):.3f}m")
    print(f"Height std: {np.std(heights):.3f}m")

    if heights[-1] > 0.5:
        print("\n✅ SUCCESS: Robot is standing!")
    else:
        print("\n❌ FAILED: Robot fell down!")

    return 0

if __name__ == "__main__":
    main()
