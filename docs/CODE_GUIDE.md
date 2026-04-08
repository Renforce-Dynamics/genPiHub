# genPiHub 代码导读

**版本**: 0.1.0  
**更新日期**: 2026-04-08

这份文档帮助你快速理解 genPiHub 代码库的关键实现细节。

---

## 📂 代码组织

```
genPiHub/
├── __init__.py                 # 🔑 入口点：load_policy(), load_environment()
├── policies/                   # 策略实现
│   ├── __init__.py            # 策略注册表
│   ├── base_policy.py         # 🔑 Policy ABC - 所有策略的基类
│   └── amo_policy.py          # AMO 策略包装器
├── environments/               # 环境实现
│   ├── __init__.py            # 环境注册表
│   ├── base_env.py            # 🔑 Environment ABC - 所有环境的基类
│   └── genesis_env.py         # Genesis 环境封装
├── configs/                    # 配置系统
│   ├── __init__.py            # 配置导出
│   ├── policy_configs.py      # 策略配置类
│   ├── env_configs.py         # 环境配置类
│   └── amo_env_builder.py     # 🔑 AMO 环境工厂函数
├── envs/amo/                   # 🔑 AMO 环境配置（自包含）
│   ├── __init__.py
│   ├── env_cfg.py             # AmoGenesisEnvCfg
│   ├── robot_cfg.py           # G1 机器人配置
│   ├── observations.py        # 观测函数
│   └── actions.py             # 动作配置
├── tools/                      # 工具模块
│   ├── __init__.py
│   ├── dof_config.py          # 🔑 DOF 管理
│   └── command_utils.py       # 键盘控制
├── utils/                      # 框架工具
│   ├── __init__.py
│   └── registry.py            # 🔑 注册系统
└── examples/
    └── amo_example.py          # 使用示例
```

🔑 = 核心文件，建议优先阅读

---

## 🎯 核心文件详解

### 1. `genPiHub/__init__.py` - 入口点

**职责**: 提供用户 API

```python
# 两个核心加载函数
def load_policy(name: str, **kwargs) -> Policy:
    """动态加载策略
    
    流程:
    1. 从 policy_registry 获取策略类
    2. 从 kwargs 构建配置对象
    3. 实例化策略
    """
    policy_class = policy_registry.get(name)
    config_class = getattr(configs, name.replace("Policy", "PolicyConfig"))
    config = config_class(**kwargs)
    return policy_class(config, device=kwargs.get("device", "cpu"))

def load_environment(name: str, **kwargs) -> Environment:
    """动态加载环境（同理）"""
```

**关键点**:
- 自动配置推断：`AMOPolicy` → `AMOPolicyConfig`
- 统一参数传递：通过 `**kwargs`
- 注册表查找：延迟加载

---

### 2. `policies/base_policy.py` - Policy 基类

**职责**: 定义策略接口

#### 核心方法

```python
class Policy(ABC):
    def __init__(self, cfg: PolicyConfig, device: str = "cpu"):
        """初始化
        
        关键属性:
        - self.model: JIT 模型（自动加载）
        - self.last_action: 用于 EMA 平滑
        - self.history_buf: 观测历史缓冲
        - self.cfg_obs_dof: 观测 DOF 配置
        - self.cfg_action_dof: 动作 DOF 配置
        """
        
    @abstractmethod
    def get_observation(self, env_data, ctrl_data) -> Tuple[obs, extras]:
        """构建策略观测
        
        Args:
            env_data: {
                "dof_pos": np.ndarray,     # 关节位置
                "dof_vel": np.ndarray,     # 关节速度
                "base_quat": np.ndarray,   # 基座四元数 [x,y,z,w]
                "base_ang_vel": np.ndarray,# 基座角速度
                ...
            }
            ctrl_data: {
                "commands": np.ndarray,    # 用户命令 [vx, vy, yaw, ...]
                ...
            }
            
        Returns:
            obs: np.ndarray - 模型输入
            extras: dict - 调试信息
        """
        
    def get_action(self, obs: np.ndarray) -> np.ndarray:
        """模型推理 + 动作后处理
        
        处理链:
        1. obs → model → raw_action
        2. EMA 平滑: action = (1-β) * last_action + β * raw_action
        3. Clipping: clip(-max, +max)
        4. Scaling: action * scale
        """
```

