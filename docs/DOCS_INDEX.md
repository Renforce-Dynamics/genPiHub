# genPiHub Documentation Index

Welcome to genPiHub! This index helps you find the right documentation.

## 📚 Quick Navigation

| What do you want to do? | Read this |
|-------------------------|-----------|
| **Get started quickly** | [QUICKSTART.md](QUICKSTART.md) ⭐ |
| **Understand the repository** | [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md) 🗺️ |
| **Learn the architecture** | [ARCHITECTURE.md](ARCHITECTURE.md) 🏗️ |
| **Read the code** | [CODE_GUIDE.md](CODE_GUIDE.md) 💻 |
| **Check technical specs** | [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) 🔧 |
| **Install genPiHub** | [INSTALL.sh](../INSTALL.sh) |
| **Learn about genPiHub** | [README.md](../README.md) |
| **Run tests** | [scripts/README.md](../scripts/README.md) |
| **Understand migration** | [MIGRATION.md](MIGRATION.md) |
| **API reference** | [QUICK_START.md](QUICK_START.md) |

## 📖 Document Guide

### For New Users

**Start Here** → [QUICKSTART.md](QUICKSTART.md)
- 5-minute setup guide
- Installation steps
- First test
- Basic usage example

**Understand Repository** → [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md) 🆕
- Repository structure
- Navigation guide
- Key concepts
- Learning paths

**Then Read** → [README.md](../README.md)
- Comprehensive overview
- Features and architecture
- Detailed examples
- Configuration guide

### For Developers

**Architecture Design** → [ARCHITECTURE.md](ARCHITECTURE.md) 🆕
- System architecture
- Design patterns
- Module details
- Extension guide

**Code Guide** → [CODE_GUIDE.md](CODE_GUIDE.md) 🆕
- Code walkthrough
- Key implementations
- Design patterns
- Debugging tips

**Technical Specs** → [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) 🆕
- Design decisions (ADRs)
- Interface specs
- Performance requirements
- Testing standards

**Test Scripts** → [../scripts/README.md](../scripts/README.md)
- All 11 test scripts explained
- How to run tests
- Expected results
- Debugging tips

**API Documentation** → [QUICK_START.md](QUICK_START.md)
- Detailed API reference
- Configuration options
- Advanced usage

### For Migrating from policy_hub

**Migration Guide** → [MIGRATION.md](MIGRATION.md)
- What changed
- How to update your code
- Verification steps
- Rollback plan

## 📁 Documentation Structure

```
genPiHub/
├── QUICKSTART.md          # ⭐ Start here!
├── README.md              # Comprehensive guide
├── INSTALL.sh             # Installation script
├── MIGRATION.md           # Migration from policy_hub
├── docs/
│   ├── DOCS_INDEX.md          # This file
│   ├── REPOSITORY_GUIDE.md    # 🆕 Repository navigation
│   ├── ARCHITECTURE.md        # 🆕 System architecture
│   ├── CODE_GUIDE.md          # 🆕 Code walkthrough
│   ├── TECHNICAL_SPEC.md      # 🆕 Technical specifications
│   ├── QUICK_START.md         # API documentation
│   ├── PROJECT_OVERVIEW.md    # Project overview
│   ├── INSTALL_GUIDE.md       # Installation details
│   ├── COMPLETION_REPORT.md   # Completion status
│   └── SUMMARY.md             # Project summary
├── scripts/
│   └── README.md          # Test scripts guide
└── examples/
    └── amo_example.py     # Usage examples
```

## 🎯 By Use Case

### I want to install genPiHub
1. Read [QUICKSTART.md](QUICKSTART.md) - Section 1
2. Run [INSTALL.sh](INSTALL.sh)
3. Verify with Section 2

### I want to test genPiHub
1. Read [scripts/README.md](scripts/README.md)
2. Run primary test:
   ```bash
   python scripts/play_amo_genesis_hub.py --viewer
   ```

### I want to use genPiHub in my code
1. Read [QUICKSTART.md](QUICKSTART.md) - Section 6
2. See [examples/amo_example.py](examples/amo_example.py)
3. Read [README.md](README.md) - Usage section

### I want to understand the architecture
1. Read [README.md](README.md) - Structure section
2. Read [docs/QUICK_START.md](docs/QUICK_START.md)
3. Explore source code with comments

