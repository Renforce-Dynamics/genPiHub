# BeyondMimic GenesisLab Scripts

GenesisLab-based scripts for running BeyondMimic whole-body motion tracking policy.

## Overview

This directory contains scripts that use **Genesis** physics engine backend for BeyondMimic policy playback, integrated with the **Policy Hub** framework.

### Key Features

- ✅ **Policy Hub Integration**: Uses `genPiHub.load_policy()` for unified policy interface
- 🎭 **Motion Playback**: Plays back pre-recorded motions embedded in ONNX models
- 🚀 **High Performance**: Genesis physics engine for fast simulation
- 🤖 **29 DOF Control**: Full G1 humanoid including wrists
- 🔄 **Loop Mode**: Optional continuous motion replay
- 📊 **Real-time Monitoring**: FPS, position, and motion timestep feedback

## Scripts

### `play_beyondmimic.py`

BeyondMimic motion playback with Genesis backend.

**Usage:**

```bash
# Basic usage (headless)
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file path/to/beyondmimic_dance.onnx

# With viewer
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file path/to/model.onnx \
    --viewer

# Adjust playback speed
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file path/to/model.onnx \
    --play-speed 0.5  # Slower playback

# Loop motion
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file path/to/model.onnx \
    --loop

# Multiple parallel environments
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file path/to/model.onnx \
    --num-envs 4 \
    --headless
```

**Arguments:**

```
Environment:
  --device {cpu,cuda}    Device for physics simulation
  --num-envs N           Number of parallel environments (default: 1)
  --viewer               Enable Genesis viewer
  --headless             Disable viewer (explicit headless mode)
  --max-steps N          Maximum simulation steps (default: 100000)

Policy & Model:
  --model-file PATH      Path to ONNX model file (REQUIRED)
  --use-model-meta       Load config from ONNX model metadata
  --without-state-estimator  Disable state estimator (WOSE mode)

Motion Playback:
  --start-timestep N     Starting timestep (default: 0)
  --max-timestep N       Maximum timestep (0 = infinite, default: 0)
  --play-speed FLOAT     Playback speed multiplier (default: 1.0)
  --loop                 Loop motion when it completes

Advanced:
  --onnx-provider {cpu,cuda,tensorrt}  ONNX Runtime provider
  --print-every N        Print status every N steps (default: 100)
```

## BeyondMimic Overview

**BeyondMimic** is a whole-body motion tracking policy that:

- Uses **29 DOF** G1 humanoid configuration (including wrists)
- Trained with **ONNX Runtime** for cross-platform deployment
- Embeds **motion data** directly in the ONNX model
- Supports **timestep-based playback** with speed control
- Can operate with or without **state estimator**

### Motion Data Format

BeyondMimic models embed motion reference data that includes:
- Joint positions (29 DOF)
- Joint velocities (29 DOF)
- Body positions (world frame)
- Body orientations (quaternions)

The policy tracks this reference motion in real-time.

## Requirements

### Python Packages

```bash
# Core dependencies
pip install onnxruntime-gpu  # For CUDA support
# OR
pip install onnxruntime      # CPU-only

# Policy Hub (should be installed)
pip install -e /path/to/genPiHub

# Genesis (should be in third_party)
# Already installed if you have genesislab environment
```

### ONNX Model Files

You need a BeyondMimic ONNX model file (`.onnx`). These models contain:
- Policy network weights
- Motion reference data
- Optional metadata (joint names, action scales, etc.)

Example model structure:
```
beyondmimic_dance.onnx       # ~50-100 MB
├── Policy network
├── Motion data (embedded)
└── Metadata (optional)
    ├── joint_names
    ├── default_joint_pos
    ├── action_scale
    └── ...
```

## Architecture

### Policy Hub Integration

```python
# Load policy via Policy Hub registry
policy = load_policy(
    "BeyondMimicPolicy",
    policy_file="path/to/model.onnx",
    device="cuda",
    use_model_meta_config=True,
    use_motion_from_model=True,
)

# Create Genesis environment
env_cfg = create_beyondmimic_genesis_env_config(
    num_envs=1,
    backend="cuda",
    viewer=True,
)
env = GenesisEnv(cfg=genesis_cfg, device="cuda", env_cfg=env_cfg)

# Main loop
for step in range(max_steps):
    env_data = env.get_data()
    obs, extras = policy.get_observation(env_data, {})
    action = policy.get_action(obs)
    env.step(action)
    policy.post_step_callback()  # Updates timestep
```

### G1 29 DOF Configuration

