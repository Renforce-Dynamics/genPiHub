#!/usr/bin/env python3
"""
genPiHub Compatibility Test

Tests that genPiHub policies work correctly with genesislab environments.
This is the PRIMARY test to verify hub-genesislab compatibility.

Usage:
    python test_hub.py
    python test_hub.py --verbose
    python test_hub.py --num-steps 100
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all imports work without conflicts."""
    print("\n" + "="*60)
    print("TEST 1: Import Compatibility")
    print("="*60)

    try:
        # Test genPiHub imports
        print("  → Importing genPiHub...")
        from genPiHub import load_policy
        from genPiHub.configs import AMOPolicyConfig
        from genPiHub.environments import GenesisEnv
        print("  ✅ genPiHub imports successful")

        # Test genesislab imports
        print("  → Importing genesislab...")
        import genesis as gs
        from genesislab.envs import ManagerBasedRlEnv
        print("  ✅ genesislab imports successful")

        # Test no conflicts
        print("  → Checking for conflicts...")
        print(f"     genPiHub version: {load_policy.__module__}")
        print(f"     Genesis backend: {gs.cuda_available()}")
        print("  ✅ No import conflicts detected")

        return True

    except Exception as e:
        print(f"  ❌ Import test FAILED: {e}")
        return False


def test_policy_loading():
    """Test that genPiHub can load policies."""
    print("\n" + "="*60)
    print("TEST 2: Policy Loading")
    print("="*60)

    try:
        from genPiHub import load_policy

        print("  → Loading AMO policy...")
        policy = load_policy(
            "AMOPolicy",
            model_dir=str(project_root / ".reference" / "AMO"),
            device="cuda"
        )
        print("  ✅ Policy loaded successfully")

        print("  → Resetting policy...")
        policy.reset()
        print("  ✅ Policy reset successful")

        return True

    except Exception as e:
        print(f"  ❌ Policy loading FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment_creation():
    """Test that Genesis environment can be created."""
    print("\n" + "="*60)
    print("TEST 3: Environment Creation")
    print("="*60)

    try:
        import genesis as gs
        from genPiHub.configs import create_amo_genesis_env_config

        print("  → Initializing Genesis...")
        gs.init(backend=gs.cuda)
        print("  ✅ Genesis initialized")

        print("  → Creating environment config...")
        env_cfg = create_amo_genesis_env_config(
            num_envs=1,
            backend="cuda",
            viewer=False,
        )
        print("  ✅ Config created")

        print("  → Creating Genesis scene...")
        scene = gs.Scene(
            show_viewer=False,
            **env_cfg.scene.__dict__
        )
        print("  ✅ Scene created")

        print("  → Building scene...")
        scene.build()
        print("  ✅ Scene built successfully")

        return True

    except Exception as e:
        print(f"  ❌ Environment creation FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration(num_steps=10, verbose=False):
    """Test full integration: policy + environment."""
    print("\n" + "="*60)
    print("TEST 4: Hub-GenesisLab Integration")
    print("="*60)

    try:
        import torch
        import genesis as gs
        from genPiHub import load_policy
        from genPiHub.configs import create_amo_genesis_env_config
        from genesislab.envs import ManagerBasedRlEnv

        # Initialize Genesis
        print("  → Initializing Genesis...")
        gs.init(backend=gs.cuda)

        # Create environment config
        print("  → Creating environment config...")
        env_cfg = create_amo_genesis_env_config(
            num_envs=1,
            backend="cuda",
            viewer=False,
        )

        # Create scene
        print("  → Creating Genesis scene...")
        scene = gs.Scene(show_viewer=False, **env_cfg.scene.__dict__)

        # Create environment
        print("  → Creating ManagerBasedRlEnv...")
        env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda")

        # Build
        print("  → Building environment...")
        scene.build()

        # Load policy
        print("  → Loading AMO policy...")
        policy = load_policy(
            "AMOPolicy",
            model_dir=str(project_root / ".reference" / "AMO"),
            device="cuda"
        )

        # Reset
        print("  → Resetting environment and policy...")
        env.reset()
        policy.reset()

        # Run integration test
        print(f"  → Running {num_steps} integration steps...")
        for step in range(num_steps):
            # Get environment data
            env_data = {
                "dof_pos": env.entities["robot"].data.dof_pos,
                "dof_vel": env.entities["robot"].data.dof_vel,
                "root_quat": env.entities["robot"].data.root_quat_w,
                "root_lin_vel": env.entities["robot"].data.root_lin_vel_b,
                "root_ang_vel": env.entities["robot"].data.root_ang_vel_b,
            }

            # Create control data
            ctrl_data = {
                "command": torch.tensor([[0.5, 0.0, 0.0]], device="cuda"),
            }

            # Get observation from policy
            obs, extras = policy.get_observation(env_data, ctrl_data)

            # Get action from policy
            action = policy.get_action(obs)

            # Step environment
            env.step(action)

            # Post-step callback
            policy.post_step_callback()

            if verbose and step % 5 == 0:
                print(f"     Step {step}: obs.shape={obs.shape}, action.shape={action.shape}")

        print(f"  ✅ Integration test PASSED ({num_steps} steps)")
        print(f"     Final observation shape: {obs.shape}")
        print(f"     Final action shape: {action.shape}")

        return True

    except Exception as e:
        print(f"  ❌ Integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Test genPiHub-genesislab compatibility")
    parser.add_argument("--num-steps", type=int, default=10, help="Number of integration steps")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  genPiHub ↔ genesislab Compatibility Test")
    print("="*60)
    print(f"\nProject root: {project_root}")
    print(f"Test steps: {args.num_steps}")

    # Run all tests
    results = []

    results.append(("Imports", test_imports()))
    results.append(("Policy Loading", test_policy_loading()))
    results.append(("Environment Creation", test_environment_creation()))
    results.append(("Integration", test_integration(args.num_steps, args.verbose)))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {name}")

    print("\n" + "-"*60)
    print(f"  Results: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 All tests PASSED! genPiHub is compatible with genesislab.")
        print("\nNext steps:")
        print("  • Run visual test: python src/genPiHub/scripts/amo/play_amo.py --viewer")
        print("  • Run performance test: python src/genPiHub/scripts/amo/play_amo_headless.py")
        return 0
    else:
        print("\n❌ Some tests FAILED. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
