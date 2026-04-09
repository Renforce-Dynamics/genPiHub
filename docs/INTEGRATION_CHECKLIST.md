# RoboJuDo 集成检查清单

**快速参考**: 用于跟踪策略集成进度

**详细规划**: 见 [ROBOJUDO_INTEGRATION_PLAN.md](ROBOJUDO_INTEGRATION_PLAN.md)

---

## 📋 策略集成状态

### Phase 1: 核心策略 (P0)

| 策略 | 优先级 | 状态 | 工作量 | 负责人 | 备注 |
|------|--------|------|--------|--------|------|
| **AMOPolicy** | P0 | ✅ 完成 | - | - | 参考实现 |
| **CLOTPolicy** | P0 | ✅ 完成 | 2 天 | - | 运动跟踪 |

### Phase 2: 扩展策略 (P1)

| 策略 | 优先级 | 状态 | 工作量 | 负责人 | 备注 |
|------|--------|------|--------|--------|------|
| **AsapPolicy** | P1 | ⏳ 待开始 | 5-6 天 | - | 双模式 (Mimic+Loco) |
| **ProtoMotionsTrackerPolicy** | P1 | ⏳ 待开始 | 4-5 天 | - | Transformer |

### Phase 3: 高级策略 (P2)

| 策略 | 优先级 | 状态 | 工作量 | 负责人 | 备注 |
|------|--------|------|--------|--------|------|
| **BeyondMimicPolicy** | P2 | 🔄 进行中 | 3 天 | - | ONNX |
| **UnitreePolicy** | P2 | ⏳ 待开始 | 2 天 | - | 官方策略 |
| **TwistPolicy** | P2 | ⏳ 待开始 | 3 天 | - | 任务导向 |

### Phase 4: 可选策略 (P3)

| 策略 | 优先级 | 状态 | 工作量 | 负责人 | 备注 |
|------|--------|------|--------|--------|------|
| **H2HStudentPolicy** | P3 | ⏳ 待开始 | 4 天 | - | 需要 PHC |
| **KungfuBotGeneralPolicy** | P3 | ⏳ 待开始 | 4 天 | - | 需要 PBHC |

---

## 📁 文件结构检查清单

### CLOTPolicy 示例

```
□ genPiHub/envs/clot/
  □ __init__.py
  □ env_cfg.py              # CLOTGenesisEnvCfg
  □ robot_cfg.py            # G1/Adam Pro 配置
  □ observations.py         # AMP 观测
  □ actions.py              # PD 动作

□ genPiHub/policies/
  □ clot_policy.py          # CLOTPolicy 类

□ genPiHub/configs/
  □ policy_configs.py       # 添加 CLOTPolicyConfig
  □ clot_env_builder.py     # 工厂函数

□ scripts/clot/
  □ test_clot_policy.py
  □ play_clot.py
  □ README.md

□ docs/policies/
  □ CLOT.md                 # 策略文档

□ examples/
  □ clot_example.py
```

---

## ✅ 每个策略的验收清单

### 功能测试

- [ ] 模型加载成功
- [ ] 配置文件解析正确
- [ ] 环境创建成功
- [ ] 推理正常工作
- [ ] 动作输出合理
- [ ] 运行 1000 步稳定

### 性能测试

- [ ] Headless FPS >50
- [ ] Viewer FPS >30
- [ ] 内存占用 <2GB
- [ ] CPU 占用合理

### 代码质量

- [ ] 所有函数有类型提示
- [ ] 所有模块有 docstring
- [ ] 通过 Black 格式化
- [ ] 配置自包含在 `envs/{policy}/`
- [ ] 零外部依赖（除基础库）

### 文档完整

- [ ] 策略文档 `docs/policies/{POLICY}.md`
- [ ] 测试脚本 `scripts/{policy}/`
- [ ] README 说明
- [ ] 示例代码 `examples/`

---

## 🎯 实施步骤模板

### 步骤 1: 创建目录结构

```bash
cd genPiHub

# 创建环境配置目录
mkdir -p envs/{policy_name}
touch envs/{policy_name}/__init__.py
touch envs/{policy_name}/env_cfg.py
touch envs/{policy_name}/robot_cfg.py
touch envs/{policy_name}/observations.py
touch envs/{policy_name}/actions.py

# 创建测试脚本
mkdir -p scripts/{policy_name}
touch scripts/{policy_name}/test_{policy_name}_policy.py
touch scripts/{policy_name}/play_{policy_name}.py
touch scripts/{policy_name}/README.md

# 创建文档
touch docs/policies/{POLICY_NAME}.md

# 创建示例
touch examples/{policy_name}_example.py
```

