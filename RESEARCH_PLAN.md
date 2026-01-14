# Run-Free / Run-Less / Run-Full: 研究执行计划

## 1. 研究概述

### 1.1 核心问题
> 在代码修复任务中，执行环境到底是"必要能力"，还是"工程捷径"？

### 1.2 四种执行范式

| 模式 | 学术命名 | 含义 | Agent 行为 | 约束类型 |
|------|----------|------|------------|----------|
| **Run-Free** | Zero-Exec | 完全不执行，纯推理修复 | Read → Infer → Fix | 硬禁止 |
| **Run-Less** | Budget-Exec | 有限次执行（K次预算） | Hypothesize → Instrument → Execute → Fix | 硬限制 |
| **Run-Cost** | Cost-Aware-Exec | 有成本约束，模型自主决策 | Assess Confidence → Decide → Execute (if needed) → Fix | 软约束 |
| **Run-Full** | Unrestricted-Exec | 任意执行 | Write → Run → See Error → Revise → Repeat | 无约束 |

### 1.3 核心论点
1. 现有 Agent 研究过度依赖 Run-Full，导致 Agent 变得"懒惰"
2. Execution 应被视为"昂贵的决策资源"，而非"免费按钮"
3. **"We trade execution frequency for execution informativeness"**

---

## 2. 实验设计

### 2.1 实验变量

**唯一控制变量**: Execution Access（执行权限）

| 设置 | 执行次数 | 是否有精细日志 | 约束类型 |
|------|----------|----------------|----------|
| A (Run-Full) | 无限 | 无（仅 stderr） | 无约束 |
| B (Run-Less) | K次 | 无 | 硬限制 |
| C (Run-Less + Log) | K次 | 有（Agent 自由插桩） | 硬限制 |
| D (Run-Cost) | 不限制但有成本 | 可选（Agent 决定） | 软约束 |
| E (Run-Free) | 0 | - | 硬禁止 |

**K 值设置**: K ∈ {1, 2, 3}，每个值多跑几遍取平均

### 2.2 Research Questions

**RQ1: Performance vs. Budget**
- 横轴：执行次数预算 (0, 1, 3, 5, 10, ∞)
- 纵轴：Pass@1 成功率
- 预期：收益边际递减，Run-Less 可能 ≈ Run-Full

**RQ2: Information Density**
- 对比 Standard Output vs. Instrumented Logging
- 预期：1次带 Log 的执行 ≈ 5次普通执行

**RQ3: Behavior Analysis**
- 分析 Agent 的 Token 分布
- Run-Free: Token 全花在推理上
- Run-Full: Token 全花在阅读报错和重试上
- Run-Less: 展现"假设-验证"行为模式

**RQ4: Code Quality**
- 评估修复后代码的可读性、泛化性
- 预期：Run-Full 产生 Spaghetti Code，Run-Less 更简洁

**RQ5: Self-Confidence Calibration (Run-Cost 特有)**
- 模型的信心水平是否与实际成功率匹配？
- 评估指标：
  - 高信心（>90%）时不运行测试的成功率
  - 低信心（<50%）时运行测试的价值
  - 信心-成功率校准曲线
  - 模型是否会过度自信或过度谨慎

### 2.3 Benchmark
- **SWE-bench Lite**: 300 题，快速验证
- **SWE-bench Verified**: 500 题，更严格的验证集

### 2.4 模型与 Agent 选择
- **主要**: Claude Opus + Claude Code
- **可选扩展**: GPT-5.2 + Codex（如有必要）

### 2.5 评估指标体系

| 指标 | 类型 | 说明 |
|------|------|------|
| **Pass@1** | 基本指标 | 首次提交通过率 |
| **Token Cost** | 性能指标 | 总 token 消耗量 |
| **Turn Count** | 效率指标 | 交互轮数 |
| **Execution Count** | 资源指标 | 实际执行次数 |
| **First Correct Turn** | 效率指标 | 首次正确补丁出现的轮数 |
| **Patch Size** | 质量指标 | 补丁代码行数（越小越好） |
| **Reasoning Ratio** | 行为指标 | 推理 token / 总 token（区分三种模式） |
| **Retry Rate** | 行为指标 | 重试次数 / 总尝试次数（Run-Full 预期更高） |

---

## 3. 技术实现

### 3.1 Agent 架构

```
┌─────────────────────────────────────────────┐
│                Agent Core                    │
├─────────────────────────────────────────────┤
│  1. Code Reader (读取代码)                   │
│  2. Reasoner (推理 Bug 位置)                 │
│  3. Instrumenter (生成插桩代码) [Run-Less]   │
│  4. Executor (执行代码) [Run-Less/Full]      │
│  5. Patcher (生成修复补丁)                   │
└─────────────────────────────────────────────┘
```

### 3.2 Run-Less 核心机制

**决策器 (Planner)**: Agent 每步输出一个 Action：
1. **Thinking**: 继续推理，不消耗 Run 预算
2. **Instrumentation**: 编写并插入 Log 代码
3. **Execution**: 消耗 1 次 Run 预算，获取 Log
4. **Submission**: 提交修复

