# RQ2: Efficiency - 数据表格

成本与效率的 Pareto 前沿分析数据。

## 成本对比表

### SWE-bench Lite

| Agent | Mode | Avg Tokens | Avg Turns | Avg Time (s) | High-Cost Exec | Low-Cost Exec |
|-------|------|------------|-----------|--------------|----------------|---------------|
| claude_code | run_free | 69,046 | 35.2 | 530.7 | 0.6 | 0.2 |
| claude_code | run_less_k1 | 105,399 | 48.5 | 844.5 | 4.0 | 2.4 |
| claude_code | run_less_k3 | 139,240 | 59.6 | 851.2 | 5.2 | 3.3 |
| claude_code | run_cost | 143,595 | 61.3 | 889.1 | 5.4 | 2.6 |
| claude_code | run_full | 158,417 | 69.7 | 1027.7 | 7.0 | 2.5 |
| codex | run_free | 409,354 | 41.0 | 570.1 | 0.0 | 0.0 |
| codex | run_less_k1 | 375,407 | 40.1 | 584.6 | 2.3 | 0.2 |
| codex | run_less_k3 | 524,471 | 46.8 | 592.4 | 4.9 | 0.4 |
| codex | run_cost | 499,336 | 44.9 | 609.9 | 4.4 | 0.4 |
| codex | run_full | 472,776 | 44.1 | 618.5 | 6.3 | 0.5 |

### SWE-bench Verified

| Agent | Mode | Avg Tokens | Avg Turns | Avg Time (s) | High-Cost Exec | Low-Cost Exec |
|-------|------|------------|-----------|--------------|----------------|---------------|
| claude_code | run_free | 63,490 | 32.7 | 572.7 | 0.5 | 0.3 |
| claude_code | run_less_k1 | 125,338 | 52.6 | 878.5 | 3.7 | 2.4 |
| claude_code | run_less_k3 | 125,776 | 53.6 | 957.3 | 4.4 | 2.9 |
| claude_code | run_cost | 134,374 | 56.6 | 1013.0 | 4.5 | 2.3 |
| claude_code | run_full | 166,745 | 68.7 | 1233.6 | 6.3 | 2.3 |
| codex | run_free | 539,301 | 46.5 | 723.5 | 0.0 | 0.0 |
| codex | run_less_k1 | 409,696 | 41.3 | 694.7 | 2.2 | 0.2 |
| codex | run_less_k3 | 578,573 | 50.3 | 725.4 | 4.5 | 0.3 |
| codex | run_cost | 491,096 | 44.9 | 689.8 | 3.8 | 0.4 |
| codex | run_full | 543,762 | 46.3 | 722.5 | 5.9 | 0.4 |

## 相对变化百分比表 (vs run_full)

以 run_full 为基准，计算各 mode 的成本变化。负值表示成本降低。

### SWE-bench Lite

| Agent | Mode | ΔTokens | ΔTurns | ΔTime |
|-------|------|---------|--------|-------|
| claude_code | run_free | -56.4% | -49.5% | -48.4% |
| claude_code | run_less_k1 | -33.5% | -30.4% | -17.8% |
| claude_code | run_less_k3 | -12.1% | -14.5% | -17.2% |
| claude_code | run_cost | -9.4% | -12.0% | -13.5% |
| claude_code | run_full | - | - | - |
| codex | run_free | -13.4% | -6.9% | -7.8% |
| codex | run_less_k1 | -20.6% | -9.1% | -5.5% |
| codex | run_less_k3 | +10.9% | +6.1% | -4.2% |
| codex | run_cost | +5.6% | +1.9% | -1.4% |
| codex | run_full | - | - | - |

### SWE-bench Verified

| Agent | Mode | ΔTokens | ΔTurns | ΔTime |
|-------|------|---------|--------|-------|
| claude_code | run_free | -61.9% | -52.4% | -53.6% |
| claude_code | run_less_k1 | -24.8% | -23.5% | -28.8% |
| claude_code | run_less_k3 | -24.6% | -21.9% | -22.4% |
| claude_code | run_cost | -19.4% | -17.7% | -17.9% |
| claude_code | run_full | - | - | - |
| codex | run_free | -0.8% | +0.3% | +0.1% |
| codex | run_less_k1 | -24.7% | -10.8% | -3.8% |
| codex | run_less_k3 | +6.4% | +8.7% | +0.4% |
| codex | run_cost | -9.7% | -3.0% | -4.5% |
| codex | run_full | - | - | - |