#### 动作平滑 (EMA)

```python
# action_beta = 0.1 表示 90% 保留上一步，10% 新动作
if self.action_beta < 1.0:
    actions = (1 - self.action_beta) * self.last_action + \
              self.action_beta * actions
self.last_action = actions.copy()
```

**为什么需要平滑?**
- 减少抖动
- 平滑过渡
- 提高稳定性

---

### 3. `environments/base_env.py` - Environment 基类

**职责**: 定义环境接口

#### 核心设计

```python
class Environment(ABC):
    def __init__(self, cfg: EnvConfig, device: str = "cpu"):
        """初始化
        
        关键属性:
        - self.dof_cfg: DOF 配置
        - self._dof_pos, self._dof_vel: 内部状态（只读）
        - self._base_quat, self._base_ang_vel: 基座状态
        """
        
    def get_data(self) -> Dict:
        """获取环境状态
        
        返回标准化字典:
        {
            "dof_pos": np.ndarray,      # 关节位置
            "dof_vel": np.ndarray,      # 关节速度
            "base_quat": np.ndarray,    # 四元数 [x,y,z,w]
            "base_ang_vel": np.ndarray, # 角速度
            "base_pos": np.ndarray,     # 位置（可选）
            "base_lin_vel": np.ndarray, # 线速度（可选）
        }
        """
        
    @abstractmethod
    def step(self, pd_target: np.ndarray):
        """PD 控制步进
        
        Args:
            pd_target: 目标关节位置（弧度）
        """
```

**关键设计**:
- 只读属性：通过 `@property` 防止外部修改
- 统一接口：所有环境返回相同格式的状态字典
- DOF 映射：内部处理关节顺序转换

---

### 4. `utils/registry.py` - 注册系统

**职责**: 动态类加载

#### 工作原理

```python
class Registry(Generic[T]):
    def __init__(self, package: str, base_class: Type[T]):
        """
        package: 包名，用于相对导入
        base_class: 基类，用于类型检查
        """
        self._registry: dict[str, str] = {}      # name → module_path
        self._loaded: dict[str, Type[T]] = {}    # name → class（缓存）
        
    def add(self, name: str, module_path: str):
        """注册（懒加载）
        
        例: policy_registry.add("AMOPolicy", ".amo_policy")
        存储: {"AMOPolicy": ".amo_policy"}
        """
        self._registry[name] = module_path
        
    def get(self, name: str) -> Type[T]:
        """获取类（首次访问时加载）
        
        流程:
        1. 检查缓存 _loaded
        2. 从 _registry 获取 module_path
        3. importlib.import_module(package + module_path)
        4. getattr(module, name)
        5. 类型检查: issubclass(cls, base_class)
        6. 缓存并返回
        """
```

**优势**:
- 懒加载：只加载使用的模块
- 缓存：避免重复导入
- 类型安全：强制继承检查

#### 使用示例

```python
# 定义注册表
policy_registry = Registry(
    package="genPiHub.policies",
    base_class=Policy
)

# 注册策略
policy_registry.add("AMOPolicy", ".amo_policy")

# 使用（首次加载）
AMOPolicy = policy_registry.get("AMOPolicy")  # 触发 import
policy = AMOPolicy(config, device="cuda")

# 再次使用（缓存）
AMOPolicy = policy_registry.get("AMOPolicy")  # 直接返回缓存
```

---

### 5. `tools/dof_config.py` - DOF 管理

**职责**: 关节配置和映射

#### DOFConfig 数据类

