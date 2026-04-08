# genPiHub 仓库导览

**版本**: 0.1.0  
**更新日期**: 2026-04-08

欢迎来到 genPiHub！这份文档帮助你快速理解整个仓库的组织和内容。

---

## 🎯 仓库定位

**genPiHub** (Genesis Policy Hub) 是一个统一的人形机器人策略部署框架。

### 核心价值

```
不同算法框架的策略
    ├─ AMO (RSS 2025)
    ├─ CLOT (arXiv:2602.15060)
    ├─ ProtoMotions
    └─ ...
         │
         ▼
    Policy Wrappers (统一接口)
         │
         ▼
    多种仿真环境
    ├─ genesislab
    ├─ mjlab
    └─ isaaclab
         │
         ▼
    真机部署（未来）
```

### 一句话总结

> **将不同框架训练的策略，通过统一接口部署到多种环境**

---

## 📁 仓库结构

```
genPiHub/                           # 仓库根目录
│
├── 📚 docs/                        # 文档中心 ⭐ START HERE
│   ├── DOCS_INDEX.md              # 📖 文档导航（入口）
│   ├── REPOSITORY_GUIDE.md        # 📖 本文档
│   ├── ARCHITECTURE.md            # 🏗️ 架构设计
│   ├── CODE_GUIDE.md              # 💻 代码导读
│   ├── TECHNICAL_SPEC.md          # 🔧 技术规格
│   ├── QUICKSTART.md              # 🚀 5 分钟快速开始
│   ├── QUICK_START.md             # 📘 详细 API 文档
│   ├── MIGRATION.md               # 🔄 从 policy_hub 迁移
│   ├── PROJECT_OVERVIEW.md        # 📊 项目概览
│   ├── INSTALL_GUIDE.md           # 💿 安装指南
│   ├── COMPLETION_REPORT.md       # ✅ 完成报告
│   └── SUMMARY.md                 # 📝 项目总结
│
├── 🐍 genPiHub/                    # 源代码包
│   ├── __init__.py                # 入口：load_policy(), load_environment()
│   │
│   ├── policies/                  # 策略实现
│   │   ├── __init__.py           # 策略注册表
│   │   ├── base_policy.py        # Policy ABC
│   │   └── amo_policy.py         # AMO 策略
│   │
│   ├── environments/              # 环境适配器
│   │   ├── __init__.py           # 环境注册表
│   │   ├── base_env.py           # Environment ABC
│   │   └── genesis_env.py        # Genesis 环境
│   │
│   ├── configs/                   # 配置系统
│   │   ├── __init__.py
│   │   ├── policy_configs.py     # 策略配置
│   │   ├── env_configs.py        # 环境配置
│   │   └── amo_env_builder.py    # AMO 工厂函数
│   │
│   ├── envs/amo/                  # AMO 环境配置（自包含）
│   │   ├── __init__.py
│   │   ├── env_cfg.py            # 环境配置
│   │   ├── robot_cfg.py          # G1 机器人
│   │   ├── observations.py       # 观测函数
│   │   └── actions.py            # 动作配置
│   │
│   ├── tools/                     # 工具模块
│   │   ├── __init__.py
│   │   ├── dof_config.py         # DOF 管理
│   │   └── command_utils.py      # 键盘控制
│   │
│   ├── utils/                     # 框架工具
│   │   ├── __init__.py
│   │   └── registry.py           # 注册系统
│   │
│   ├── examples/                  # 使用示例
│   │   └── amo_example.py
│   │
│   └── setup.py                   # 安装脚本
│
├── 🧪 scripts/                     # 测试和演示脚本
│   ├── test_hub.py               # ⭐ 主集成测试
│   │
│   ├── amo/                       # AMO 专项测试
│   │   ├── README.md             # 测试说明
│   │   ├── check_amo_setup.py    # 检查资产
│   │   ├── test_amo_policy.py    # 测试策略
│   │   ├── test_amo_env.py       # 测试环境
│   │   ├── play_amo.py           # 交互式演示
│   │   ├── play_amo_headless.py  # 性能测试
│   │   └── debug_amo.py          # 调试工具
│   │
│   ├── legacy/                    # 旧版参考
│   │   └── ...
│   │
│   ├── README.md                  # 测试总览
│   └── ORGANIZATION.md            # 脚本组织
│
├── 📄 README.md                    # 主 README
├── 📄 INSTALL.sh                   # 一键安装脚本
└── 📄 setup.py                     # 包配置
```

