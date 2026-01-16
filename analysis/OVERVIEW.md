# 实验分析概述

## 研究背景

本研究探讨 **执行权限（Execution Regimes）** 对 LLM Agent 在软件工程任务上的影响。我们对比了 5 种执行模式：

| 模式 | 描述 |
|------|------|
| Run-Free | 完全不执行代码 |
| Run-Less-K1 | 限制执行 1 次 |
| Run-Less-K3 | 限制执行 3 次 |
| Run-Cost | 有成本约束的执行 |
| Run-Full | 无限制执行 |

**实验设置**：
- Agent: Claude Code, Codex
- 数据集: SWE-bench Lite (100 instances), SWE-bench Verified (100 instances)
- 评估指标: Pass Rate, Token 消耗, 执行次数, 运行时间

---

## 核心发现总结

### 一句话结论

> **Execution primarily affects efficiency and trajectory quality, while its marginal benefit on correctness is limited.**

> **执行权限主要影响效率和轨迹质量，对正确性的边际收益有限。**

---

## RQ1: Effectiveness - 执行权限对成功率的影响

**研究问题**: Run-Free、Run-Less、Run-Full 对修复成功率有什么影响？

### 核心数据

| Agent | Dataset | Run-Free | Run-Full | ΔPass |
|-------|---------|----------|----------|-------|
| Claude Code | Lite | 63.0% | 64.0% | +1.0% |
| Claude Code | Verified | 64.0% | 67.0% | +3.0% |
| Codex | Lite | 74.5% | 73.5% | -1.0% |
| Codex | Verified | 73.0% | 75.0% | +2.0% |

**平均差异**: Run-Full 相比 Run-Free 仅提升 **1.2%**

### 关键发现

1. **执行权限对成功率影响很小** - 差异在统计噪声范围内
2. **不存在"执行越多越强"的单调关系** - 4 组实验中仅 1 组呈单调递增
3. **Run-Less 模式表现不如预期** - 限制执行次数反而普遍低于 Run-Free
4. **Codex Run-Free 表现异常优秀** - 甚至略优于 Run-Full (74.5% vs 73.5%)

### 结论

> 执行环境并非必要条件，Run-Free 已能达到接近最佳的性能（差距 < 5%）

---

## RQ2: Efficiency - 成本与效率的 Pareto 前沿

**研究问题**: 不同执行权限对成本的影响有多大？

### 核心数据

| Agent | Dataset | Run-Free Tokens | Run-Full Tokens | 节省 |
|-------|---------|-----------------|-----------------|------|
| Claude Code | Lite | 69K | 158K | **56.4%** |
| Claude Code | Verified | 63K | 167K | **61.9%** |
| Codex | Lite | 409K | 473K | 13.4% |
| Codex | Verified | 539K | 544K | 0.8% |

### 关键发现

1. **Run-Free 是最具成本效益的选择** - 平均节省 33% Token，仅损失 1.2% Pass Rate
2. **Claude Code 成本节省显著** - 56-62% Token 节省
3. **Codex 成本几乎不受执行模式影响** - 仅 0.8-13% 变化
4. **时间节省与 Token 节省成正比** - Claude Code 节省 48-54% 时间

### 结论

> Run-Free 模式可大幅降低计算成本和碳排放，是成本敏感场景的首选

---

## RQ3: Execution Utility - 执行行为的目的分析

**研究问题**: 执行行为主要用于什么目的？哪些是高价值执行？

### 核心数据

**Claude Code 执行分布 (Lite):**

| Mode | 总执行 | 验证 | 定位 | 环境 | 探索 |
|------|--------|------|------|------|------|
| run_free | 693 | 8.5% | 2.3% | 6.3% | **71.1%** |
| run_full | 1804 | **39.0%** | 13.2% | 19.0% | 20.8% |

### 关键发现

1. **验证是主要执行目的** - Run-Full 模式下验证执行占 35-40%
2. **探索执行占比高但价值低** - 可被静态分析替代
3. **试错循环普遍存在** - Codex 约 2000 次重复命令
4. **执行效率极低** - 每次验证执行带来的 Pass Rate 提升 < 0.01%

### 结论

> 大部分执行属于"低价值开销"，验证执行虽有价值但边际收益极低

---

## RQ4: Agent Sensitivity - 不同 Agent 的敏感性差异

**研究问题**: 执行权限对不同 Agent 的影响是否一致？

### 核心数据

