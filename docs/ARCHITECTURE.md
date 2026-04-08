# genPiHub 架构文档

**版本**: 0.1.0  
**更新日期**: 2026-04-08

## 📐 项目定位

**genPiHub** 是 **Genesis Policy Hub** 的缩写，是一个统一的人形机器人策略部署框架。

### 核心目标

- 存放不同算法框架训练出来的策略（AMO, CLOT, ProtoMotions 等）
- 提供统一的 policy wrapper 接口
- 对接多种仿真环境（genesislab, mjlab, isaaclab）
- 支持未来的真机部署

### 设计理念

> **"Just load, just run"** - 插拔式策略部署

**三大解耦原则**:
1. **Policy** ↔ **Environment** - 策略与环境完全独立
2. **Config** ↔ **Implementation** - 配置与实现分离
3. **Interface** ↔ **Backend** - 接口与后端解耦

---

## 🏗️ 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    User Application                     │
│  from genPiHub import load_policy, load_environment    │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   genPiHub Core API                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────────┐   │
│  │  Registry  │  │   Loader   │  │  DOF Mapping   │   │
│  │   System   │  │  System    │  │     Tools      │   │
│  └────────────┘  └────────────┘  └────────────────┘   │
└──────┬────────────────────────────────────┬────────────┘
       │                                    │
       ▼                                    ▼
┌─────────────────┐              ┌──────────────────────┐
│   Policy Layer  │              │  Environment Layer   │
├─────────────────┤              ├──────────────────────┤
│ • base_policy   │              │ • base_env           │
│ • amo_policy    │              │ • genesis_env        │
│ • clot_policy   │              │ • mujoco_env (TODO)  │
│ • ...           │              │ • isaac_env (TODO)   │
└─────────────────┘              └──────────────────────┘
       │                                    │
       └────────────┬───────────────────────┘
                    ▼
        ┌────────────────────────┐
        │   Configuration Layer  │
        ├────────────────────────┤
        │ • policy_configs.py    │
        │ • env_configs.py       │
        │ • amo_env_builder.py   │
        └────────────────────────┘
```

---

## 📦 模块详细设计

### 1. 策略层 (Policy Layer)

**位置**: `genPiHub/policies/`

#### 基础接口 (`base_policy.py`)

定义了所有策略必须实现的抽象接口：

```python
class Policy(ABC):
    @abstractmethod
    def reset(self):
        """重置策略状态"""
        
    @abstractmethod
    def get_observation(self, env_data, ctrl_data) -> Tuple[obs, extras]:
        """从环境数据构建策略观测"""
        
    def get_action(self, obs) -> np.ndarray:
        """从观测计算动作"""
        
    @abstractmethod
    def post_step_callback(self, commands=None):
        """步进后回调"""
```

**核心设计**:
- 统一观测接口：`env_data` (环境状态) + `ctrl_data` (控制数据)
- 动作处理链：Model Inference → EMA Smoothing → Clipping → Scaling
- 历史管理：支持观测历史缓冲（deque）
- DOF 配置：分离观测 DOF 和动作 DOF

#### AMO Policy (`amo_policy.py`)

AMO (Adaptive Motion Optimization) 策略包装器：

```python
class AMOPolicy(Policy):
    def __init__(self, cfg: AMOPolicyConfig, device: str = "cpu"):
        # 加载 AMO 模型：amo_jit.pt + adapter_jit.pt
        # 继承 Policy 接口
        
    def get_action(self, obs: Dict) -> np.ndarray:
        # 直接使用环境状态调用 AMO act()
        # 转换 PD target → action
```

**特点**:
- 完全自包含：复制了 AMO 必要的配置到 `envs/amo/`
- 零外部依赖：不依赖原始 AMO 代码库
- JIT 模型加载：使用 torch.jit.load

---

### 2. 环境层 (Environment Layer)

**位置**: `genPiHub/environments/`

#### 基础接口 (`base_env.py`)

定义了环境的统一接口：

```python
class Environment(ABC):
    @abstractmethod
    def reset(self):
        """重置环境"""
        
    @abstractmethod
    def update(self):
        """从后端更新状态"""
        
    @abstractmethod
    def step(self, pd_target: np.ndarray):
        """执行 PD 控制"""
        
    @abstractmethod
    def set_gains(self, stiffness, damping):
        """设置 PD 增益"""
        
    def get_data(self) -> Dict:
        """获取环境状态字典"""
        return {
            "dof_pos": self._dof_pos,
            "dof_vel": self._dof_vel,
            "base_quat": self._base_quat,
            "base_ang_vel": self._base_ang_vel,
            ...
        }