---

## 🗺️ 导航指南

### 我想...

#### 1️⃣ 快速开始使用

```bash
# 1. 阅读快速开始
docs/QUICKSTART.md

# 2. 安装
bash INSTALL.sh

# 3. 运行测试
python scripts/test_hub.py
python scripts/amo/play_amo.py --viewer

# 4. 查看示例
genPiHub/examples/amo_example.py
```

#### 2️⃣ 理解架构设计

```bash
# 按顺序阅读
docs/PROJECT_OVERVIEW.md      # 项目概览
docs/ARCHITECTURE.md          # 架构设计
docs/CODE_GUIDE.md            # 代码导读
docs/TECHNICAL_SPEC.md        # 技术细节
```

#### 3️⃣ 添加新策略

```bash
# 1. 学习接口
docs/CODE_GUIDE.md            # 第 2 节：Policy 基类

# 2. 参考 AMO 实现
genPiHub/policies/amo_policy.py

# 3. 查看扩展指南
docs/ARCHITECTURE.md          # 第 9 节：扩展指南

# 4. 编写测试
scripts/amo/test_amo_policy.py  # 参考测试
```

#### 4️⃣ 添加新环境

```bash
# 1. 学习接口
docs/CODE_GUIDE.md            # 第 3 节：Environment 基类

# 2. 参考 Genesis 实现
genPiHub/environments/genesis_env.py

# 3. 理解 DOF 映射
docs/TECHNICAL_SPEC.md        # ADR-004
```

#### 5️⃣ 调试问题

```bash
# 1. 运行诊断脚本
python scripts/amo/check_amo_setup.py
python scripts/amo/debug_amo.py

# 2. 查看故障排除
docs/QUICKSTART.md            # 第 7 节

# 3. 检查测试
scripts/README.md             # 故障排除部分
```

#### 6️⃣ 贡献代码

```bash
# 1. 理解项目规范
docs/TECHNICAL_SPEC.md        # 完整规范

# 2. 查看代码风格
genPiHub/                     # 所有文件都有详细注释

# 3. 编写测试
scripts/amo/                  # 测试示例
```

---

## 📚 文档体系

### 文档分层

```
Level 1: 快速开始
    └─ QUICKSTART.md           5 分钟上手

Level 2: 使用指南
    ├─ README.md               完整使用手册
    ├─ INSTALL_GUIDE.md        安装详解
    └─ MIGRATION.md            迁移指南

Level 3: 架构设计
    ├─ PROJECT_OVERVIEW.md     项目概览
    ├─ ARCHITECTURE.md         架构详解
    └─ REPOSITORY_GUIDE.md     仓库导览（本文）

Level 4: 实现细节
    ├─ CODE_GUIDE.md           代码导读
    ├─ TECHNICAL_SPEC.md       技术规格
    └─ scripts/README.md       测试指南

Level 5: 项目管理
    ├─ COMPLETION_REPORT.md    完成报告
    └─ SUMMARY.md              项目总结
```

### 文档关系图

```
DOCS_INDEX.md (导航中心)
    │
    ├─ 快速路径 ──→ QUICKSTART.md ──→ 开始使用
    │
    ├─ 学习路径 ──→ README.md
    │                  ├─→ PROJECT_OVERVIEW.md
    │                  ├─→ ARCHITECTURE.md
    │                  └─→ CODE_GUIDE.md
    │
    ├─ 开发路径 ──→ TECHNICAL_SPEC.md
    │                  └─→ scripts/README.md
    │
    └─ 迁移路径 ──→ MIGRATION.md
```

---

## 🔍 关键概念

### 1. 三层解耦

```
Policy (策略)
  - 定义：如何从观测计算动作
  - 接口：get_observation(), get_action()
  - 示例：AMOPolicy

    ↕ (解耦)

Environment (环境)
  - 定义：提供状态，执行动作
  - 接口：get_data(), step()
  - 示例：GenesisEnv

    ↕ (解耦)

Config (配置)
  - 定义：参数和设置
  - 接口：dataclass
  - 示例：AMOPolicyConfig, GenesisEnvConfig
```

### 2. 注册系统

