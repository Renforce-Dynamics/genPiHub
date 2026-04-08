# genPiHub Quick Start

Get started with genPiHub in 5 minutes!

## 1. Installation

```bash
# Activate environment
conda activate genesislab

# Install genPiHub
cd src/genPiHub
bash INSTALL.sh

# Or manually:
pip install -e .
```

## 2. Verify Installation

```bash
python -c "import genPiHub; print(f'genPiHub v{genPiHub.__version__}')"
```

Expected output: `genPiHub v0.1.0`

## 3. Check Assets

```bash
python scripts/check_amo_setup.py
```

This verifies that AMO model files exist:
- `.reference/AMO/amo_jit.pt`
- `.reference/AMO/adapter_jit.pt`
- `data/amo_assets/g1.xml`

## 4. Run First Test

```bash
# Quick policy test (5 seconds)
python scripts/test_amo_policy.py
```

Expected output:
```
✓ Policy loaded successfully
✓ Observation shape: torch.Size([1, 153])
✓ Action shape: torch.Size([1, 23])
✓ AMO policy test PASSED
```

## 5. Interactive Demo

```bash
# Launch interactive viewer (PRIMARY TEST)
python scripts/play_amo_genesis_hub.py --viewer
```

**Expected**:
- Genesis viewer opens
- Robot stands at default pose
- FPS: 37-38

**Controls**:
- Arrow keys: Move forward/backward, turn left/right
- W/S: Move up/down
- A/D: Lean left/right
- Q: Quit

## 6. Headless Test

```bash
# Run headless for performance
python scripts/play_amo_headless.py --num-steps 1000
```

Expected: 50+ FPS, completes 1000 steps

## Usage in Your Code

### Load and Run a Policy

```python
from genPiHub import load_policy
from genPiHub.environments import GenesisEnv
from genPiHub.configs import create_amo_genesis_env_config

# Create environment
env_cfg = create_amo_genesis_env_config(
    num_envs=1,
    backend="cuda",
    viewer=True,
)

# Note: GenesisEnv needs genesis_cfg (from genesislab) and env_cfg
# See scripts/play_amo_genesis_hub.py for complete example

# Load policy
policy = load_policy(
    "AMOPolicy",
    model_dir=".reference/AMO",
    device="cuda"
)

# Reset
policy.reset()

# Run loop
for step in range(1000):
    # Get observation from environment
    env_data = env.get_data()
    ctrl_data = {
        "command": [0.5, 0.0, 0.0],  # [vx, vy, yaw_rate]
        # ... other commands
    }
    
    obs, extras = policy.get_observation(env_data, ctrl_data)
    
    # Get action
    action = policy.get_action(obs)
    
    # Step environment
    env.step(action)
    
    # Post-step callback
    policy.post_step_callback()
```

### Complete Example

See `scripts/play_amo_genesis_hub.py` for a complete working example with:
- Environment setup
- Policy loading
- Keyboard control
- Main loop
- FPS tracking

## Directory Structure

```
genPiHub/
├── policies/           # Policy implementations
├── environments/       # Environment adapters
├── configs/            # Configuration system
├── envs/amo/          # Self-contained AMO configs
├── tools/             # Utilities (DOF config, keyboard)
├── utils/             # Framework utils (registry)
├── scripts/           # Test scripts
├── examples/          # Usage examples
└── docs/              # Documentation
```

## Key Concepts

### 1. Policy Interface

All policies implement the `Policy` ABC:
- `reset()` - Reset policy state
- `get_observation(env_data, ctrl_data)` - Build observation
- `get_action(obs)` - Compute action
- `post_step_callback()` - Update after step

### 2. Environment Interface

All environments implement the `Environment` ABC:
- `reset()` - Reset environment
- `step(action)` - Execute action
- `get_data()` - Get current state
- `update()` - Update internal state

### 3. Configuration

- `PolicyConfig` - Base policy configuration
- `EnvConfig` - Base environment configuration
- `AMOPolicyConfig` - AMO-specific config
- `GenesisEnvConfig` - Genesis-specific config

### 4. Registry System

Dynamic loading of policies and environments:

```python
from genPiHub import policy_registry, environment_registry

# List available
print(policy_registry.list_registered())
# Output: ['AMOPolicy']

print(environment_registry.list_registered())
# Output: ['GenesisEnv']

# Load dynamically
policy_class = policy_registry.get("AMOPolicy")
```

## Troubleshooting

### Import Error

```bash
pip install -e src/genPiHub
```

### Robot Collapses

Joint order mismatch. Run debug tool:
```bash
python scripts/debug_amo_integration.py
```

### Low FPS

Use headless mode:
```bash
python scripts/play_amo_headless.py
```

### Keyboard Not Working

- Click terminal window for focus
- Unix-only feature (uses termios)

## Next Steps

1. ✅ Complete installation and tests
2. 📖 Read `README.md` for detailed documentation
3. 🔍 Explore `examples/amo_example.py`
4. 🧪 Run all tests: `scripts/README.md`
5. 🚀 Integrate genPiHub into your project

## Support

- Documentation: `docs/QUICK_START.md`
- Test Scripts: `scripts/README.md`
- Examples: `examples/`
- Issues: Check migration checklist

---

**genPiHub** - Just load, just run. 🚀
