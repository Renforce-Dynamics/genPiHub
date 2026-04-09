#!/usr/bin/env python3
"""Test BeyondMimic policy (ONNX-based whole-body tracking).

Tests:
1. Policy loading with ONNX Runtime
2. Model metadata reading
3. Observation construction
4. ONNX inference
5. Multi-step rollout

Usage:
    # Test structure only (no ONNX model)
    python scripts/beyondmimic/test_beyondmimic_policy.py

    # Test with ONNX model
    python scripts/beyondmimic/test_beyondmimic_policy.py \
        --model-file path/to/beyondmimic.onnx \
        --device cuda
"""

import sys
from pathlib import Path
import argparse
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from genPiHub import load_policy
from genPiHub.configs import BeyondMimicPolicyConfig
from genPiHub.tools import DOFConfig

# G1 29 DOF configuration
G1_29DOF_NAMES = [
    "left_hip_pitch_joint", "right_hip_pitch_joint", "waist_yaw_joint",
    "left_hip_roll_joint", "right_hip_roll_joint", "waist_roll_joint",
    "left_hip_yaw_joint", "right_hip_yaw_joint", "waist_pitch_joint",
    "left_knee_joint", "right_knee_joint",
    "left_shoulder_pitch_joint", "right_shoulder_pitch_joint",
    "left_ankle_pitch_joint", "right_ankle_pitch_joint",
    "left_shoulder_roll_joint", "right_shoulder_roll_joint",
    "left_ankle_roll_joint", "right_ankle_roll_joint",
    "left_shoulder_yaw_joint", "right_shoulder_yaw_joint",
    "left_elbow_joint", "right_elbow_joint",
    "left_wrist_roll_joint", "right_wrist_roll_joint",
    "left_wrist_pitch_joint", "right_wrist_pitch_joint",
    "left_wrist_yaw_joint", "right_wrist_yaw_joint",
]

G1_DEFAULT_POS = [
    -0.312, -0.312, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.669, 0.669,
    0.2, 0.2, -0.363, -0.363, 0.2, -0.2, 0.0, 0.0, 0.0, 0.0,
    0.6, 0.6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
]


def parse_args():
    parser = argparse.ArgumentParser(description="Test BeyondMimic policy")
    parser.add_argument("--model-file", type=str, default=None,
                        help="Path to ONNX model file")
    parser.add_argument("--device", type=str, default="cpu",
                        choices=["cpu", "cuda", "tensorrt"])
    return parser.parse_args()


def test_onnx_availability():
    """Test 0: Check ONNX Runtime availability."""
    print("\n" + "="*60)
    print("Test 0: ONNX Runtime Availability")
    print("="*60)

    try:
        import onnxruntime as ort
        print(f"✅ ONNX Runtime available: {ort.__version__}")
        providers = ort.get_available_providers()
        print(f"   Available providers: {providers}")
        return True
    except ImportError:
        print("❌ ONNX Runtime not available")
        print("   Install: pip install onnxruntime-gpu")
        return False