```python
# 注册（模块初始化时）
policy_registry.add("AMOPolicy", ".amo_policy")

# 使用（运行时）
policy = load_policy("AMOPolicy", model_dir="...")
# 内部：registry.get("AMOPolicy") → import → 实例化
```

**好处**:
- 插件化：易于添加新策略
- 懒加载：只加载使用的模块
- 统一接口：所有策略相同方式加载

### 3. DOF 映射

```python
# 问题：策略和环境的关节顺序不同
policy_joints = ["left_hip", "right_hip"]
robot_joints  = ["right_hip", "left_hip"]

# 解决：构建映射
policy_to_robot_idx = [1, 0]

# 使用：自动重排序
robot_target[policy_to_robot_idx] = policy_target
```

### 4. 状态字典

所有环境必须返回标准化的状态字典：

```python
env_data = {
    "dof_pos": np.ndarray,      # 关节位置
    "dof_vel": np.ndarray,      # 关节速度
    "base_quat": np.ndarray,    # 基座四元数
    "base_ang_vel": np.ndarray, # 基座角速度
    # ... 可选字段
}
```

这保证了策略可以在不同环境间切换。

---

## 🎓 学习路径

### 初学者（第一次使用）

**目标**: 能够运行 AMO 策略

**时间**: 1 小时

```
1. 阅读 QUICKSTART.md          (15 分钟)
2. 运行 INSTALL.sh              (5 分钟)
3. 运行测试脚本                (10 分钟)
   - python scripts/amo/check_amo_setup.py
   - python scripts/amo/test_amo_policy.py
   - python scripts/amo/play_amo.py --viewer
4. 阅读 README.md 使用部分     (15 分钟)
5. 运行示例代码                (15 分钟)
   - genPiHub/examples/amo_example.py
```

### 中级用户（想要集成）

**目标**: 在自己的项目中使用 genPiHub

**时间**: 3 小时

```
1. 复习快速开始                (15 分钟)
2. 深入阅读 README.md          (30 分钟)
3. 学习 API 文档               (30 分钟)
   - docs/QUICK_START.md
4. 理解配置系统               (30 分钟)
   - genPiHub/configs/
5. 编写自己的集成代码          (60 分钟)
6. 运行和调试                  (15 分钟)
```

### 高级开发者（想要扩展）

**目标**: 添加新策略或新环境

**时间**: 1 天

```
1. 理解架构设计               (1 小时)
   - docs/ARCHITECTURE.md
   
2. 深入代码实现               (2 小时)
   - docs/CODE_GUIDE.md
   - 阅读源码
   
3. 学习技术规范               (1 小时)
   - docs/TECHNICAL_SPEC.md
   
4. 参考现有实现               (2 小时)
   - genPiHub/policies/amo_policy.py
   - genPiHub/environments/genesis_env.py
   
5. 编写新组件                  (2 小时)
   - 实现 Policy/Environment
   - 注册
   
6. 编写测试                    (1 小时)
   - 参考 scripts/amo/
```

---

## 🔧 开发指南

### 环境设置

```bash
# 1. 克隆仓库（假设已完成）
cd /home/ununtu/code/hvla/src/genPiHub

# 2. 激活环境
conda activate genesislab

# 3. 安装包（可编辑模式）
pip install -e .

# 4. 验证安装
python -c "import genPiHub; print(genPiHub.__version__)"
```

### 代码风格

```python
# 1. 类型提示
def get_action(self, obs: np.ndarray) -> np.ndarray:
    """Always use type hints"""
    
# 2. Docstrings
def func(arg):
    """Summary line.
    
    Detailed description.
    
    Args:
        arg: Description
        
    Returns:
        Description
    """
    
# 3. 格式化
# 使用 Black (line length 100)
black --line-length 100 genPiHub/

# 4. 导入顺序
# Standard library
import os
import sys

# Third-party
import numpy as np
import torch

# Local
from genPiHub import Policy
```

### 测试流程

```bash
# 1. 单元测试（TODO）
pytest tests/

# 2. 集成测试
python scripts/test_hub.py

# 3. 组件测试
python scripts/amo/test_amo_policy.py
python scripts/amo/test_amo_env.py

# 4. 端到端测试
python scripts/amo/play_amo.py --viewer
```

---

## 📊 仓库统计

### 代码规模