| Agent | ΔTokens% (Free→Full) | ΔPass% | 敏感性比 |
|-------|----------------------|--------|----------|
| Claude Code | +129% ~ +163% | +1% ~ +3% | **54-129** |
| Codex | +0.8% ~ +15% | -1% ~ +2% | **0.4-15** |

### 关键发现

1. **Claude Code 是成本敏感型** - 执行权限显著增加成本 (+146%)
2. **Codex 是成本稳定型** - 执行权限对成本影响小 (+8%)
3. **基础成本决定敏感性** - Claude Code 基础成本低 (65K)，Codex 基础成本高 (470K)
4. **不同 Agent 需要不同的执行策略** - "One size fits all" 不适用

### 结论

> 如果追求成本效益，Claude Code + Run-Free 是最佳选择

---

## RQ5: Failure Modes - 失败模式分析

**研究问题**: 不同执行 regime 会诱发哪些典型失败模式？

### 核心数据

| 类型 | 数量 |
|------|------|
| Run-Free 成功但 Run-Full 失败 | 16 |
| Run-Full 成功但 Run-Free 失败 | 21 |
| **净差异（Run-Full 优势）** | **5** |

### 关键发现

1. **失败模式差异不大** - Run-Free 和 Run-Full 的失败数量接近
2. **执行反馈是双刃剑** - 16 个案例中执行反馈反而导致失败
3. **净收益仅 5 个案例** - Run-Full 的优势非常有限
4. **Run-Free 失败更容易调试** - trace 短，原因直接

### 结论

> 执行反馈并非总是有益，Run-Free 失败后的调试负担更低

---

## 统计可靠性

### Wilson 95% 置信区间

所有 agent 在所有数据集上，Run-Free 和 Run-Full 的 95% 置信区间**高度重叠**：

| Agent | Dataset | Run-Free CI | Run-Full CI | 重叠 |
|-------|---------|-------------|-------------|------|
| Claude Code | Lite | [53.2%, 71.8%] | [54.2%, 72.7%] | ✓ |
| Codex | Verified | [63.6%, 80.7%] | [65.7%, 82.5%] | ✓ |

### McNemar 配对检验

所有比较的 p-value > 0.05，差异**不显著**：

| Agent | Dataset | b (Free胜) | c (Full胜) | p-value |
|-------|---------|------------|------------|---------|
| Claude Code | Lite | 5 | 6 | 1.0000 |
| Codex | Verified | 1 | 3 | 0.6250 |

### 跨数据集一致性

主要趋势在 Lite 和 Verified 两个数据集上**一致**，支持结论的稳健性。

---

## 总结与建议

### 核心结论

| 维度 | 发现 |
|------|------|
| **正确性** | 执行权限对 Pass Rate 影响很小（< 5%） |
| **成本** | Run-Free 可节省 33-62% Token |
| **效率** | 大部分执行是低价值开销 |
| **Agent 差异** | Claude Code 成本敏感，Codex 成本稳定 |
| **失败模式** | 执行反馈是双刃剑，净收益有限 |
| **任务难度** | 简单任务执行无影响，困难任务执行无法解决 |

### 实践建议

1. **默认使用 Run-Free** - 成本效益最高
2. **Claude Code + Run-Free** - 最佳成本效益组合
3. **仅在必要时使用 Run-Full** - 需要环境验证的复杂问题
4. **不推荐 Run-Less** - 表现不如 Run-Free

### 学术贡献

> **Correctness appears robust to execution access, whereas cost is highly sensitive to it.**

本研究表明，当前 LLM 的推理能力已经足够强大，执行环境更像是"工程捷径"而非"必要能力"。

---

## 文件索引

| 文件 | 描述 |
|------|------|
| [RQ1_effectiveness/](./RQ1_effectiveness/) | 执行权限对成功率的影响 |
| [RQ2_efficiency/](./RQ2_efficiency/) | 成本与效率的 Pareto 前沿 |
| [RQ3_execution_utility/](./RQ3_execution_utility/) | 执行行为的目的分析 |
| [RQ4_agent_sensitivity/](./RQ4_agent_sensitivity/) | 不同 Agent 的敏感性差异 |
| [RQ5_failure_modes/](./RQ5_failure_modes/) | 失败模式分析 |
| [RQ6_case_study/](./RQ6_case_study/) | 案例分析与任务难度分层 |
| [common/data_statistical.md](./common/data_statistical.md) | 统计分析数据 |
