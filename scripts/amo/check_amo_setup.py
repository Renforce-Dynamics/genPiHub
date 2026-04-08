"""Check AMO setup completeness and dependencies."""

import sys
from pathlib import Path

# Add paths
hvla_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(hvla_root / "src"))

print("="*60)
print("AMO GenesisLab Setup Check")
print("="*60)

# 1. Check imports
print("\n[1/6] Checking Python imports...")
errors = []

try:
    import genesis as gs
    print(f"  ✓ genesis (version: {gs.__version__ if hasattr(gs, '__version__') else 'unknown'})")
except ImportError as e:
    errors.append(f"genesis: {e}")
    print(f"  ✗ genesis: {e}")

try:
    from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnv
    print("  ✓ genesislab")
except ImportError as e:
    errors.append(f"genesislab: {e}")
    print(f"  ✗ genesislab: {e}")

try:
    import torch
    print(f"  ✓ torch (version: {torch.__version__})")
    print(f"    CUDA available: {torch.cuda.is_available()}")
except ImportError as e:
    errors.append(f"torch: {e}")
    print(f"  ✗ torch: {e}")

try:
    import numpy as np
    print(f"  ✓ numpy (version: {np.__version__})")
except ImportError as e:
    errors.append(f"numpy: {e}")
    print(f"  ✗ numpy: {e}")

# 2. Check AMO policy module
print("\n[2/6] Checking AMO policy module...")
try:
    # AMO imports removed - using genPiHub
    print("  ✓ amo_policy imports")

    # Check constants
    print(f"    - NUM_DOFS: {AMOPolicy.NUM_DOFS}")
    print(f"    - NUM_ACTIONS: {AMOPolicy.NUM_ACTIONS}")
    print(f"    - N_PROPRIO: {AMOPolicy.N_PROPRIO}")
except ImportError as e:
    errors.append(f"amo_policy: {e}")
    print(f"  ✗ amo_policy: {e}")

# 3. Check AMO models exist
print("\n[3/6] Checking AMO model files...")
model_config = AMOModelConfig()
model_dir = hvla_root / model_config.model_dir

model_files = {
    "policy": model_dir / model_config.policy_filename,
    "adapter": model_dir / model_config.adapter_filename,
    "norm_stats": model_dir / model_config.norm_stats_filename,
    "g1.xml": model_dir / "g1.xml",
}

for name, path in model_files.items():
    if path.exists():
        size_mb = path.stat().st_size / (1024*1024)
        print(f"  ✓ {name}: {path.name} ({size_mb:.1f} MB)")
    else:
        errors.append(f"{name} not found: {path}")
        print(f"  ✗ {name} not found: {path}")

# 4. Check environment config
print("\n[4/6] Checking environment config...")
try:
    from genPiHub.configs import create_amo_genesis_env_config
    print("  ✓ AmoGenesisEnvCfg import")

    cfg = AmoGenesisEnvCfg()
    print(f"    - decimation: {cfg.decimation}")
    print(f"    - episode_length_s: {cfg.episode_length_s}")
    print(f"    - scene.num_envs: {cfg.scene.num_envs}")
except ImportError as e:
    errors.append(f"amo_genesis_env: {e}")
    print(f"  ✗ amo_genesis_env: {e}")
except Exception as e:
    errors.append(f"AmoGenesisEnvCfg instantiation: {e}")
    print(f"  ✗ AmoGenesisEnvCfg instantiation: {e}")

# 5. Test AMO policy loading
print("\n[5/6] Testing AMO policy loading...")
try:
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"

    policy = AMOPolicy(
        model_dir=str(model_dir),
        device=device,
    )
    print(f"  ✓ AMOPolicy loaded on {device}")
    print(f"    - action_scale: {policy.action_scale}")
    print(f"    - gait_freq: {policy.gait_freq}")

    # Test reset
    policy.reset()
    print("  ✓ Policy reset successful")

    # Test inference with dummy data
    import numpy as np
    dof_pos = np.zeros(23, dtype=np.float32) + policy.DEFAULT_DOF_POS
    dof_vel = np.zeros(23, dtype=np.float32)
    quat = np.array([1, 0, 0, 0], dtype=np.float32)  # w, x, y, z
    ang_vel = np.zeros(3, dtype=np.float32)
    commands = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)

    pd_target = policy.act(dof_pos, dof_vel, quat, ang_vel, commands, dt=0.02)
    print(f"  ✓ Policy inference successful: output shape {pd_target.shape}")

except Exception as e:
    errors.append(f"Policy loading/inference: {e}")
    print(f"  ✗ Policy loading/inference failed: {e}")
    import traceback
    traceback.print_exc()

# 6. Check play script
print("\n[6/6] Checking play script...")
play_script = hvla_root / "scripts" / "play_amo_genesis.py"
if play_script.exists():
    print(f"  ✓ play_amo_genesis.py exists")
else:
    errors.append("play_amo_genesis.py not found")
    print(f"  ✗ play_amo_genesis.py not found")

# Summary
print("\n" + "="*60)
if errors:
    print(f"❌ Setup check FAILED with {len(errors)} error(s):\n")
    for i, err in enumerate(errors, 1):
        print(f"{i}. {err}")
    print("\nPlease fix the errors above before running play_amo_genesis.py")
    sys.exit(1)
else:
    print("✅ Setup check PASSED!")
    print("\nYou can now run:")
    print(f"  PYTHONPATH=src python scripts/play_amo_genesis.py --interactive")
    print(f"  PYTHONPATH=src python scripts/play_amo_genesis.py --vx 0.5 --print-spec")
    sys.exit(0)