```

**核心设计**:
- 统一状态访问：通过 `get_data()` 返回标准化字典
- DOF 配置管理：通过 `DOFConfig` 处理关节映射
- 只读属性：`dof_pos`, `dof_vel`, `base_quat` 等

#### Genesis Environment (`genesis_env.py`)

Genesis 物理引擎的封装：

```python
class GenesisEnv(Environment):
    def __init__(self, cfg: GenesisEnvConfig, device: str = "cuda", env_cfg=None):
        # 初始化 Genesis backend
        # 创建 ManagerBasedRlEnv
        # 构建关节映射
        
    def _build_joint_mapping(self):
        # Policy DOF 顺序 → Robot 关节顺序
        # 自动处理不同命名约定
```

**特点**:
- 封装 genesislab 的 `ManagerBasedRlEnv`
- 自动关节映射：处理 policy DOF 和 robot joint 顺序差异
- 支持矢量化环境：多并行环境

---

### 3. 配置层 (Configuration Layer)

**位置**: `genPiHub/configs/`

#### 策略配置 (`policy_configs.py`)

```python
@dataclass
class PolicyConfig:
    policy_file: Path | None = None
    device: str = "cpu"
    freq: int = 50
    obs_dof: DOFConfig = None
    action_dof: DOFConfig = None
    action_scale: float = 1.0
    action_clip: float | None = None
    action_beta: float = 1.0  # EMA smoothing
    history_length: int = 0
    disable_autoload: bool = False

@dataclass
class AMOPolicyConfig(PolicyConfig):
    adapter_file: Path | None = None
    norm_stats_file: Path | None = None
    gait_freq: float = 3.0
    scales_ang_vel: float = 0.25
    scales_dof_vel: float = 0.05
```

#### 环境配置 (`env_configs.py`)

```python
@dataclass
class EnvConfig:
    robot: str = "G1"
    backend: str = "cuda"
    num_envs: int = 1
    dof: DOFConfig = None

@dataclass
class GenesisEnvConfig(EnvConfig):
    viewer: bool = False
    terrain: str = "flat"
```

#### AMO 环境构建器 (`amo_env_builder.py`)

工厂函数，快速创建 AMO 环境配置：

```python
def create_amo_genesis_env_config(
    num_envs: int = 1,
    viewer: bool = False,
    device: str = "cuda"
) -> Tuple[GenesisEnvConfig, Any]:
    """创建 AMO + Genesis 环境配置
    
    Returns:
        (GenesisEnvConfig, AmoGenesisEnvCfg) 元组
    """
```

---

### 4. 工具层 (Tools Layer)

**位置**: `genPiHub/tools/`

#### DOF 配置 (`dof_config.py`)

关节自由度管理：

```python
@dataclass
class DOFConfig:
    joint_names: List[str]          # 关节名称列表
    num_dofs: int                   # 自由度数量
    default_pos: np.ndarray         # 默认位置
    position_limits: np.ndarray     # 位置限制
    velocity_limits: np.ndarray     # 速度限制
    torque_limits: np.ndarray       # 力矩限制
    stiffness: np.ndarray           # PD 刚度 (Kp)
    damping: np.ndarray             # PD 阻尼 (Kd)
    
def merge_dof_configs(base, override) -> DOFConfig:
    """合并 DOF 配置（override 优先）"""
```

**用途**:
- 定义机器人关节配置
- 处理不同策略的 DOF 顺序
- 管理 PD 控制参数

#### 命令工具 (`command_utils.py`)

键盘控制和命令管理：

```python
@dataclass
class CommandState:
    """8-DOF 命令状态"""
    vx: float = 0.0          # 前进速度
    vy: float = 0.0          # 侧向速度
    yaw_rate: float = 0.0    # 偏航率
    height: float = 0.0      # 高度
    roll: float = 0.0        # 横滚
    pitch: float = 0.0       # 俯仰
    # ...

class TerminalController:
    """终端键盘控制器"""
    def get_commands(self) -> List[str]:
        """非阻塞读取键盘输入"""
```

---

### 5. 注册系统 (Registry System)

**位置**: `genPiHub/utils/registry.py`

动态类加载系统：

```python
class Registry(Generic[T]):
    def __init__(self, package: str, base_class: Type[T]):
        """初始化注册表"""
        
    def add(self, name: str, module_path: str):
        """注册类（懒加载）"""
        
    def get(self, name: str) -> Type[T]:
        """获取类（首次访问时加载）"""
```

**使用示例**:

```python
# 在 policies/__init__.py 中
policy_registry = Registry(
    package="genPiHub.policies",
    base_class=Policy
)
policy_registry.add("AMOPolicy", ".amo_policy")

