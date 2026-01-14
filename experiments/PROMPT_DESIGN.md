# Prompt Design for Execution-Constrained Code Repair

## 1. Overview

本文档描述了用于研究执行约束对 LLM 代码修复能力影响的 prompt 设计方法。我们设计了 4 种执行模式，通过严格控制变量来隔离"执行能力"这一单一因素的影响。

## 2. Design Principles

### 2.1 Controlled Variables

为确保实验结果的可比性，我们采用了严格的控制变量设计：

- **统一的基础结构**：所有模式的 prompt 遵循完全一致的结构框架
- **单一差异点**：唯一的差异仅在"执行约束"（Execution Constraint）部分
- **最小化指导**：避免引入额外的工作流程建议、代码示例或策略指导
- **一致的输出要求**：所有模式使用相同的输出格式要求

### 2.2 Prompt Structure

所有模式的 prompt 遵循以下统一结构：

```
1. Task Description (任务描述)
2. Repository Information (仓库信息)
3. Problem Description (问题描述)
4. Execution Constraint (执行约束) ← 唯一的差异点
5. What You CAN Do (允许的操作)
6. What You CANNOT Do (禁止的操作)
7. Output Format (输出格式)
```

### 2.3 Cost Model Design

对于涉及成本评估的模式（Run-Less 和 Run-Cost），我们采用了以下设计原则：

- **不写死成本值**：只提供参考范围（~1.0 和 ~0.3），让 Agent 自主估算
- **区分执行类型**：
  - 高成本执行：完整测试套件（pytest, unittest, Django tests 等）≈ 1.0 点
  - 低成本执行：简单脚本（python script.py）≈ 0.3 点
- **要求显式输出**：强制 Agent 在执行前后输出成本评估和预算追踪

## 3. Execution Modes

### 3.1 Run-Free (完全不执行)

**定义**：Agent 完全不能运行测试或执行 Python 脚本，只能通过静态分析修复代码。

**执行约束**：
```
You CANNOT run tests or execute Python scripts.
You must generate a fix by reading code and reasoning about the root cause.
```

**特点**：
- 只能使用 bash 命令查看文件（ls, cat, grep 等）
- 无法验证修复的正确性
- 完全依赖代码理解和逻辑推理能力

**研究目的**：作为性能下限基准，测试纯静态分析的修复能力。

---

### 3.2 Run-Less (有限成本预算)

**定义**：Agent 拥有有限的执行成本预算（k 点），需要战略性地分配资源。

**执行约束**：
```
You have a limited execution budget of k.0 cost points.

Different executions have different costs. Estimate the cost before each execution:
- Running full test suites (pytest, unittest, Django tests, etc.): ~1.0 point
- Running simple scripts (python script.py): ~0.3 point

Before each execution, output:
[EXECUTION] Estimated cost: X.X points | Remaining budget: Y.Y points | Purpose: ...

After each execution, output:
Remaining budget: X.X points
```

**特点**：
- 需要在执行前估算成本
- 必须追踪剩余预算
- 强制做出战略性决策（何时执行、执行什么）

**研究目的**：测试 Agent 在资源受限情况下的决策能力和资源管理能力。

**实验参数**：
- k=1: 极度受限（约 1 次完整测试或 3 次脚本执行）
- k=2: 中度受限（约 2 次完整测试或 6 次脚本执行）
- k=3: 轻度受限（约 3 次完整测试或 10 次脚本执行）

---

### 3.3 Run-Cost (成本意识但不限制)

**定义**：Agent 可以无限次执行，但需要意识到每次执行都有成本。

**执行约束**：
```
Every Python execution has a cost (time, compute, money).
You can run code without hard limits, but be cost-aware in your decisions.

Different executions have different costs. Estimate the cost before each execution:
- Running full test suites (pytest, unittest, Django tests, etc.): ~1.0 point
- Running simple scripts (python script.py): ~0.3 point

Before each execution, output:
[EXECUTION] Estimated cost: X.X points | Purpose: ...
```

**特点**：
- 无硬性预算限制
- 需要在执行前评估成本
- 鼓励成本效益权衡

**研究目的**：测试成本意识是否能在不牺牲性能的前提下减少资源消耗。

---

### 3.4 Run-Full (无限制执行)

**定义**：Agent 可以随意运行测试和脚本，没有任何限制。

**执行约束**：
```
You have UNLIMITED Python executions.
Feel free to run tests and scripts as many times as needed.
```

**特点**：
- 完全无限制
- 无需成本评估
- 最接近"理想状态"

**研究目的**：作为性能上限基准，代表 Agent 在无约束条件下的最佳表现。

## 4. Experimental Hypotheses

基于上述设计，我们提出以下研究假设：