## Pareto 前沿数据

Pass Rate vs Avg Total Tokens 数据点，用于绘制 Pareto 前沿图。

### SWE-bench Lite

| Agent | Mode | Pass Rate (%) | Avg Tokens | Pareto Optimal? |
|-------|------|---------------|------------|-----------------|
| claude_code | run_free | 63.0 | 69,046 | ✓ |
| claude_code | run_less_k1 | 61.0 | 105,399 |  |
| claude_code | run_less_k3 | 62.0 | 139,240 |  |
| claude_code | run_cost | 63.0 | 143,595 |  |
| claude_code | run_full | 64.0 | 158,417 | ✓ |
| codex | run_free | 74.5 | 409,354 | ✓ |
| codex | run_less_k1 | 67.3 | 375,407 | ✓ |
| codex | run_less_k3 | 69.4 | 524,471 |  |
| codex | run_cost | 70.4 | 499,336 |  |
| codex | run_full | 73.5 | 472,776 |  |

### SWE-bench Verified

| Agent | Mode | Pass Rate (%) | Avg Tokens | Pareto Optimal? |
|-------|------|---------------|------------|-----------------|
| claude_code | run_free | 64.0 | 63,490 | ✓ |
| claude_code | run_less_k1 | 64.0 | 125,338 |  |
| claude_code | run_less_k3 | 65.0 | 125,776 | ✓ |
| claude_code | run_cost | 67.0 | 134,374 | ✓ |
| claude_code | run_full | 67.0 | 166,745 |  |
| codex | run_free | 73.0 | 539,301 | ✓ |
| codex | run_less_k1 | 72.0 | 409,696 | ✓ |
| codex | run_less_k3 | 73.0 | 578,573 |  |
| codex | run_cost | 71.0 | 491,096 |  |
| codex | run_full | 75.0 | 543,762 | ✓ |

## 效率分析

### SWE-bench Lite

**claude_code:**

- Run-Free vs Run-Full:
  - Pass Rate 差异: +1.0%
  - Token 节省: 56.4%
  - 时间节省: 48.4%
  - 效率比 (Token节省/Pass差异): 56.4

**codex:**

- Run-Free vs Run-Full:
  - Pass Rate 差异: -1.0%
  - Token 节省: 13.4%
  - 时间节省: 7.8%
  - 效率比 (Token节省/Pass差异): 13.1

### SWE-bench Verified

**claude_code:**

- Run-Free vs Run-Full:
  - Pass Rate 差异: +3.0%
  - Token 节省: 61.9%
  - 时间节省: 53.6%
  - 效率比 (Token节省/Pass差异): 20.6

**codex:**

- Run-Free vs Run-Full:
  - Pass Rate 差异: +2.0%
  - Token 节省: 0.8%
  - 时间节省: -0.1%
  - 效率比 (Token节省/Pass差异): 0.4

## 关键发现

### 1. Token 消耗对比

- **claude_code** (SWE-bench Lite): Run-Free 69,046 vs Run-Full 158,417 (节省 56.4%)
- **codex** (SWE-bench Lite): Run-Free 409,354 vs Run-Full 472,776 (节省 13.4%)
- **claude_code** (SWE-bench Verified): Run-Free 63,490 vs Run-Full 166,745 (节省 61.9%)
- **codex** (SWE-bench Verified): Run-Free 539,301 vs Run-Full 543,762 (节省 0.8%)

### 2. 时间消耗对比

- **claude_code** (SWE-bench Lite): Run-Free 531s vs Run-Full 1028s (节省 48.4%)
- **codex** (SWE-bench Lite): Run-Free 570s vs Run-Full 618s (节省 7.8%)
- **claude_code** (SWE-bench Verified): Run-Free 573s vs Run-Full 1234s (节省 53.6%)
- **codex** (SWE-bench Verified): Run-Free 724s vs Run-Full 723s (节省 -0.1%)

### 3. 成本效益结论

- 平均 Token 节省: **33.1%**
- 平均时间节省: **27.4%**
- 平均 Pass Rate 差异: **+1.2%**

**结论**: Run-Free 模式以 33% 的成本节省换取 1.2% 的性能损失，是最具成本效益的选择。