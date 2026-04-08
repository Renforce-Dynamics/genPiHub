"""Example: Using AMO policy through Policy Hub.

This demonstrates how to use the Policy Hub framework to load and run AMO policy.
"""

import sys
from pathlib import Path

# Add policy_hub parent to path
example_dir = Path(__file__).resolve().parent
policy_hub_dir = example_dir.parent
project_root = policy_hub_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import numpy as np

def main():
    print("="*60)
    print("Policy Hub - AMO Example")
    print("="*60)

    # Import Policy Hub
    try:
        from genPiHub import load_policy
        print("✅ Policy Hub imported")
    except ImportError as e:
        print(f"❌ Policy Hub not installed: {e}")
        print("   Run: pip install -e policy_hub")
        return 1

    # Load AMO policy
    print("\n[1] Loading AMO policy...")
    try:
        import torch
        model_dir = Path(".reference/AMO")
        device = "cuda" if torch.cuda.is_available() else "cpu"

        policy = load_policy(
            "AMOPolicy",
            policy_file=str(model_dir / "amo_jit.pt"),
            adapter_file=str(model_dir / "adapter_jit.pt"),
            norm_stats_file=str(model_dir / "adapter_norm_stats.pt"),
            device=device
        )
        print(f"✅ AMO policy loaded")
        print(f"   - Device: {device}")
        print(f"   - Control frequency: {policy.freq} Hz")
        print(f"   - Number of actions: {policy.num_actions}")
    except Exception as e:
        print(f"❌ Failed to load policy: {e}")
        return 1

    # Reset policy
    print("\n[2] Resetting policy...")
    policy.reset()
    print("✅ Policy reset")

    # Create dummy environment data
    print("\n[3] Creating dummy environment data...")
    env_data = {
        "dof_pos": np.zeros(23, dtype=np.float32),
        "dof_vel": np.zeros(23, dtype=np.float32),
        "base_quat": np.array([0, 0, 0, 1], dtype=np.float32),
        "base_ang_vel": np.zeros(3, dtype=np.float32),
        "commands": np.array([0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),  # vx=0.3
    }
    print("✅ Environment data created")

    # Get observation
    print("\n[4] Getting observation...")
    obs, extras = policy.get_observation(env_data, {})
    print(f"✅ Observation retrieved")

    # Get action
    print("\n[5] Getting action...")
    action = policy.get_action(obs)
    print(f"✅ Action computed: shape={action.shape}")

    # Get init pose
    print("\n[6] Getting initial DOF positions...")
    init_pos = policy.get_init_dof_pos()
    print(f"✅ Initial positions: {init_pos[:5]}... (showing first 5)")

    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60)
    print("\nPolicy Hub is working correctly.")
    print("You can now use it to load and run different policies.")
    print("\nNext steps:")
    print("  - Integrate with Genesis environment")
    print("  - Add more policies (CLOT, ProtoMotions, etc.)")
    print("  - Create environment adapters")

    return 0


if __name__ == "__main__":
    exit(main())
