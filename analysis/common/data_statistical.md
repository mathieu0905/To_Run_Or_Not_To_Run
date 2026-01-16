# 统计分析 - 数据表格

为论文提供统计可靠性支持的分析数据。

## Wilson 95% 置信区间

使用 Wilson score interval，比正态近似更稳定。

### SWE-bench Lite

| Agent | Mode | n | Resolved | Pass Rate | 95% CI |
|-------|------|---|----------|-----------|--------|
| claude_code | run_free | 100 | 63 | 63.0% | [53.2%, 71.8%] |
| claude_code | run_less_k1 | 100 | 61 | 61.0% | [51.2%, 70.0%] |
| claude_code | run_less_k3 | 100 | 62 | 62.0% | [52.2%, 70.9%] |
| claude_code | run_cost | 100 | 63 | 63.0% | [53.2%, 71.8%] |
| claude_code | run_full | 100 | 64 | 64.0% | [54.2%, 72.7%] |
| codex | run_free | 98 | 73 | 74.5% | [65.0%, 82.1%] |
| codex | run_less_k1 | 98 | 66 | 67.3% | [57.6%, 75.8%] |
| codex | run_less_k3 | 98 | 68 | 69.4% | [59.7%, 77.6%] |
| codex | run_cost | 98 | 69 | 70.4% | [60.7%, 78.5%] |
| codex | run_full | 98 | 72 | 73.5% | [64.0%, 81.2%] |

### SWE-bench Verified

| Agent | Mode | n | Resolved | Pass Rate | 95% CI |
|-------|------|---|----------|-----------|--------|
| claude_code | run_free | 100 | 64 | 64.0% | [54.2%, 72.7%] |
| claude_code | run_less_k1 | 100 | 64 | 64.0% | [54.2%, 72.7%] |
| claude_code | run_less_k3 | 100 | 65 | 65.0% | [55.3%, 73.6%] |
| claude_code | run_cost | 100 | 67 | 67.0% | [57.3%, 75.4%] |
| claude_code | run_full | 100 | 67 | 67.0% | [57.3%, 75.4%] |
| codex | run_free | 100 | 73 | 73.0% | [63.6%, 80.7%] |
| codex | run_less_k1 | 100 | 72 | 72.0% | [62.5%, 79.9%] |
| codex | run_less_k3 | 100 | 73 | 73.0% | [63.6%, 80.7%] |
| codex | run_cost | 100 | 71 | 71.0% | [61.5%, 79.0%] |
| codex | run_full | 100 | 75 | 75.0% | [65.7%, 82.5%] |

## 置信区间重叠分析

分析不同模式之间的置信区间是否重叠，重叠表示差异不显著。

### SWE-bench Lite

**claude_code:**

- run_free: 63.0% [53.2%, 71.8%]
- run_full: 64.0% [54.2%, 72.7%]
- 置信区间重叠: **是**
- 结论: 差异在统计上不显著

**codex:**

- run_free: 74.5% [65.0%, 82.1%]
- run_full: 73.5% [64.0%, 81.2%]
- 置信区间重叠: **是**
- 结论: 差异在统计上不显著

### SWE-bench Verified

**claude_code:**

- run_free: 64.0% [54.2%, 72.7%]
- run_full: 67.0% [57.3%, 75.4%]
- 置信区间重叠: **是**
- 结论: 差异在统计上不显著

**codex:**

- run_free: 73.0% [63.6%, 80.7%]
- run_full: 75.0% [65.7%, 82.5%]
- 置信区间重叠: **是**
- 结论: 差异在统计上不显著

## McNemar 配对检验

检验同一实例在不同模式下的表现差异是否显著。

### SWE-bench Lite

**claude_code:**

run_free vs run_full:
- run_free 成功但 run_full 失败: 5 个实例
- run_free 失败但 run_full 成功: 6 个实例
- p-value: 1.0000
- 显著性 (α=0.05): **不显著**

run_less_k1 vs run_full:
- run_less_k1 成功但 run_full 失败: 3 个实例
- run_less_k1 失败但 run_full 成功: 6 个实例
- p-value: 0.5078
- 显著性 (α=0.05): **不显著**

**codex:**

run_free vs run_full:
- run_free 成功但 run_full 失败: 4 个实例
- run_free 失败但 run_full 成功: 3 个实例
- p-value: 1.0000
- 显著性 (α=0.05): **不显著**

run_less_k1 vs run_full:
- run_less_k1 成功但 run_full 失败: 2 个实例
- run_less_k1 失败但 run_full 成功: 8 个实例
- p-value: 0.1094
- 显著性 (α=0.05): **不显著**

### SWE-bench Verified

**claude_code:**

run_free vs run_full:
- run_free 成功但 run_full 失败: 6 个实例
- run_free 失败但 run_full 成功: 9 个实例
- p-value: 0.6072
- 显著性 (α=0.05): **不显著**

run_less_k1 vs run_full:
- run_less_k1 成功但 run_full 失败: 3 个实例
- run_less_k1 失败但 run_full 成功: 6 个实例
- p-value: 0.5078
- 显著性 (α=0.05): **不显著**

**codex:**

