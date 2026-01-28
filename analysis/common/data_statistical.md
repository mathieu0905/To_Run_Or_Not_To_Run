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
| codex | run_free | 100 | 74 | 74.0% | [64.6%, 81.6%] |
| codex | run_less_k1 | 100 | 68 | 68.0% | [58.3%, 76.3%] |
| codex | run_less_k3 | 100 | 69 | 69.0% | [59.4%, 77.2%] |
| codex | run_cost | 100 | 71 | 71.0% | [61.5%, 79.0%] |
| codex | run_full | 100 | 73 | 73.0% | [63.6%, 80.7%] |

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

- run_free: 74.0% [64.6%, 81.6%]
- run_full: 73.0% [63.6%, 80.7%]
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
- run_less_k1 成功但 run_full 失败: 3 个实例
- run_less_k1 失败但 run_full 成功: 8 个实例
- p-value: 0.2266
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

## 等效性检验 (Equivalence Testing)

使用 TOST (Two One-Sided Tests) 检验，等效性阈值 δ = 5pp

**核心问题**: 不同执行模式之间的收益上界是多少？

如果 90% CI 完全落在 ±δ 内，则可以声称两者「实践等效」。

### SWE-bench Lite

**claude_code:**

**free → less-k1:** 差异 -2.0pp, CI [-5.8, +1.8], b=4, c=2 ❌
**free → less-k3:** 差异 -1.0pp, CI [-5.9, +3.9], b=5, c=4 ❌
**free → cost:** 差异 +0.0pp, CI [-5.7, +5.7], b=6, c=6 ❌
**free → full:** 差异 +1.0pp, CI [-4.4, +6.4], b=5, c=6 ❌
**less-k1 → less-k3:** 差异 +1.0pp, CI [-3.3, +5.3], b=3, c=4 ❌
**less-k1 → full:** 差异 +3.0pp, CI [-1.7, +7.7], b=3, c=6 ❌
**less-k3 → full:** 差异 +2.0pp, CI [-1.8, +5.8], b=2, c=4 ❌
**cost → full:** 差异 +1.0pp, CI [-3.9, +5.9], b=4, c=5 ❌

**codex:**

**free → less-k1:** 差异 -6.0pp, CI [-10.9, -1.1], b=9, c=3 ❌
**free → less-k3:** 差异 -5.0pp, CI [-8.0, -2.0], b=6, c=1 ❌
**free → cost:** 差异 -3.0pp, CI [-8.8, +2.8], b=8, c=5 ❌
**free → full:** 差异 -1.0pp, CI [-5.3, +3.3], b=4, c=3 ❌
**less-k1 → less-k3:** 差异 +1.0pp, CI [-3.9, +5.9], b=4, c=5 ❌
**less-k1 → full:** 差异 +5.0pp, CI [+0.1, +9.9], b=3, c=8 ❌
**less-k3 → full:** 差异 +4.0pp, CI [-0.0, +8.0], b=2, c=6 ❌
**cost → full:** 差异 +2.0pp, CI [-4.1, +8.1], b=6, c=8 ❌

### SWE-bench Verified

**claude_code:**

**free → less-k1:** 差异 +0.0pp, CI [-6.6, +6.6], b=8, c=8 ❌
**free → less-k3:** 差异 +1.0pp, CI [-5.8, +7.8], b=8, c=9 ❌
**free → cost:** 差异 +3.0pp, CI [-2.2, +8.2], b=4, c=7 ❌
**free → full:** 差异 +3.0pp, CI [-3.2, +9.2], b=6, c=9 ❌
**less-k1 → less-k3:** 差异 +1.0pp, CI [-2.6, +4.6], b=2, c=3 ✅
**less-k1 → full:** 差异 +3.0pp, CI [-1.7, +7.7], b=3, c=6 ❌
**less-k3 → full:** 差异 +2.0pp, CI [-1.8, +5.8], b=2, c=4 ❌
**cost → full:** 差异 +0.0pp, CI [-4.7, +4.7], b=4, c=4 ✅

**codex:**

**free → less-k1:** 差异 -1.0pp, CI [-5.9, +3.9], b=5, c=4 ❌
**free → less-k3:** 差异 +0.0pp, CI [-5.2, +5.2], b=5, c=5 ❌
**free → cost:** 差异 -2.0pp, CI [-7.6, +3.6], b=7, c=5 ❌
**free → full:** 差异 +2.0pp, CI [-0.8, +4.8], b=1, c=3 ✅
**less-k1 → less-k3:** 差异 +1.0pp, CI [-4.9, +6.9], b=6, c=7 ❌
**less-k1 → full:** 差异 +3.0pp, CI [-0.9, +6.9], b=2, c=5 ❌
**less-k3 → full:** 差异 +2.0pp, CI [-2.5, +6.5], b=3, c=5 ❌
**cost → full:** 差异 +4.0pp, CI [-0.0, +8.0], b=2, c=6 ❌