### I want to add a new policy
1. Read [README.md](README.md) - Extension section
2. Study `policies/amo_policy.py`
3. Implement `Policy` ABC

### I want to debug issues
1. Read [scripts/README.md](scripts/README.md) - Troubleshooting
2. Run debug tools:
   ```bash
   python scripts/debug_amo_integration.py
   ```

## 📝 Original Documentation

The original Policy Hub documentation is available in `/home/ununtu/code/hvla/docs/`:
- `POLICY_HUB_HANDOVER.md` - Complete handover document
- `GENPIHUB_MIGRATION_CHECKLIST.md` - Detailed migration steps
- `POLICY_HUB_COMPONENTS.md` - Component breakdown
- `GENPIHUB_QUICK_REFERENCE.md` - Quick reference

These provide deep technical details for advanced users.

## 🚀 Recommended Reading Path

### Beginner (First Time User)
1. **Day 1** (30 min)
   - Read [QUICKSTART.md](QUICKSTART.md)
   - Run installation and tests
   - Try interactive demo

2. **Day 2** (1 hour)
   - Read [README.md](README.md)
   - Explore [scripts/README.md](scripts/README.md)
   - Run all test scripts

3. **Day 3** (1 hour)
   - Study [examples/amo_example.py](examples/amo_example.py)
   - Read [docs/QUICK_START.md](docs/QUICK_START.md)
   - Integrate into your project

### Intermediate (Familiar with Policy Hub)
1. **Quick Update** (15 min)
   - Read [MIGRATION.md](MIGRATION.md)
   - Update imports in your code
   - Run tests

### Advanced (Contributing)
1. **Deep Dive** (3 hours)
   - Read all documentation
   - Study source code
   - Read original Policy Hub docs in `/docs/`

## 🔍 Finding Information

### By Topic

| Topic | Document | Section |
|-------|----------|---------|
| **Installation** | QUICKSTART.md | 1 |
| **Testing** | scripts/README.md | All |
| **Usage** | README.md | Quick Start |
| **Configuration** | README.md | Configuration |
| **Policies** | README.md | Structure |
| **Environments** | README.md | Structure |
| **Registry** | QUICKSTART.md | Key Concepts |
| **Migration** | MIGRATION.md | All |
| **Troubleshooting** | QUICKSTART.md | Troubleshooting |

### By Component

| Component | File | Description |
|-----------|------|-------------|
| **Policy Interface** | `policies/base_policy.py` | Abstract base class |
| **AMO Policy** | `policies/amo_policy.py` | AMO implementation |
| **Environment Interface** | `environments/base_env.py` | Abstract base class |
| **Genesis Environment** | `environments/genesis_env.py` | Genesis backend |
| **Registry** | `utils/registry.py` | Dynamic loading |
| **DOF Config** | `tools/dof_config.py` | Joint management |
| **Keyboard Control** | `tools/command_utils.py` | Terminal controller |

## 📞 Support

### Quick Answers
- **Import error?** → Run `bash INSTALL.sh`
- **Test failing?** → Read `scripts/README.md` troubleshooting
- **Low FPS?** → Use headless mode
- **Migration issue?** → Check `MIGRATION.md`

### Documentation Quality

All documentation follows these principles:
- ✅ Clear and concise
- ✅ Example-driven
- ✅ Tested and verified
- ✅ Up-to-date with code

## 🎓 Learning Resources

### Quick Start (< 30 min)
- [QUICKSTART.md](QUICKSTART.md)

### Complete Guide (1-2 hours)
- [README.md](README.md)
- [scripts/README.md](scripts/README.md)

### Deep Dive (3+ hours)
- [docs/QUICK_START.md](docs/QUICK_START.md)
- Original Policy Hub docs in `/docs/`
- Source code with comments

## ✅ Documentation Checklist

- [x] Quick start guide
- [x] Installation script
- [x] Comprehensive README
- [x] Test scripts guide
- [x] Migration guide
- [x] API documentation
- [x] Examples
- [x] Troubleshooting

---

**Documentation Version**: 1.0  
**Last Updated**: 2026-04-08  
**Status**: Complete ✅

Happy coding with genPiHub! 🚀
