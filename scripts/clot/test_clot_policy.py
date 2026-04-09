#!/usr/bin/env python3
"""Test CLOT policy loading and basic functionality.

This script tests the CLOT policy implementation to ensure:
1. Policy loads correctly
2. Configuration is valid
3. Observations can be constructed
4. Actions can be generated
5. No runtime errors occur

Usage:
    python scripts/clot/test_clot_policy.py
    python scripts/clot/test_clot_policy.py --model-file path/to/clot_policy.pt
"""

import sys
from pathlib import Path
import argparse
import numpy as np

# Add genPiHub to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from genPiHub import load_policy
from genPiHub.configs import CLOTPolicyConfig
from genPiHub.tools import DOFConfig

# G1 joint names and default positions (copied to avoid importing env_cfg)
G1_23DOF_NAMES = [
    "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
    "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
    "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
    "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
    "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint", "left_elbow_joint",
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint", "right_elbow_joint",
]

G1_CLOT_DEFAULT_POS = [
    -0.1, 0.0, 0.0, 0.3, -0.2, 0.0,  # Left leg
    -0.1, 0.0, 0.0, 0.3, -0.2, 0.0,  # Right leg
    0.0, 0.0, 0.0,  # Torso
    0.5, 0.0, 0.2, 0.3,  # Left arm
    0.5, 0.0, -0.2, 0.3,  # Right arm
]


def parse_args():
    parser = argparse.ArgumentParser(description="Test CLOT policy")
    parser.add_argument("--model-file", type=str, default=None,
                        help="Path to CLOT model file (.pt)")
    parser.add_argument("--motion-lib-dir", type=str, default=None,
                        help="Path to motion library directory")
    parser.add_argument("--device", type=str, default="cpu",
                        choices=["cpu", "cuda"])
    return parser.parse_args()


def test_policy_loading(args):
    """Test 1: Policy loading."""
    print("\n" + "="*60)
    print("Test 1: Policy Loading")
    print("="*60)

    # Create DOF config
    dof_cfg = DOFConfig(
        joint_names=G1_23DOF_NAMES,
        num_dofs=23,
        default_pos=G1_CLOT_DEFAULT_POS,
    )

    # Create policy config
    cfg = CLOTPolicyConfig(
        policy_file=args.model_file if args.model_file else None,
        motion_lib_dir=args.motion_lib_dir if args.motion_lib_dir else None,
        device=args.device,
        obs_dof=dof_cfg,
        action_dof=dof_cfg,
        action_scale=0.25,
        disable_autoload=(args.model_file is None),  # Don't load if no file provided
    )

    # Load policy
    try:
        from genPiHub.policies.clot_policy import CLOTPolicy
        policy = CLOTPolicy(cfg, device=args.device)
        print(f"✅ Policy loaded successfully")
        print(f"   - num_obs: {policy.num_obs}")
        print(f"   - num_actions: {policy.num_actions}")
        print(f"   - device: {policy.device}")
        print(f"   - has_model: {policy.model is not None}")
        print(f"   - has_motion_lib: {policy.motion_lib is not None}")
        return policy
    except Exception as e:
        print(f"❌ Failed to load policy: {e}")
        raise


def test_observation(policy):
    """Test 2: Observation construction."""
    print("\n" + "="*60)
    print("Test 2: Observation Construction")
    print("="*60)

    # Create fake environment data
    env_data = {
        "dof_pos": np.array(G1_CLOT_DEFAULT_POS, dtype=np.float32),
        "dof_vel": np.zeros(23, dtype=np.float32),
        "base_quat": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        "base_ang_vel": np.zeros(3, dtype=np.float32),
        "base_lin_vel": np.zeros(3, dtype=np.float32),
        "base_pos": np.array([0.0, 0.0, 0.75], dtype=np.float32),
    }

    ctrl_data = {}

    try:
        obs, extras = policy.get_observation(env_data, ctrl_data)
        print(f"✅ Observation constructed successfully")

        if isinstance(obs, dict):
            print(f"   - Observation type: dict")
            for key, value in obs.items():
                if isinstance(value, np.ndarray):
                    print(f"   - {key}: shape={value.shape}, dtype={value.dtype}")
        else:
            print(f"   - Observation shape: {obs.shape}")
            print(f"   - Observation dtype: {obs.dtype}")

        if extras:
            print(f"   - Extras keys: {list(extras.keys())}")
            if "amp_obs" in extras:
                print(f"   - AMP obs shape: {extras['amp_obs'].shape}")

        return obs, extras
    except Exception as e:
        print(f"❌ Failed to construct observation: {e}")
        raise


