"""Quick test for AMO policy through genPiHub.

Tests that the policy loads correctly and can perform inference.

Usage:
    python src/genPiHub/scripts/amo/test_amo_policy.py
"""

import sys
from pathlib import Path
import torch
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

# Import from genPiHub (not amo!)
from genPiHub import load_policy


def test_policy_loading():
    """Test that policy loads correctly."""
    print("="*60)
    print("TEST: Policy Loading")
    print("="*60)

    print("  → Loading AMO policy through genPiHub...")
    policy = load_policy(
        "AMOPolicy",
        model_dir=str(project_root / ".reference" / "AMO"),
        device="cuda" if torch.cuda.is_available() else "cpu"
    )

    print(f"  ✅ Policy loaded successfully")
    print(f"     Device: {policy.device}")
    print(f"     DOF count: {len(policy.dof_config.names)}")
    print(f"     Joint names: {policy.dof_config.names[:5]}... (showing first 5)")

    return policy


def test_observation_building(policy):
    """Test observation building."""
    print("\n" + "="*60)
    print("TEST: Observation Building")
    print("="*60)

    # Create dummy environment data
    batch_size = 1
    device = policy.device

    env_data = {
        "dof_pos": torch.zeros(batch_size, 23, device=device),
        "dof_vel": torch.zeros(batch_size, 23, device=device),
        "root_quat": torch.tensor([[1.0, 0.0, 0.0, 0.0]], device=device),  # identity quat
        "root_ang_vel": torch.zeros(batch_size, 3, device=device),
        "root_lin_vel": torch.zeros(batch_size, 3, device=device),
    }

    ctrl_data = {
        "command": torch.zeros(batch_size, 3, device=device),  # vx, vy, yaw_rate
    }

    print("  → Building observation...")
    obs, extras = policy.get_observation(env_data, ctrl_data)

    print(f"  ✅ Observation built successfully")
    print(f"     Shape: {obs.shape}")
    print(f"     Device: {obs.device}")
    print(f"     Dtype: {obs.dtype}")
    print(f"     Range: [{obs.min().item():.3f}, {obs.max().item():.3f}]")

    # Expected: 153 dim for AMO
    expected_dim = 153
    if obs.shape[-1] == expected_dim:
        print(f"  ✅ Observation dimension correct ({expected_dim})")
    else:
        print(f"  ⚠️  Warning: Expected {expected_dim} but got {obs.shape[-1]}")

    return obs


def test_action_generation(policy, obs):
    """Test action generation."""
    print("\n" + "="*60)
    print("TEST: Action Generation")
    print("="*60)

    print("  → Generating action...")
    action = policy.get_action(obs)

    print(f"  ✅ Action generated successfully")
    print(f"     Shape: {action.shape}")
    print(f"     Device: {action.device}")
    print(f"     Dtype: {action.dtype}")
    print(f"     Range: [{action.min().item():.3f}, {action.max().item():.3f}]")

    # Expected: 23 DOF for AMO
    expected_dof = 23
    if action.shape[-1] == expected_dof:
        print(f"  ✅ Action dimension correct ({expected_dof})")
    else:
        print(f"  ⚠️  Warning: Expected {expected_dof} but got {action.shape[-1]}")

    return action


def test_reset(policy):
    """Test policy reset."""
    print("\n" + "="*60)
    print("TEST: Policy Reset")
    print("="*60)

    print("  → Resetting policy...")
    policy.reset()

    print(f"  ✅ Policy reset successfully")


def test_multiple_steps(policy):
    """Test multiple inference steps."""
    print("\n" + "="*60)
    print("TEST: Multiple Steps")
    print("="*60)

    device = policy.device
    batch_size = 1

    # Create dummy data
    env_data = {
        "dof_pos": torch.zeros(batch_size, 23, device=device),
        "dof_vel": torch.zeros(batch_size, 23, device=device),
        "root_quat": torch.tensor([[1.0, 0.0, 0.0, 0.0]], device=device),
        "root_ang_vel": torch.zeros(batch_size, 3, device=device),
        "root_lin_vel": torch.zeros(batch_size, 3, device=device),
    }

    ctrl_data = {
        "command": torch.tensor([[0.5, 0.0, 0.0]], device=device),  # walk forward
    }

    print(f"  → Running 10 inference steps...")
    policy.reset()

    for step in range(10):
        obs, _ = policy.get_observation(env_data, ctrl_data)
        action = policy.get_action(obs)
        policy.post_step_callback()

        if step == 0:
            print(f"     Step {step}: obs {obs.shape}, action {action.shape}")

    print(f"  ✅ Multiple steps completed successfully")
    print(f"     Final action range: [{action.min().item():.3f}, {action.max().item():.3f}]")


def main():
    print("\n" + "="*60)
    print("  genPiHub AMO Policy Test")
    print("="*60)
    print(f"\nProject root: {project_root}")

    try:
        # Run all tests
        policy = test_policy_loading()
        test_reset(policy)
        obs = test_observation_building(policy)
        action = test_action_generation(policy, obs)
        test_multiple_steps(policy)

        # Summary
        print("\n" + "="*60)
        print("  ✅ ALL TESTS PASSED")
        print("="*60)
        print("\nAMO policy works correctly through genPiHub!")
        print("\nNext steps:")
        print("  • Test environment: python src/genPiHub/scripts/amo/test_amo_env.py")
        print("  • Run visual demo: python src/genPiHub/scripts/amo/play_amo.py --viewer")

        return 0

    except Exception as e:
        print("\n" + "="*60)
        print("  ❌ TEST FAILED")
        print("="*60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
