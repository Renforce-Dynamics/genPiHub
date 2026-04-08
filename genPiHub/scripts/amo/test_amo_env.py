"""Test AMO environment initialization and observation building."""

import sys
from pathlib import Path

hvla_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(hvla_root / "src"))

import numpy as np
import torch
import genesis as gs

print("="*60)
print("AMO Environment Initialization Test")
print("="*60)

# Initialize Genesis
backend = "cuda" if torch.cuda.is_available() else "cpu"
gs.init(backend=gs.gpu if backend == "cuda" else gs.cpu, logging_level="WARNING")

print(f"\n[1/4] Genesis initialized (backend: {backend})")

# Load environment config
try:
    from genPiHub.configs import create_amo_genesis_env_config
    from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnv

    cfg = AmoGenesisEnvCfg()
    cfg.scene.num_envs = 1
    cfg.scene.backend = backend
    cfg.scene.viewer = False  # No viewer for testing
    cfg.observations.policy.enable_corruption = False

    print(f"\n[2/4] Creating environment...")
    print(f"  - num_envs: {cfg.scene.num_envs}")
    print(f"  - decimation: {cfg.decimation}")
    print(f"  - dt: {cfg.scene.dt}")
    print(f"  - episode_length: {cfg.episode_length_s}s")

    env = ManagerBasedRlEnv(cfg=cfg, device=backend)
    print(f"✓ Environment created successfully")
    print(f"  - action_dim: {env.action_manager.total_action_dim}")
    print(f"  - observation_dim: {env.observation_manager.group_obs_dim}")

except Exception as e:
    print(f"✗ Environment creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test reset
print(f"\n[3/4] Testing environment reset...")
try:
    obs_dict, _ = env.reset()
    print(f"✓ Reset successful")

    if "policy" in obs_dict:
        policy_obs = obs_dict["policy"]
        print(f"  - policy observation shape: {policy_obs.shape}")
        print(f"  - policy observation device: {policy_obs.device}")
        print(f"  - policy observation dtype: {policy_obs.dtype}")
        print(f"  - policy observation range: [{policy_obs.min():.3f}, {policy_obs.max():.3f}]")
    else:
        print(f"  Available observations: {list(obs_dict.keys())}")

except Exception as e:
    print(f"✗ Reset failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test stepping with AMO policy
print(f"\n[4/4] Testing AMO policy + environment step...")
try:
    from genPiHub import load_policy

    policy = AMOPolicy(
        model_dir=str(hvla_root / ".reference/AMO"),
        device=backend,
    )
    policy.reset()

    robot = env.entities["robot"]
    robot_joint_names = list(robot.joint_names)

    # Build joint mapping
    from scripts.play_amo_genesis import _build_index_map
    amo_to_robot, robot_to_amo = _build_index_map(AMOPolicy.DOF_NAMES, robot_joint_names)

    print(f"  - Joint mapping built: {len(amo_to_robot)} AMO joints -> {len(robot_joint_names)} robot joints")

    # Run a few steps
    for step in range(5):
        # Extract robot state
        joint_pos_robot = robot.data.joint_pos[0].detach().cpu().numpy()
        joint_vel_robot = robot.data.joint_vel[0].detach().cpu().numpy()
        quat_wxyz = robot.data.root_quat_w[0].detach().cpu().numpy()
        ang_vel_b = robot.data.root_ang_vel_b[0].detach().cpu().numpy()

        # Map to AMO joint order
        dof_pos_amo = joint_pos_robot[amo_to_robot].astype(np.float32)
        dof_vel_amo = joint_vel_robot[amo_to_robot].astype(np.float32)

        # Commands (zero for testing)
        commands = np.zeros(8, dtype=np.float32)

        # Run policy
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
        usable = min(env.action_manager.total_action_dim, action_robot.shape[0])
        actions[:, :usable] = torch.from_numpy(action_robot[:usable]).to(env.device)

        # Step environment
        obs_dict, rewards, terminated, truncated, info = env.step(actions)

        if step == 0:
            print(f"  ✓ First step successful")
            print(f"    - action range: [{action_robot.min():.3f}, {action_robot.max():.3f}]")
            print(f"    - reward: {rewards[0].item():.3f}")

    print(f"  ✓ All 5 steps completed successfully")

except Exception as e:
    print(f"  ✗ Stepping failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("✅ All tests PASSED!")
print("\nEnvironment is ready. You can now run:")
print("  PYTHONPATH=src python scripts/play_amo_genesis.py --interactive")
print("="*60)
