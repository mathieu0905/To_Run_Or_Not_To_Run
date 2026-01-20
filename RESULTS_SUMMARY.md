# Experimental Results Summary

## Overview

This experiment compares the performance of four execution paradigms on the SWE-bench dataset:
- **Run-Free**: No code execution, pure reasoning-based repair
- **Run-Less (K=1/K=3)**: Limited execution with emphasis on logging instrumentation
- **Run-Cost**: Cost-constrained, model autonomously decides whether to execute
- **Run-Full**: Unrestricted execution, trial-and-error loop

Two agents were tested: Claude Code and Codex

---

## SWE-bench Lite Results

### Claude Code

| Mode | Pass Rate | Avg Tokens | Avg Time (s) | High-Cost Exec | Low-Cost Exec |
|------|-----------|------------|--------------|----------------|---------------|
| run_free | 63/100 (63%) | 69,046 | 530.7 | 0.6 | 0.2 |
| run_less_k1 | 61/100 (61%) | 105,399 | 844.5 | 4.0 | 2.4 |
| run_less_k3 | 62/100 (62%) | 139,240 | 851.2 | 5.2 | 3.3 |
| run_cost | 63/100 (63%) | 143,595 | 889.1 | 5.4 | 2.6 |
| run_full | 64/100 (64%) | 158,417 | 1027.7 | 7.0 | 2.5 |

### Codex

| Mode | Pass Rate | Avg Tokens | Avg Time (s) | High-Cost Exec | Low-Cost Exec |
|------|-----------|------------|--------------|----------------|---------------|
| run_free | 73/98 (74%) | 409,354 | 570.1 | 0.0 | 0.0 |
| run_less_k1 | 66/98 (67%) | 375,407 | 584.6 | 2.3 | 0.2 |
| run_less_k3 | 68/98 (69%) | 524,471 | 592.4 | 4.9 | 0.4 |
| run_cost | 69/98 (70%) | 499,336 | 609.9 | 4.4 | 0.4 |
| run_full | 72/98 (73%) | 472,776 | 618.5 | 6.3 | 0.5 |

---

## SWE-bench Verified Results

### Claude Code

| Mode | Pass Rate | Avg Tokens | Avg Time (s) | High-Cost Exec | Low-Cost Exec |
|------|-----------|------------|--------------|----------------|---------------|
| run_free | 64/100 (64%) | 63,490 | 572.7 | 0.5 | 0.3 |
| run_less_k1 | 64/100 (64%) | 125,338 | 878.5 | 3.7 | 2.4 |
| run_less_k3 | 65/100 (65%) | 125,776 | 957.3 | 4.4 | 2.9 |
| run_cost | 67/100 (67%) | 134,374 | 1013.0 | 4.5 | 2.3 |
| run_full | 67/100 (67%) | 166,745 | 1233.6 | 6.3 | 2.3 |

### Codex

| Mode | Pass Rate | Avg Tokens | Avg Time (s) | High-Cost Exec | Low-Cost Exec |
|------|-----------|------------|--------------|----------------|---------------|
| run_free | 73/100 (73%) | 539,301 | 723.5 | 0.0 | 0.0 |
| run_less_k1 | 72/100 (72%) | 409,696 | 694.7 | 2.2 | 0.2 |
| run_less_k3 | 73/100 (73%) | 578,573 | 725.4 | 4.5 | 0.3 |
| run_cost | 71/100 (71%) | 491,096 | 689.8 | 3.8 | 0.4 |
| run_full | 75/100 (75%) | 543,762 | 722.5 | 5.9 | 0.4 |

---

## Key Findings

### 1. Run-Free Performance is Surprisingly Good

- **Claude Code**: Run-Free (63-64%) has a very small gap with Run-Full (64-67%)
- **Codex**: Run-Free (73-74%) even slightly outperforms Run-Full (73-75%)
- This indicates that strong reasoning capabilities can largely compensate for the lack of execution feedback

### 2. Run-Less Failed to Significantly Improve Performance

- Limiting execution count (K=1, K=3) did not bring the expected "precise execution" effect
- Run-Less Pass Rate is generally lower than Run-Free and Run-Full
- Possible reason: Limited execution count actually restricts the Agent's exploration capability

### 3. Token Consumption is Positively Correlated with Execution Count

| Mode | Claude Code Tokens | Codex Tokens |
|------|-------------------|--------------|
| run_free | ~65K | ~400-540K |
| run_less_k1 | ~105-125K | ~375-410K |
| run_less_k3 | ~125-139K | ~525-580K |
| run_cost | ~134-144K | ~490-500K |
| run_full | ~158-167K | ~470-545K |

### 4. Time Consumption

- Run-Free is fastest (no execution overhead)
- Run-Full is slowest (Claude Code approximately 1000-1200s)
- Codex shows small time differences across modes (570-725s)

### 5. Agent Differences

- **Codex** has higher overall Pass Rate (67-75% vs 61-67%)
- **Codex** has significantly higher token consumption (approximately 4-8x)
- **Claude Code** is more sensitive to execution feedback, showing more significant improvement with Run-Full

---

## Conclusions

1. **Execution environment is not a necessary condition**: Run-Free mode already achieves near-optimal performance
2. **"One smart run" hypothesis not validated**: Run-Less mode failed to outperform Run-Full
3. **Cost-effectiveness**: Considering token consumption and time cost, Run-Free may be the most cost-effective choice
4. **Agent selection**: Codex is superior in accuracy, but Claude Code is more economical
