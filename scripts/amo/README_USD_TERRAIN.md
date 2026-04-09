# AMO Policy on USD Terrain

Deploy AMO humanoid policy on custom USD terrains (like Scene.usd).

## 🎯 What This Does

This script combines:
- ✅ **AMO policy** - Pre-trained humanoid locomotion controller
- ✅ **USD terrain** - Custom 3D environments (Scene.usd)
- ✅ **Interactive control** - Real-time keyboard commands
- ✅ **Multi-environment** - Multiple robots on the same terrain

---

## 🚀 Quick Start

### 1. Basic Test (Recommended First)

```bash
cd /home/ununtu/code/glab/genesislab

# Run with viewer on Scene.usd
python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py --viewer
```

**What you'll see:**
- AMO humanoid walking on the Scene.usd terrain
- 3D interactive viewer
- Real-time position and command display

---

### 2. Interactive Control

```bash
# Enable keyboard control
python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py --viewer --interactive
```

**Keyboard controls:**
- `W`/`S` - Forward/backward velocity
- `A`/`D` - Turn left/right
- `E`/`C` - Strafe left/right
- `Z`/`X` - Height up/down
- `Q` - Quit

---

### 3. Multiple Environments

```bash
# 4 robots on the terrain
python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py --viewer --num-envs 4 --env-spacing 12.0
```

---

## 📋 Command Line Options

### Terrain Options

```bash
# Custom USD file
--usd-path path/to/your/scene.usd

# Environment spacing (meters)
--env-spacing 10.0

# Number of environments
--num-envs 4
```

### Control Options

```bash
# Enable interactive keyboard control
--interactive

# Set fixed velocities
--vx 0.5          # Forward velocity (m/s)
--vy 0.1          # Lateral velocity (m/s)
--yaw-rate 0.2    # Yaw rate (rad/s)
```

### Simulation Options

```bash
# Enable viewer (recommended)
--viewer

# Headless mode
--headless

# Maximum steps
--max-steps 10000

# Device selection
--device cuda     # or 'cpu'
```

---

## 📝 Usage Examples

### Example 1: Walk Forward

```bash
python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py \
    --viewer \
    --vx 0.5
```

### Example 2: Interactive Exploration

```bash
python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py \
    --viewer \
    --interactive \
    --num-envs 1
```

### Example 3: Multiple Robots

```bash
python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py \
    --viewer \
    --num-envs 4 \
    --env-spacing 15.0 \
    --vx 0.3
```

### Example 4: Custom USD Terrain

```bash
python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py \
    --viewer \
    --usd-path /path/to/your/custom_scene.usd \
    --env-spacing 8.0
```

### Example 5: Headless Testing

```bash
python third_party/genPiHub/scripts/amo/play_amo_usd_terrain.py \
    --headless \
    --max-steps 500 \
    --print-every 50
```

---

## 🎬 Expected Output

```
================================================================================
🏃 AMO Policy on USD Terrain
================================================================================
Mode: 🎬 Viewer
USD terrain: third_party/genPiHub/data/assets/CWDL_LW_Assets_20260310/Scene.usd
Environments: 1
Env spacing: 10.0m
================================================================================

✅ USD file found: Scene.usd
✅ Backend: cuda

[1/4] Creating AMO policy configuration...
✅ Policy config: 23 DOFs, 50.0Hz

[2/4] Creating environment with USD terrain...
✅ Environment: 1 envs, 23 DOFs
   Terrain: USD (grid-based, 10.0m spacing)

[3/4] Loading AMO policy...
✅ Policy loaded: AMOPolicy
   Device: cuda
   Action scale: 0.25

✅ Fixed command: vx=0.30 m/s, vy=0.00 m/s, yaw=0.00 rad/s

[4/4] Resetting environment...
✅ Ready to run!

================================================================================
👁️  VIEWER CONTROLS:
   - Mouse drag: Rotate camera
   - Mouse wheel: Zoom in/out
   - Arrow keys: Pan camera
   - Ctrl+C: Emergency stop
================================================================================

▶️  Running for 100000 steps...

Step 000000 | FPS   50.2 | Pos [  0.00,   0.00, 0.750] | Cmd [vx=0.30, vy=0.00, yaw=0.00]
Step 000100 | FPS   50.1 | Pos [  0.45,   0.02, 0.752] | Cmd [vx=0.30, vy=0.00, yaw=0.00]
Step 000200 | FPS   50.0 | Pos [  0.91,   0.01, 0.751] | Cmd [vx=0.30, vy=0.00, yaw=0.00]
...
```

