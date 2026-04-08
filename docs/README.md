# genPiHub 文档中心

**版本**: 0.1.0  
**更新日期**: 2026-04-08

欢迎来到 genPiHub 文档中心！这里是所有文档的入口。

---

## 🎯 快速开始

**第一次使用？**

1. 阅读 [QUICKSTART.md](QUICKSTART.md) - 5 分钟快速上手
2. 运行 `bash ../INSTALL.sh` - 安装
3. 阅读 [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md) - 理解仓库结构

---

## 📚 完整文档列表

### 🚀 入门文档

| 文档 | 用途 | 阅读时间 |
|-----|------|---------|
| **[QUICKSTART.md](QUICKSTART.md)** | 5 分钟快速开始指南 | 5 min |
| **[INSTALL_GUIDE.md](INSTALL_GUIDE.md)** | 详细安装步骤 | 10 min |
| **[../README.md](../README.md)** | 主 README，完整使用手册 | 30 min |

### 🗺️ 理解项目

| 文档 | 用途 | 阅读时间 |
|-----|------|---------|
| **[REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md)** | 仓库导览和导航指南 | 20 min |
| **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** | 项目概览和现状 | 15 min |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | 系统架构设计 | 45 min |

### 💻 开发文档

| 文档 | 用途 | 阅读时间 |
|-----|------|---------|
| **[CODE_GUIDE.md](CODE_GUIDE.md)** | 代码导读和实现细节 | 60 min |
| **[TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)** | 技术规格和设计决策 | 60 min |
| **[QUICK_START.md](QUICK_START.md)** | API 参考文档 | 15 min |
| **[../scripts/README.md](../scripts/README.md)** | 测试脚本指南 | 20 min |

### 🔄 迁移和维护

| 文档 | 用途 | 阅读时间 |
|-----|------|---------|
| **[MIGRATION.md](MIGRATION.md)** | 从 policy_hub 迁移指南 | 15 min |
| **[COMPLETION_REPORT.md](COMPLETION_REPORT.md)** | 项目完成报告 | 10 min |
| **[SUMMARY.md](SUMMARY.md)** | 项目总结 | 10 min |

---

## 🎓 推荐学习路径

### 路径 1: 快速使用（1 小时）

```
1. QUICKSTART.md          (5 min)  → 快速开始
2. 运行安装和测试         (15 min) → 验证环境
3. README.md 使用部分     (20 min) → 学习 API
4. 运行示例代码          (20 min) → 实际使用
```

### 路径 2: 深入理解（半天）

```
1. QUICKSTART.md          (5 min)  → 快速回顾
2. REPOSITORY_GUIDE.md    (20 min) → 理解结构
3. PROJECT_OVERVIEW.md    (15 min) → 项目概览
4. ARCHITECTURE.md        (45 min) → 架构设计
5. CODE_GUIDE.md          (60 min) → 代码实现
6. 阅读源码             (120 min) → 深入细节
```

### 路径 3: 扩展开发（1 天）

```
1. 完成路径 2           (4 hours)
2. TECHNICAL_SPEC.md    (60 min)  → 技术规格
3. 参考实现            (120 min) → AMO/Genesis 源码
4. 编写新组件          (180 min) → 实践开发
5. 编写测试             (60 min)  → 验证实现
```

---

## 📖 文档关系图

```
                    DOCS_INDEX.md
                   (文档导航中心)
                         |
        +----------------+------------------+
        |                |                  |
    快速路径          学习路径            开发路径
        |                |                  |
   QUICKSTART.md    README.md      TECHNICAL_SPEC.md
        |                |                  |
        |          PROJECT_OVERVIEW         |
        |          ARCHITECTURE         CODE_GUIDE
        |          REPOSITORY_GUIDE         |
        |                |              scripts/
        |                |              README.md
        +----------------+------------------+
                         |
                  MIGRATION.md
                  COMPLETION_REPORT.md
```

---

## 🔍 按主题查找

### 我想了解...

#### ⚙️ 安装和配置
- [QUICKSTART.md](QUICKSTART.md) - 快速安装
- [INSTALL_GUIDE.md](INSTALL_GUIDE.md) - 详细步骤
- [../INSTALL.sh](../INSTALL.sh) - 安装脚本

#### 🎯 使用方法
- [../README.md](../README.md) - 主文档
- [QUICK_START.md](QUICK_START.md) - API 参考
- [../genPiHub/examples/](../genPiHub/examples/) - 示例代码

