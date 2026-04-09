# AMO Policy in USD Scenes - User Guide

## Overview

This guide demonstrates how to run AMO locomotion policy in USD scenes with interactive furniture using the new **EnvironmentObjectsConfig** system.

## What's New

### Environment Objects System

The new system allows:
- ✅ **Interactive furniture** - Chairs, cabinets with articulated joints
- ✅ **Robot interaction** - Robot can physically interact with scene objects
- ✅ **No joint conflicts** - Proper DOF space isolation between robot (23 DOF) and scene objects
- ✅ **Backward compatible** - Existing scripts work unchanged

### Key Innovation

**Load Order**:
```
1. Add terrain (optional)
2. Add robot (defines robot DOF space: 0-22)
3. Add environment objects (separate DOF space)
4. Build scene (freeze layout)
5. Initialize robot actuators (use indices 0-22, no conflict!)
```

## Available Scripts

### 1. `play_amo_with_terrain_usd.py` - Simplified Test ✅ Recommended First

Uses static Terrain.usd (Floor, Wall, Ceiling - no articulated furniture).

**Usage:**
```bash
# Headless mode
python third_party/genPiHub/scripts/amo/play_amo_with_terrain_usd.py

# With viewer (recommended for visualization)
python third_party/genPiHub/scripts/amo/play_amo_with_terrain_usd.py --viewer

# Interactive keyboard control
python third_party/genPiHub/scripts/amo/play_amo_with_terrain_usd.py --viewer --interactive

# Custom velocity
python third_party/genPiHub/scripts/amo/play_amo_with_terrain_usd.py --viewer --vx 0.5
```

**Why start here?**
- Fast to load (no articulated furniture)
- No collision parameter tuning needed
- Validates that environment_objects system works
- Good for initial testing

### 2. `play_amo_with_usd_scene.py` - Full Interactive Scene

Uses complete Scene.usd with articulated furniture (254 joints).

**Usage:**
```bash
# Headless mode
python third_party/genPiHub/scripts/amo/play_amo_with_usd_scene.py

# With viewer (recommended)
python third_party/genPiHub/scripts/amo/play_amo_with_usd_scene.py --viewer

# Interactive control
python third_party/genPiHub/scripts/amo/play_amo_with_usd_scene.py --viewer --interactive

# Custom scene
python third_party/genPiHub/scripts/amo/play_amo_with_usd_scene.py \
    --viewer \
    --usd-scene path/to/your/scene.usd

# Static mode (no articulated joints)
python third_party/genPiHub/scripts/amo/play_amo_with_usd_scene.py \
    --viewer \
    --no-articulation
```

**Features:**
- Complete Scene.usd with furniture
- Articulated objects (chairs, cabinets with joints)
- Robot can push/interact with furniture
- Collision parameters automatically increased

**Note:** May require longer loading time due to complex collision geometry.

### 3. `play_amo.py` - Original Script (Plane Terrain)

Original AMO test script with simple plane terrain (no USD).

**Usage:**
```bash
python third_party/genPiHub/scripts/amo/play_amo.py --viewer
```

**Use when:** You just want basic AMO testing without scene complexity.

## Command Line Options

### Common Options

```bash
--viewer              # Enable Genesis viewer (visual mode)
--headless            # Explicit headless mode
--device cuda|cpu     # Force device (auto-detected by default)
--num-envs N          # Number of parallel environments (default: 1)
--max-steps N         # Maximum simulation steps (default: 100000)
--print-every N       # Print status every N steps (default: 100)
```

### Interactive Control Options

```bash
--interactive         # Enable keyboard control
--vx 0.4              # Forward velocity (m/s, default: 0.3)
--vy 0.0              # Lateral velocity (m/s, default: 0.0)
--yaw-rate 0.0        # Yaw rate (rad/s, default: 0.0)
--height 0.0          # Height adjustment (default: 0.0)
```

### USD Scene Options (play_amo_with_usd_scene.py only)