```python
@dataclass
class DOFConfig:
    # 基础信息
    joint_names: List[str]      # 关节名称（顺序重要！）
    num_dofs: int               # 自由度数量
    
    # 默认状态
    default_pos: np.ndarray     # 默认关节位置
    
    # 物理限制
    position_limits: np.ndarray # [[min, max], ...] 形状 (N, 2)
    velocity_limits: np.ndarray # [max_vel, ...]
    torque_limits: np.ndarray   # [max_torque, ...]
    
    # PD 控制参数
    stiffness: np.ndarray       # Kp 增益
    damping: np.ndarray         # Kd 增益
```

#### 关节映射示例

**问题**: Policy 和 Robot 的关节顺序可能不同

```python
# Policy DOF
policy_joints = [
    "left_hip_pitch",
    "left_hip_roll",
    "right_hip_pitch",
    "right_hip_roll",
]

# Robot joints (Genesis 顺序)
robot_joints = [
    "right_hip_pitch",  # 0
    "right_hip_roll",   # 1
    "left_hip_pitch",   # 2
    "left_hip_roll",    # 3
]

# 构建映射
policy_to_robot_idx = []
for policy_joint in policy_joints:
    idx = robot_joints.index(policy_joint)
    policy_to_robot_idx.append(idx)
    
# 结果: [2, 3, 0, 1]

# 使用
pd_target_robot = np.zeros(4)
pd_target_robot[policy_to_robot_idx] = pd_target_policy
```

**在 GenesisEnv 中的实现**: 见 `_build_joint_mapping()`

---

### 6. `configs/amo_env_builder.py` - AMO 环境工厂

**职责**: 快速创建 AMO 环境配置

#### 核心函数

```python
def create_amo_genesis_env_config(
    num_envs: int = 1,
    viewer: bool = False,
    device: str = "cuda",
) -> Tuple[GenesisEnvConfig, Any]:
    """创建 AMO + Genesis 环境配置
    
    Returns:
        (GenesisEnvConfig, AmoGenesisEnvCfg)
        - GenesisEnvConfig: genPiHub 环境配置
        - AmoGenesisEnvCfg: genesislab 内部配置
    """
    # 1. 导入 AMO 环境配置
    from genPiHub.envs.amo import build_amo_env_config
    
    # 2. 创建 genesislab 配置
    amo_env_cfg = build_amo_env_config(
        num_envs=num_envs,
        viewer=viewer,
        device=device,
    )
    
    # 3. 提取 DOF 信息
    dof_cfg = DOFConfig(
        joint_names=AMO_DOF_NAMES,
        num_dofs=23,
        default_pos=AMO_DEFAULT_POS,
        stiffness=AMO_STIFFNESS,
        damping=AMO_DAMPING,
    )
    
    # 4. 创建 genPiHub 配置
    genesis_cfg = GenesisEnvConfig(
        robot="G1",
        backend=device,
        num_envs=num_envs,
        viewer=viewer,
        dof=dof_cfg,
    )
    
    return genesis_cfg, amo_env_cfg
```

**为什么返回两个配置?**
- `GenesisEnvConfig`: genPiHub 标准接口
- `AmoGenesisEnvCfg`: genesislab 内部使用

---

### 7. `envs/amo/` - AMO 环境配置

**职责**: AMO 特定的环境设置（自包含）

#### 文件职责

