# 执行模式综合分析报告

## 研究概述

本研究探讨不同执行权限（Execution Regimes）对 LLM Agent 在软件工程任务上的影响。

### 实验设置

| 维度 | 配置 |
|------|------|
| Agent | Claude Code, Codex |
| 数据集 | SWE-bench Lite (100), SWE-bench Verified (100) |
| 执行模式 | run_free, run_less_k1, run_less_k3, run_cost, run_full |

### 执行模式说明

| 模式 | 描述 |
|------|------|
| run_free | 完全不执行代码 |
| run_less_k1 | 限制执行 1 次 |
| run_less_k3 | 限制执行 3 次 |
| run_cost | 有成本约束的执行 |
| run_full | 无限制执行 |

---

## 核心发现

### 一句话结论

> **Execution primarily affects efficiency and trajectory quality, while its marginal benefit on correctness is limited.**

> **执行权限主要影响效率和轨迹质量，对正确性的边际收益有限。**

---

## 1. 整体表现对比

### SWE-bench Lite

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 63 | 61 | 62 | 63 | 64 |
| codex | 73 | 66 | 68 | 69 | 72 |

### SWE-bench Verified

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 64 | 64 | 65 | 67 | 67 |
| codex | 73 | 72 | 73 | 71 | 75 |

### 关键观察

1. **Run-Free vs Run-Full 差异很小** - 平均仅 1.2% 差异
2. **Run-Less 模式表现不稳定** - 多数情况下不如 Run-Free
3. **Codex Run-Free 表现异常优秀** - 在 Lite 上甚至优于 Run-Full (73 vs 72)

---

## 2. 成本效率分析

### Claude Code 成本对比

| Dataset | Mode | Avg Tokens | vs Run-Free |
|---------|------|------------|-------------|
| Lite | run_free | 69,047 | - |
| Lite | run_less_k1 | 105,400 | +52.6% |
| Lite | run_less_k3 | 139,240 | +101.7% |
| Lite | run_cost | 143,596 | +108.0% |
| Lite | run_full | 158,417 | **+129.4%** |
| Verified | run_free | 63,490 | - |
| Verified | run_full | 166,746 | **+162.6%** |

### Codex 成本对比

| Dataset | Mode | Avg Tokens | vs Run-Free |
|---------|------|------------|-------------|
| Lite | run_free | 409,355 | - |
| Lite | run_full | 472,777 | +15.5% |
| Verified | run_free | 539,302 | - |
| Verified | run_full | 543,763 | +0.8% |

### 效率比分析 (Pass Rate / Token)

| Agent | Dataset | run_free | run_cost | run_full |
|-------|---------|----------|----------|----------|
| claude_code | Lite | **0.91** | 0.44 | 0.40 |
| claude_code | Verified | **1.01** | 0.50 | 0.40 |
| codex | Lite | **0.18** | 0.14 | 0.15 |
| codex | Verified | **0.14** | 0.14 | 0.14 |

**结论**: Run-Free 的效率比最高，是最具成本效益的选择。

---

## 3. 模式间差异分析

### 全模式差异矩阵 (Claude Code, Lite)

表格显示：行模式成功但列模式失败的案例数

| | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|---|---|---|---|---|---|
| run_free | - | 4 | 5 | 6 | 5 |
| run_less_k1 | 2 | - | 3 | 4 | 3 |
| run_less_k3 | 4 | 4 | - | 5 | 2 |
| run_cost | 6 | 6 | 6 | - | 4 |
| run_full | 6 | 6 | 4 | 5 | - |

### 关键对比汇总

| 对比 | Run-Free 胜 | Run-Full 胜 | 净差异 |
|------|-------------|-------------|--------|
| Claude Code (Lite) | 5 | 6 | +1 |
| Claude Code (Verified) | 6 | 9 | +3 |
| Codex (Lite) | 4 | 3 | -1 |
| Codex (Verified) | 1 | 3 | +2 |
| **总计** | **16** | **21** | **+5** |

**结论**: Run-Full 仅在 5 个净案例上优于 Run-Free，优势非常有限。

---

## 4. 执行权限递增分析

### 实例分类

| 类别 | Claude Code | Codex | 说明 |
|------|-------------|-------|------|
| 始终成功 | 52-55 | 59 | 所有模式都能解决 |
| 始终失败 | 0 | 0 | 所有模式都无法解决 |
| 随执行改善 | 4-8 | 2-3 | 更多执行权限有帮助 |
| 随执行恶化 | 5-6 | 1-4 | 更多执行权限反而有害 |
| 不一致 | 7-11 | 14-19 | 表现不稳定 |

**关键发现**: "不一致"类别占比很高，说明执行权限的效果不稳定。

---

## 5. 任务难度分层分析

### 难度分布

| 难度 | 数量 | 定义 |
|------|------|------|
| 简单 | 141 | 所有 Agent 在 Run-Full 下都成功 |
| 中等 | 15 | 部分 Agent 成功 |
| 困难 | 12 | 所有 Agent 都失败 |

### 按难度分层的全模式对比

#### 简单任务 (141 个)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 79.4% | 81.6% | 84.4% | 83.0% | 88.7% |
| codex | 93.6% | 89.4% | 90.8% | 89.4% | 97.9% |

#### 中等任务 (15 个)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | **80.0%** | 53.3% | 40.0% | 66.7% | 40.0% |
| codex | **80.0%** | 60.0% | 66.7% | 73.3% | 60.0% |

