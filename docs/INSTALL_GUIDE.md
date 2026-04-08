# genPiHub Installation & Verification Guide

## Prerequisites

- Conda environment: `genesislab` (Python 3.10)
- CUDA-capable GPU (tested on RTX 4090)
- Linux OS (for keyboard control features)

## Installation

### Method 1: Automated (Recommended)

```bash
cd /home/ununtu/code/hvla/src/genPiHub
bash INSTALL.sh
```

### Method 2: Manual

```bash
cd /home/ununtu/code/hvla/src/genPiHub
conda activate genesislab
pip install -e .
```

## Verification

### Step 1: Import Test
```bash
python -c "import genPiHub; print(f'✅ genPiHub v{genPiHub.__version__}')"
```

Expected output: `✅ genPiHub v0.1.0`

### Step 2: Check Assets
```bash
cd /home/ununtu/code/hvla
python src/genPiHub/scripts/check_amo_setup.py
```

Expected output:
```
✅ AMO policy model found
✅ AMO adapter model found
✅ G1 robot MJCF found
✅ All assets verified
```

### Step 3: Policy Test
```bash
python src/genPiHub/scripts/test_amo_policy.py
```

Expected output:
```
✅ Policy loaded successfully
✅ Observation shape: torch.Size([1, 153])
✅ Action shape: torch.Size([1, 23])
✅ AMO policy test PASSED
```

### Step 4: Environment Test
```bash
python src/genPiHub/scripts/test_amo_env.py
```

Expected output:
```
✅ Environment created successfully
✅ Reset successful
✅ State dict contains all required keys
✅ Environment test PASSED
```

### Step 5: Integration Test (Primary)
```bash
python src/genPiHub/scripts/play_amo_genesis_hub.py --viewer
```

**Expected**:
- Genesis viewer window opens
- Robot stands at default pose
- FPS display shows 37-38 FPS
- Keyboard controls work

**Controls**:
- ⬆️⬇️⬅️➡️: Velocity and yaw control
- W/S: Height adjustment
- A/D: Torso lean
- Q: Quit

Press Q to exit after verification.

## Troubleshooting

### Import Error: "No module named 'genPiHub'"

**Solution**:
```bash
cd src/genPiHub
pip install -e .
```

### Asset Not Found

**Solution**: Check that `.reference/AMO/` directory exists with models
```bash
ls -la .reference/AMO/
# Should show: amo_jit.pt, adapter_jit.pt
```

### Genesis Not Installed

**Solution**:
```bash
conda activate genesislab
pip install genesis-world
```

### Low FPS in Viewer

**Solution**: Use headless mode for better performance
```bash
python src/genPiHub/scripts/play_amo_headless.py --num-steps 1000
```

### Keyboard Control Not Working

**Possible causes**:
1. Terminal window not in focus (click terminal)
2. Non-Unix OS (keyboard control uses Unix termios)

**Alternative**: Use headless mode with pre-programmed commands

## Post-Installation

### Update Your Code

If migrating from policy_hub:

```python
# Before
from policy_hub import load_policy
from policy_hub.configs import AMOPolicyConfig

# After
from genPiHub import load_policy
from genPiHub.configs import AMOPolicyConfig
```

### Example Usage

```python
from genPiHub import load_policy
from genPiHub.configs import AMOPolicyConfig

# Load policy
policy = load_policy(
    "AMOPolicy",
    model_dir=".reference/AMO",
    device="cuda"
)

# Use policy
policy.reset()
# ... (see QUICKSTART.md for complete example)
```

## Next Steps

1. ✅ Installation verified
2. 📖 Read [QUICKSTART.md](QUICKSTART.md) for usage guide
3. 🧪 Explore test scripts in [scripts/README.md](scripts/README.md)
4. 💡 Check examples in `examples/amo_example.py`
5. 🚀 Integrate genPiHub into your project

## Support

- Quick Start: [QUICKSTART.md](QUICKSTART.md)
- Documentation: [README.md](README.md)
- Tests: [scripts/README.md](scripts/README.md)
- Migration: [MIGRATION.md](MIGRATION.md)

---

**Installation complete!** Start using genPiHub now. 🎉