```python
# env_cfg.py - 主环境配置
@configclass
class AmoGenesisEnvCfg(ManagerBasedRlEnvCfg):
    scene = G1SceneCfg(num_envs=4096, env_spacing=2.5)
    observations = AmoObservationsCfg()
    actions = AmoActionsCfg()
    # ... 其他配置

# robot_cfg.py - G1 机器人配置
def G1_CFG() -> ArticulationCfg:
    return ArticulationCfg(
        spawn=sim_utils.UsdFileCfg(
            usd_path="Robots/Unitree/G1/g1.usd"
        ),
        actuators={
            "legs": ImplicitActuatorCfg(
                joint_names_expr=[".*_hip_.*", ".*_knee", ".*_ankle_.*"],
                stiffness=STIFFNESS_LEG,
                damping=DAMPING_LEG,
            ),
            # ... 其他执行器
        },
    )

# observations.py - 观测函数
@configclass
class AmoObservationsCfg(ObservationsCfg):
    """AMO 观测配置"""
    @configclass
    class PolicyCfg(ObsGroup):
        # 观测项定义
        base_ang_vel = ObsTerm(func=mdp.base_ang_vel)
        projected_gravity = ObsTerm(func=mdp.projected_gravity)
        # ...

# actions.py - 动作配置
@configclass
class AmoActionsCfg(ActionsCfg):
    joint_pos = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=[".*"],
        scale=0.25,
    )
```

**设计原则**:
- **自包含**: 不依赖外部 AMO 代码库
- **模块化**: 每个配置文件职责单一
- **可复用**: 可作为其他策略的模板

---

## 🔄 关键流程源码追踪

### 流程 1: 加载 AMO 策略

```python
# 用户代码
from genPiHub import load_policy

policy = load_policy("AMOPolicy", model_dir=".reference/AMO", device="cuda")

# ↓ genPiHub/__init__.py::load_policy()
def load_policy(name: str, **kwargs):
    # 1. 获取策略类
    policy_class = policy_registry.get("AMOPolicy")
    # ↓ utils/registry.py::get()
    #   → importlib.import_module("genPiHub.policies.amo_policy")
    #   → getattr(module, "AMOPolicy")
    #   → 返回 AMOPolicy 类
    
    # 2. 构建配置
    config_class = getattr(configs, "AMOPolicyConfig")
    config = AMOPolicyConfig(model_dir=".reference/AMO", device="cuda")
    
    # 3. 实例化
    return AMOPolicy(config, device="cuda")
    # ↓ policies/amo_policy.py::__init__()
    #   → super().__init__()  # 调用 Policy.__init__()
    #   → 加载 JIT 模型: torch.jit.load("amo_jit.pt")
    #   → 初始化 AMO 内部实现
```

### 流程 2: 环境步进

```python
# 用户代码
env.reset()
policy.reset()

for step in range(1000):
    env.update()                              # 更新状态
    env_data = env.get_data()                 # 获取状态字典
    obs, _ = policy.get_observation(env_data, {})  # 构建观测
    action = policy.get_action(obs)           # 推理动作
    pd_target = default_pos + action * scale  # 计算 PD 目标
    env.step(pd_target)                       # 执行步进

# ↓ environments/genesis_env.py::update()
def update(self):
    # 从 Genesis 读取状态
    joint_pos = self.robot.data.joint_pos[0].cpu().numpy()
    joint_vel = self.robot.data.joint_vel[0].cpu().numpy()
    
    # 应用关节映射
    self._dof_pos = joint_pos[self.policy_to_robot_idx]
    self._dof_vel = joint_vel[self.policy_to_robot_idx]
    
    # 更新基座状态
    self._base_quat = self.robot.data.root_quat_w[0].cpu().numpy()
    self._base_ang_vel = self.robot.data.root_ang_vel_w[0].cpu().numpy()

# ↓ policies/base_policy.py::get_action()
def get_action(self, obs):
    # 模型推理
    obs_tensor = torch.from_numpy(obs).to(self.device)
    with torch.no_grad():
        actions = self.model(obs_tensor).cpu().numpy()
    
    # EMA 平滑
    if self.action_beta < 1.0:
        actions = (1 - self.action_beta) * self.last_action + \
                  self.action_beta * actions
    self.last_action = actions.copy()
    
    # Clipping + Scaling
    if self.action_clip:
        actions = np.clip(actions, -self.action_clip, self.action_clip)
    actions *= self.action_scale
    
    return actions

# ↓ environments/genesis_env.py::step()
def step(self, pd_target):
    # 应用反向映射（Policy DOF → Robot Joint）
    robot_target = np.zeros_like(self.robot.data.joint_pos[0])
    robot_target[self.policy_to_robot_idx] = pd_target
    
    # 设置 PD 目标
    self.robot.set_joint_position_target(
        torch.from_numpy(robot_target).to(self.device)
    )
    
    # 步进物理引擎
    self.env.step()
```