# 在用户代码中
policy_class = policy_registry.get("AMOPolicy")
policy = policy_class(config, device="cuda")
```

**优势**:
- 懒加载：仅在需要时导入模块
- 类型检查：确保注册类继承自 base_class
- 统一管理：集中式策略和环境注册

---

### 6. AMO 环境配置 (envs/amo/)

**位置**: `genPiHub/envs/amo/`

完全自包含的 AMO 环境配置，移植自原始 AMO 代码库：

```
envs/amo/
├── __init__.py          # 导出配置类
├── env_cfg.py           # 环境配置 (AmoGenesisEnvCfg)
├── robot_cfg.py         # 机器人配置 (G1 + PD 参数)
├── observations.py      # 观测函数
└── actions.py           # 动作配置
```

**核心文件**:

#### `env_cfg.py` - 环境配置

```python
@configclass
class AmoGenesisEnvCfg(ManagerBasedRlEnvCfg):
    """AMO 在 Genesis 中的环境配置"""
    scene = G1SceneCfg(num_envs=4096)
    observations = AmoObservationsCfg()
    actions = AmoActionsCfg()
    # ... 其他配置
```

#### `robot_cfg.py` - G1 机器人配置

```python
def G1_CFG() -> ArticulationCfg:
    """Unitree G1 机器人配置（23 DOF）"""
    return ArticulationCfg(
        spawn=sim_utils.UsdFileCfg(
            usd_path=f"{ISAACLAB_NUCLEUS_DIR}/Robots/Unitree/G1/g1.usd",
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.75),
            joint_pos={...},  # 默认姿态
        ),
        actuators={
            "legs": ImplicitActuatorCfg(...),
            "torso": ImplicitActuatorCfg(...),
            "arms": ImplicitActuatorCfg(...),
        },
    )
```

**设计原则**:
- ✅ 自包含：不依赖外部 AMO 代码
- ✅ 模块化：每个文件职责单一
- ✅ 可扩展：便于添加新配置

---

## 🔄 数据流设计

### 完整流程

```
User Code
    │
    ├─ load_policy("AMOPolicy")
    │      └─ Registry → AMOPolicy class → __init__
    │             └─ Load models (amo_jit.pt, adapter_jit.pt)
    │
    ├─ load_environment("GenesisEnv")
    │      └─ Registry → GenesisEnv class → __init__
    │             └─ Genesis backend → ManagerBasedRlEnv
    │
    └─ Run Loop:
           │
           ├─ env.reset()
           │      └─ Genesis: 重置机器人状态
           │
           ├─ policy.reset()
           │      └─ 清空历史缓冲、last_action
           │
           └─ for step in range(N):
                  │
                  ├─ env.update()
                  │      └─ Genesis: 更新内部状态
                  │
                  ├─ env_data = env.get_data()
                  │      └─ 返回 {dof_pos, dof_vel, base_quat, ...}
                  │
                  ├─ obs, extras = policy.get_observation(env_data, ctrl_data)
                  │      └─ AMO: 直接返回 env_data（AMO 内部处理）
                  │
                  ├─ action = policy.get_action(obs)
                  │      ├─ Model inference
                  │      ├─ EMA smoothing
                  │      ├─ Clipping
                  │      └─ Scaling
                  │
                  ├─ pd_target = default_pos + action * action_scale
                  │
                  ├─ env.step(pd_target)
                  │      └─ Genesis: PD 控制 → 物理步进
                  │
                  └─ policy.post_step_callback()
                         └─ 更新内部状态
```

### 关节映射流程

```
Policy DOF Order              Robot Joint Order
  (配置在 DOFConfig)             (Genesis/真机顺序)
        │                              │
        │   _build_joint_mapping()     │
        └──────────────┬────────────────┘
                       │
                policy_to_robot_idx[]
                       │
        action[i] ───→ pd_target[policy_to_robot_idx[i]]
```

**示例**:
- Policy: `["left_hip_pitch", "right_hip_pitch", ...]`
- Robot: `["right_hip_pitch", "left_hip_pitch", ...]`
- Mapping: `[1, 0, ...]` - 自动重排序

---

## 🧪 测试架构

**位置**: `scripts/`

```
scripts/
├── test_hub.py              # ⭐ 主集成测试
├── amo/                     # AMO 专项测试
│   ├── check_amo_setup.py   # 检查资产文件
│   ├── test_amo_policy.py   # 测试策略加载
│   ├── test_amo_env.py      # 测试环境创建
│   ├── play_amo.py          # 交互式演示（带viewer）
│   ├── play_amo_headless.py # 性能测试（无头模式）
│   └── debug_amo.py         # 调试工具
└── legacy/                  # 旧版参考实现
    └── ...