Joint ordering (BeyondMimic-specific):
```
0-2:   left_hip_pitch, right_hip_pitch, waist_yaw
3-5:   left_hip_roll, right_hip_roll, waist_roll
6-8:   left_hip_yaw, right_hip_yaw, waist_pitch
9-10:  left_knee, right_knee
11-12: left_shoulder_pitch, right_shoulder_pitch
13-14: left_ankle_pitch, right_ankle_pitch
15-16: left_shoulder_roll, right_shoulder_roll
17-18: left_ankle_roll, right_ankle_roll
19-20: left_shoulder_yaw, right_shoulder_yaw
21-22: left_elbow, right_elbow
23-24: left_wrist_roll, right_wrist_roll
25-26: left_wrist_pitch, right_wrist_pitch
27-28: left_wrist_yaw, right_wrist_yaw
```

## Comparison with Other Backends

| Feature | GenesisLab | MuJoCo | Isaac Sim |
|---------|------------|--------|-----------|
| **Speed** | ~10-50x faster | ~Real-time | ~5-10x faster |
| **Parallel Envs** | ✅ 1000+ | ❌ Single | ✅ 100+ |
| **Viewer** | ✅ Genesis viewer | ✅ mujoco_viewer | ✅ Isaac viewer |
| **Use Case** | Training, benchmarking | Visualization | Eval, rendering |
| **GPU Acceleration** | ✅ Full | ❌ Limited | ✅ Full |

## Troubleshooting

### Model file not found

```bash
# Make sure the ONNX file exists
ls -lh path/to/model.onnx
```

### ONNX Runtime errors

```bash
# Check ONNX Runtime installation
python -c "import onnxruntime as ort; print(ort.__version__)"

# Check available providers
python -c "import onnxruntime as ort; print(ort.get_available_providers())"

# Reinstall if needed
pip install --upgrade onnxruntime-gpu  # For CUDA
# OR
pip install --upgrade onnxruntime      # CPU-only
```

### Import errors

```bash
# Make sure genPiHub is installed
pip install -e /path/to/genPiHub

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/genPiHub"
```

### Device/CUDA errors

```bash
# Force CPU mode
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file path/to/model.onnx \
    --device cpu \
    --onnx-provider cpu
```

### Motion not playing

If the robot doesn't move:

1. **Check model has motion data**: Use `--use-model-meta` to load metadata
2. **Check timestep bounds**: Use `--max-timestep 0` for infinite playback
3. **Check play speed**: Use `--play-speed 1.0` (default)
4. **Enable viewer**: Use `--viewer` to visualize

### Performance issues

For faster simulation:

```bash
# Use headless mode
--headless

# Reduce print frequency
--print-every 1000

# Use GPU
--device cuda --onnx-provider cuda
```

## Examples

### Basic Motion Playback

```bash
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file data/beyondmimic/dance.onnx \
    --viewer
```

### Slow Motion Replay

```bash
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file data/beyondmimic/dance.onnx \
    --play-speed 0.3 \
    --viewer
```

### Continuous Loop

```bash
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file data/beyondmimic/dance.onnx \
    --loop \
    --viewer
```

### Batch Processing (Headless)

```bash
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file data/beyondmimic/dance.onnx \
    --num-envs 16 \
    --headless \
    --max-steps 10000
```

### With State Estimator

```bash
# Default mode (with state estimator)
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file data/beyondmimic/dance.onnx

# Without state estimator (WOSE mode)
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file data/beyondmimic/dance.onnx \
    --without-state-estimator
```

## Model Metadata

If your ONNX model includes metadata, you can use:

```bash
python scripts/beyondmimic/genesislab/play_beyondmimic.py \
    --model-file path/to/model.onnx \
    --use-model-meta  # Auto-load joint names, scales, etc.
```

This will automatically configure:
- Joint names and ordering
- Default joint positions
- Action scales
- PD controller gains (if available)

## Performance Benchmarks

Typical performance on RTX 4090:

| Num Envs | Headless FPS | Viewer FPS |
|----------|--------------|------------|
| 1        | ~5000        | ~60        |
| 4        | ~15000       | ~50        |
| 16       | ~40000       | N/A        |
| 64       | ~100000      | N/A        |

## License

Follows the same license as the BeyondMimic project.

## References

- **BeyondMimic**: Whole-body motion tracking policy
- **Policy Hub**: genPiHub unified policy framework
- **Genesis**: https://github.com/Genesis-Embodied-AI/Genesis
- **ONNX Runtime**: https://onnxruntime.ai/