**插桩格式**:
```python
# Agent 必须回答：
# Hypothesis: 我怀疑 calculation() 函数在处理负数时有问题
# Probe: 在入口处插入
print(f"DEBUG: input={x}, state={self.state}")
# Outcome: 获得 Trace 而非仅 Error
```

### 3.3 System Prompt 设计

**Run-Free Prompt**:
```
You are a code repair agent. You CANNOT execute any code.
Read the buggy code, understand the logic, and generate a fix.
You must get it right on the first try.
```

**Run-Less Prompt**:
```
You have a strict budget of {K} executions. You cannot waste them.
Before you run the code, you must:
1. Formulate a hypothesis (what might be wrong?)
2. Insert detailed logging/print statements to capture specific variables
3. Only then execute
Treat every execution as a high-stakes experiment.
```

**Run-Cost Prompt**:
```
Every test execution has a cost (time, resources, money).
Before running tests, evaluate your confidence level:
- High confidence (>90%): Consider not running tests
- Medium confidence (50-90%): Evaluate if the information gain is worth the cost
- Low confidence (<50%): Usually worth running tests

For each decision, output:
- Current confidence level: X%
- Decision: [Run / Don't Run]
- Reasoning: [Explain why]
```

**Run-Full Prompt**:
```
You can execute code freely. Fix the bug by running tests,
observing errors, and iterating until all tests pass.
```

---

## 4. 执行步骤

### Phase 1: 环境搭建
- [ ] 搭建 SWE-bench 评估环境
- [ ] 准备 Docker sandbox 用于代码执行
- [ ] 实现 Agent 框架（支持三种模式切换）
- [ ] 实现日志插桩模块

### Phase 2: MVP 实验
- [ ] 选取 20 道 SWE-bench Lite 题目
- [ ] 实现 Group A (Run-Full): 允许 10 次执行
- [ ] 实现 Group B (Run-Less + Log): 只允许 1-2 次执行，必须先插桩
- [ ] 对比成功率、Token 消耗、代码质量

### Phase 3: 完整实验
- [ ] 扩展到完整 SWE-bench Lite (300 题)
- [ ] 测试不同执行预算 (K = 0, 1, 3, 5, 10, ∞)
- [ ] 收集行为数据（Token 分布、执行模式）
- [ ] 代码质量评估（人工 + GPT-4 评分）

### Phase 4: 分析与写作
- [ ] 绘制 Efficiency-Effectiveness Frontier 图
- [ ] 行为模式分析（Gambler vs. Scientist）
- [ ] 撰写论文

---

## 5. 预期结果

### 5.1 核心发现
> **"One smart run is worth ten blind runs."**

### 5.2 预期曲线
```
Success Rate
    │
    │         ┌─────────── Run-Full (plateau)
    │        /
    │   ┌───/─────────── Run-Less + Log (快速达到)
    │  /
    │ /
    │/
    └──────────────────────────────────────── Execution Budget
       0    1    3    5    10   ∞
```

### 5.3 论文叙事
1. **现状**: 大家以为给 Agent 越多执行次数越好
2. **问题**: 无限执行让 Agent 变懒，陷入"补丁循环"
3. **方法**: Log-Driven Budgeted Execution
4. **结果**: 限制 2 次执行 + 插桩 ≈ 或 > 50 次盲目执行
5. **结论**: Agent 设计应关注"实验设计"而非 Sandbox 并发能力

---

## 6. 论文定位

### 6.1 目标会议
- **首选**: ISSTA 2026 (符合动态分析/插桩传统)
- **备选**: FSE / ICSE

### 6.2 标题候选
- *Is More Execution Always Better? The "Less is More" Paradox in LLM-based Program Repair*
- *Agent as a Scientist: Hypothesis-Driven Debugging with Budget-Constrained Execution*
- *Quality over Quantity: Why Constraint Elicits Better Reasoning in Code Agents*

### 6.3 Distinguished Paper 要素
1. **反直觉**: 少跑点，多想点
2. **Green AI**: 降低执行成本
3. **理论高度**: Debug = Experimental Design Problem
4. **现实意义**: 生产环境/涉密环境本就是 Run-Less

---

## 7. 已确认决策

1. **执行预算 K**: K ∈ {1, 2, 3}，每个值多跑几遍取平均
2. **插桩粒度**: Agent 自由插桩（不限制插桩模板）
3. **Benchmark**: SWE-bench Lite + SWE-bench Verified
4. **模型**: Claude Opus + Claude Code（主要），GPT-5.2 + Codex（可选扩展）
5. **评估指标**: Pass@1（基本）+ Token Cost（性能）+ 行为指标（见 2.5）

---

## 8. 下一步行动

1. **立即**: 搭建 SWE-bench 环境
2. **本周**: 完成 MVP 实验（20 题对比）
3. **验证假设**: Run-Less + Log ≈ Run-Full
4. **根据结果**: 调整实验设计，扩展规模
