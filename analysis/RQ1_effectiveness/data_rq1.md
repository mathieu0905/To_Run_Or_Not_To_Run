# RQ1: Effectiveness - 数据表格

执行权限对修复成功率的影响分析数据。

## Pass Rate 对比表

### SWE-bench Lite

| Agent | Mode | Resolved | Total | Pass Rate |
|-------|------|----------|-------|-----------|
| claude_code | run_free | 63 | 100 | 63.0% |
| claude_code | run_less_k1 | 61 | 100 | 61.0% |
| claude_code | run_less_k3 | 62 | 100 | 62.0% |
| claude_code | run_cost | 63 | 100 | 63.0% |
| claude_code | run_full | 64 | 100 | 64.0% |
| codex | run_free | 73 | 98 | 74.5% |
| codex | run_less_k1 | 66 | 98 | 67.3% |
| codex | run_less_k3 | 68 | 98 | 69.4% |
| codex | run_cost | 69 | 98 | 70.4% |
| codex | run_full | 72 | 98 | 73.5% |

### SWE-bench Verified

| Agent | Mode | Resolved | Total | Pass Rate |
|-------|------|----------|-------|-----------|
| claude_code | run_free | 64 | 100 | 64.0% |
| claude_code | run_less_k1 | 64 | 100 | 64.0% |
| claude_code | run_less_k3 | 65 | 100 | 65.0% |
| claude_code | run_cost | 67 | 100 | 67.0% |
| claude_code | run_full | 67 | 100 | 67.0% |
| codex | run_free | 73 | 100 | 73.0% |
| codex | run_less_k1 | 72 | 100 | 72.0% |
| codex | run_less_k3 | 73 | 100 | 73.0% |
| codex | run_cost | 71 | 100 | 71.0% |
| codex | run_full | 75 | 100 | 75.0% |

## 差异分析表 (ΔPass)

以 run_full 为基准，计算各 mode 的 Pass Rate 差异。

### SWE-bench Lite

| Agent | Mode | Pass Rate | vs run_full | ΔPass |
|-------|------|-----------|-------------|-------|
| claude_code | run_free | 63.0% | 64.0% | -1.0% |
| claude_code | run_less_k1 | 61.0% | 64.0% | -3.0% |
| claude_code | run_less_k3 | 62.0% | 64.0% | -2.0% |
| claude_code | run_cost | 63.0% | 64.0% | -1.0% |
| claude_code | run_full | 64.0% | 64.0% | - |
| codex | run_free | 74.5% | 73.5% | +1.0% |
| codex | run_less_k1 | 67.3% | 73.5% | -6.1% |
| codex | run_less_k3 | 69.4% | 73.5% | -4.1% |
| codex | run_cost | 70.4% | 73.5% | -3.1% |
| codex | run_full | 73.5% | 73.5% | - |

### SWE-bench Verified

| Agent | Mode | Pass Rate | vs run_full | ΔPass |
|-------|------|-----------|-------------|-------|
| claude_code | run_free | 64.0% | 67.0% | -3.0% |
| claude_code | run_less_k1 | 64.0% | 67.0% | -3.0% |
| claude_code | run_less_k3 | 65.0% | 67.0% | -2.0% |
| claude_code | run_cost | 67.0% | 67.0% | +0.0% |
| claude_code | run_full | 67.0% | 67.0% | - |
| codex | run_free | 73.0% | 75.0% | -2.0% |
| codex | run_less_k1 | 72.0% | 75.0% | -3.0% |
| codex | run_less_k3 | 73.0% | 75.0% | -2.0% |
| codex | run_cost | 71.0% | 75.0% | -4.0% |
| codex | run_full | 75.0% | 75.0% | - |

## 单调性分析

检验是否存在'执行越多越强'的单调关系。

执行权限排序（从少到多）: run_free < run_less_k1 < run_less_k3 < run_cost ≈ run_full

### SWE-bench Lite

**claude_code:**
- run_free: 63.0% → run_less_k1: 61.0% → run_less_k3: 62.0% → run_cost: 63.0% → run_full: 64.0%
- 结论: ✗ 不存在单调递增关系

**codex:**
- run_free: 74.5% → run_less_k1: 67.3% → run_less_k3: 69.4% → run_cost: 70.4% → run_full: 73.5%
- 结论: ✗ 不存在单调递增关系

### SWE-bench Verified

**claude_code:**
- run_free: 64.0% → run_less_k1: 64.0% → run_less_k3: 65.0% → run_cost: 67.0% → run_full: 67.0%
- 结论: ✓ 存在单调递增关系

**codex:**
- run_free: 73.0% → run_less_k1: 72.0% → run_less_k3: 73.0% → run_cost: 71.0% → run_full: 75.0%
- 结论: ✗ 不存在单调递增关系

## 关键发现

### 1. Run-Free vs Run-Full 对比

- **claude_code** (SWE-bench Lite): Run-Free 63.0% vs Run-Full 64.0% (Δ = +1.0%)
- **codex** (SWE-bench Lite): Run-Free 74.5% vs Run-Full 73.5% (Δ = -1.0%)
- **claude_code** (SWE-bench Verified): Run-Free 64.0% vs Run-Full 67.0% (Δ = +3.0%)
- **codex** (SWE-bench Verified): Run-Free 73.0% vs Run-Full 75.0% (Δ = +2.0%)

### 2. 平均差异

- Run-Full 相比 Run-Free 的平均提升: **1.2%**

### 3. 结论

- 执行权限对修复成功率的影响**较小**（< 5%）
- Run-Free 模式已能达到接近最佳的性能
- 执行环境可能**不是必要条件**，而是'工程捷径'