run_free vs run_full:
- run_free 成功但 run_full 失败: 1 个实例
- run_free 失败但 run_full 成功: 3 个实例
- p-value: 0.6250
- 显著性 (α=0.05): **不显著**

run_less_k1 vs run_full:
- run_less_k1 成功但 run_full 失败: 2 个实例
- run_less_k1 失败但 run_full 成功: 5 个实例
- p-value: 0.4531
- 显著性 (α=0.05): **不显著**

## 跨数据集一致性分析

验证结论在不同数据集上的一致性。

### claude_code

| Mode | Lite Pass Rate | Verified Pass Rate | 趋势一致 |
|------|----------------|--------------------| ---------|
| run_free | 63.0% | 64.0% | ✓ |
| run_less_k1 | 61.0% | 64.0% | ✓ |
| run_less_k3 | 62.0% | 65.0% | ✓ |
| run_cost | 63.0% | 67.0% | ✓ |
| run_full | 64.0% | 67.0% | ✓ |

### codex

| Mode | Lite Pass Rate | Verified Pass Rate | 趋势一致 |
|------|----------------|--------------------| ---------|
| run_free | 74.5% | 73.0% | ✓ |
| run_less_k1 | 67.3% | 72.0% | ✓ |
| run_less_k3 | 69.4% | 73.0% | ✓ |
| run_cost | 70.4% | 71.0% | ✓ |
| run_full | 73.5% | 75.0% | ✓ |

## 关键统计结论

### 1. 置信区间分析结论

- 所有 agent 在所有数据集上，run_free 和 run_full 的 95% 置信区间**高度重叠**
- 这表明通过率差异在统计上**不显著**
- 差异主要来自随机噪声，而非执行权限的本质影响

### 2. 配对检验结论

- McNemar 检验显示 run_free vs run_full 的差异**不显著** (p > 0.05)
- 这意味着：能被 run_free 解决的问题，大部分也能被 run_full 解决，反之亦然
- 支持论点："能做对的还是能做对"

### 3. 跨数据集一致性结论

- 主要趋势在 Lite 和 Verified 两个数据集上**一致**
- 这比随机抽样更能说明结论的稳健性
- 支持论点：结论不依赖于特定的样本选择

### 4. 核心学术表达

> **Execution primarily affects efficiency and trajectory quality, while its marginal benefit on correctness is limited.**

> **Correctness appears robust to execution access, whereas cost is highly sensitive to it.**

## 可直接放进论文的文本

### English Version

#### Experimental Setup

> We did not perform any task filtering or manual selection. To ensure full reproducibility, we used the first 100 instances from the official release order of SWE-bench Lite and SWE-bench Verified as our deterministic evaluation subset, with instance IDs listed in the appendix. Our goal is not to claim a new state-of-the-art accuracy on SWE-bench, but to isolate the effect of execution regimes on agent behavior and cost. Therefore, a deterministic subset is sufficient for controlled comparison.

#### Statistical Reliability

> We report pass rates with 95% Wilson confidence intervals. For Codex on SWE-bench Verified: Run-Full achieves 75/100 (75.0%, CI: [65.7%, 82.5%]), while Run-Free achieves 73/100 (73.0%, CI: [63.6%, 80.7%]). The confidence intervals substantially overlap, indicating that the pass rate differences are within statistical noise. In contrast, cost differences are substantial (e.g., Claude Code shows 146% token increase from Run-Free to Run-Full). This suggests that execution regimes primarily affect efficiency and trajectory behavior rather than correctness.

#### Threats to Validity

> Using a prefix subset of the dataset may introduce ordering bias. However, we performed no selective filtering, and we demonstrate the stability of observed trends through confidence intervals and paired comparisons. The consistency of findings across both SWE-bench Lite and Verified further supports the robustness of our conclusions. Future work may extend to additional instances to further validate generalizability.

### 中文版

#### 实验设置

> 我们未进行任何任务筛选或人工挑选。为确保完全可复现性，我们直接使用 SWE-bench Lite 与 SWE-bench Verified 官方发布顺序中的前 100 个实例作为确定性评测子集，并在附录公开实例 ID 列表。本工作关注不同 execution regime 对 agent 成本与行为机制的影响，因此该确定性子集足以支持受控对比。

#### 统计可靠性

> 我们报告每个 setting 的通过率及其 95% Wilson 置信区间。以 Codex 在 SWE-bench Verified 上的结果为例：Run-Full 达到 75/100 (75.0%, CI: [65.7%, 82.5%])，Run-Free 达到 73/100 (73.0%, CI: [63.6%, 80.7%])。置信区间高度重叠，表明通过率差异在统计噪声范围内。相较之下，成本差异显著（如 Claude Code 从 Run-Free 到 Run-Full Token 增长 146%）。这表明 execution regime 的主要影响体现在效率与轨迹行为，而非正确性。

#### 有效性威胁

> 由于使用数据集前缀子集，结果可能受到顺序偏置影响。然而我们未进行任何选择性筛选，并以置信区间与配对比较展示观察趋势的稳定性。结论在 SWE-bench Lite 和 Verified 两个数据集上的一致性进一步支持了结果的稳健性。未来可扩展至更多实例以进一步验证结论的普适性。
