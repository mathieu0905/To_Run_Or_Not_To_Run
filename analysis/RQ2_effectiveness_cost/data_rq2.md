# RQ2: Efficiency - Data Tables

Pareto frontier analysis data for cost and efficiency.

## Cost Comparison Table

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

## Relative Change Percentage Table (vs run_full)

Using run_full as baseline, calculate cost changes for each mode. Negative values indicate cost reduction.

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

## Pareto Frontier Data

Pass Rate vs Avg Total Tokens data points for plotting Pareto frontier.

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

## Efficiency Analysis

### SWE-bench Lite

**claude_code:**

- Run-Free vs Run-Full:
  - Pass Rate difference: +1.0%
  - Token savings: 56.4%
  - Time savings: 48.4%
  - Efficiency ratio (Token savings/Pass difference): 56.4

**codex:**

- Run-Free vs Run-Full:
  - Pass Rate difference: -1.0%
  - Token savings: 13.4%
  - Time savings: 7.8%
  - Efficiency ratio (Token savings/Pass difference): 13.1

### SWE-bench Verified

**claude_code:**

- Run-Free vs Run-Full:
  - Pass Rate difference: +3.0%
  - Token savings: 61.9%
  - Time savings: 53.6%
  - Efficiency ratio (Token savings/Pass difference): 20.6

**codex:**

- Run-Free vs Run-Full:
  - Pass Rate difference: +2.0%
  - Token savings: 0.8%
  - Time savings: -0.1%
  - Efficiency ratio (Token savings/Pass difference): 0.4

## Key Findings

### 1. Token Consumption Comparison

- **claude_code** (SWE-bench Lite): Run-Free 69,046 vs Run-Full 158,417 (savings 56.4%)
- **codex** (SWE-bench Lite): Run-Free 409,354 vs Run-Full 472,776 (savings 13.4%)
- **claude_code** (SWE-bench Verified): Run-Free 63,490 vs Run-Full 166,745 (savings 61.9%)
- **codex** (SWE-bench Verified): Run-Free 539,301 vs Run-Full 543,762 (savings 0.8%)

### 2. Time Consumption Comparison

- **claude_code** (SWE-bench Lite): Run-Free 531s vs Run-Full 1028s (savings 48.4%)
- **codex** (SWE-bench Lite): Run-Free 570s vs Run-Full 618s (savings 7.8%)
- **claude_code** (SWE-bench Verified): Run-Free 573s vs Run-Full 1234s (savings 53.6%)
- **codex** (SWE-bench Verified): Run-Free 724s vs Run-Full 723s (savings -0.1%)

### 3. Cost-Effectiveness Conclusion

- Average token savings: **33.1%**
- Average time savings: **27.4%**
- Average Pass Rate difference: **+1.2%**

**Conclusion**: Run-Free mode achieves 33% cost savings in exchange for 1.2% performance loss, making it the most cost-effective choice.
