# CLOT Policy

**Closed-Loop Motion Tracking** for humanoid robots.

## Overview

CLOT (Closed-Loop Motion Tracking) is a motion tracking policy from the `humanoid_benchmark` project that enables humanoid robots to track and reproduce complex human motions using AMP (Adversarial Motion Priors).

**Key Features:**
- ✅ Closed-loop global motion tracking
- ✅ AMP-based motion quality assessment
- ✅ Large-scale parallel training
- ✅ Supports multiple robot platforms (G1, H1, Adam Pro)
- ✅ Self-contained implementation in genPiHub

**Paper:** [CLOT: Closed-Loop Global Motion Tracking](https://arxiv.org/abs/2602.15060)

**Original Project:** [humanoid_benchmark](https://github.com/humanoidverse/humanoid_benchmark)

---

## Installation

CLOT is included in genPiHub. No additional installation required.

```bash
# Install genPiHub
cd genPiHub
pip install -e .
```

---

## Quick Start

### 1. Basic Usage

```python
from genPiHub import load_policy

# Load CLOT policy
policy = load_policy(
    name="CLOTPolicy",
    policy_file="data/CLOT/clot_policy.pt",
    device="cuda"
)

# Reset policy
policy.reset()

# Get observation and action
obs, extras = policy.get_observation(env_data, {})
action = policy.get_action(obs)
```

### 2. With Motion Library

```python
from genPiHub import load_policy

# Load CLOT with reference motions
policy = load_policy(
    name="CLOTPolicy",
    policy_file="data/CLOT/clot_policy.pt",
    motion_lib_dir="data/CLOT/motions",  # Reference motions
    device="cuda"
)
```

### 3. With Genesis Environment

```python
from genPiHub import load_policy
from genPiHub.configs import create_clot_genesis_env_config
from genPiHub.environments import GenesisEnv

# Create environment config
env_cfg = create_clot_genesis_env_config(
    num_envs=1,
    viewer=True,
    device="cuda"
)

# Create environment
env = GenesisEnv(env_cfg=env_cfg, device="cuda")

# Load policy
policy = load_policy(
    name="CLOTPolicy",
    policy_file="data/CLOT/clot_policy.pt",
    device="cuda"
)

# Run simulation
for step in range(1000):
    env_data = env.get_data()
    obs, extras = policy.get_observation(env_data, {})
    action = policy.get_action(obs)
    env.step(action)
```

---

## Configuration

### CLOTPolicyConfig

Full configuration options for CLOT policy:

```python
from genPiHub.configs import CLOTPolicyConfig
from genPiHub.tools import DOFConfig
from pathlib import Path

# Create DOF config (23 DOF G1)
dof_cfg = DOFConfig(
    joint_names=[...],  # 23 joint names
    num_dofs=23,
    default_pos=[...],  # Default positions
)

# Create CLOT config
config = CLOTPolicyConfig(
    # Model
    policy_file=Path("data/CLOT/clot_policy.pt"),
    
    # Motion library
    motion_lib_dir=Path("data/CLOT/motions"),
    motion_files=[],  # Empty = load all .npy files
    
    # AMP
    use_amp=True,
    amp_obs_dim=0,  # Auto-computed
    
    # Tracking
    tracking_sigma=0.5,  # Position tolerance
    tracking_sigma_vel=0.1,  # Velocity tolerance
    
    # Action
    action_scale=0.25,
    action_clip=10.0,
    
    # DOF
    obs_dof=dof_cfg,
    action_dof=dof_cfg,
    
    # Device
    device="cuda",
)
```

---

## Observations

CLOT uses two types of observations:

### 1. Policy Observation

Used by the tracking policy for control:

```python
obs = [
    projected_gravity,    # (3,)  - Gravity in base frame
    base_ang_vel,        # (3,)  - Angular velocity (scaled 0.25)
    base_lin_vel,        # (3,)  - Linear velocity
    joint_pos_rel,       # (23,) - Joint positions relative to default
    joint_vel,           # (23,) - Joint velocities (scaled 0.05)
    last_action,         # (23,) - Previous action
]
# Total: 64 dimensions
```

### 2. AMP Observation

Used by discriminator for motion quality:

```python
amp_obs = [
    root_height,         # (1,)  - Base height
    root_quat,          # (4,)  - Base orientation
    root_lin_vel,       # (3,)  - Linear velocity
    root_ang_vel,       # (3,)  - Angular velocity
    joint_pos,          # (23,) - Joint positions
    joint_vel,          # (23,) - Joint velocities
]
# Total: 57 dimensions
```

---

## Actions

CLOT outputs PD target positions:

```python
action = policy.get_action(obs)  # (23,) - Target joint positions
```

**Action Processing:**
1. Policy outputs normalized actions
2. Scaled by `action_scale` (default 0.25)
3. Added to default joint positions
4. Clipped to `action_clip` (default ±10.0)

---

## Robot Support

### Unitree G1 (23 DOF)

Default robot for CLOT. Includes:
- 6 DOF legs (left + right)
- 3 DOF torso
- 4 DOF arms (left + right, no hands)

**Joint Names:**
```python
from genPiHub.envs.clot.robot_cfg import G1_23DOF_NAMES
print(G1_23DOF_NAMES)
```

**PD Gains:**
- Legs: stiffness=250, damping=6
- Torso: stiffness=350, damping=12
- Arms: stiffness=50, damping=2.5

### Future Support

- [ ] Unitree H1 (19/25 DOF)
- [ ] FFTAI Gr1 (29 DOF)
- [ ] Adam Pro

---

## Motion Library

CLOT can use reference motions for tracking:

### Format

Motion files are NumPy arrays (`.npy`) containing:
```python
motion_data = {
    "root_pos": (T, 3),     # Root position trajectory
    "root_rot": (T, 4),     # Root orientation (quat)
    "dof_pos": (T, num_dofs),  # Joint positions
    "dof_vel": (T, num_dofs),  # Joint velocities
}
```

### Loading Motions

```python
# Option 1: Load all motions from directory
policy = load_policy(
    name="CLOTPolicy",
    motion_lib_dir="data/CLOT/motions",
)

# Option 2: Load specific motions
from genPiHub.configs import CLOTPolicyConfig

config = CLOTPolicyConfig(
    motion_lib_dir="data/CLOT/motions",
    motion_files=["walk.npy", "run.npy"],
)
```

---

## Examples

### Example 1: Basic Testing

```bash
# Test policy structure (no model required)
python scripts/clot/test_clot_policy.py

# Test with model
python scripts/clot/test_clot_policy.py --model-file data/CLOT/clot_policy.pt
```

### Example 2: Programmatic Use

```python
from genPiHub import load_policy
import numpy as np

# Load policy
policy = load_policy(
    name="CLOTPolicy",
    policy_file="data/CLOT/clot_policy.pt",
    device="cuda"
)

# Create environment data
env_data = {
    "dof_pos": np.zeros(23),
    "dof_vel": np.zeros(23),
    "base_quat": np.array([0, 0, 0, 1]),
    "base_ang_vel": np.zeros(3),
    "base_lin_vel": np.zeros(3),
    "base_pos": np.array([0, 0, 0.75]),
}

# Get action
obs, extras = policy.get_observation(env_data, {})
action = policy.get_action(obs)

print(f"Action: {action}")
print(f"AMP obs: {extras.get('amp_obs')}")
```

---

## Technical Details

### Architecture

CLOT uses:
1. **Tracking Policy**: Neural network that outputs joint positions
2. **AMP Discriminator**: Assesses motion quality (not included in policy)
3. **Motion Library**: Reference motions for tracking

### Training

CLOT is trained with:
- **Simulator**: MjLab (MuJoCo Warp) or Isaac Sim
- **Algorithm**: PPO + AMP
- **Parallelization**: 8-GPU multi-node setup
- **Motion Dataset**: Large-scale human motion capture

### Performance

- **Inference FPS**: >1000 Hz (RTX 4090, headless)
- **Control Frequency**: 50 Hz (decimation=4)
- **Physics Frequency**: 200 Hz (dt=0.005)

---

## Troubleshooting

### "No model file provided"

```python
# Solution: Provide model file
policy = load_policy(
    name="CLOTPolicy",
    policy_file="data/CLOT/clot_policy.pt",  # Add this
)
```

### "Motion library directory not found"

Motion library is optional. CLOT can run without it:

```python
# Without motion library
policy = load_policy(
    name="CLOTPolicy",
    policy_file="data/CLOT/clot_policy.pt",
    # motion_lib_dir not required
)
```

### "Observation shape mismatch"

Check your observation DOF configuration matches the model:

```python
from genPiHub.envs.clot.robot_cfg import G1_23DOF_NAMES, G1_CLOT_DEFAULT_POS
from genPiHub.tools import DOFConfig

dof_cfg = DOFConfig(
    joint_names=G1_23DOF_NAMES,
    num_dofs=23,
    default_pos=G1_CLOT_DEFAULT_POS,
)
```

---

## Comparison with AMO

| Feature | AMO | CLOT |
|---------|-----|------|
| **Purpose** | Whole-body control | Motion tracking |
| **Method** | Adaptive optimization | AMP-based imitation |
| **Inputs** | Velocity commands | Reference motions |
| **Outputs** | PD targets | PD targets |
| **Training** | Online RL | Offline + online RL |
| **Complexity** | Moderate | High |

**When to use:**
- **AMO**: Interactive control, locomotion tasks, real-time commands
- **CLOT**: Motion reproduction, performance capture, pre-recorded motions

---

## References

- **Paper**: [CLOT: Closed-Loop Global Motion Tracking](https://arxiv.org/abs/2602.15060)
- **Project**: [humanoid_benchmark](https://github.com/humanoidverse/humanoid_benchmark)
- **AMP Paper**: [Adversarial Motion Priors](https://arxiv.org/abs/2104.02180)

---

## Status

✅ **Implemented**
- [x] Policy wrapper
- [x] Environment configuration
- [x] Observation construction
- [x] Basic motion library support
- [x] Test scripts
- [x] Documentation

🚧 **In Progress**
- [ ] Full motion library integration
- [ ] Interactive play script
- [ ] Genesis environment integration
- [ ] AMP discriminator integration

📝 **Planned**
- [ ] H1 robot support
- [ ] Gr1 robot support
- [ ] Advanced motion sampling
- [ ] Multi-motion tracking

---

**Last Updated**: 2026-04-09  
**Version**: 1.0  
**Status**: Core implementation complete
