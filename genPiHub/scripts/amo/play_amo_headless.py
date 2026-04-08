"""Run AMO policy in headless mode (no viewer).

Requires: pip install -e . (from project root)
"""

import numpy as np
import torch

import genesis as gs
from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnv

# Import from genPiHub (not amo package!)
from genPiHub import load_policy
from genPiHub.configs import create_amo_genesis_env_config
from genPiHub.tools import build_joint_index_map


def main():
    print("="*60)
    print("AMO GenesisLab Headless Test")
    print("="*60)

    # Initialize
    gs.init(backend=gs.gpu, logging_level="WARNING")

    # Create environment config using genPiHub
    env_cfg = create_amo_genesis_env_config(
        num_envs=1,
        backend="cuda",
        viewer=False,  # Headless mode
    )

    # Create environment
    env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda")

    # Load policy using genPiHub
    policy = load_policy("AMOPolicy", model_dir=".reference/AMO", device="cuda")

    robot = env.entities["robot"]
    robot_joint_names = list(robot.joint_names)

    # Get DOF names from policy
    policy_dof_names = policy.dof_config.names

    # Build joint mapping using genPiHub utility
    amo_to_robot, _ = build_joint_index_map(policy_dof_names, robot_joint_names)

    print(f"\n✅ Environment created")
    print(f"   - Robot joints: {len(robot_joint_names)}")
    print(f"   - Action dim: {env.action_manager.total_action_dim}")
    print(f"   - Physics dt: {env.physics_dt:.5f}s")
    print(f"   - Control dt: {env.step_dt:.5f}s")

    # Test with zero velocity command (standing)
    env.reset()
    policy.reset()

    # Command: zero velocity (standing)
    commands = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)

    print("\n" + "="*60)
    print("Running 500 steps with zero velocity (standing)...")
    print("="*60)

    heights = []
    x_positions = []
    for step in range(500):
        # Read state
        joint_pos_robot = robot.data.joint_pos[0].detach().cpu().numpy()
        joint_vel_robot = robot.data.joint_vel[0].detach().cpu().numpy()
        quat_wxyz = robot.data.root_quat_w[0].detach().cpu().numpy()
        ang_vel_b = robot.data.root_ang_vel_b[0].detach().cpu().numpy()
        base_pos = robot.data.root_pos_w[0].detach().cpu().numpy()
        base_vel = robot.data.root_lin_vel_b[0].detach().cpu().numpy()  # Body frame velocity

        # Map to AMO order
        dof_pos_amo = joint_pos_robot[amo_to_robot].astype(np.float32)
        dof_vel_amo = joint_vel_robot[amo_to_robot].astype(np.float32)

        # Build observation using policy interface
        env_data = {
            "dof_pos": torch.from_numpy(dof_pos_amo).unsqueeze(0).to(env.device),
            "dof_vel": torch.from_numpy(dof_vel_amo).unsqueeze(0).to(env.device),
            "root_quat": torch.from_numpy(quat_wxyz).unsqueeze(0).to(env.device),
            "root_ang_vel": torch.from_numpy(ang_vel_b).unsqueeze(0).to(env.device),
            "root_lin_vel": torch.from_numpy(base_vel).unsqueeze(0).to(env.device),
        }

        ctrl_data = {
            "command": torch.from_numpy(commands[:3]).unsqueeze(0).to(env.device),
        }

        # Get observation and action through genPiHub policy interface
        obs, _ = policy.get_observation(env_data, ctrl_data)
        action_tensor = policy.get_action(obs)
        action_amo = action_tensor[0].detach().cpu().numpy()

        actions = torch.zeros(
            (env.num_envs, env.action_manager.total_action_dim),
            dtype=torch.float32,
            device=env.device
        )
        usable = min(env.action_manager.total_action_dim, len(action_amo))
        actions[:, :usable] = torch.from_numpy(action_amo[:usable]).to(env.device)

        # Step
        _, _, term, trunc, _ = env.step(actions)

        heights.append(base_pos[2])
        x_positions.append(base_pos[0])

        if step % 50 == 0:
            roll_deg = np.rad2deg(np.arcsin(np.clip(2*(quat_wxyz[0]*quat_wxyz[1] + quat_wxyz[2]*quat_wxyz[3]), -1, 1)))
            pitch_deg = np.rad2deg(np.arcsin(np.clip(2*(quat_wxyz[0]*quat_wxyz[2] - quat_wxyz[3]*quat_wxyz[1]), -1, 1)))
            print(f"Step {step:3d}: x={base_pos[0]:6.2f}m, h={base_pos[2]:.3f}m, vx={base_vel[0]:5.2f}m/s, "
                  f"roll={roll_deg:5.1f}°, pitch={pitch_deg:5.1f}°")

        if term[0] or trunc[0]:
            print(f"\n⚠️  Episode ended at step {step}!")
            print(f"   Terminated: {term[0].item()}, Truncated: {trunc[0].item()}")
            break

    print("\n" + "="*60)
    print("Test Results:")
    print("="*60)
    print(f"Steps completed: {len(heights)}/500")
    print(f"Distance traveled: {x_positions[-1] - x_positions[0]:.2f}m")
    print(f"Average velocity: {(x_positions[-1] - x_positions[0]) / (len(heights) * env.step_dt):.3f}m/s")
    print(f"Final height: {heights[-1]:.3f}m")
    print(f"Min height: {min(heights):.3f}m")
    print(f"Max height: {max(heights):.3f}m")
    print(f"Height std: {np.std(heights):.3f}m")

    if len(heights) >= 500 and heights[-1] > 0.5:
        print("\n✅ SUCCESS: Robot is walking stably!")
    elif len(heights) < 500:
        print(f"\n❌ FAILED: Robot fell at step {len(heights)}")
    else:
        print(f"\n⚠️  WARNING: Robot height too low ({heights[-1]:.3f}m)")

    del env
    return 0

if __name__ == "__main__":
    main()
