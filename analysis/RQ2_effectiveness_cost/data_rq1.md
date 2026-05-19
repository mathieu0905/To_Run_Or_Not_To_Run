# RQ1: Effectiveness - Data Tables

Analysis data on the impact of execution permissions on fix success rate.

## Pass Rate Comparison Table

### SWE-bench Lite

| Agent | Mode | Resolved | Total | Pass Rate |
|-------|------|----------|-------|-----------|
| claude_code | run_free | 63 | 100 | 63.0% |
| claude_code | run_less_k1 | 61 | 100 | 61.0% |
| claude_code | run_less_k3 | 62 | 100 | 62.0% |
| claude_code | run_cost | 63 | 100 | 63.0% |
| claude_code | run_full | 64 | 100 | 64.0% |
| codex | run_free | 74 | 100 | 74.0% |
| codex | run_less_k1 | 68 | 100 | 68.0% |
| codex | run_less_k3 | 69 | 100 | 69.0% |
| codex | run_cost | 71 | 100 | 71.0% |
| codex | run_full | 73 | 100 | 73.0% |
| opencode | run_free | 7 | 100 | 7.0% |
| opencode | run_less_k1 | 14 | 100 | 14.0% |
| opencode | run_less_k3 | 7 | 100 | 7.0% |
| opencode | run_cost | 9 | 100 | 9.0% |
| opencode | run_full | 6 | 100 | 6.0% |

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
| opencode | run_free | 13 | 100 | 13.0% |
| opencode | run_less_k1 | 17 | 100 | 17.0% |
| opencode | run_less_k3 | 11 | 100 | 11.0% |
| opencode | run_cost | 13 | 100 | 13.0% |
| opencode | run_full | 14 | 100 | 14.0% |

## Difference Analysis Table (ΔPass)

Using run_full as baseline, calculate Pass Rate differences for each mode.

### SWE-bench Lite

| Agent | Mode | Pass Rate | vs run_full | ΔPass |
|-------|------|-----------|-------------|-------|
| claude_code | run_free | 63.0% | 64.0% | -1.0% |
| claude_code | run_less_k1 | 61.0% | 64.0% | -3.0% |
| claude_code | run_less_k3 | 62.0% | 64.0% | -2.0% |
| claude_code | run_cost | 63.0% | 64.0% | -1.0% |
| claude_code | run_full | 64.0% | 64.0% | - |
| codex | run_free | 74.0% | 73.0% | +1.0% |
| codex | run_less_k1 | 68.0% | 73.0% | -5.0% |
| codex | run_less_k3 | 69.0% | 73.0% | -4.0% |
| codex | run_cost | 71.0% | 73.0% | -2.0% |
| codex | run_full | 73.0% | 73.0% | - |
| opencode | run_free | 7.0% | 6.0% | +1.0% |
| opencode | run_less_k1 | 14.0% | 6.0% | +8.0% |
| opencode | run_less_k3 | 7.0% | 6.0% | +1.0% |
| opencode | run_cost | 9.0% | 6.0% | +3.0% |
| opencode | run_full | 6.0% | 6.0% | - |

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
| opencode | run_free | 13.0% | 14.0% | -1.0% |
| opencode | run_less_k1 | 17.0% | 14.0% | +3.0% |
| opencode | run_less_k3 | 11.0% | 14.0% | -3.0% |
| opencode | run_cost | 13.0% | 14.0% | -1.0% |
| opencode | run_full | 14.0% | 14.0% | - |

## Monotonicity Analysis

Test whether there exists a monotonic relationship of 'more execution leads to better performance'.

Execution permission ordering (from less to more): run_free < run_less_k1 < run_less_k3 < run_cost ≈ run_full

### SWE-bench Lite

**claude_code:**
- run_free: 63.0% → run_less_k1: 61.0% → run_less_k3: 62.0% → run_cost: 63.0% → run_full: 64.0%
- Conclusion: ✗ No monotonic increasing relationship

**codex:**
- run_free: 74.0% → run_less_k1: 68.0% → run_less_k3: 69.0% → run_cost: 71.0% → run_full: 73.0%
- Conclusion: ✗ No monotonic increasing relationship

**opencode:**
- run_free: 7.0% → run_less_k1: 14.0% → run_less_k3: 7.0% → run_cost: 9.0% → run_full: 6.0%
- Conclusion: ✗ No monotonic increasing relationship

### SWE-bench Verified

**claude_code:**
- run_free: 64.0% → run_less_k1: 64.0% → run_less_k3: 65.0% → run_cost: 67.0% → run_full: 67.0%
- Conclusion: ✓ Monotonic increasing relationship exists

**codex:**
- run_free: 73.0% → run_less_k1: 72.0% → run_less_k3: 73.0% → run_cost: 71.0% → run_full: 75.0%
- Conclusion: ✗ No monotonic increasing relationship

**opencode:**
- run_free: 13.0% → run_less_k1: 17.0% → run_less_k3: 11.0% → run_cost: 13.0% → run_full: 14.0%
- Conclusion: ✗ No monotonic increasing relationship

## Key Findings

### 1. Run-Free vs Run-Full Comparison

- **claude_code** (SWE-bench Lite): Run-Free 63.0% vs Run-Full 64.0% (Δ = +1.0%)
- **codex** (SWE-bench Lite): Run-Free 74.0% vs Run-Full 73.0% (Δ = -1.0%)
- **opencode** (SWE-bench Lite): Run-Free 7.0% vs Run-Full 6.0% (Δ = -1.0%)
- **claude_code** (SWE-bench Verified): Run-Free 64.0% vs Run-Full 67.0% (Δ = +3.0%)
- **codex** (SWE-bench Verified): Run-Free 73.0% vs Run-Full 75.0% (Δ = +2.0%)
- **opencode** (SWE-bench Verified): Run-Free 13.0% vs Run-Full 14.0% (Δ = +1.0%)

### 2. Average Difference

- Average improvement of Run-Full compared to Run-Free: **0.8%**

### 3. Conclusion

- Execution permission has **minor impact** on fix success rate (< 5%)
- Run-Free mode already achieves near-optimal performance
- Execution environment may **not be a necessary condition**, but rather an 'engineering shortcut'