"""Example: Load & run a HoloMotion (Horizon Robotics) ONNX checkpoint.

Run the velocity-tracking checkpoint in isolation (no simulator) with dummy
environment data. Verifies that the wrapper loads, obs/action shapes match the
exported ONNX graph, and a forward pass returns a real action vector.

Before running, download the checkpoint:

    bash scripts/download/download_holomotion_ckpt.sh velocity

...or manually copy the ``holomotion_v1.2_velocity_tracking_model/`` folder
(containing ``config.yaml`` and ``exported/*.onnx``) to the path passed below.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np

# Add genPiHub parent to path (mirrors amo_example.py layout).
example_dir = Path(__file__).resolve().parent
genpihub_dir = example_dir.parent
project_root = genpihub_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


DEFAULT_MODEL_DIR = Path(
    os.environ.get(
        "HOLOMOTION_MODEL_DIR",
        str(Path.home() / ".cache/genesis/holomotion/holomotion_v1.2_velocity_tracking_model"),
    )
)


def main() -> int:
    print("=" * 60)
    print("genPiHub - HoloMotion velocity_tracking example")
    print("=" * 60)

    try:
        from genPiHub import load_policy
        print("[ok] genPiHub imported")
    except ImportError as e:
        print(f"[fail] genPiHub not installed: {e}")
        print("       pip install -e src/genPiHub")
        return 1

    if not DEFAULT_MODEL_DIR.exists():
        print(f"[fail] model dir not found: {DEFAULT_MODEL_DIR}")
        print("       Run: bash scripts/download/download_holomotion_ckpt.sh velocity")
        return 1

    device = "cpu"  # swap to "cuda" after installing onnxruntime-gpu
    print(f"\n[1] Loading HoloMotion velocity_tracking model from {DEFAULT_MODEL_DIR}")
    policy = load_policy(
        "HoloMotionPolicy",
        model_dir=str(DEFAULT_MODEL_DIR),
        task_type="velocity_tracking",
        device=device,
    )
    print(f"[ok] loaded: task_type={policy.task_type}, num_actions={policy.num_actions}, "
          f"freq={policy.freq}Hz")
    print(f"     ONNX joint order (first 8): {policy.joint_names_onnx[:8]}")

    print("\n[2] Resetting policy")
    policy.reset()
    print("[ok] reset")

    print("\n[3] Building dummy env_data (URDF order == ONNX order, no remap)")
    n = policy.num_actions
    env_data = {
        # Start at default standing pose so delta obs == 0.
        "dof_pos": policy.default_angles_onnx.astype(np.float32).copy(),
        "dof_vel": np.zeros(n, dtype=np.float32),
        "base_quat": np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),  # wxyz, identity
        "base_ang_vel": np.zeros(3, dtype=np.float32),
    }
    ctrl_data = {"commands": np.array([0.3, 0.0, 0.0], dtype=np.float32)}  # vx=0.3 m/s

    print("\n[4] Rolling forward 5 steps")
    for step in range(5):
        obs, extras = policy.get_observation(env_data, ctrl_data)
        action = policy.get_action(obs)
        policy.post_step_callback()
        if step == 0:
            expected_obs_dim = policy.session.get_inputs()[0].shape[-1]
            assert obs.shape == (expected_obs_dim,), (
                f"obs shape mismatch: got {obs.shape}, expected ({expected_obs_dim},)"
            )
            assert action.shape == (n,), (
                f"action shape mismatch: got {action.shape}, expected ({n},)"
            )
            print(f"[ok] obs_dim={obs.shape[0]}, action_dim={action.shape[0]}")
        print(
            f"     step {step}: |obs|={np.linalg.norm(obs):.3f} "
            f"|action|={np.linalg.norm(action):.3f} "
            f"action[:4]={np.array2string(action[:4], precision=3)}"
        )

    print("\n[5] get_init_dof_pos()")
    init = policy.get_init_dof_pos()
    print(f"[ok] init_dof_pos shape={init.shape}, first 4 = {np.array2string(init[:4], precision=3)}")

    print("\n" + "=" * 60)
    print("[ok] All checks passed.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