---

## 🧩 设计模式

### 1. 抽象基类模式 (ABC Pattern)

**目的**: 强制子类实现接口

```python
from abc import ABC, abstractmethod

class Policy(ABC):
    @abstractmethod
    def get_observation(self, env_data, ctrl_data):
        """子类必须实现"""
        raise NotImplementedError
```

**好处**:
- 编译时检查（mypy/pyright）
- 统一接口
- 文档清晰

### 2. 注册表模式 (Registry Pattern)

**目的**: 动态类发现和加载

```python
# 注册
policy_registry.add("AMOPolicy", ".amo_policy")

# 使用
PolicyClass = policy_registry.get("AMOPolicy")
```

**好处**:
- 插件化架构
- 懒加载
- 解耦

### 3. 工厂模式 (Factory Pattern)

**目的**: 简化对象创建

```python
def create_amo_policy(**kwargs) -> AMOPolicy:
    """工厂函数"""
    config = AMOPolicyConfig(**kwargs)
    return AMOPolicy(config)
```

**好处**:
- 隐藏复杂性
- 默认参数
- 可测试性

### 4. 适配器模式 (Adapter Pattern)

**目的**: 适配不同接口

```python
class AMOPolicy(Policy):
    """将 AMO 原始实现适配到 Policy 接口"""
    def get_action(self, obs):
        # 调用原始 AMO
        return self.amo_policy.act(...)
```

**好处**:
- 复用现有代码
- 统一接口
- 隔离变化

---

## 🐛 调试技巧

### 1. 打印关节映射

```python
env = GenesisEnv(...)
print("Policy joints:", env.joint_names)
print("Robot joints:", env.robot_joint_names)
print("Mapping:", env.policy_to_robot_idx)
```

### 2. 检查观测维度

```python
obs, extras = policy.get_observation(env_data, {})
print(f"Observation shape: {obs.shape}")
print(f"Expected: {policy.num_dofs * 2 + ...}")
```

### 3. 可视化动作

```python
action = policy.get_action(obs)
pd_target = default_pos + action * scale
print(f"Action range: [{action.min():.3f}, {action.max():.3f}]")
print(f"PD target range: [{pd_target.min():.3f}, {pd_target.max():.3f}]")
```

### 4. 使用调试脚本

```bash
python scripts/amo/debug_amo.py
```

---

## 📖 推荐阅读顺序

### 初级（理解接口）
1. `genPiHub/__init__.py` - 入口 API
2. `policies/base_policy.py` - Policy 接口
3. `environments/base_env.py` - Environment 接口
4. `tools/dof_config.py` - DOF 配置

### 中级（理解实现）
5. `utils/registry.py` - 注册系统
6. `policies/amo_policy.py` - AMO 策略
7. `environments/genesis_env.py` - Genesis 环境
8. `configs/amo_env_builder.py` - 工厂函数

### 高级（理解配置）
9. `envs/amo/env_cfg.py` - AMO 环境配置
10. `envs/amo/robot_cfg.py` - G1 机器人配置
11. `scripts/amo/play_amo.py` - 完整示例

---

## 🔗 相关文档

- **架构设计**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **快速开始**: [QUICKSTART.md](QUICKSTART.md)
- **API 文档**: [QUICK_START.md](QUICK_START.md)

---

**提示**: 建议结合源码注释阅读，所有核心文件都有详细的 docstring。

**维护者**: hvla Team  
**最后更新**: 2026-04-08
