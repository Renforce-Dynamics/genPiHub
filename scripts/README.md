# genPiHub Test Scripts

**Organized test suite for genPiHub framework**

## 📁 Directory Structure

```
scripts/
├── amo/              # AMO policy tests (main)
├── legacy/           # Reference/comparison scripts
└── test_hub.py       # Main compatibility test ⭐
```

## 🧪 Main Tests

### Hub Compatibility Test ⭐
**Test genPiHub policies with genesislab environments**

```bash
# Run from project root
python src/genPiHub/scripts/test_hub.py
```

This is the **primary test** to verify that:
- ✅ genPiHub policies work with genesislab
- ✅ No import conflicts
- ✅ Performance matches expectations
- ✅ Full integration works correctly

## 📦 AMO Tests (`amo/`)

**Specific tests for AMO policy integration**

### Quick Test Suite
```bash
cd src/genPiHub/scripts/amo

# 1. Check assets (5 seconds)
python check_amo_setup.py

# 2. Test policy (10 seconds)
python test_amo_policy.py

# 3. Test environment (10 seconds)
python test_amo_env.py
```

### Interactive Demo
```bash
# Main test - Interactive with viewer
python amo/play_amo.py --viewer
```

**Expected**:
- Genesis viewer opens
- Robot stands at default pose
- FPS: 37-38
- Keyboard controls work

**Controls**:
- Arrow keys: Velocity control
- W/S: Height adjustment
- A/D: Torso lean
- Q: Quit

### Headless Performance Test
```bash
# High-performance headless mode
python amo/play_amo_headless.py --num-steps 1000
```

Expected: 50+ FPS

### Debug Tools
```bash
# Debug observation/action flow
python amo/debug_amo.py
```

Prints:
- Observation dimensions
- Joint mapping
- Action ranges

## 📚 Legacy Scripts (`legacy/`)

**Reference implementations for comparison**

These scripts are kept for:
- Baseline performance comparison
- Testing different approaches
- Historical reference

```bash
# Direct genesislab usage (no genPiHub)
python legacy/play_amo_genesislab.py

# Earlier genPiHub versions
python legacy/play_amo_genesis.py
python legacy/play_amo_genesis_old.py
python legacy/play_amo_genesis_simple.py
```

## 🎯 Recommended Testing Workflow

### For Development
1. **Quick check**: `python test_hub.py`
2. **Component tests**: Run AMO tests
3. **Visual verification**: `python amo/play_amo.py --viewer`

### For CI/Automated Testing
```bash
# Headless test suite
python amo/check_amo_setup.py && \
python amo/test_amo_policy.py && \
python amo/test_amo_env.py && \
python amo/play_amo_headless.py --num-steps 500
```

### For Debugging
1. **Check setup**: `python amo/check_amo_setup.py`
2. **Run debug**: `python amo/debug_amo.py`
3. **Compare**: Run legacy scripts for baseline

## 📊 Test Coverage

| Test | What it checks | Duration |
|------|----------------|----------|
| **test_hub.py** ⭐ | Hub-genesislab compatibility | ~30s |
| **check_amo_setup.py** | Asset files exist | ~2s |
| **test_amo_policy.py** | Policy loads & infers | ~10s |
| **test_amo_env.py** | Environment creates | ~10s |
| **play_amo.py** | Full integration (visual) | Interactive |
| **play_amo_headless.py** | Performance test | ~20s |
| **debug_amo.py** | Observation/action debug | ~5s |

## ✅ Success Criteria

All tests should show:
- ✅ No import errors
- ✅ Assets found
- ✅ Policy loads correctly
- ✅ Environment creates successfully
- ✅ Viewer mode: 37-38 FPS
- ✅ Headless mode: 50+ FPS
- ✅ Robot moves naturally

## 🐛 Troubleshooting

### Import Error
```bash
cd /home/ununtu/code/hvla/src/genPiHub
pip install -e .
```

### Asset Not Found
Check that `.reference/AMO/` exists with models:
```bash
ls -la .reference/AMO/
# Should show: amo_jit.pt, adapter_jit.pt
```

### Low FPS
- Use headless mode for max performance
- Check GPU usage: `nvidia-smi`
- Reduce num_envs if needed

### Robot Behaves Strangely
Run debug script to check joint mapping:
```bash
python amo/debug_amo.py
```

## 📖 More Info

- **Installation**: `src/genPiHub/QUICKSTART.md`
- **Documentation**: `src/genPiHub/README.md`
- **Migration**: `src/genPiHub/MIGRATION.md`

---

**Quick Start**: Run `python test_hub.py` to verify everything works!
