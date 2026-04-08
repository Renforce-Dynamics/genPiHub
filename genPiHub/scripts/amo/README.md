# AMO Policy Tests

**Tests for AMO (Adaptive Motion Optimization) policy with genPiHub**

## 🎯 Purpose

Test that the AMO policy works correctly with genPiHub framework and genesislab environments.

## 📋 Test Scripts

### 1. Asset Check
```bash
python check_amo_setup.py
```
**Verifies**:
- ✅ `.reference/AMO/amo_jit.pt` exists
- ✅ `.reference/AMO/adapter_jit.pt` exists
- ✅ `data/amo_assets/g1.xml` exists

**Duration**: ~2 seconds

---

### 2. Policy Test
```bash
python test_amo_policy.py
```
**Tests**:
- ✅ Policy loads from JIT models
- ✅ Observation building (153-dim)
- ✅ Action generation (23-DOF)
- ✅ History buffer management

**Duration**: ~10 seconds

---

### 3. Environment Test
```bash
python test_amo_env.py
```
**Tests**:
- ✅ Genesis scene creation
- ✅ Robot spawning
- ✅ Environment reset
- ✅ State dict structure

**Duration**: ~10 seconds

---

### 4. Interactive Demo ⭐
```bash
python play_amo.py --viewer
```
**Full integration test with visualization**

**Features**:
- Genesis viewer window
- Real-time FPS display
- Keyboard control
- Visual debugging

**Controls**:
- ⬆️⬇️: Forward/backward velocity
- ⬅️➡️: Yaw rotation
- W/S: Height adjustment
- A/D: Torso lean
- Q: Quit

**Expected Performance**: 37-38 FPS

---

### 5. Headless Performance Test
```bash
python play_amo_headless.py --num-steps 1000
```
**Performance benchmark without viewer**

**Expected**: 50+ FPS  
**Purpose**: Measure maximum throughput

**Options**:
```bash
python play_amo_headless.py --num-steps 500    # Quick test
python play_amo_headless.py --num-steps 5000   # Extended test
```

---

### 6. Debug Tool
```bash
python debug_amo.py
```
**Diagnostic information**

**Outputs**:
- Observation dimensions and structure
- Joint order mapping (AMO ↔ Genesis)
- Action ranges and offsets
- DOF configuration

**Use when**:
- Robot behaves strangely
- Joint order seems wrong
- Debugging observation issues

---

## 🚀 Quick Test Suite

Run all tests in sequence:

```bash
# From amo/ directory
python check_amo_setup.py && \
python test_amo_policy.py && \
python test_amo_env.py && \
echo "✅ All component tests passed!"
```

**Total time**: ~30 seconds

---

## 🎯 Test Workflow

### First Time Setup
1. `check_amo_setup.py` - Verify assets
2. `test_amo_policy.py` - Test policy
3. `test_amo_env.py` - Test environment
4. `play_amo.py --viewer` - Visual verification

### Development Workflow
1. Make changes
2. `test_amo_policy.py` - Quick policy check
3. `play_amo.py --viewer` - Visual test
4. `play_amo_headless.py` - Performance check

### Before Commit
1. Run quick test suite (above)
2. Run headless test
3. Run visual test for sanity check

---

## ✅ Success Criteria

All tests should show:
- ✅ No import errors
- ✅ Models load correctly
- ✅ Observations are 153-dim
- ✅ Actions are 23-DOF
- ✅ Robot stands stable
- ✅ FPS: 37-38 (viewer), 50+ (headless)

---

## 🐛 Common Issues

### Robot Collapses Immediately
**Cause**: Joint order mismatch  
**Fix**: Run `debug_amo.py` to check joint mapping

### Wrong Starting Pose
**Cause**: Action offset issue  
**Fix**: Verify `use_default_offset=False` in AMO config

### Low FPS
**Cause**: Viewer overhead  
**Fix**: Use `play_amo_headless.py` for max performance

### Policy Crashes
**Cause**: Wrong observation dimension  
**Fix**: Run `test_amo_policy.py` to diagnose

---

## 📊 Expected Output Examples

### check_amo_setup.py
```
Checking AMO setup...
✅ AMO policy model found: .reference/AMO/amo_jit.pt
✅ AMO adapter model found: .reference/AMO/adapter_jit.pt
✅ G1 robot MJCF found: data/amo_assets/g1.xml
✅ All assets verified!
```

### test_amo_policy.py
```
Testing AMO policy...
✅ Policy loaded successfully
✅ Observation shape: torch.Size([1, 153])
✅ Action shape: torch.Size([1, 23])
✅ AMO policy test PASSED
```

### play_amo.py --viewer
```
Initializing AMO policy with Genesis...
✅ Genesis initialized
✅ Environment created
✅ Policy loaded
✅ Starting simulation

FPS: 37.8 | Step: 100
Command: [vx=0.5, vy=0.0, yaw=0.0]
...
```

---

## 📖 More Info

- **Main test**: `../test_hub.py` (compatibility test)
- **Installation**: `../../QUICKSTART.md`
- **Documentation**: `../../README.md`

---

**Run `python play_amo.py --viewer` to see it in action!** 🚀