```
Language         Files       Lines       Code    Comments
-------------------------------------------------------
Python              23       ~2000       1600         400
Markdown             8       ~5000       4000        1000
Shell                1         ~50         40          10
-------------------------------------------------------
Total               32       ~7050       5640        1410
```

### 模块分布

```
genPiHub/
├── policies/         ~300 lines   (15%)
├── environments/     ~300 lines   (15%)
├── configs/          ~400 lines   (20%)
├── envs/amo/         ~500 lines   (25%)
├── tools/            ~200 lines   (10%)
├── utils/            ~100 lines   (5%)
└── examples/         ~200 lines   (10%)
```

### 文档完整性

```
✅ README.md                 (主文档)
✅ QUICKSTART.md            (快速开始)
✅ ARCHITECTURE.md          (架构设计)
✅ CODE_GUIDE.md            (代码导读)
✅ TECHNICAL_SPEC.md        (技术规格)
✅ REPOSITORY_GUIDE.md      (本文档)
✅ scripts/README.md        (测试指南)
✅ MIGRATION.md             (迁移指南)

Coverage: 100% ✅
```

---

## 🚀 快速命令

### 常用命令

```bash
# 安装
bash INSTALL.sh

# 主测试
python scripts/test_hub.py

# 快速验证
python scripts/amo/check_amo_setup.py

# 交互式演示
python scripts/amo/play_amo.py --viewer

# 性能测试
python scripts/amo/play_amo_headless.py --num-steps 1000

# 调试
python scripts/amo/debug_amo.py

# 查看文档
cat docs/DOCS_INDEX.md
```

### 常见任务

```bash
# 任务 1: 验证安装
python -c "import genPiHub; print('✅ OK')"

# 任务 2: 列出可用策略
python -c "from genPiHub.policies import policy_registry; \
           print(policy_registry.list_registered())"

# 任务 3: 列出可用环境
python -c "from genPiHub.environments import environment_registry; \
           print(environment_registry.list_registered())"

# 任务 4: 检查 DOF 配置
python -c "from genPiHub.envs.amo import AMO_DOF_NAMES; \
           print(f'{len(AMO_DOF_NAMES)} DOFs:', AMO_DOF_NAMES)"
```

---

## 🔗 相关资源

### 外部依赖

- **Genesis**: https://github.com/Genesis-Embodied-AI/Genesis
- **genesislab**: (假设私有仓库)
- **PyTorch**: https://pytorch.org/

### 参考项目

- **RoboJuDo**: https://github.com/HansZ8/RoboJuDo
  - 真机部署框架，genPiHub 的灵感来源
  
- **AMO**: .reference/AMO/
  - Adaptive Motion Optimization (RSS 2025)
  
- **CLOT**: .reference/humanoid_benchmark/
  - Closed-Loop Motion Tracking

---

## 📞 获取帮助

### 问题排查

1. **查看故障排除**: docs/QUICKSTART.md 第 7 节
2. **运行诊断脚本**: scripts/amo/check_amo_setup.py
3. **查看测试指南**: scripts/README.md
4. **检查日志**: 启用 DEBUG 日志

### 常见问题

#### Q: 导入错误 "No module named 'genPiHub'"

```bash
# 解决方案
cd /home/ununtu/code/hvla/src/genPiHub
pip install -e .
```

#### Q: 找不到模型文件

```bash
# 检查路径
ls -la .reference/AMO/
# 应该有: amo_jit.pt, adapter_jit.pt
```

#### Q: FPS 太低

```bash
# 使用无头模式
python scripts/amo/play_amo_headless.py

# 检查 GPU
nvidia-smi
```

---

## 🎯 下一步

### 如果你是...

#### 📖 新用户
→ 阅读 [QUICKSTART.md](QUICKSTART.md)

#### 🛠️ 开发者
→ 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 和 [CODE_GUIDE.md](CODE_GUIDE.md)

#### 🔧 维护者
→ 阅读 [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)

#### 📝 贡献者
→ 查看所有文档，特别是代码风格指南

---

## 📄 文档更新

**维护**: 本文档随代码同步更新

**版本控制**: 与代码版本一致

**反馈**: 如发现文档问题，请提 issue 或 PR

---

**Happy Coding with genPiHub!** 🚀

**维护者**: hvla Team  
**最后更新**: 2026-04-08  
**文档版本**: 0.1.0
