# CLOT Test Scripts

Test scripts for CLOT (Closed-Loop Motion Tracking) policy.

## Scripts

### 1. `test_clot_policy.py`

Basic functionality test for CLOT policy.

**Tests:**
- ✅ Policy loading
- ✅ Observation construction
- ✅ Action generation
- ✅ Policy reset
- ✅ Multi-step rollout

**Usage:**
```bash
# Test without model (structure only)
python scripts/clot/test_clot_policy.py

# Test with model file
python scripts/clot/test_clot_policy.py --model-file path/to/clot_policy.pt

# Test with motion library
python scripts/clot/test_clot_policy.py \
    --model-file path/to/clot_policy.pt \
    --motion-lib-dir path/to/motions \
    --device cuda
```

**Expected Output:**
```
====================================================================================================
CLOT Policy Test Suite
====================================================================================================
Model file: None (testing without model)
Motion lib: None
Device: cpu

============================================================
Test 1: Policy Loading
============================================================
✅ Policy loaded successfully
   - num_obs: 0
   - num_actions: 23
   - device: cpu
   - has_model: False
   - has_motion_lib: False

============================================================
Test 2: Observation Construction
============================================================
✅ Observation constructed successfully
   - Observation shape: (64,)
   - Observation dtype: float32

... (more tests)

============================================================
Test Summary
============================================================
✅ All tests passed!

✨ CLOT policy implementation is working correctly!
```

## Policy Files

CLOT requires:
1. **Policy model file** (`clot_policy.pt` or `.jit`)
   - Trained CLOT tracking policy
   - Can be JIT compiled PyTorch model

2. **Motion library** (optional)
   - Directory containing reference motion files (`.npy`)
   - Used for motion tracking tasks

## Getting CLOT Models

CLOT models are from the `humanoid_benchmark` project:
- Paper: https://arxiv.org/abs/2602.15060
- Code: https://github.com/humanoidverse/humanoid_benchmark

**Extract models from humanoid_benchmark:**
```bash
# Copy trained policy
cp /path/to/humanoid_benchmark/logs/motion_tracking/model.pt data/CLOT/clot_policy.pt

# Copy motion library
cp -r /path/to/humanoid_benchmark/data/motions data/CLOT/motions
```

## Configuration

CLOT policy configuration (`CLOTPolicyConfig`):

```python
from genPiHub import load_policy

policy = load_policy(
    name="CLOTPolicy",
    policy_file="data/CLOT/clot_policy.pt",
    motion_lib_dir="data/CLOT/motions",
    device="cuda",
    action_scale=0.25,
    use_amp=True,
)
```

## Troubleshooting

### "No model file provided"
- This is expected when testing structure only
- Provide `--model-file` to test with actual model

### "Motion library directory not found"
- Motion library is optional
- CLOT can run without it (using policy only)

### "Import error"
- Make sure genPiHub is installed: `pip install -e .`
- Check that all dependencies are installed

## Next Steps

After successful tests:
1. Use `play_clot.py` for interactive simulation (to be implemented)
2. Integrate CLOT into your application
3. See `docs/policies/CLOT.md` for detailed documentation

## Status

🚧 **Work in Progress**
- [x] Policy structure
- [x] Basic tests
- [ ] Interactive play script
- [ ] Motion library integration
- [ ] Genesis environment integration
