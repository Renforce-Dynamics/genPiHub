# Legacy Scripts

**Reference implementations and historical versions**

## 📚 Purpose

These scripts are kept for:
- **Baseline comparison**: Compare performance with direct genesislab usage
- **Historical reference**: Track evolution of implementation
- **Debugging**: Reference older working versions
- **Education**: Learn different approaches

⚠️ **Not recommended for regular use** - Use main scripts in `../amo/` instead

---

## 📁 Contents

### Direct genesislab Usage

**`play_amo_genesislab.py`**
- Direct use of genesislab without genPiHub
- Baseline performance reference
- Shows what genPiHub abstracts away

```bash
python play_amo_genesislab.py
```

**Use when**: Need baseline performance comparison

---

### Historical genPiHub Versions

**`play_amo_genesis.py`**
- Earlier version with some amo package imports
- Works but less clean than current version

**`play_amo_genesis_old.py`**
- Very early version
- Multiple iterations of refactoring

**`play_amo_genesis_simple.py`**
- Simplified debug version
- Minimal features for testing

**`test_amo_headless.py`**
- Quick headless test
- Merged into main test suite

---

## 🔬 Use Cases

### Performance Comparison
```bash
# Baseline (direct genesislab)
python play_amo_genesislab.py

# Current (genPiHub)
python ../amo/play_amo.py --viewer
```

Compare FPS to ensure genPiHub doesn't add overhead.

### Understanding Evolution
Read these in order to see how the code evolved:
1. `play_amo_genesis_old.py` - Initial version
2. `play_amo_genesis.py` - Improved version
3. `play_amo_genesis_simple.py` - Simplified
4. `../amo/play_amo.py` - Current clean version

### Debugging Reference
If current version breaks, these can help identify:
- What changed
- What used to work
- Alternative approaches

---

## ⚠️ Important Notes

### These scripts may:
- ❌ Use outdated import paths
- ❌ Have direct amo package dependencies
- ❌ Miss latest optimizations
- ❌ Have inconsistent naming

### Current scripts are better because:
- ✅ Clean genPiHub integration
- ✅ Zero unnecessary imports
- ✅ Better organization
- ✅ Latest optimizations
- ✅ Full documentation

---

## 📊 Performance Baseline

### Expected FPS (baseline)

| Script | Mode | Expected FPS |
|--------|------|--------------|
| `play_amo_genesislab.py` | Direct | ~40 FPS |
| `../amo/play_amo.py` | genPiHub | 37-38 FPS |

**Conclusion**: genPiHub overhead is ~5%, which is acceptable for the abstraction benefits.

---

## 🗑️ Deprecation Plan

These scripts will be:
- ✅ Kept for reference (short term)
- ⚠️ Archived after stable release (medium term)
- ❌ Removed after full migration (long term)

Current status: **Reference only** - do not use for new development

---

## 📖 Recommended Reading Order

For learning:
1. Start with `../amo/play_amo.py` (current clean version)
2. Read `play_amo_genesislab.py` (understand baseline)
3. Compare implementations to see genPiHub benefits

For debugging:
1. Run current version
2. If issues, check `play_amo_genesis.py` to see if old version works
3. Compare differences to find regression

---

## 🚀 Migration Path

If you're using these scripts:

### From `play_amo_genesislab.py`
→ Use `../amo/play_amo.py` for same functionality with better abstraction

### From `play_amo_genesis.py`
→ Already migrated! Current version is in `../amo/play_amo.py`

### From `test_amo_headless.py`
→ Use `../amo/play_amo_headless.py --num-steps 100` for quick test

---

## 📞 Questions?

- **Want to use AMO?** → Use `../amo/play_amo.py`
- **Need performance?** → Use `../amo/play_amo_headless.py`
- **Debugging?** → Compare with `play_amo_genesislab.py` baseline
- **Learning?** → Read all versions to see evolution

---

**Remember**: These are reference only. Use scripts in `../amo/` for active development!