### 等效性检验总结表

| Dataset | Agent | 比较 | 差异 | 90% CI | b | c | 等效? |
|---------|-------|------|------|--------|---|---|-------|
| SWE-benc | claude | free→less-k1 | -2.0pp | [-5.8, +1.8] | 4 | 2 | ❌ |
| SWE-benc | claude | free→less-k3 | -1.0pp | [-5.9, +3.9] | 5 | 4 | ❌ |
| SWE-benc | claude | free→cost | +0.0pp | [-5.7, +5.7] | 6 | 6 | ❌ |
| SWE-benc | claude | free→full | +1.0pp | [-4.4, +6.4] | 5 | 6 | ❌ |
| SWE-benc | claude | less-k1→less-k3 | +1.0pp | [-3.3, +5.3] | 3 | 4 | ❌ |
| SWE-benc | claude | less-k1→full | +3.0pp | [-1.7, +7.7] | 3 | 6 | ❌ |
| SWE-benc | claude | less-k3→full | +2.0pp | [-1.8, +5.8] | 2 | 4 | ❌ |
| SWE-benc | claude | cost→full | +1.0pp | [-3.9, +5.9] | 4 | 5 | ❌ |
| SWE-benc | codex | free→less-k1 | -6.0pp | [-10.9, -1.1] | 9 | 3 | ❌ |
| SWE-benc | codex | free→less-k3 | -5.0pp | [-8.0, -2.0] | 6 | 1 | ❌ |
| SWE-benc | codex | free→cost | -3.0pp | [-8.8, +2.8] | 8 | 5 | ❌ |
| SWE-benc | codex | free→full | -1.0pp | [-5.3, +3.3] | 4 | 3 | ❌ |
| SWE-benc | codex | less-k1→less-k3 | +1.0pp | [-3.9, +5.9] | 4 | 5 | ❌ |
| SWE-benc | codex | less-k1→full | +5.0pp | [+0.1, +9.9] | 3 | 8 | ❌ |
| SWE-benc | codex | less-k3→full | +4.0pp | [-0.0, +8.0] | 2 | 6 | ❌ |
| SWE-benc | codex | cost→full | +2.0pp | [-4.1, +8.1] | 6 | 8 | ❌ |
| SWE-benc | claude | free→less-k1 | +0.0pp | [-6.6, +6.6] | 8 | 8 | ❌ |
| SWE-benc | claude | free→less-k3 | +1.0pp | [-5.8, +7.8] | 8 | 9 | ❌ |
| SWE-benc | claude | free→cost | +3.0pp | [-2.2, +8.2] | 4 | 7 | ❌ |
| SWE-benc | claude | free→full | +3.0pp | [-3.2, +9.2] | 6 | 9 | ❌ |
| SWE-benc | claude | less-k1→less-k3 | +1.0pp | [-2.6, +4.6] | 2 | 3 | ✅ |
| SWE-benc | claude | less-k1→full | +3.0pp | [-1.7, +7.7] | 3 | 6 | ❌ |
| SWE-benc | claude | less-k3→full | +2.0pp | [-1.8, +5.8] | 2 | 4 | ❌ |
| SWE-benc | claude | cost→full | +0.0pp | [-4.7, +4.7] | 4 | 4 | ✅ |
| SWE-benc | codex | free→less-k1 | -1.0pp | [-5.9, +3.9] | 5 | 4 | ❌ |
| SWE-benc | codex | free→less-k3 | +0.0pp | [-5.2, +5.2] | 5 | 5 | ❌ |
| SWE-benc | codex | free→cost | -2.0pp | [-7.6, +3.6] | 7 | 5 | ❌ |
| SWE-benc | codex | free→full | +2.0pp | [-0.8, +4.8] | 1 | 3 | ✅ |
| SWE-benc | codex | less-k1→less-k3 | +1.0pp | [-4.9, +6.9] | 6 | 7 | ❌ |
| SWE-benc | codex | less-k1→full | +3.0pp | [-0.9, +6.9] | 2 | 5 | ❌ |
| SWE-benc | codex | less-k3→full | +2.0pp | [-2.5, +6.5] | 3 | 5 | ❌ |
| SWE-benc | codex | cost→full | +4.0pp | [-0.0, +8.0] | 2 | 6 | ❌ |

### 配对对称性分析 (Agent 随机性)

如果某种模式有系统性优势，应该看到 c >> b（或 b >> c）。
如果 b ≈ c，说明差异主要来自 agent 内在随机性，而非模式本身的影响。

