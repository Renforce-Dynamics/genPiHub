# genPiHub 🎯

*A unified framework for deploying humanoid robot policies. Just load, just run.*

## Overview

genPiHub provides a standardized interface for loading and running different humanoid robot policies across multiple simulation and real robot platforms. Inspired by [RoboJuDo](https://github.com/HansZ8/RoboJuDo), this framework decouples **Policy**, **Environment**, and **Configuration** for maximum flexibility.

## Features

- **🔌 Plug-and-Play**: Unified interface for different policies (AMO, CLOT, ProtoMotions, etc.)
- **🧩 Modular Design**: Policy, Environment, and Config are completely decoupled
- **🚀 Multi-Backend**: Support for Genesis, MuJoCo, Isaac Sim, and real robots
- **📦 Registry System**: Easy policy/environment registration and dynamic loading
- **🔧 Extensible**: Add new policies and environments with minimal code changes

## Structure

```
genPiHub/
├── policies/               # Policy implementations
│   ├── base_policy.py     # Base policy interface
│   ├── amo_policy.py      # AMO policy (RSS 2025)
│   ├── clot_policy.py     # CLOT policy (TODO)
│   └── ...                # More policies
│
├── environments/          # Environment adapters
│   ├── base_env.py        # Base environment interface
│   ├── genesis_env.py     # Genesis physics
│   ├── mujoco_env.py      # MuJoCo physics
│   └── ...                # More backends
│
├── configs/               # Configuration definitions
│   ├── policy_configs.py  # Policy configurations
│   └── env_configs.py     # Environment configurations
│
├── utils/                 # Utilities
│   ├── registry.py        # Registration system
│   └── ...
│
└── tools/                 # Common tools
    ├── dof_config.py      # DOF management
    └── ...
```

## Quick Start

### Installation

```bash
cd /home/ununtu/code/hvla
pip install -e genPiHub
```

### Usage

```python
from genPiHub import load_policy, load_environment

# Load policy
policy = load_policy(
    name="AMOPolicy",
    model_dir=".reference/AMO",
    device="cuda"
)

# Load environment
env = load_environment(
    name="GenesisEnv",
    robot="G1",
    backend="gpu"
)

# Run
env.reset()
policy.reset()

for step in range(1000):
    obs, extras = policy.get_observation(env.get_data(), {})
    action = policy.get_action(obs)
    env.step(action)
```

## Supported Policies

| Policy | Status | Description |
|--------|--------|-------------|
| **AMOPolicy** | ✅ Ready | Adaptive Motion Optimization (RSS 2025) |
| **CLOTPolicy** | 🔧 Planned | Closed-Loop Global Motion Tracking |
| **ProtoMotionsPolicy** | 🔧 Planned | Physics-based character animation |
| **ASAPPolicy** | 🔧 Planned | ASAP locomotion/manipulation |
| **BeyondMimicPolicy** | 🔧 Planned | Beyond Mimic policy |

## Supported Environments

| Environment | Status | Description |
|-------------|--------|-------------|
| **GenesisEnv** | ✅ Ready | Genesis physics engine |
| **MuJoCoEnv** | 🔧 Planned | MuJoCo physics engine |
| **IsaacEnv** | 🔧 Planned | Isaac Sim/Lab |
| **UnitreeEnv** | 🔧 Planned | Unitree real robot SDK |

## Design Principles

### 1. Unified Policy Interface

All policies implement the same interface:
- `reset()` - Reset policy state
- `get_observation(env_data, ctrl_data)` - Get policy observations
- `get_action(obs)` - Compute actions from observations
- `post_step_callback()` - Post-step updates

### 2. Unified Environment Interface

All environments provide:
- `reset()` - Reset environment
- `step(action)` - Execute action
- `get_data()` - Get current state (dof_pos, dof_vel, base_quat, etc.)
- `update()` - Update environment state

### 3. Configuration-Driven

All policies and environments are configured through config objects:
- `PolicyConfig` - Policy-specific settings
- `EnvConfig` - Environment-specific settings
- `DOFConfig` - Joint/DOF specifications

### 4. Registry System

Policies and environments are registered for dynamic loading:
```python
from genPiHub.utils.registry import Registry

policy_registry = Registry(base_class=Policy)
policy_registry.add("AMOPolicy", ".amo_policy")
```

## Adding New Policies

1. **Create policy file**: `policies/my_policy.py`
2. **Inherit from BasePolicy**: Implement required methods
3. **Register**: Add to `policies/__init__.py`

Example:
```python
from genPiHub.policies import Policy, PolicyConfig

class MyPolicy(Policy):
    def __init__(self, cfg: PolicyConfig, device: str = "cpu"):
        super().__init__(cfg, device)
        # Load your model
        
    def reset(self):
        # Reset policy state
        pass
        
    def get_observation(self, env_data, ctrl_data):
        # Build observation from env data
        return obs, extras
        
    def get_action(self, obs):
        # Compute action
        return action
```

## Adding New Environments

1. **Create environment file**: `environments/my_env.py`
2. **Inherit from BaseEnvironment**: Implement required methods
3. **Register**: Add to `environments/__init__.py`

## Comparison with RoboJuDo

| Feature | RoboJuDo | genPiHub |
|---------|----------|------------|
| **Focus** | Real robot deployment | Multi-backend simulation + research |
| **Policies** | 10+ policies | Starting with AMO, extensible |
| **Environments** | Real robot focus | Simulation focus (Genesis, MuJoCo) |
| **Design** | Mature, production-ready | Research-oriented, extensible |
| **Language** | Python + C++ SDK | Pure Python |

genPiHub is designed for **research and rapid prototyping** while RoboJuDo targets **production deployment**.

## Roadmap

### Phase 1: Foundation (Current)
- [x] Design base interfaces
- [x] Implement AMOPolicy
- [x] Implement GenesisEnv
- [x] Registry system
- [ ] Complete documentation

### Phase 2: More Policies
- [ ] CLOTPolicy
- [ ] ProtoMotionsPolicy
- [ ] ASAPPolicy

### Phase 3: More Environments
- [ ] MuJoCoEnv
- [ ] IsaacEnv
- [ ] Real robot environments

### Phase 4: Advanced Features
- [ ] Multi-policy switching
- [ ] Policy interpolation
- [ ] Visualization tools
- [ ] Benchmarking suite

## Documentation

- [Policy Interface](docs/policy_interface.md)
- [Environment Interface](docs/environment_interface.md)
- [Configuration Guide](docs/configuration.md)
- [Adding Policies](docs/adding_policies.md)
- [Adding Environments](docs/adding_environments.md)

## Citation

```bibtex
@software{genPiHub2026,
  title={genPiHub: A Unified Framework for Humanoid Robot Policies},
  author={Your Name},
  year={2026},
  url={https://github.com/your-org/genPiHub}
}
```

## License

MIT License

## Acknowledgments

- Inspired by [RoboJuDo](https://github.com/HansZ8/RoboJuDo)
- AMO policy from RSS 2025
- GenesisLab framework