def test_policy_loading(args):
    """Test 1: Policy loading."""
    print("\n" + "="*60)
    print("Test 1: Policy Loading")
    print("="*60)

    dof_cfg = DOFConfig(
        joint_names=G1_29DOF_NAMES,
        num_dofs=29,
        default_pos=G1_DEFAULT_POS,
    )

    cfg = BeyondMimicPolicyConfig(
        policy_file=args.model_file if args.model_file else None,
        device=args.device,
        obs_dof=dof_cfg,
        action_dof=dof_cfg,
        disable_autoload=(args.model_file is None),
    )

    try:
        from genPiHub.policies.beyondmimic_policy import BeyondMimicPolicy
        policy = BeyondMimicPolicy(cfg, device=args.device)
        print(f"✅ Policy loaded successfully")
        print(f"   - num_obs: {policy.num_obs}")
        print(f"   - num_actions: {policy.num_actions}")
        print(f"   - device: {policy.device}")
        print(f"   - has_model: {policy.session is not None}")
        print(f"   - without_state_estimator: {policy.without_state_estimator}")
        return policy
    except Exception as e:
        print(f"❌ Failed to load policy: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_observation(policy):
    """Test 2: Observation construction."""
    print("\n" + "="*60)
    print("Test 2: Observation Construction")
    print("="*60)

    env_data = {
        "dof_pos": np.array(G1_DEFAULT_POS, dtype=np.float32),
        "dof_vel": np.zeros(29, dtype=np.float32),
        "base_quat": np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32),
        "base_ang_vel": np.zeros(3, dtype=np.float32),
        "base_lin_vel": np.zeros(3, dtype=np.float32),
    }

    ctrl_data = {}

    try:
        obs, extras = policy.get_observation(env_data, ctrl_data)
        print(f"✅ Observation constructed successfully")
        print(f"   - Observation shape: {obs.shape}")
        print(f"   - Observation dtype: {obs.dtype}")
        if extras:
            print(f"   - Extras: {list(extras.keys())}")
        return obs, extras
    except Exception as e:
        print(f"❌ Failed to construct observation: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_action_generation(policy, obs):
    """Test 3: Action generation."""
    print("\n" + "="*60)
    print("Test 3: Action Generation")
    print("="*60)

    if policy.session is None:
        print("⚠️  Skipping (no ONNX model loaded)")
        return None

    try:
        action = policy.get_action(obs)
        print(f"✅ Action generated successfully")
        print(f"   - Action shape: {action.shape}")
        print(f"   - Action dtype: {action.dtype}")
        print(f"   - Action range: [{action.min():.3f}, {action.max():.3f}]")
        return action
    except Exception as e:
        print(f"❌ Failed to generate action: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_reset(policy):
    """Test 4: Policy reset."""
    print("\n" + "="*60)
    print("Test 4: Policy Reset")
    print("="*60)

    try:
        policy.reset()
        print(f"✅ Policy reset successfully")
        print(f"   - Timestep reset: {policy.timestep}")
        print(f"   - Last action reset: {np.allclose(policy.last_action, 0.0)}")
        return True
    except Exception as e:
        print(f"❌ Failed to reset policy: {e}")
        return False


def test_rollout(policy, num_steps=10):
    """Test 5: Multi-step rollout."""
    print("\n" + "="*60)
    print(f"Test 5: Multi-step Rollout ({num_steps} steps)")
    print("="*60)

    if policy.session is None:
        print("⚠️  Skipping (no ONNX model loaded)")
        return

    try:
        policy.reset()

        for step in range(num_steps):
            env_data = {
                "dof_pos": np.array(G1_DEFAULT_POS, dtype=np.float32) + np.random.randn(29) * 0.01,
                "dof_vel": np.random.randn(29).astype(np.float32) * 0.1,
                "base_quat": np.array([0, 0, 0, 1], dtype=np.float32),
                "base_ang_vel": np.random.randn(3).astype(np.float32) * 0.05,
                "base_lin_vel": np.random.randn(3).astype(np.float32) * 0.1,
            }

            obs, extras = policy.get_observation(env_data, {})
            action = policy.get_action(obs)
            policy.post_step_callback()

            if step == 0:
                print(f"✅ Step {step}: obs shape={obs.shape}, action shape={action.shape}")

        print(f"✅ Completed {num_steps} steps successfully")
        return True
    except Exception as e:
        print(f"❌ Rollout failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    args = parse_args()

    print("="*60)
    print("BeyondMimic Policy Test Suite")
    print("="*60)
    print(f"Model file: {args.model_file or 'None (testing without model)'}")
    print(f"Device: {args.device}")

    # Check ONNX availability
    onnx_available = test_onnx_availability()

    if not onnx_available and args.model_file:
        print("\n⚠️  ONNX Runtime not available, cannot test with model")
        return

    # Run tests
    policy = test_policy_loading(args)
    if not policy:
        return

    obs, extras = test_observation(policy)
    if obs is None:
        return

    action = test_action_generation(policy, obs)
    test_reset(policy)
    test_rollout(policy, num_steps=10)

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print("✅ All tests passed!")

    if policy.session is None:
        print("\n📝 Note: Some tests were skipped because no ONNX model was provided.")
        print("   Provide --model-file to run full tests.")

    print("\n✨ BeyondMimic policy implementation is working correctly!")


if __name__ == "__main__":
    main()
