"""Debug AMO integration - check all key parameters."""

import sys
from pathlib import Path
import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import genesis as gs
from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnv
from genPiHub.configs import create_amo_genesis_env_config
from genPiHub import load_policy

def main():
    print("="*60)
    print("AMO Integration Debug")
    print("="*60)

    # Initialize Genesis
    gs.init(backend=gs.gpu, logging_level="WARNING")

    # Create environment
    cfg = AmoGenesisEnvCfg()
    cfg.scene.num_envs = 1
    cfg.scene.backend = "cuda"
    cfg.scene.viewer = False
    env = ManagerBasedRlEnv(cfg=cfg, device="cuda")

    # Load AMO policy
    policy = AMOPolicy(
        model_dir=".reference/AMO",
        device="cuda",
    )

    # Get robot info
    robot = env.entities["robot"]
    robot_joint_names = list(robot.joint_names)

    print("\n1. Joint Names Comparison:")
    print("-" * 60)
    print("AMO joint names (23):")
    for i, name in enumerate(AMOPolicy.DOF_NAMES):
        print(f"  {i:2d}: {name}")

    print("\nGenesis robot joint names:")
    for i, name in enumerate(robot_joint_names):
        print(f"  {i:2d}: {name}")

    print("\n2. Default Joint Positions:")
    print("-" * 60)
    print("AMO DEFAULT_DOF_POS:")
    print(policy.DEFAULT_DOF_POS)

    print("\nGenesis default_joint_pos:")
    genesis_default = robot.data.default_joint_pos[0].detach().cpu().numpy()
    print(genesis_default)

    print("\nDifference:")
    if len(genesis_default) == len(policy.DEFAULT_DOF_POS):
        diff = genesis_default - policy.DEFAULT_DOF_POS
        print(diff)
        print(f"Max abs difference: {np.abs(diff).max():.6f}")
    else:
        print(f"Length mismatch: Genesis={len(genesis_default)}, AMO={len(policy.DEFAULT_DOF_POS)}")

    print("\n3. Action Manager Info:")
    print("-" * 60)
    action_term = env.action_manager.get_term("joint_pos")
    print(f"Action dimension: {action_term.action_dim}")
    print(f"Scale values: {action_term._scale_values.cpu().numpy()}")
    print(f"Offset values: {action_term._offset_values.cpu().numpy()}")
    print(f"Use default offset: {action_term._use_default_offset}")

    print("\n4. Control Parameters:")
    print("-" * 60)
    print(f"Decimation: {env.cfg.decimation}")
    print(f"Physics dt: {env.physics_dt:.5f}")
    print(f"Step dt (control): {env.step_dt:.5f}")
    print(f"Expected control freq: {1.0/env.step_dt:.1f} Hz")

    print("\n5. PD Parameters (from robot):")
    print("-" * 60)
    # Try to get kp/kd from robot
    if hasattr(robot, 'actuators'):
        print("Robot has actuators")
        for name, actuator in robot.actuators.items():
            print(f"  {name}: {type(actuator).__name__}")

    print("\nAMO expected PD params:")
    print(f"Stiffness: {policy.STIFFNESS}")
    print(f"Damping: {policy.DAMPING}")

    print("\n6. Test policy inference:")
    print("-" * 60)
    env.reset()

    # Get current state
    joint_pos = robot.data.joint_pos[0].detach().cpu().numpy()
    joint_vel = robot.data.joint_vel[0].detach().cpu().numpy()
    quat = robot.data.root_quat_w[0].detach().cpu().numpy()
    ang_vel = robot.data.root_ang_vel_b[0].detach().cpu().numpy()

    print(f"Current joint_pos: {joint_pos}")
    print(f"Current joint_vel: {joint_vel}")
    print(f"Current quat: {quat}")
    print(f"Current ang_vel: {ang_vel}")

    # Test policy
    commands = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)

    try:
        pd_target = policy.act(
            dof_pos=joint_pos[:23],
            dof_vel=joint_vel[:23],
            quat=quat,
            ang_vel=ang_vel,
            commands=commands,
            dt=env.step_dt,
        )
        print(f"\nPolicy output (pd_target): {pd_target}")
        print(f"PD target shape: {pd_target.shape}")
        print(f"PD target - default: {pd_target - policy.DEFAULT_DOF_POS}")
    except Exception as e:
        print(f"\nPolicy inference FAILED: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("Debug complete")
    print("="*60)

if __name__ == "__main__":
    main()
