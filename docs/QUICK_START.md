## Policy Hub Quick Start

### Installation

```bash
cd /home/ununtu/code/hvla
pip install -e policy_hub
```

### Basic Usage

```python
from policy_hub import load_policy

# Load AMO policy
policy = load_policy(
    "AMOPolicy",
    model_dir=".reference/AMO",
    device="cuda"
)

# Reset policy
policy.reset()

# Get action (using dict observation)
env_data = {
    "dof_pos": ...,      # Joint positions
    "dof_vel": ...,      # Joint velocities
    "base_quat": ...,    # Base quaternion [x,y,z,w]
    "base_ang_vel": ..., # Base angular velocity
    "commands": ...,     # Velocity commands [vx, yaw_rate, vy, ...]
}

obs, extras = policy.get_observation(env_data, {})
action = policy.get_action(obs)
```

### Available Policies

- **AMOPolicy**: Adaptive Motion Optimization (RSS 2025)
- More coming soon...

### Adding Your Own Policy

1. Create `policies/my_policy.py`:
```python
from policy_hub.policies import Policy

class MyPolicy(Policy):
    def reset(self):
        # Reset policy state
        pass
        
    def get_observation(self, env_data, ctrl_data):
        # Build observation
        return obs, {}
        
    def get_action(self, obs):
        # Compute action
        return action
        
    def post_step_callback(self, commands=None):
        # Post-step updates
        pass
```

2. Register in `policies/__init__.py`:
```python
policy_registry.add("MyPolicy", ".my_policy")
```

3. Use it:
```python
policy = load_policy("MyPolicy", ...)
```

See [Adding Policies](adding_policies.md) for details.