```bash
--usd-scene PATH      # Path to USD file (default: Scene.usd)
--load-articulation   # Load furniture with joints (default: true)
--no-articulation     # Load as static (no moving furniture)
```

### Policy Options

```bash
--model-dir PATH      # AMO model directory (default: data/AMO)
--action-scale 0.25   # Action scaling factor
```

## Interactive Keyboard Controls

When using `--interactive` mode:

```
w / s  - Increase/decrease forward velocity (vx)
a / d  - Increase/decrease yaw rate (turning)
e / c  - Increase/decrease lateral velocity (vy)
z / x  - Increase/decrease height
q      - Quit
```

## Configuration API

### Using in Python Scripts

```python
from genPiHub.configs import create_amo_genesis_env_config_with_usd_scene
from genPiHub.environments import GenesisEnv

# Create AMO environment with USD scene
env_cfg = create_amo_genesis_env_config_with_usd_scene(
    usd_scene_path="path/to/Scene.usd",
    num_envs=1,
    backend="cuda",
    viewer=True,
    load_articulation=True,  # Interactive furniture
    increase_collision_limits=True,  # For complex scenes
)

# Create environment
env = GenesisEnv(cfg=genesis_cfg, device="cuda", env_cfg=env_cfg)

# Environment objects are accessible
objects = env._env.scene.environment_objects
print(f"Loaded objects: {list(objects.keys())}")
```

### Configuration Parameters

```python
create_amo_genesis_env_config_with_usd_scene(
    usd_scene_path: str,              # Path to USD file
    num_envs: int = 1,                # Number of environments
    backend: str = "cuda",            # Physics backend
    viewer: bool = False,             # Enable viewer
    enable_corruption: bool = False,  # Observation noise
    resampling_time: float = 1e9,     # Command resampling
    standing_envs_ratio: float = 0.0, # Standing command ratio
    load_articulation: bool = True,   # Load joints
    increase_collision_limits: bool = True,  # For complex scenes
)
```

## Troubleshooting

### Issue: "Exceeding max number of broad phase candidate contact pairs"

**Cause:** Complex USD scenes with many collision geometries exceed default limits.

**Solution:** The `create_amo_genesis_env_config_with_usd_scene()` function automatically sets `increase_collision_limits=True` to handle this.

If you still encounter issues, you can manually adjust:
```python
from genesislab.engine.sim import RigidOptionsCfg

env_cfg.scene.rigid_options = RigidOptionsCfg(
    multiplier_collision_broad_phase=20,  # Increase further if needed
)
```

### Issue: "Joint indexing conflicts" or ActionManager errors

**Cause:** USD objects loaded before robot, interfering with robot DOF space.

**Solution:** This is automatically handled by `environment_objects` system which loads objects AFTER robots. No action needed.

### Issue: Long loading time

**Cause:** Genesis is processing complex USD collision geometries.

**Expected:** First load of Scene.usd may take 2-5 minutes while Genesis computes collision decomposition.

**Optimization:**
- Use static mode (`--no-articulation`) if you don't need interactive furniture
- Start with Terrain.usd (simpler) before using full Scene.usd

### Issue: Robot falls through floor

**Cause:** USD terrain might be at wrong height or have missing collision.

**Solution:**
- Check USD file has proper collision geometry
- Verify terrain is at z=0
- Try adding plane terrain: modify config to include `terrain=TerrainCfg(terrain_type="plane")`

## Examples

### Example 1: Quick Test with Static Terrain

```bash
# Simple test - should work immediately
python third_party/genPiHub/scripts/amo/play_amo_with_terrain_usd.py --viewer
```

### Example 2: Interactive Exploration in Full Scene

```bash
# Full scene with keyboard control
python third_party/genPiHub/scripts/amo/play_amo_with_usd_scene.py \
    --viewer \
    --interactive \
    --vx 0.2
```

### Example 3: Multi-Environment with Custom Scene

