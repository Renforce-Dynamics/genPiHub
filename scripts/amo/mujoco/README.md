# AMO MuJoCo Scripts

MuJoCo-based scripts for running AMO (Adaptive Motion Optimization) policy with interactive viewer.

## Overview

This directory contains scripts that use **MuJoCo** backend with **mujoco_viewer** for visualization, integrated with the **Policy Hub** framework.

### Key Features

- ✅ **Policy Hub Integration**: Uses `genPiHub.load_policy()` for unified policy interface
- 🎮 **Interactive Keyboard Control**: Real-time command adjustment via keyboard
- 🖥️ **MuJoCo Viewer**: Native MuJoCo visualization with mujoco_viewer
- 🤖 **Full Body Control**: Lower body (policy) + upper body (random/default poses)
- 📊 **Real-time Monitoring**: FPS, position, and command feedback

## Scripts

### `play_amo.py`

Interactive AMO policy playback with MuJoCo viewer.

**Usage:**

```bash
# Default: Interactive mode with keyboard control
python scripts/amo/mujoco/play_amo.py

# Custom initial commands
python scripts/amo/mujoco/play_amo.py --vx 0.4 --yaw-rate 0.2

# Headless mode (no viewer)
python scripts/amo/mujoco/play_amo.py --no-viewer --max-steps 1000

# Specify model directory
python scripts/amo/mujoco/play_amo.py --model-dir .reference/AMO
```

**Arguments:**

```
Environment:
  --model-xml PATH       MuJoCo model XML file (default: g1.xml)
  --device {cpu,cuda}    Device for policy inference
  --no-viewer            Disable viewer (headless mode)
  --max-steps N          Maximum simulation steps (default: 100000)

Policy:
  --model-dir PATH       AMO model directory (default: data/AMO)
  --action-scale FLOAT   Action scaling factor (default: 0.25)

Initial Commands:
  --vx FLOAT            Forward velocity in m/s (default: 0.0)
  --vy FLOAT            Lateral velocity in m/s (default: 0.0)
  --yaw-rate FLOAT      Yaw rate in rad/s (default: 0.0)
  --height FLOAT        Height adjustment (default: 0.0)

Other:
  --print-every N       Print status every N steps (default: 100)
```

## Keyboard Controls

When running with viewer (default), use these keys to control the robot in real-time:

| Key | Function | Description |
|-----|----------|-------------|
| **W** / **S** | Forward / Backward | Increase/decrease forward velocity (vx) |
| **A** / **D** | Turn Left / Right | Increase/decrease yaw rate |
| **Q** / **E** | Strafe Left / Right | Increase/decrease lateral velocity (vy) |
| **Z** / **X** | Height Up / Down | Adjust base height |
| **J** / **U** | Torso Yaw | Adjust torso yaw angle |
| **K** / **I** | Torso Pitch | Adjust torso pitch angle |
| **L** / **O** | Torso Roll | Adjust torso roll angle |
| **T** | Toggle Arms | Enable/disable random arm motion |
| **ESC** | Quit | Exit simulation |

## Requirements

### Python Packages

```bash
# Core dependencies (should be in AMO environment)
pip install mujoco mujoco-viewer
pip install numpy torch glfw

# Policy Hub (should be installed)
pip install -e /path/to/genPiHub
```

### Model Files

The script expects AMO model files in the specified model directory (default: `data/AMO`):

```
data/AMO/
├── amo_jit.pt              # Main policy network (~17MB)
├── adapter_jit.pt          # Adapter network (~1.6MB)
└── adapter_norm_stats.pt   # Normalization statistics
```

And the G1 MJCF model:

```
.reference/AMO/
└── g1.xml                  # G1 robot model
```

## Architecture

### MuJoCo Environment Wrapper

The `MuJoCoG1Env` class provides:

- MuJoCo simulation management
- State extraction (compatible with Policy Hub)
- PD controller with proper gains
- Interactive keyboard control
- Viewer integration

### Policy Hub Integration

```python
# Load policy via Policy Hub registry
policy = load_policy("AMOPolicy", 
                     policy_file="data/AMO/amo_jit.pt",
                     adapter_file="data/AMO/adapter_jit.pt",
                     ...)

# Get state from MuJoCo
env_data = env.get_state()  # Returns dict with dof_pos, dof_vel, etc.

# Get action via Policy Hub interface
obs, extras = policy.get_observation(env_data, {})
action = policy.get_action(obs)

# Convert to PD targets and step
pd_target = action * policy.action_scale + default_pos
env.step(pd_target)
```

## Comparison with GenesisLab Version

| Feature | MuJoCo Version | GenesisLab Version |
|---------|----------------|---------------------|
| **Backend** | MuJoCo + mujoco_viewer | Genesis physics engine |
| **Viewer** | mujoco_viewer | Genesis viewer |
| **Speed** | ~Real-time (1x) | ~10-50x faster |
| **Interactivity** | ✅ Full keyboard control | ✅ Full keyboard control |
| **Parallel Envs** | ❌ Single env | ✅ Vectorized (4096+ envs) |
| **Use Case** | Visualization, debugging | Training, benchmarking |

## Troubleshooting

### Model file not found

If you get `FileNotFoundError: Model file not found: g1.xml`:

```bash
# The script automatically looks in .reference/AMO/
# Make sure the file exists there
ls .reference/AMO/g1.xml
```

### Import errors

If you get import errors for `genPiHub`:

```bash
# Make sure genPiHub is installed
pip install -e /path/to/genPiHub

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/genPiHub"
```

### MuJoCo/viewer issues

```bash
# Install/reinstall MuJoCo and viewer
pip install --upgrade mujoco mujoco-viewer

# Check GLFW installation
pip install --upgrade glfw
```

### Device errors

```bash
# Force CPU mode if CUDA issues
python scripts/amo/mujoco/play_amo.py --device cpu
```

## Examples

### Basic Forward Walk

```bash
python scripts/amo/mujoco/play_amo.py --vx 0.3
```

### Circle Walk

```bash
python scripts/amo/mujoco/play_amo.py --vx 0.3 --yaw-rate 0.5
```

### Strafe Test

```bash
python scripts/amo/mujoco/play_amo.py --vy 0.2
```

### Height Adjustment

```bash
python scripts/amo/mujoco/play_amo.py --height 0.1
```

## License

Follows the same license as the AMO project (Apache 2.0).

## References

- **AMO Paper**: Adaptive Motion Optimization for Humanoid Whole-Body Control (RSS 2025)
- **Policy Hub**: genPiHub unified policy framework
- **MuJoCo**: https://mujoco.org/