### H1: 执行能力的影响
```
Performance: Run-Free < Run-Less < Run-Cost ≤ Run-Full
```
执行能力对修复成功率有显著正向影响。

### H2: 资源管理能力
在有限预算下（Run-Less），Agent 能够：
- 正确估算不同执行的成本
- 做出合理的资源分配决策
- 在预算约束内完成修复任务

### H3: 成本意识的效果
Run-Cost 模式相比 Run-Full：
- 执行次数显著减少（资源节省）
- 修复成功率无显著差异（性能保持）

### H4: 预算阈值
存在一个预算阈值 k*，当 k ≥ k* 时，Run-Less 的性能接近 Run-Full。

## 5. Implementation Details

### 5.1 Cost Tracking

在 Run-Less 和 Run-Cost 模式中，我们通过分析 Agent 的输出来追踪成本：

- **执行前声明**：匹配 `[EXECUTION]` 标记，提取估算成本
- **执行后追踪**：匹配 `Remaining budget` 输出，验证预算管理
- **实际成本计算**：基于执行的命令类型自动分类：
  - 高成本：pytest, unittest, Django tests 等测试框架
  - 低成本：python script.py 等脚本执行

### 5.2 Metrics

我们收集以下指标来评估不同模式的表现：

- **修复成功率**：通过 SWE-bench 测试套件验证
- **执行次数**：
  - 总执行次数
  - 高成本执行次数
  - 低成本执行次数
- **成本消耗**：总成本点数（高成本 × 1.0 + 低成本 × 0.3）
- **交互轮数**：Agent 与环境的交互次数
- **执行时间**：任务完成的总时间

## 6. Design Rationale

### 6.1 为什么不写死成本值？

我们选择提供参考范围（~1.0 和 ~0.3）而非精确值，原因如下：

1. **避免过度约束**：精确值可能导致 Agent 机械地遵循规则，而非真正理解成本
2. **鼓励自主判断**：Agent 需要根据具体情况（测试规模、复杂度）自行估算
3. **更接近真实场景**：实际开发中，执行成本往往是估算而非精确值

### 6.2 为什么区分高成本和低成本执行？

初步实验发现，如果不区分执行类型，Agent 可能通过多次低成本执行（脚本）来绕过预算限制。区分执行类型可以：

1. **更准确地反映真实成本**：完整测试套件的成本远高于简单脚本
2. **防止预算规避**：避免 Agent 用多次脚本执行替代一次测试执行
3. **鼓励高效策略**：引导 Agent 先用低成本脚本定位问题，再用高成本测试验证

### 6.3 为什么 Run-Cost 不限制预算？

Run-Cost 模式的设计目的是测试"成本意识"而非"成本限制"：

1. **隔离成本意识的影响**：与 Run-Full 对比，评估成本意识本身的效果
2. **避免硬性约束**：测试 Agent 是否能在无强制要求下自主节省资源
3. **更接近实际场景**：实际开发中，开发者通常有成本意识但无硬性限制

## 7. Validation

### 7.1 Prompt 一致性验证

我们通过以下方式验证 prompt 的一致性：

- 所有模式的非约束部分完全相同（字符串匹配）
- 唯一差异在"Execution Constraint"部分
- 无额外的工作流程建议或代码示例

### 7.2 成本追踪验证

我们验证 Agent 是否正确遵循成本追踪要求：

- Run-Less: 检查是否输出预算追踪信息
- Run-Cost: 检查是否输出成本评估信息
- 统计实际执行次数与声明的成本是否一致

## 8. Limitations and Future Work

### 8.1 当前限制

1. **成本模型简化**：实际执行成本受多种因素影响（测试数量、复杂度、环境等）
2. **预算遵守依赖 Agent**：Agent 可能不完全遵守预算约束
3. **单一任务类型**：当前仅在代码修复任务上验证

### 8.2 未来方向

1. **动态成本模型**：根据实际执行时间动态调整成本
2. **强制预算约束**：在系统层面强制执行预算限制
3. **扩展到其他任务**：测试在代码生成、重构等任务上的效果

## 9. Conclusion

本 prompt 设计通过严格的控制变量方法，隔离了"执行能力"这一单一因素的影响。4 种执行模式形成了从完全受限到完全自由的连续谱，使我们能够系统地研究执行约束对 LLM 代码修复能力的影响。

设计的关键创新点包括：
1. 统一的 prompt 结构，确保实验可比性
2. 灵活的成本模型，鼓励 Agent 自主判断
3. 区分高成本和低成本执行，更准确地反映真实场景
4. Run-Cost 模式，隔离成本意识的独立效果

---

**文档版本**: 1.0
**最后更新**: 2026-01-14
**实现文件**: `prompt_builder.py`