### 步骤 2: 实现策略类

```python
# genPiHub/policies/{policy_name}_policy.py

from genPiHub.policies.base_policy import Policy
from genPiHub.configs.policy_configs import {PolicyName}Config

class {PolicyName}Policy(Policy):
    def __init__(self, cfg: {PolicyName}Config, device: str = "cpu"):
        super().__init__(cfg, device)
        # 加载模型
        self.model = self._load_model(cfg)
    
    def reset(self):
        super().reset()
        # 策略特定重置
    
    def get_observation(self, env_data, ctrl_data):
        # 构建观测
        obs = ...
        return obs, {}
    
    def post_step_callback(self, commands=None):
        # 更新状态
        pass
```

### 步骤 3: 配置环境

```python
# genPiHub/envs/{policy_name}/env_cfg.py

@configclass
class {PolicyName}GenesisEnvCfg(ManagerBasedRlEnvCfg):
    scene = G1SceneCfg(num_envs=4096)
    observations = {PolicyName}ObservationsCfg()
    actions = {PolicyName}ActionsCfg()
```

### 步骤 4: 创建工厂函数

```python
# genPiHub/configs/{policy_name}_env_builder.py

def create_{policy_name}_genesis_env_config(
    num_envs=1,
    viewer=False,
    device="cuda"
):
    # 创建配置
    from genPiHub.envs.{policy_name} import build_{policy_name}_env_config
    
    env_cfg = build_{policy_name}_env_config(num_envs, viewer, device)
    genesis_cfg = GenesisEnvConfig(...)
    
    return genesis_cfg, env_cfg
```

### 步骤 5: 注册策略

```python
# genPiHub/policies/__init__.py

policy_registry.add("{PolicyName}Policy", ".{policy_name}_policy")
```

### 步骤 6: 添加配置类

```python
# genPiHub/configs/policy_configs.py

@dataclass
class {PolicyName}PolicyConfig(PolicyConfig):
    model_file: Path
    # 策略特定配置
    ...
```

### 步骤 7: 编写测试

```python
# scripts/{policy_name}/test_{policy_name}_policy.py

def test_policy_loading():
    policy = load_policy("{PolicyName}Policy", ...)
    assert policy is not None

def test_inference():
    policy = load_policy("{PolicyName}Policy", ...)
    obs = np.random.randn(policy.num_obs)
    action = policy.get_action(obs)
    assert action.shape == (policy.num_actions,)
```

### 步骤 8: 编写文档

```markdown
# docs/policies/{POLICY_NAME}.md

# {PolicyName} Policy

## 介绍
...

## 使用方法
```python
from genPiHub import load_policy
policy = load_policy("{PolicyName}Policy", ...)
```

## 配置选项
...

## 示例
...
```

---

## 🔧 常用命令

### 运行测试

```bash
# 测试策略加载
python scripts/{policy}/test_{policy}_policy.py

# 运行交互演示
python scripts/{policy}/play_{policy}.py --viewer

# 运行性能测试
python scripts/{policy}/play_{policy}.py --headless --max-steps 1000
```

### 代码质量

```bash
# 格式化
black --line-length 100 genPiHub/

# 类型检查
mypy genPiHub/policies/{policy}_policy.py

# 文档检查
python -m pydocstyle genPiHub/policies/{policy}_policy.py
```

---

## 📊 进度跟踪

### 总体进度

- **已完成**: 2/9 (22%) ✅ AMO, CLOT
- **进行中**: 1/9 (11%) 🔄 BeyondMimic
- **待开始**: 6/9 (67%)

### 估计时间

- **Phase 1**: 4-6 天
- **Phase 2**: 9-11 天
- **Phase 3**: 8 天
- **Phase 4**: 8 天
- **总计**: 29-33 天 (~6-7 周)

---

## 📝 笔记和问题

### 已知问题

- [ ] 某些策略需要特定版本的依赖
- [ ] 运动库格式不统一
- [ ] ONNX vs JIT 模型加载差异

### 解决方案

- 使用可选依赖 + 条件导入
- 创建统一的运动库接口
- Policy 基类支持多种模型格式

---

**最后更新**: 2026-04-09  
**下次更新**: 开始 Phase 1 后
