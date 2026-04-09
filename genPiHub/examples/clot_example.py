"""CLOT policy example.

This example demonstrates how to use the CLOT policy for motion tracking.
"""

import numpy as np
from pathlib import Path

def basic_example():
    """Basic CLOT policy usage."""
    print("="*60)
    print("CLOT Policy - Basic Example")
    print("="*60)

    from genPiHub import load_policy

    # Load CLOT policy (without model for demonstration)
    policy = load_policy(
        name="CLOTPolicy",
        policy_file=None,  # Set to your model path
        device="cpu",
        disable_autoload=True,  # Don't try to load model
    )

    print(f"✅ Policy loaded: {policy.name}")
    print(f"   - num_actions: {policy.num_actions}")
    print(f"   - device: {policy.device}")

    # Reset policy
    policy.reset()
    print("✅ Policy reset")

    # Create fake environment data
    env_data = {
        "dof_pos": np.zeros(23, dtype=np.float32),
        "dof_vel": np.zeros(23, dtype=np.float32),
        "base_quat": np.array([0, 0, 0, 1], dtype=np.float32),
        "base_ang_vel": np.zeros(3, dtype=np.float32),
        "base_lin_vel": np.zeros(3, dtype=np.float32),
        "base_pos": np.array([0, 0, 0.75], dtype=np.float32),
    }

    # Get observation
    obs, extras = policy.get_observation(env_data, {})
    print(f"✅ Observation: shape={obs.shape if not isinstance(obs, dict) else 'dict'}")

    if "amp_obs" in extras:
        print(f"   - AMP observation: shape={extras['amp_obs'].shape}")

    print("\nBasic example complete!")


def with_model_example(model_path: str):
    """Example with actual model file."""
    print("\n" + "="*60)
    print("CLOT Policy - With Model Example")
    print("="*60)

    from genPiHub import load_policy

    # Load CLOT policy with model
    policy = load_policy(
        name="CLOTPolicy",
        policy_file=model_path,
        device="cuda",  # Use GPU if available
    )

    print(f"✅ Policy loaded with model")
    print(f"   - model: {policy.model is not None}")

    # Reset
    policy.reset()

    # Create environment data
    env_data = {
        "dof_pos": np.zeros(23, dtype=np.float32),
        "dof_vel": np.zeros(23, dtype=np.float32),
        "base_quat": np.array([0, 0, 0, 1], dtype=np.float32),
        "base_ang_vel": np.zeros(3, dtype=np.float32),
        "base_lin_vel": np.zeros(3, dtype=np.float32),
        "base_pos": np.array([0, 0, 0.75], dtype=np.float32),
    }

    # Get observation and action
    obs, extras = policy.get_observation(env_data, {})
    action = policy.get_action(obs)

    print(f"✅ Action generated: shape={action.shape}")
    print(f"   - range: [{action.min():.3f}, {action.max():.3f}]")

    print("\nModel example complete!")


def motion_library_example(model_path: str, motion_dir: str):
    """Example with motion library."""
    print("\n" + "="*60)
    print("CLOT Policy - Motion Library Example")
    print("="*60)

    from genPiHub import load_policy

    # Load CLOT policy with motion library
    policy = load_policy(
        name="CLOTPolicy",
        policy_file=model_path,
        motion_lib_dir=motion_dir,
        device="cuda",
    )

    print(f"✅ Policy loaded with motion library")
    print(f"   - has motion lib: {policy.motion_lib is not None}")

    if policy.motion_lib:
        num_motions = policy.motion_lib.get("num_motions", 0)
        print(f"   - num motions: {num_motions}")

    print("\nMotion library example complete!")


def main():
    """Run all examples."""
    import argparse

    parser = argparse.ArgumentParser(description="CLOT policy examples")
    parser.add_argument("--model-file", type=str, default=None,
                        help="Path to CLOT model file")
    parser.add_argument("--motion-lib-dir", type=str, default=None,
                        help="Path to motion library directory")
    args = parser.parse_args()

    # Always run basic example
    basic_example()

    # Run model example if provided
    if args.model_file:
        with_model_example(args.model_file)

        # Run motion library example if provided
        if args.motion_lib_dir:
            motion_library_example(args.model_file, args.motion_lib_dir)
    else:
        print("\n" + "="*60)
        print("ℹ️  To run examples with model:")
        print("   python examples/clot_example.py --model-file path/to/model.pt")
        print("\nTo include motion library:")
        print("   python examples/clot_example.py --model-file path/to/model.pt --motion-lib-dir path/to/motions")
        print("="*60)


if __name__ == "__main__":
    main()