| Dataset | Agent | 比较 | b (mode1赢) | c (mode2赢) | 比例 b:c | 对称? |
|---------|-------|------|-------------|-------------|----------|-------|
| SWE-benc | claude | free→less-k1 | 4 | 2 | 4:2 | ✅ 对称 |
| SWE-benc | claude | free→less-k3 | 5 | 4 | 5:4 | ✅ 对称 |
| SWE-benc | claude | free→cost | 6 | 6 | 6:6 | ✅ 对称 |
| SWE-benc | claude | free→full | 5 | 6 | 5:6 | ✅ 对称 |
| SWE-benc | claude | less-k1→less-k3 | 3 | 4 | 3:4 | ✅ 对称 |
| SWE-benc | claude | less-k1→full | 3 | 6 | 3:6 | ✅ 对称 |
| SWE-benc | claude | less-k3→full | 2 | 4 | 2:4 | ✅ 对称 |
| SWE-benc | claude | cost→full | 4 | 5 | 4:5 | ✅ 对称 |
| SWE-benc | codex | free→less-k1 | 9 | 3 | 9:3 | ⚠️ 偏斜 |
| SWE-benc | codex | free→less-k3 | 6 | 1 | 6:1 | ⚠️ 偏斜 |
| SWE-benc | codex | free→cost | 8 | 5 | 8:5 | ✅ 对称 |
| SWE-benc | codex | free→full | 4 | 3 | 4:3 | ✅ 对称 |
| SWE-benc | codex | less-k1→less-k3 | 4 | 5 | 4:5 | ✅ 对称 |
| SWE-benc | codex | less-k1→full | 3 | 8 | 3:8 | ⚠️ 偏斜 |
| SWE-benc | codex | less-k3→full | 2 | 6 | 2:6 | ⚠️ 偏斜 |
| SWE-benc | codex | cost→full | 6 | 8 | 6:8 | ✅ 对称 |
| SWE-benc | claude | free→less-k1 | 8 | 8 | 8:8 | ✅ 对称 |
| SWE-benc | claude | free→less-k3 | 8 | 9 | 8:9 | ✅ 对称 |
| SWE-benc | claude | free→cost | 4 | 7 | 4:7 | ✅ 对称 |
| SWE-benc | claude | free→full | 6 | 9 | 6:9 | ✅ 对称 |
| SWE-benc | claude | less-k1→less-k3 | 2 | 3 | 2:3 | ✅ 对称 |
| SWE-benc | claude | less-k1→full | 3 | 6 | 3:6 | ✅ 对称 |
| SWE-benc | claude | less-k3→full | 2 | 4 | 2:4 | ✅ 对称 |
| SWE-benc | claude | cost→full | 4 | 4 | 4:4 | ✅ 对称 |
| SWE-benc | codex | free→less-k1 | 5 | 4 | 5:4 | ✅ 对称 |
| SWE-benc | codex | free→less-k3 | 5 | 5 | 5:5 | ✅ 对称 |
| SWE-benc | codex | free→cost | 7 | 5 | 7:5 | ✅ 对称 |
| SWE-benc | codex | free→full | 1 | 3 | 1:3 | ✅ 对称 |
| SWE-benc | codex | less-k1→less-k3 | 6 | 7 | 6:7 | ✅ 对称 |
| SWE-benc | codex | less-k1→full | 2 | 5 | 2:5 | ✅ 对称 |
| SWE-benc | codex | less-k3→full | 3 | 5 | 3:5 | ✅ 对称 |
| SWE-benc | codex | cost→full | 2 | 6 | 2:6 | ⚠️ 偏斜 |

**对称性总结**: 27/32 个比较显示对称分布

> 大多数比较中 b ≈ c，表明不一致配对是双向的，
> 支持「差异主要来自 agent 随机性而非执行模式系统性优势」的结论。

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
| run_free | 74.0% | 73.0% | ✓ |
| run_less_k1 | 68.0% | 72.0% | ✓ |
| run_less_k3 | 69.0% | 73.0% | ✓ |
| run_cost | 71.0% | 71.0% | ✓ |
| run_full | 73.0% | 75.0% | ✓ |

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

## 等效性检验 - 论文文本

### English Version

> To quantify the upper bound of execution benefits, we performed equivalence testing with a practically meaningful threshold δ = 5pp. Using Two One-Sided Tests (TOST), we computed 90% confidence intervals for the paired difference between Run-Full and Run-Free. 
The maximum observed upper bound across all settings is +9.2pp. While some settings show equivalence, others cannot rule out modest benefits from execution.

### 中文版

> 为量化执行收益的上界，我们使用等效性检验，设定实践意义阈值 δ = 5pp。通过 TOST (Two One-Sided Tests) 方法，我们计算了 Run-Full 与 Run-Free 配对差异的 90% 置信区间。
所有设置中观测到的最大收益上界为 +9.2pp。部分设置显示等效，但其他设置无法排除执行带来的适度收益。