---

## 🐛 Troubleshooting

### USD file not found

```
❌ ERROR: USD file not found: third_party/genPiHub/data/assets/CWDL_LW_Assets_20260310/Scene.usd
```

**Solution:** Check the USD file path. Update `--usd-path` if needed.

### AMO model not found

```
❌ ERROR: AMO model files not found in data/AMO/
```

**Solution:** Ensure AMO models are available:
- `data/AMO/amo_jit.pt`
- `data/AMO/adapter_jit.pt`
- `data/AMO/adapter_norm_stats.pt`

Use `--model-dir` to specify a different location.

### Genesis not initialized

```
❌ ERROR: Genesis backend not initialized
```

**Solution:** Make sure Genesis is installed:
```bash
pip install genesis-world
```

### Import errors

```
❌ ERROR: No module named 'genPiHub'
```

**Solution:** Install genPiHub:
```bash
cd third_party/genPiHub
pip install -e .
```

---

## 🔧 How It Works

### 1. Environment Configuration

The script modifies the AMO environment to use USD terrain:

```python
# Default AMO config (plane terrain)
cfg.scene.terrain = TerrainCfg(terrain_type="plane")

# Modified for USD terrain
cfg.scene.terrain = TerrainCfg(
    terrain_type="usd",
    usd_path="path/to/Scene.usd",
    env_spacing=10.0,
)
```

### 2. Environment Origins

USD terrain uses **grid-based** placement:
- Environments are arranged in a square grid
- Spacing controlled by `env_spacing` parameter
- No curriculum (static terrain)

```
Env 0: [  0.00,   0.00, 0.00]
Env 1: [ 10.00,   0.00, 0.00]
Env 2: [  0.00,  10.00, 0.00]
Env 3: [ 10.00,  10.00, 0.00]
```

### 3. Policy Integration

AMO policy receives:
- Robot state (joint positions, velocities, base orientation)
- Contact sensors (foot contacts)
- Command inputs (vx, vy, yaw_rate, etc.)

Outputs:
- Joint position targets (23 DOF)
- Scaled by `action_scale` (default: 0.25)

---

## 📊 Performance Tips

### For Best Performance

```bash
# Use CUDA backend (automatic if available)
--device cuda

# Reduce environments for complex terrains
--num-envs 1

# Disable viewer for headless testing
--headless
```

### For Best Visualization

```bash
# Enable viewer
--viewer

# Single environment for close-up view
--num-envs 1

# Interactive control for exploration
--interactive
```

---

## 🎨 Customization

### Create Your Own USD Terrain

1. **Design in Blender/Maya/Houdini**
2. **Export as USD** (.usd or .usda)
3. **Use with this script**:
   ```bash
   python scripts/amo/play_amo_usd_terrain.py \
       --viewer \
       --usd-path /path/to/your/custom_terrain.usd
   ```

### Adjust Environment Spacing

- **Small terrain**: `--env-spacing 5.0`
- **Medium terrain**: `--env-spacing 10.0` (default)
- **Large terrain**: `--env-spacing 20.0`

Rule of thumb: spacing should be 2-3x the terrain feature size.

---

## 📚 Related Scripts

- [`play_amo.py`](play_amo.py) - Original AMO script (plane terrain)
- [`test_amo_env.py`](test_amo_env.py) - AMO environment test
- [`check_amo_setup.py`](check_amo_setup.py) - AMO setup validation

---

## 🎉 Success Checklist

Your setup is working if:

- ✅ Script starts without errors
- ✅ Viewer opens and shows USD terrain
- ✅ Humanoid robot appears on the terrain
- ✅ Robot walks in response to commands
- ✅ FPS is stable (>30 fps for single env)

---

## 💡 Tips & Tricks

### 1. Debugging

Start with minimal setup:
```bash
python scripts/amo/play_amo_usd_terrain.py --viewer --num-envs 1 --max-steps 500
```

### 2. Recording Videos

Use Genesis viewer's built-in recording:
- Open viewer
- Press record button
- Run the script
- Video saved automatically

### 3. Testing New Terrains

Quick test without viewer:
```bash
python scripts/amo/play_amo_usd_terrain.py \
    --headless \
    --usd-path new_terrain.usd \
    --max-steps 100
```

---

## 🚀 Next Steps

1. ✅ Try different USD terrains
2. ✅ Experiment with command velocities
3. ✅ Test multi-environment scenarios
4. ✅ Integrate with your training pipeline

---

**Questions?** Check the [main USD terrain documentation](../../../../scripts/README_USD_TERRAIN.md)