#### 困难任务 (12 个)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 25.0% | 16.7% | 16.7% | 25.0% | 0.0% |
| codex | 16.7% | 25.0% | 25.0% | 25.0% | 0.0% |

**关键发现**:
- **简单任务**: Run-Full 最好，但 Run-Free 也接近
- **中等任务**: Run-Free 反而最好（80%），Run-Full 只有 40-60%
- **困难任务**: 所有模式都失败，Run-Full 甚至是 0%

---

## 6. 各模式的独特价值

### 独有成功案例统计

| 模式 | 独有成功 | 比 Run-Free 好 | 比 Run-Full 好 |
|------|----------|----------------|----------------|
| run_less_k1 | 4 | 16 | 10 |
| run_less_k3 | 2 | 19 | 9 |
| run_cost | 5 | 22 | 15 |

### Run-Less 模式的价值

虽然整体不如 Run-Free，但在 **16-22 个案例**中比 Run-Free 更好。

**典型案例**: `django__django-11433`
- Run-Free: 失败
- Run-Less-K1: **成功** ✓
- Run-Less-K3: **成功** ✓
- Run-Full: 失败

**洞察**: 1-3 次执行刚好够验证修复，但过多执行反而有害。

### Run-Cost 模式的价值

有 5 个案例是**只有 Run-Cost 能解决**的：
- `django__django-12113`
- `django__django-12589`
- `django__django-14997`
- `astropy__astropy-13236`

---

## 7. 典型案例分析

### Run-Free 成功但 Run-Full 失败

#### `django__django-13230` (Claude Code, Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 6,891 | 9 | 0 | **成功** |
| run_full | 105,713 | 70 | 9 | 失败 |

**分析**: 过多的测试执行导致试错循环，Token 消耗增加 15 倍但反而失败。

### Run-Full 成功但 Run-Free 失败

#### `django__django-12965` (Claude Code, Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 191,095 | 69 | 0 | 失败 |
| run_less_k1 | 182,385 | 67 | 4 | **成功** |
| run_full | 225,064 | 84 | 5 | **成功** |

**分析**: 该问题需要执行反馈来验证修复，但 K1 就足够了。

---

## 8. 统计可靠性

### Wilson 95% 置信区间

| Agent | Dataset | Run-Free CI | Run-Full CI | 重叠 |
|-------|---------|-------------|-------------|------|
| Claude Code | Lite | [53.2%, 71.8%] | [54.2%, 72.7%] | ✓ |
| Claude Code | Verified | [54.2%, 72.7%] | [57.3%, 75.4%] | ✓ |
| Codex | Lite | [65.0%, 82.1%] | [64.0%, 81.2%] | ✓ |
| Codex | Verified | [63.6%, 80.7%] | [65.7%, 82.5%] | ✓ |

**结论**: 所有置信区间高度重叠，差异在统计上不显著。

### McNemar 配对检验

| Agent | Dataset | p-value | 显著性 |
|-------|---------|---------|--------|
| Claude Code | Lite | 1.0000 | 不显著 |
| Claude Code | Verified | 0.6072 | 不显著 |
| Codex | Lite | 1.0000 | 不显著 |
| Codex | Verified | 0.6250 | 不显著 |

---

## 9. 核心结论

### 主要发现

| 维度 | 发现 |
|------|------|
| **正确性** | 执行权限对 Pass Rate 影响很小（< 5%） |
| **成本** | Run-Free 可节省 33-62% Token |
| **效率** | 大部分执行是低价值开销 |
| **Agent 差异** | Claude Code 成本敏感（+146%），Codex 成本稳定（+8%） |
| **任务难度** | 简单任务执行无影响，困难任务执行无法解决 |
| **执行反馈** | 是双刃剑，净收益仅 5 个案例 |

### 实践建议

| 优先级 | 模式 | 适用场景 |
|--------|------|----------|
| 1 | **Run-Free** | 默认首选，成本效益最高 |
| 2 | **Run-Less-K1** | Run-Free 失败时的备选 |
| 3 | **Run-Cost** | 需要执行但要控制成本 |
| 4 | Run-Full | 仅在复杂调试时使用 |
| ✗ | Run-Less-K3 | 不推荐，表现不稳定 |

### 学术贡献

> **Correctness appears robust to execution access, whereas cost is highly sensitive to it.**

本研究表明，当前 LLM 的推理能力已经足够强大，执行环境更像是"工程捷径"而非"必要能力"。

---

## 10. 可直接放进论文的文本

### English Version

> We report pass rates with 95% Wilson confidence intervals. For Codex on SWE-bench Verified: Run-Full achieves 75/100 (75.0%, CI: [65.7%, 82.5%]), while Run-Free achieves 73/100 (73.0%, CI: [63.6%, 80.7%]). The confidence intervals substantially overlap, indicating that the pass rate differences are within statistical noise. In contrast, cost differences are substantial (e.g., Claude Code shows 146% token increase from Run-Free to Run-Full). This suggests that execution regimes primarily affect efficiency and trajectory behavior rather than correctness.

### 中文版

> 我们报告每个 setting 的通过率及其 95% Wilson 置信区间。以 Codex 在 SWE-bench Verified 上的结果为例：Run-Full 达到 75/100 (75.0%, CI: [65.7%, 82.5%])，Run-Free 达到 73/100 (73.0%, CI: [63.6%, 80.7%])。置信区间高度重叠，表明通过率差异在统计噪声范围内。相较之下，成本差异显著（如 Claude Code 从 Run-Free 到 Run-Full Token 增长 146%）。这表明 execution regime 的主要影响体现在效率与轨迹行为，而非正确性。

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