#### 🏗️ 架构设计
- [ARCHITECTURE.md](ARCHITECTURE.md) - 完整架构
- [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md) - 仓库结构
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - 项目概览

#### 💡 实现细节
- [CODE_GUIDE.md](CODE_GUIDE.md) - 代码导读
- [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md) - 技术规格
- 源码文件（都有详细注释）

#### 🧪 测试
- [../scripts/README.md](../scripts/README.md) - 测试指南
- [../scripts/amo/](../scripts/amo/) - AMO 测试脚本
- [QUICKSTART.md](QUICKSTART.md#troubleshooting) - 故障排除

#### 🔄 迁移
- [MIGRATION.md](MIGRATION.md) - 迁移指南
- [SUMMARY.md](SUMMARY.md) - 变更总结

---

## 📝 文档约定

### 标记说明

- ⭐ 推荐优先阅读
- 🆕 新增文档
- 🔧 开发者文档
- 📖 用户文档
- 🗺️ 导航文档

### 阅读时间

- **5-10 min**: 快速浏览
- **15-30 min**: 完整阅读
- **45-60 min**: 深入学习
- **2+ hours**: 详细研究

---

## 🎯 不同角色的文档推荐

### 👤 最终用户（使用 genPiHub）

**必读**:
- [QUICKSTART.md](QUICKSTART.md)
- [../README.md](../README.md)

**选读**:
- [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md)
- [QUICK_START.md](QUICK_START.md)

### 👨‍💻 集成开发者（集成到项目）

**必读**:
- [QUICKSTART.md](QUICKSTART.md)
- [../README.md](../README.md)
- [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md)
- [QUICK_START.md](QUICK_START.md)

**选读**:
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [CODE_GUIDE.md](CODE_GUIDE.md)

### 🔧 核心开发者（扩展功能）

**必读**:
- 所有入门文档
- [REPOSITORY_GUIDE.md](REPOSITORY_GUIDE.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [CODE_GUIDE.md](CODE_GUIDE.md)
- [TECHNICAL_SPEC.md](TECHNICAL_SPEC.md)

**选读**:
- 所有源码文件

### 📊 项目维护者

**必读**:
- 所有文档

---

## 🆘 获取帮助

### 问题查找顺序

1. **查看 [QUICKSTART.md](QUICKSTART.md) 故障排除部分**
   - 常见问题和解决方案

2. **运行诊断脚本**
   ```bash
   python scripts/amo/check_amo_setup.py
   python scripts/amo/debug_amo.py
   ```

3. **查看 [scripts/README.md](../scripts/README.md)**
   - 测试和调试指南

4. **搜索文档**
   - 使用 grep 搜索关键词
   ```bash
   grep -r "关键词" docs/
   ```

---

## 📊 文档统计

### 总览

```
文档类型           数量    总字数    总行数
-----------------------------------------------
入门文档            3      ~5K      ~200
理解文档            3      ~8K      ~350
开发文档            4     ~15K      ~650
维护文档            3      ~6K      ~250
-----------------------------------------------
总计               13     ~34K     ~1450
```

### 完整性

- ✅ 快速开始指南
- ✅ 安装文档
- ✅ 使用手册
- ✅ API 文档
- ✅ 架构设计文档
- ✅ 代码导读
- ✅ 技术规格
- ✅ 测试指南
- ✅ 迁移指南
- ✅ 项目总结

**覆盖率**: 100% ✅

---

## 🔄 文档更新

### 更新策略

- **与代码同步**: 文档随代码版本更新
- **及时更新**: 架构变更后立即更新文档
- **版本控制**: 文档版本与代码版本一致

### 贡献文档

如果你发现文档问题或想要改进：

1. 直接编辑对应的 Markdown 文件
2. 确保格式正确（使用 markdownlint）
3. 提交 PR

---

## 📞 反馈

如有文档相关问题或建议，请：

1. 提交 Issue（标记 `documentation`）
2. 提交 PR
3. 联系维护者

---

## 🎉 文档质量承诺

我们承诺：

- ✅ **清晰**: 易于理解，结构清晰
- ✅ **完整**: 覆盖所有重要主题
- ✅ **准确**: 与代码保持同步
- ✅ **示例驱动**: 提供丰富的代码示例
- ✅ **及时更新**: 随代码同步更新

---

**Happy Reading! 📚**

**维护者**: hvla Team  
**最后更新**: 2026-04-08  
**文档版本**: 0.1.0
