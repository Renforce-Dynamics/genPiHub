# RoboJuDo 策略集成规划

**版本**: 1.0  
**创建日期**: 2026-04-09  
**状态**: 规划文档  
**目标**: 将 RoboJuDo 的所有策略包装到 genPiHub 框架

---

## 📋 目录

1. [项目概述](#1-项目概述)
2. [RoboJuDo 架构分析](#2-robojudo-架构分析)
3. [当前 AMO 实现参考](#3-当前-amo-实现参考)
4. [策略集成规划](#4-策略集成规划)
5. [环境构建规划](#5-环境构建规划)
6. [机器人配置规划](#6-机器人配置规划)
7. [实施优先级](#7-实施优先级)
8. [技术债务和挑战](#8-技术债务和挑战)
9. [验收标准](#9-验收标准)

---

## 1. 项目概述

### 1.1 目标

将 RoboJuDo 框架中的多个人形机器人策略集成到 genPiHub，提供统一的策略部署接口。

### 1.2 核心原则

- **自包含**: 每个策略的配置文件自包含在 `genPiHub/envs/{policy_name}/`
- **统一接口**: 所有策略继承 `genPiHub.policies.Policy` ABC
- **优先 GenesisLab**: 环境优先使用 genesislab 作为后端
- **零耦合**: 不依赖原始 RoboJuDo 代码，完全独立实现

### 1.3 设计参考

基于 RoboJuDo 的设计理念：
- **解耦架构**: Policy ↔ Environment ↔ Controller
- **模块化**: 易于添加新策略
- **配置驱动**: 通过配置文件管理所有参数

---

## 2. RoboJuDo 架构分析

### 2.1 RoboJuDo 核心组件

```
robojudo/
├── policy/                  # 策略实现
│   ├── base_policy.py      # 基类
│   ├── amo_policy.py       # AMO (✅ 已实现)
│   ├── asap_policy.py      # ASAP
│   ├── beyondmimic_policy.py
│   ├── h2h_student_policy.py
│   ├── kungfubot_policy.py
│   ├── protomotions_tracker_policy.py
│   ├── twist_policy.py
│   └── unitree_policy.py
│
├── environment/            # 环境适配器
│   ├── sim_env.py         # 仿真环境
│   └── real_env.py        # 真机环境
│
├── controller/            # 控制器
│   ├── joystick_ctrl.py
│   ├── keyboard_ctrl.py
│   └── motion_*_ctrl.py
│
├── pipeline/              # 运行管线
│   └── rl_pipeline.py
│
└── config/                # 配置系统
    ├── g1/               # G1 机器人
    ├── h1/               # H1 机器人
    └── gr1/              # Gr1 机器人
```

### 2.2 支持的策略列表

| 策略名称 | 状态 | 用途 | 依赖 |
|---------|------|------|------|
| **UnitreePolicy** | ⏳ | Unitree 官方策略 | unitree_rl_gym |
| **AMOPolicy** | ✅ | 全身控制 (RSS 2025) | 已集成 |
| **AsapPolicy** | ⏳ | 深度模仿学习 | ASAP |
| **BeyondMimicPolicy** | ⏳ | 全身跟踪 | whole_body_tracking |
| **H2HStudentPolicy** | ⏳ | 人到人形迁移 | human2humanoid + PHC |
| **KungfuBotGeneralPolicy** | ⏳ | 武术机器人 | PBHC + PHC |
| **TwistPolicy** | ⏳ | 任务驱动运动 | TWIST |
| **ProtoMotionsTrackerPolicy** | ⏳ | 物理运动跟踪 | ProtoMotions |

### 2.3 支持的机器人

| 机器人 | DOF | 状态 | 优先级 |
|-------|-----|------|--------|
| **Unitree G1** | 23/29 | ✅ AMO 已支持 | P0 |
| **Unitree H1** | 19/25 | ⏳ | P1 |
| **FFTAI Gr1** | 29 | ⏳ | P2 |

---

## 3. 当前 AMO 实现参考

### 3.1 AMO 实现结构

```
genPiHub/
├── policies/
│   ├── base_policy.py           # ✅ 基类接口
│   └── amo_policy.py            # ✅ AMO 实现
│
├── environments/
│   ├── base_env.py              # ✅ 环境基类
│   └── genesis_env.py           # ✅ Genesis 适配器
│
├── envs/amo/                     # ✅ AMO 自包含配置
│   ├── env_cfg.py               # 环境配置
│   ├── robot_cfg.py             # G1 配置
│   ├── observations.py          # 观测函数
│   └── actions.py               # 动作配置
│
└── configs/
    ├── policy_configs.py        # ✅ AMOPolicyConfig
    ├── env_configs.py           # ✅ GenesisEnvConfig
    └── amo_env_builder.py       # ✅ 工厂函数
```

### 3.2 AMO 关键设计模式

#### 模式 1: 自包含环境配置

```python
# envs/amo/env_cfg.py
@configclass
class AmoGenesisEnvCfg(ManagerBasedRlEnvCfg):
    """完全自包含，不依赖外部 AMO 代码"""
    scene = G1SceneCfg(num_envs=4096)
    observations = AmoObservationsCfg()
    actions = AmoActionsCfg()
```

**优点**:
- 零外部依赖
- 版本隔离
- 清晰的所有权

#### 模式 2: Policy Wrapper

```python
# policies/amo_policy.py
class AMOPolicy(Policy):
    def __init__(self, cfg: AMOPolicyConfig, device: str = "cpu"):
        super().__init__(cfg, device)
        # 加载 JIT 模型
        self.model = torch.jit.load(cfg.policy_file)
    
    def get_observation(self, env_data, ctrl_data):
        # AMO 直接使用环境状态
        return env_data, {}
    
    def get_action(self, obs):
        # 调用模型推理
        return super().get_action(obs)
```

**优点**:
- 统一接口
- 适配器模式
- 易于扩展

#### 模式 3: 工厂函数

```python
# configs/amo_env_builder.py
def create_amo_genesis_env_config(num_envs=1, viewer=False, device="cuda"):
    """快速创建 AMO 环境配置"""
    # 1. 导入自包含配置
    from genPiHub.envs.amo import build_amo_env_config
    
    # 2. 创建 genesislab 配置
    amo_env_cfg = build_amo_env_config(num_envs, viewer, device)
    
    # 3. 创建 genPiHub 配置
    genesis_cfg = GenesisEnvConfig(...)
    
    return genesis_cfg, amo_env_cfg
```

**优点**:
- 简化使用
- 封装复杂性
- 提供默认值

---

## 4. 策略集成规划

### 4.1 CLOT Policy (优先级 P0)

**来源**: `humanoid_benchmark` 项目

**特点**:
- 闭环运动跟踪
- 大规模 AMP 训练
- 支持 MjLab + Isaac Sim

**集成步骤**:

```
1. 创建目录结构
   genPiHub/envs/clot/
   ├── __init__.py
   ├── env_cfg.py              # CLOTGenesisEnvCfg
   ├── robot_cfg.py            # G1/Adam Pro 配置
   ├── observations.py         # Motion tracking 观测
   └── actions.py              # PD 动作配置

2. 实现策略包装
   genPiHub/policies/clot_policy.py
   
   class CLOTPolicy(Policy):
       def __init__(self, cfg: CLOTPolicyConfig, device: str):
           # 加载 CLOT 模型
           self.policy = load_clot_model(cfg.model_file)
           self.motion_lib = MotionLibrary(cfg.motion_dir)
       
       def get_observation(self, env_data, ctrl_data):
           # 构建 AMP 观测
           obs = build_amp_observation(env_data, self.motion_lib)
           return obs, {}

3. 配置类
   configs/policy_configs.py
   
   @dataclass
   class CLOTPolicyConfig(PolicyConfig):
       model_file: Path
       motion_dir: Path
       amp_observation_scale: float = 1.0

4. 环境构建器
   configs/clot_env_builder.py
   
   def create_clot_genesis_env_config(...):
       # 类似 AMO
```

**技术要点**:
- 运动库加载 (`.npy` 格式)
- AMP 观测构建
- 相位管理
- 地形生成

**预计工作量**: 3-4 天

---

### 4.2 ASAP Policy (优先级 P1)

**来源**: RoboJuDo + ASAP 项目

**特点**:
- 深度模仿学习
- Loco + Mimic 双模式
- 支持任务切换

**集成步骤**:

```
1. 目录结构
   genPiHub/envs/asap/
   ├── deepmimic/
   │   ├── env_cfg.py          # DeepMimic 配置
   │   ├── observations.py
   │   └── actions.py
   └── locomotion/
       ├── env_cfg.py          # Locomotion 配置
       ├── observations.py
       └── actions.py

2. 双策略实现
   genPiHub/policies/asap_policy.py
   
   class AsapMimicPolicy(Policy):
       """深度模仿策略"""
       def __init__(self, cfg: AsapMimicPolicyConfig, device: str):
           self.motion_lib = load_motion_lib(cfg.motion_dir)
           self.models = load_mimic_models(cfg.model_dir)
       
       def get_observation(self, env_data, ctrl_data):
           # 运动跟踪观测
           ...
   
   class AsapLocoPolicy(Policy):
       """运动策略"""
       def __init__(self, cfg: AsapLocoPolicyConfig, device: str):
           self.loco_model = load_loco_model(cfg.model_file)
       
       def get_observation(self, env_data, ctrl_data):
           # 速度跟踪观测
           ...

3. 策略切换支持
   tools/policy_switch.py
   
   class PolicySwitcher:
       def __init__(self, policies: List[Policy]):
           self.policies = policies
           self.current_idx = 0
       
       def switch(self, idx: int, interpolate: bool = True):
           # 带插值的策略切换
           ...
```

**技术要点**:
- 运动库格式转换
- 策略热切换
- 插值平滑
- 键盘/手柄映射

**预计工作量**: 5-6 天

---

### 4.3 ProtoMotions Tracker Policy (优先级 P1)

**来源**: RoboJuDo + NVIDIA ProtoMotions

**特点**:
- 基于物理的运动跟踪
- Transformer 架构
- 高质量运动生成

**集成步骤**:

```
1. 目录结构
   genPiHub/envs/protomotions/
   ├── env_cfg.py              # ProtoMotions 环境
   ├── robot_cfg.py            # G1 配置
   ├── observations.py         # Transformer 观测
   ├── actions.py
   └── motion_lib.py           # 运动库管理

2. 策略实现
   genPiHub/policies/protomotions_policy.py
   
   class ProtoMotionsTrackerPolicy(Policy):
       def __init__(self, cfg: ProtoMotionsPolicyConfig, device: str):
           self.tracker = load_protomotions_tracker(cfg.model_file)
           self.motion_lib = ProtoMotionsMotionLib(cfg.motion_dir)
       
       def get_observation(self, env_data, ctrl_data):
           # 构建 Transformer 观测序列
           obs_seq = build_observation_sequence(
               env_data, 
               self.history, 
               self.motion_lib
           )
           return obs_seq, {}

3. 历史管理
   - 观测历史缓冲 (deque)
   - 运动相位跟踪
   - 关键帧对齐
```

**技术要点**:
- Transformer 输入格式
- 观测历史管理
- 运动库接口
- 相位同步

**预计工作量**: 4-5 天

---

### 4.4 BeyondMimic Policy (优先级 P2)

**来源**: RoboJuDo + whole_body_tracking

**特点**:
- ONNX 模型部署
- 支持无状态估计器版本
- 内嵌运动数据

**集成步骤**:

```
1. 目录结构
   genPiHub/envs/beyondmimic/
   ├── env_cfg.py              # BeyondMimic 环境
   ├── env_cfg_wose.py         # 无状态估计器版本
   ├── robot_cfg.py
   ├── observations.py
   └── actions.py

2. ONNX 策略实现
   genPiHub/policies/beyondmimic_policy.py
   
   class BeyondMimicPolicy(Policy):
       def __init__(self, cfg: BeyondMimicPolicyConfig, device: str):
           import onnxruntime as ort
           self.session = ort.InferenceSession(cfg.model_file)
           self.use_state_estimator = cfg.use_state_estimator
       
       def get_observation(self, env_data, ctrl_data):
           if self.use_state_estimator:
               obs = build_obs_with_estimator(env_data)
           else:
               obs = build_obs_without_estimator(env_data)
           return obs, {}
       
       def get_action(self, obs):
           # ONNX 推理
           ort_inputs = {self.session.get_inputs()[0].name: obs}
           ort_outs = self.session.run(None, ort_inputs)
           return ort_outs[0]
```

**技术要点**:
- ONNX Runtime 集成
- 模型元数据解析
- 状态估计器可选
- NPZ 运动文件支持

**预计工作量**: 3 天

---

### 4.5 其他策略 (优先级 P3)

#### UnitreePolicy
- Unitree 官方策略
- 简单速度控制
- 工作量: 2 天

#### TwistPolicy
- 任务导向运动
- Redis/本地运动源
- 工作量: 3 天

#### H2HStudentPolicy
- 人到人形迁移
- 需要 PHC 依赖
- 工作量: 4 天

#### KungfuBotGeneralPolicy
- 武术机器人
- 需要 PHC + PBHC
- 工作量: 4 天

---

## 5. 环境构建规划

### 5.1 GenesisLab 环境优先

**原则**: 所有策略优先使用 genesislab 作为后端

```
genPiHub/environments/
├── base_env.py              # ✅ 已有
├── genesis_env.py           # ✅ 已有（通用）
├── mujoco_env.py            # TODO: MuJoCo 后端
└── isaac_env.py             # TODO: Isaac Sim 后端
```

### 5.2 环境配置模板

每个策略的环境配置遵循相同模板：

```python
# genPiHub/envs/{policy_name}/env_cfg.py

from genesislab.envs.manager_based_rl_env import ManagerBasedRlEnvCfg
from genesislab.utils.configclass import configclass

@configclass
class {PolicyName}GenesisEnvCfg(ManagerBasedRlEnvCfg):
    """
    {Policy} 在 Genesis 中的环境配置
    
    完全自包含，不依赖外部代码
    """
    # 场景配置
    scene = {Robot}SceneCfg(
        num_envs=4096,
        env_spacing=2.5,
        replicate_physics=True,
    )
    
    # 观测配置
    observations = {PolicyName}ObservationsCfg()
    
    # 动作配置
    actions = {PolicyName}ActionsCfg()
    
    # 其他配置
    ...
```

### 5.3 机器人场景配置

```python
# genPiHub/envs/{policy_name}/robot_cfg.py

def G1_CFG() -> ArticulationCfg:
    """Unitree G1 机器人配置"""
    return ArticulationCfg(
        spawn=sim_utils.UsdFileCfg(
            usd_path=f"{ISAACLAB_NUCLEUS_DIR}/Robots/Unitree/G1/g1.usd",
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.75),
            joint_pos={
                # G1 23/29 DOF 默认姿态
                ".*_hip_pitch": -0.1,
                ".*_knee": 0.3,
                ".*_ankle_pitch": -0.2,
                # ...
            },
        ),
        actuators={
            "legs": ImplicitActuatorCfg(
                joint_names_expr=[".*_hip_.*", ".*_knee", ".*_ankle_.*"],
                stiffness={...},
                damping={...},
            ),
            "torso": ImplicitActuatorCfg(...),
            "arms": ImplicitActuatorCfg(...),
        },
    )
```

### 5.4 观测和动作配置

```python
# genPiHub/envs/{policy_name}/observations.py

@configclass
class {PolicyName}ObservationsCfg(ObservationsCfg):
    @configclass
    class PolicyCfg(ObsGroup):
        # 策略特定观测
        base_ang_vel = ObsTerm(func=mdp.base_ang_vel)
        projected_gravity = ObsTerm(func=mdp.projected_gravity)
        velocity_commands = ObsTerm(func=mdp.generated_commands, params={"command_name": "base_velocity"})
        joint_pos = ObsTerm(func=mdp.joint_pos_rel)
        joint_vel = ObsTerm(func=mdp.joint_vel_rel)
        actions = ObsTerm(func=mdp.last_action)
        # 策略特定的额外观测...

    policy: PolicyCfg = PolicyCfg()


# genPiHub/envs/{policy_name}/actions.py

@configclass
class {PolicyName}ActionsCfg(ActionsCfg):
    joint_pos = mdp.JointPositionActionCfg(
        asset_name="robot",
        joint_names=[".*"],
        scale=0.25,  # 策略特定的 action scale
        use_default_offset=True,
    )
```

---

## 6. 机器人配置规划

### 6.1 支持的机器人

#### Unitree G1 (优先级 P0)

**DOF 配置**:
- **23 DOF**: 腿部 + 躯干 + 手臂 (无手指)
- **29 DOF**: 23 DOF + 手指 (6 DOF)

**关节名称**:
```python
G1_23DOF_NAMES = [
    # 左腿 (6)
    "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
    "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
    
    # 右腿 (6)
    "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
    "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
    
    # 躯干 (3)
    "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
    
    # 左臂 (4)
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint", 
    "left_shoulder_yaw_joint", "left_elbow_joint",
    
    # 右臂 (4)
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint", "right_elbow_joint",
]
```

**PD 参数** (AMO 示例):
```python
G1_PD_PARAMS = {
    "legs": {"stiffness": 200.0, "damping": 5.0},
    "torso": {"stiffness": 300.0, "damping": 10.0},
    "arms": {"stiffness": 40.0, "damping": 2.0},
}
```

#### Unitree H1 (优先级 P1)

**DOF 配置**:
- **19 DOF**: 基础版本
- **25 DOF**: 带手指

**特点**:
- 更高更重
- 不同的关节限制
- PD 参数需要重新调整

#### FFTAI Gr1 (优先级 P2)

**DOF 配置**:
- **29 DOF**

**特点**:
- 不同的 URDF
- 不同的默认姿态

### 6.2 机器人配置组织

```
genPiHub/robots/
├── __init__.py
├── g1/
│   ├── g1_23dof.py         # G1 23 DOF 配置
│   ├── g1_29dof.py         # G1 29 DOF 配置
│   └── g1_constants.py     # 常量定义
├── h1/
│   ├── h1_19dof.py
│   └── h1_25dof.py
└── gr1/
    └── gr1_29dof.py
```

---

## 7. 实施优先级

### Phase 1: 核心策略 (2-3 周)

**P0 任务**:

1. **CLOT Policy** (3-4 天)
   - [ ] 创建 `envs/clot/` 配置
   - [ ] 实现 `CLOTPolicy` 类
   - [ ] 运动库加载
   - [ ] AMP 观测构建
   - [ ] 测试脚本

2. **完善 AMO Policy** (1-2 天)
   - [ ] 添加更多命令模式
   - [ ] 优化性能
   - [ ] 补充文档

3. **基础设施** (2 天)
   - [ ] 统一机器人配置模块 `genPiHub/robots/`
   - [ ] 改进 DOF 映射工具
   - [ ] 环境构建器模板

### Phase 2: 扩展策略 (3-4 周)

**P1 任务**:

4. **ASAP Policy** (5-6 天)
   - [ ] Mimic + Loco 双策略
   - [ ] 策略切换机制
   - [ ] 运动库集成

5. **ProtoMotions Policy** (4-5 天)
   - [ ] Transformer 观测
   - [ ] 历史管理
   - [ ] 运动库接口

6. **H1 机器人支持** (3 天)
   - [ ] H1 配置文件
   - [ ] 测试 AMO/CLOT on H1

### Phase 3: 高级功能 (2-3 周)

**P2 任务**:

7. **BeyondMimic Policy** (3 天)
8. **UnitreePolicy** (2 天)
9. **TwistPolicy** (3 天)

**P3 任务**:

10. **H2HStudentPolicy** (4 天)
11. **KungfuBotGeneralPolicy** (4 天)

### Phase 4: 优化和文档 (1-2 周)

12. **性能优化**
    - [ ] 批处理推理
    - [ ] JIT 编译观测函数
    - [ ] 多环境并行

13. **完善文档**
    - [ ] 每个策略的详细文档
    - [ ] 使用示例
    - [ ] 最佳实践

---

## 8. 技术债务和挑战

### 8.1 依赖管理

**挑战**: 不同策略依赖不同的库

**解决方案**:
```python
# 可选依赖模式
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

class BeyondMimicPolicy(Policy):
    def __init__(self, ...):
        if not ONNX_AVAILABLE:
            raise ImportError(
                "BeyondMimic requires onnxruntime. "
                "Install: pip install onnxruntime-gpu"
            )
```

### 8.2 运动库格式

**挑战**: 不同项目使用不同格式
- CLOT: `.npy` (AMP format)
- ASAP: custom format
- ProtoMotions: custom format

**解决方案**:
```python
# 统一运动库接口
class MotionLibrary(ABC):
    @abstractmethod
    def load(self, path: Path):
        """加载运动数据"""
    
    @abstractmethod
    def sample(self, motion_id: int, frame: int):
        """采样运动帧"""

class AMPMotionLibrary(MotionLibrary):
    """CLOT AMP 格式"""
    ...

class AsapMotionLibrary(MotionLibrary):
    """ASAP 格式"""
    ...
```

### 8.3 模型格式

**挑战**: JIT vs ONNX vs 原生 PyTorch

**解决方案**:
```python
# 策略配置中指定格式
@dataclass
class PolicyConfig:
    model_format: str = "jit"  # "jit" | "onnx" | "pytorch"
    
# Policy 基类支持多种加载方式
class Policy(ABC):
    def _load_model(self, cfg: PolicyConfig):
        if cfg.model_format == "jit":
            return torch.jit.load(cfg.model_file)
        elif cfg.model_format == "onnx":
            import onnxruntime
            return onnxruntime.InferenceSession(cfg.model_file)
        elif cfg.model_format == "pytorch":
            model = create_model(cfg)
            model.load_state_dict(torch.load(cfg.model_file))
            return model
```

### 8.4 环境差异

**挑战**: GenesisLab vs MjLab vs Isaac Sim API 差异

**解决方案**:
- 优先 GenesisLab
- 通过 `Environment` ABC 抽象差异
- 后续按需添加其他后端

---

## 9. 验收标准

### 9.1 功能性标准

每个集成的策略必须满足：

- [ ] **加载测试**: 能成功加载模型和配置
- [ ] **推理测试**: 能正常推理并输出动作
- [ ] **环境测试**: 能在 Genesis 环境中运行
- [ ] **性能测试**: 达到预期 FPS (headless >50, viewer >30)
- [ ] **稳定性测试**: 运行 1000 步不崩溃

### 9.2 代码质量标准

- [ ] **类型提示**: 所有公共 API 有类型提示
- [ ] **文档字符串**: 所有模块、类、函数有 docstring
- [ ] **代码风格**: 通过 Black 格式化 (line-length=100)
- [ ] **自包含**: 配置文件在 `envs/{policy}/` 目录
- [ ] **零耦合**: 不依赖原始项目代码

### 9.3 文档标准

每个策略需要：

- [ ] **策略文档**: `docs/policies/{POLICY_NAME}.md`
  - 策略介绍
  - 使用方法
  - 配置选项
  - 示例代码
  
- [ ] **测试脚本**: `scripts/{policy}/`
  - `test_{policy}_policy.py`
  - `play_{policy}.py`
  - `README.md`

- [ ] **示例代码**: `examples/{policy}_example.py`

### 9.4 性能标准

| 模式 | 目标 FPS | 环境数 | 备注 |
|------|---------|--------|------|
| Headless | >50 | 1 | RTX 4090 |
| Viewer | >30 | 1 | RTX 4090 |
| Multi-env | >150 | 4 | RTX 4090 |

---

## 10. 实施建议

### 10.1 开发流程

1. **规划阶段** (本文档)
   - 分析 RoboJuDo 架构
   - 确定优先级
   - 制定实施计划

2. **原型阶段**
   - 选择一个策略 (建议 CLOT)
   - 完整实现端到端流程
   - 验证设计模式

3. **批量实施**
   - 按优先级依次实现
   - 复用成功模式
   - 持续优化

4. **测试和文档**
   - 每个策略独立测试
   - 编写详细文档
   - 创建示例代码

### 10.2 质量保证

- **代码审查**: 每个策略由另一个开发者审查
- **集成测试**: 定期运行全部测试
- **性能基准**: 记录每个策略的性能数据
- **文档更新**: 及时更新文档

### 10.3 风险管理

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 依赖冲突 | 高 | 使用可选依赖 + 虚拟环境隔离 |
| 模型格式不兼容 | 中 | 支持多种格式加载器 |
| 性能不达标 | 中 | 性能分析 + 优化关键路径 |
| 原始代码不开源 | 高 | 参考公开信息 + 自行实现 |

---

## 11. 参考资源

### 11.1 代码仓库

- **RoboJuDo**: `/home/ununtu/code/hvla/.reference/RoboJuDo`
- **AMO**: `/home/ununtu/code/hvla/.reference/AMO`
- **humanoid_benchmark (CLOT)**: `/home/ununtu/code/hvla/.reference/humanoid_benchmark`
- **Psi0**: `/home/ununtu/code/hvla/.reference/Psi0`

### 11.2 文档

- **RoboJuDo Policy Docs**: `.reference/RoboJuDo/docs/policy.md`
- **genPiHub Architecture**: `docs/ARCHITECTURE.md`
- **genPiHub Code Guide**: `docs/CODE_GUIDE.md`

### 11.3 论文

- **AMO**: RSS 2025
- **CLOT**: arXiv:2602.15060
- **ProtoMotions**: NVIDIA Research
- **ASAP**: LeCAR-Lab

---

## 12. 附录

### 附录 A: RoboJuDo Policy 接口对比

**RoboJuDo Policy 接口**:
```python
class Policy(ABC):
    @abstractmethod
    def reset(self):
        pass
    
    @abstractmethod
    def _get_observation(self, env_data: dict, ctrl_data: dict) -> np.ndarray:
        pass
    
    @abstractmethod
    def _compute_action(self, obs: np.ndarray) -> np.ndarray:
        pass
    
    @abstractmethod
    def _get_commands(self, ctrl_data: dict) -> list:
        pass
```

**genPiHub Policy 接口** (已标准化):
```python
class Policy(ABC):
    @abstractmethod
    def reset(self):
        pass
    
    @abstractmethod
    def get_observation(self, env_data: Dict, ctrl_data: Dict) -> Tuple[np.ndarray, Dict]:
        pass
    
    def get_action(self, obs: np.ndarray) -> np.ndarray:
        # 默认实现: model + EMA + clip + scale
        pass
    
    @abstractmethod
    def post_step_callback(self, commands: List[str] | None = None):
        pass
```

**主要差异**:
1. genPiHub 使用 `get_observation/get_action` (更清晰)
2. genPiHub 返回 `(obs, extras)` 元组 (支持调试)
3. genPiHub 提供默认 `get_action` 实现 (减少重复代码)
4. genPiHub 添加 `post_step_callback` (状态更新)

### 附录 B: 环境状态字典标准

**genPiHub 标准格式**:
```python
env_data = {
    # 必需字段 (所有环境必须提供)
    "dof_pos": np.ndarray,        # (num_dofs,) 关节位置
    "dof_vel": np.ndarray,        # (num_dofs,) 关节速度
    "base_quat": np.ndarray,      # (4,) 四元数 [x,y,z,w]
    "base_ang_vel": np.ndarray,   # (3,) 角速度
    
    # 可选字段
    "base_pos": np.ndarray,       # (3,) 位置
    "base_lin_vel": np.ndarray,   # (3,) 线速度
    "base_lin_acc": np.ndarray,   # (3,) 线加速度
    
    # 策略特定字段
    "commands": np.ndarray,       # 用户命令
    ...
}
```

---

**文档版本**: 1.0  
**作者**: genPiHub Team  
**日期**: 2026-04-09  
**状态**: 规划完成，等待实施

**下一步**: 与 Agent 对接，开始 Phase 1 实施。