def test_action_generation(policy, obs):
    """Test 3: Action generation."""
    print("\n" + "="*60)
    print("Test 3: Action Generation")
    print("="*60)

    # Skip if no model loaded
    if policy.model is None:
        print("⚠️  Skipping (no model loaded)")
        print("   Provide --model-file to test action generation")
        return None

    try:
        action = policy.get_action(obs)
        print(f"✅ Action generated successfully")
        print(f"   - Action shape: {action.shape}")
        print(f"   - Action dtype: {action.dtype}")
        print(f"   - Action range: [{action.min():.3f}, {action.max():.3f}]")
        print(f"   - Action mean: {action.mean():.3f}")
        print(f"   - Action std: {action.std():.3f}")
        return action
    except Exception as e:
        print(f"❌ Failed to generate action: {e}")
        raise


def test_reset(policy):
    """Test 4: Policy reset."""
    print("\n" + "="*60)
    print("Test 4: Policy Reset")
    print("="*60)

    try:
        policy.reset()
        print(f"✅ Policy reset successfully")
        print(f"   - Last action reset to zeros: {np.allclose(policy.last_action, 0.0)}")
        return True
    except Exception as e:
        print(f"❌ Failed to reset policy: {e}")
        raise


def test_rollout(policy, num_steps=10):
    """Test 5: Multi-step rollout."""
    print("\n" + "="*60)
    print(f"Test 5: Multi-step Rollout ({num_steps} steps)")
    print("="*60)

    # Skip if no model
    if policy.model is None:
        print("⚠️  Skipping (no model loaded)")
        return

    try:
        policy.reset()

        for step in range(num_steps):
            # Create env data
            env_data = {
                "dof_pos": np.array(G1_CLOT_DEFAULT_POS, dtype=np.float32) + np.random.randn(23) * 0.01,
                "dof_vel": np.random.randn(23).astype(np.float32) * 0.1,
                "base_quat": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
                "base_ang_vel": np.random.randn(3).astype(np.float32) * 0.05,
                "base_lin_vel": np.random.randn(3).astype(np.float32) * 0.1,
                "base_pos": np.array([0.0, 0.0, 0.75], dtype=np.float32),
            }

            # Get observation and action
            obs, extras = policy.get_observation(env_data, {})
            action = policy.get_action(obs)

            if step == 0:
                print(f"✅ Step {step}: obs shape={obs.shape if not isinstance(obs, dict) else 'dict'}, "
                      f"action shape={action.shape}")

        print(f"✅ Completed {num_steps} steps successfully")
        return True
    except Exception as e:
        print(f"❌ Rollout failed at step {step}: {e}")
        raise


def main():
    args = parse_args()

    print("="*60)
    print("CLOT Policy Test Suite")
    print("="*60)
    print(f"Model file: {args.model_file or 'None (testing without model)'}")
    print(f"Motion lib: {args.motion_lib_dir or 'None'}")
    print(f"Device: {args.device}")

    # Run tests
    policy = test_policy_loading(args)
    obs, extras = test_observation(policy)
    action = test_action_generation(policy, obs)
    test_reset(policy)
    test_rollout(policy, num_steps=10)

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print("✅ All tests passed!")

    if policy.model is None:
        print("\n📝 Note: Some tests were skipped because no model was provided.")
        print("   Provide --model-file to run full tests.")

    print("\n✨ CLOT policy implementation is working correctly!")


if __name__ == "__main__":
    main()