```bash
# 4 parallel environments with custom USD
python third_party/genPiHub/scripts/amo/play_amo_with_usd_scene.py \
    --viewer \
    --num-envs 4 \
    --usd-scene /path/to/custom_scene.usd
```

### Example 4: Headless Training Setup

```bash
# Headless mode for training/data collection
python third_party/genPiHub/scripts/amo/play_amo_with_usd_scene.py \
    --headless \
    --num-envs 16 \
    --max-steps 1000000
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│ create_amo_genesis_env_config_with_usd_scene()     │
│                                                     │
│ Returns: AmoGenesisEnvCfg with:                    │
│   scene.environment_objects = EnvironmentObjectsConfig(
│       usd_objects=[                                │
│           USDObjectCfg(                            │
│               name="usd_scene",                    │
│               usd_path="path/to/Scene.usd",        │
│               load_articulation=True,              │
│           ),                                       │
│       ],                                           │
│   )                                                │
│   scene.rigid_options = RigidOptionsCfg(...)      │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ LabScene.build()                                    │
│                                                     │
│ 1. Add terrain (optional)                          │
│ 2. Add robot (G1 - 23 DOF)         ← Robot control │
│ 3. Add environment objects         ← Separate DOF  │
│ 4. scene.build()                   ← Freeze layout │
│ 5. Initialize robot actuators      ← Use 0-22     │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Runtime                                             │
│                                                     │
│ - Robot: 23 controllable DOF                       │
│ - Objects: Separate DOF space (simulated)          │
│ - Collision: Robot ↔ Objects interactions work    │
│ - Access: env.scene.environment_objects            │
└─────────────────────────────────────────────────────┘
```

## Performance Notes

### Loading Times

- **Plane terrain**: < 1 second
- **Terrain.usd** (static): 5-10 seconds (collision decomposition)
- **Scene.usd** (full): 2-5 minutes (first time, many collision geometries)

### Runtime Performance

- **FPS**: 200-500 Hz on CUDA (depends on scene complexity)
- **Memory**: ~2-3 GB GPU for single environment with Scene.usd
- **Multi-env**: Linear scaling (4 envs ≈ 8 GB GPU)

## Migration from Old usd_scene_path

**Old approach (deprecated, caused joint conflicts):**
```python
cfg = SceneCfg(
    usd_scene_path="path/to/Scene.usd",  # ❌ Causes joint indexing issues
)
```

**New approach (recommended):**
```python
cfg = create_amo_genesis_env_config_with_usd_scene(
    usd_scene_path="path/to/Scene.usd",  # ✅ Proper joint isolation
)
```

**Why?**
- Old: USD loaded before robot → furniture joints occupy indices 0-253, robot gets 254-276 → ActionManager errors
- New: Robot loaded first → robot gets indices 0-22, furniture uses separate DOF space → No conflicts

## Next Steps

1. **Start simple**: Run `play_amo_with_terrain_usd.py --viewer` first
2. **Test full scene**: Try `play_amo_with_usd_scene.py --viewer` 
3. **Explore interactively**: Use `--interactive` mode
4. **Custom scenes**: Use `--usd-scene` with your own USD files
5. **Integrate**: Use `create_amo_genesis_env_config_with_usd_scene()` in your own scripts

## Support

For issues or questions:
- Check `ENVIRONMENT_OBJECTS_INTEGRATION_DESIGN.md` for architecture details
- See test scripts for usage examples
- Refer to GenesisLab documentation for core concepts

## References

- **Design Doc**: `/home/ununtu/code/glab/genesislab/ENVIRONMENT_OBJECTS_INTEGRATION_DESIGN.md`
- **Implementation Summary**: `/home/ununtu/code/glab/genesislab/ENVIRONMENT_OBJECTS_IMPLEMENTATION_SUMMARY.md`
- **GenesisLab**: `/home/ununtu/code/glab/genesislab/`
- **Policy Hub**: `/home/ununtu/code/glab/genesislab/third_party/genPiHub/`