```

### 测试覆盖

| 测试 | 覆盖范围 | 耗时 |
|------|---------|------|
| `test_hub.py` | genPiHub ↔ genesislab 兼容性 | ~30s |
| `check_amo_setup.py` | 资产文件存在性 | ~2s |
| `test_amo_policy.py` | 策略加载 + 推理 | ~10s |
| `test_amo_env.py` | 环境创建 | ~10s |
| `play_amo.py` | 完整集成（视觉） | 交互式 |
| `play_amo_headless.py` | 性能基准 | ~20s |

---

## 📊 性能指标

### 运行性能

| 配置 | FPS | 说明 |
|-----|-----|------|
| **Viewer 模式** | 37-38 | 可视化 + 键盘控制 |
| **Headless 模式** | 50+ | 最大吞吐量 |
| **多环境 (4 envs)** | ~150 | 并行环境 |

**硬件**: RTX 4090 24GB, CUDA backend

### 代码规模

| 指标 | 数量 |
|-----|------|
| Python 文件 | 23 |
| 代码行数 | ~2,000 |
| 测试脚本 | 11 |
| 文档文件 | 8 |

---

## 🎯 扩展指南

### 添加新策略

1. **创建策略文件**: `policies/my_policy.py`

```python
from genPiHub.policies import Policy, PolicyConfig

class MyPolicy(Policy):
    def __init__(self, cfg: PolicyConfig, device: str = "cpu"):
        super().__init__(cfg, device)
        # 加载模型
        
    def reset(self):
        self.last_action = np.zeros(self.num_actions)
        
    def get_observation(self, env_data, ctrl_data):
        # 构建观测
        obs = np.concatenate([
            env_data["dof_pos"],
            env_data["dof_vel"],
            # ...
        ])
        return obs, {}
        
    def get_action(self, obs):
        # 推理 + 后处理
        return super().get_action(obs)
        
    def post_step_callback(self, commands=None):
        # 更新内部状态
        pass
```

2. **注册策略**: 在 `policies/__init__.py`

```python
policy_registry.add("MyPolicy", ".my_policy")
```

3. **创建配置**: 在 `configs/policy_configs.py`

```python
@dataclass
class MyPolicyConfig(PolicyConfig):
    my_param: float = 1.0
```

4. **使用**:

```python
from genPiHub import load_policy

policy = load_policy("MyPolicy", policy_file="path/to/model.pt")
```

### 添加新环境

1. **创建环境文件**: `environments/my_env.py`

```python
from genPiHub.environments import Environment, EnvConfig

class MyEnv(Environment):
    def __init__(self, cfg: EnvConfig, device: str = "cpu"):
        super().__init__(cfg, device)
        # 初始化后端
        
    def reset(self):
        # 重置环境
        pass
        
    def update(self):
        # 更新状态
        self._dof_pos = ...
        self._dof_vel = ...
        self._base_quat = ...
        
    def step(self, pd_target):
        # 执行 PD 控制
        pass
        
    def set_gains(self, stiffness, damping):
        # 设置增益
        pass
```

2. **注册环境**: 在 `environments/__init__.py`

```python
environment_registry.add("MyEnv", ".my_env")
```

---

## 🔒 设计约束

### 不可修改

- ❌ **third_party/**: 只读包
- ❌ **.reference/**: 参考实现

### 可修改

- ✅ 根目录配置文件
- ✅ 文档
- ✅ 新增源代码

### 环境隔离

不同项目使用不同的 Python 环境：

| 项目 | 环境 | Python | 包管理器 |
|-----|------|--------|----------|
| genPiHub | `genesislab` | 3.10 | conda |
| AMO (参考) | `amo` | 3.8 | conda |
| CLOT (参考) | `clot` | 3.11 | conda |

---

## 📚 相关文档

- **快速开始**: [QUICKSTART.md](QUICKSTART.md)
- **完整指南**: [README.md](../README.md)
- **迁移指南**: [MIGRATION.md](MIGRATION.md)
- **测试指南**: [scripts/README.md](../scripts/README.md)
- **文档索引**: [DOCS_INDEX.md](DOCS_INDEX.md)

---

## 🔮 路线图

### Q2 2026
- [ ] CLOT Policy 实现
- [ ] MuJoCo Environment
- [ ] 性能优化

### Q3 2026
- [ ] Isaac Sim Environment
- [ ] 更多策略（ProtoMotions, ASAP）
- [ ] 多策略切换

### Q4 2026
- [ ] 真机集成（Unitree SDK）
- [ ] 基准测试套件
- [ ] 生产部署工具

---

**架构设计原则**: 简单、解耦、可扩展、易测试

**维护者**: hvla Team  
**最后更新**: 2026-04-08
