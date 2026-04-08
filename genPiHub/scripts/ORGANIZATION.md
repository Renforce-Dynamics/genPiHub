# Scripts Organization

**Clean, organized test structure for genPiHub**

## 📁 New Structure

```
scripts/
├── test_hub.py           ⭐ Main compatibility test
├── README.md             Documentation index
│
├── amo/                  AMO-specific tests (6 scripts)
│   ├── play_amo.py       ⭐ Interactive demo
│   ├── play_amo_headless.py
│   ├── test_amo_policy.py
│   ├── test_amo_env.py
│   ├── check_amo_setup.py
│   ├── debug_amo.py
│   └── README.md
│
└── legacy/               Reference/historical (5 scripts)
    ├── play_amo_genesislab.py
    ├── play_amo_genesis.py
    ├── play_amo_genesis_old.py
    ├── play_amo_genesis_simple.py
    ├── test_amo_headless.py
    └── README.md
```

## 🎯 Key Changes

### Before (Messy)
```
scripts/
├── play_amo_genesis_hub.py
├── play_amo_headless.py
├── test_amo_policy.py
├── test_amo_env.py
├── check_amo_setup.py
├── debug_amo_integration.py
├── play_amo_genesis.py         # duplicate
├── play_amo_genesis_old.py     # duplicate
├── play_amo_genesis_simple.py  # duplicate
├── play_amo_genesislab.py      # duplicate
└── test_amo_headless.py        # duplicate
```

**Problems**:
- ❌ 11 files in one directory
- ❌ Unclear which to use
- ❌ Mixed active and legacy
- ❌ No clear entry point

### After (Clean)
```
scripts/
├── test_hub.py          # ⭐ START HERE
├── amo/                 # Active tests
└── legacy/              # Reference only
```

**Benefits**:
- ✅ Clear organization
- ✅ Obvious entry point
- ✅ Separate active/legacy
- ✅ Easy to navigate

---

## 🚀 Quick Start

### New Users
```bash
# 1. Test compatibility (⭐ PRIMARY)
python test_hub.py

# 2. Run visual demo
python amo/play_amo.py --viewer

# 3. Check performance
python amo/play_amo_headless.py
```

### Development
```bash
# Quick component tests
cd amo
python check_amo_setup.py && \
python test_amo_policy.py && \
python test_amo_env.py
```

### Debugging
```bash
# Check diagnostics
python amo/debug_amo.py

# Compare with baseline
python legacy/play_amo_genesislab.py
```

---

## 📊 Test Hierarchy

```
test_hub.py                    ⭐ Main Entry Point
    ├── Test 1: Imports
    ├── Test 2: Policy Loading
    ├── Test 3: Environment Creation
    └── Test 4: Integration
        │
        ├── amo/test_amo_policy.py    (detailed policy test)
        ├── amo/test_amo_env.py       (detailed env test)
        └── amo/play_amo.py           (full integration)
```

**Philosophy**: 
- `test_hub.py` = Quick compatibility check (30s)
- `amo/*` = Detailed component tests
- `legacy/*` = Reference/comparison only

---

## 🎯 Purpose of Each Script

### Main Test
| Script | Purpose | When to Use |
|--------|---------|-------------|
| **test_hub.py** | Verify hub-genesislab compatibility | Always run first |

### AMO Tests
| Script | Purpose | When to Use |
|--------|---------|-------------|
| **play_amo.py** | Interactive visual demo | Development, demos |
| **play_amo_headless.py** | Performance benchmark | CI, performance testing |
| **test_amo_policy.py** | Policy unit test | Policy changes |
| **test_amo_env.py** | Environment unit test | Environment changes |
| **check_amo_setup.py** | Asset verification | Setup, debugging |
| **debug_amo.py** | Diagnostic tool | Debugging issues |

### Legacy Scripts
| Script | Purpose | When to Use |
|--------|---------|-------------|
| **play_amo_genesislab.py** | Baseline performance | Comparison only |
| **Others** | Historical reference | Learning, debugging |

---

## 🔄 Migration Guide

### Old Command → New Command

```bash
# Before
python scripts/play_amo_genesis_hub.py --viewer

# After
python src/genPiHub/scripts/amo/play_amo.py --viewer
```

```bash
# Before
python scripts/test_amo_policy.py

# After
python src/genPiHub/scripts/amo/test_amo_policy.py
```

```bash
# Before
python scripts/check_amo_setup.py

# After
python src/genPiHub/scripts/amo/check_amo_setup.py
```

### New Workflow

```bash
# 1. Main compatibility test (NEW!)
python src/genPiHub/scripts/test_hub.py

# 2. Visual verification
python src/genPiHub/scripts/amo/play_amo.py --viewer

# 3. Performance test
python src/genPiHub/scripts/amo/play_amo_headless.py
```

---

## ✅ Benefits of New Organization

### For Users
- ✅ Clear entry point (`test_hub.py`)
- ✅ Organized by purpose
- ✅ Easy to find scripts
- ✅ Better documentation

### For Developers
- ✅ Separate concerns (AMO vs legacy)
- ✅ Easier to maintain
- ✅ Clear test hierarchy
- ✅ Reduced confusion

### For Testing
- ✅ Comprehensive compatibility test
- ✅ Focused component tests
- ✅ Easy CI integration
- ✅ Performance baselines

---

## 📖 Documentation

Each directory has its own README:

- **`scripts/README.md`** - Overall guide
- **`scripts/amo/README.md`** - AMO test details
- **`scripts/legacy/README.md`** - Legacy script info

Plus this file for organization overview.

---

## 🎯 Recommended Reading Order

1. **This file** - Understand organization
2. **`README.md`** - Learn available tests
3. **`amo/README.md`** - Learn AMO specifics
4. **Run `test_hub.py`** - Verify setup

---

## 🚀 Testing Workflow

### Daily Development
```bash
python test_hub.py                    # Quick check
python amo/test_amo_policy.py        # After policy changes
python amo/play_amo.py --viewer      # Visual verification
```

### Before Commit
```bash
# Full test suite
python test_hub.py && \
python amo/test_amo_policy.py && \
python amo/test_amo_env.py && \
python amo/play_amo_headless.py --num-steps 500
```

### CI/CD
```bash
# Automated testing (no viewer)
python test_hub.py --num-steps 50 && \
python amo/check_amo_setup.py && \
python amo/play_amo_headless.py --num-steps 1000
```

---

## 📊 File Count

- **Active scripts**: 7 (1 main + 6 AMO)
- **Legacy scripts**: 5 (reference)
- **Documentation**: 4 README files
- **Total**: 16 files

Previously: 12 files in flat structure  
Now: 16 files in organized structure (+4 READMEs)

---

## 🎉 Summary

**Old**: Flat directory with 11 mixed scripts  
**New**: Organized structure with clear purpose

**Main test**: `test_hub.py` ⭐  
**Active tests**: `amo/` directory  
**Reference**: `legacy/` directory

**Result**: Much clearer, easier to use, better for testing hub-genesislab compatibility!

---

**Start here**: `python test_hub.py` 🚀
