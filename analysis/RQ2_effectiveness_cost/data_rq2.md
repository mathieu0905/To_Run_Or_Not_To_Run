# RQ2: Efficiency - Data Tables

Cost and efficiency Pareto frontier analysis data.

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
| codex | run_less_k1 | 375,407 | 40.1 | 584.6 | 1.1 | 0.1 |
| codex | run_less_k3 | 524,471 | 46.8 | 592.4 | 2.4 | 0.2 |
| codex | run_cost | 499,336 | 44.9 | 609.9 | 2.2 | 0.2 |
| codex | run_full | 472,776 | 44.1 | 618.5 | 3.2 | 0.3 |
| opencode | run_free | 195,342 | 8.0 | 585.0 | 0.3 | 0.5 |
| opencode | run_less_k1 | 363,359 | 12.8 | 918.9 | 13.1 | 1.8 |
| opencode | run_less_k3 | 350,272 | 12.8 | 1051.5 | 11.5 | 1.3 |
| opencode | run_cost | 445,311 | 15.4 | 1052.1 | 9.6 | 4.6 |
| opencode | run_full | 266,345 | 11.0 | 1032.5 | 9.4 | 2.2 |

### SWE-bench Verified

| Agent | Mode | Avg Tokens | Avg Turns | Avg Time (s) | High-Cost Exec | Low-Cost Exec |
|-------|------|------------|-----------|--------------|----------------|---------------|
| claude_code | run_free | 63,490 | 32.7 | 572.7 | 0.5 | 0.3 |
| claude_code | run_less_k1 | 125,338 | 52.6 | 878.5 | 3.7 | 2.4 |
| claude_code | run_less_k3 | 125,776 | 53.6 | 957.3 | 4.4 | 2.9 |
| claude_code | run_cost | 134,374 | 56.6 | 1013.0 | 4.5 | 2.3 |
| claude_code | run_full | 166,745 | 68.7 | 1233.6 | 6.3 | 2.3 |
| codex | run_free | 539,301 | 46.5 | 723.5 | 0.0 | 0.0 |
| codex | run_less_k1 | 409,696 | 41.3 | 694.7 | 1.1 | 0.1 |
| codex | run_less_k3 | 578,573 | 50.3 | 725.4 | 2.2 | 0.2 |
| codex | run_cost | 491,096 | 44.9 | 689.8 | 1.9 | 0.2 |
| codex | run_full | 543,762 | 46.3 | 722.5 | 3.0 | 0.2 |
| opencode | run_free | 109,313 | 5.6 | 401.7 | 0.0 | 0.0 |
| opencode | run_less_k1 | 336,866 | 12.8 | 1016.6 | 11.5 | 1.0 |
| opencode | run_less_k3 | 350,743 | 13.0 | 1104.9 | 11.6 | 0.5 |
| opencode | run_cost | 393,991 | 14.0 | 1117.6 | 11.0 | 1.3 |
| opencode | run_full | 337,273 | 12.5 | 1231.6 | 10.6 | 0.8 |

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
| opencode | run_free | -26.7% | -27.7% | -43.3% |
| opencode | run_less_k1 | +36.4% | +15.9% | -11.0% |
| opencode | run_less_k3 | +31.5% | +16.1% | +1.8% |
| opencode | run_cost | +67.2% | +40.0% | +1.9% |
| opencode | run_full | - | - | - |

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
| opencode | run_free | -67.6% | -55.1% | -67.4% |
| opencode | run_less_k1 | -0.1% | +2.3% | -17.5% |
| opencode | run_less_k3 | +4.0% | +3.9% | -10.3% |
| opencode | run_cost | +16.8% | +11.7% | -9.3% |
| opencode | run_full | - | - | - |

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
| codex | run_free | 74.0 | 409,354 | ✓ |
| codex | run_less_k1 | 68.0 | 375,407 | ✓ |
| codex | run_less_k3 | 69.0 | 524,471 |  |
| codex | run_cost | 71.0 | 499,336 |  |
| codex | run_full | 73.0 | 472,776 |  |
| opencode | run_free | 7.0 | 195,342 |  |
| opencode | run_less_k1 | 14.0 | 363,359 |  |
| opencode | run_less_k3 | 7.0 | 350,272 |  |
| opencode | run_cost | 9.0 | 445,311 |  |
| opencode | run_full | 6.0 | 266,345 |  |

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
| opencode | run_free | 13.0 | 109,313 |  |
| opencode | run_less_k1 | 17.0 | 336,866 |  |
| opencode | run_less_k3 | 11.0 | 350,743 |  |
| opencode | run_cost | 13.0 | 393,991 |  |
| opencode | run_full | 14.0 | 337,273 |  |

## Efficiency Analysis

### SWE-bench Lite

**claude_code:**

- Run-Free vs Run-Full:
  - Pass Rate 差异: +1.0%
  - Token 节省: 56.4%
  - 时间节省: 48.4%
  - Efficiency ratio (Token saving/Pass difference): 56.4

**codex:**

- Run-Free vs Run-Full:
  - Pass Rate 差异: -1.0%
  - Token 节省: 13.4%
  - 时间节省: 7.8%
  - Efficiency ratio (Token saving/Pass difference): 13.4

**opencode:**

- Run-Free vs Run-Full:
  - Pass Rate 差异: -1.0%
  - Token 节省: 26.7%
  - 时间节省: 43.3%
  - Efficiency ratio (Token saving/Pass difference): 26.7

### SWE-bench Verified

**claude_code:**

- Run-Free vs Run-Full:
  - Pass Rate 差异: +3.0%
  - Token 节省: 61.9%
  - 时间节省: 53.6%
  - Efficiency ratio (Token saving/Pass difference): 20.6

**codex:**

- Run-Free vs Run-Full:
  - Pass Rate 差异: +2.0%
  - Token 节省: 0.8%
  - 时间节省: -0.1%
  - Efficiency ratio (Token saving/Pass difference): 0.4

**opencode:**

- Run-Free vs Run-Full:
  - Pass Rate 差异: +1.0%
  - Token 节省: 67.6%
  - 时间节省: 67.4%
  - Efficiency ratio (Token saving/Pass difference): 67.6

## Key Findings

### 1. Token Consumption Comparison

- **claude_code** (SWE-bench Lite): Run-Free 69,046 vs Run-Full 158,417 (saving 56.4%)
- **codex** (SWE-bench Lite): Run-Free 409,354 vs Run-Full 472,776 (saving 13.4%)
- **opencode** (SWE-bench Lite): Run-Free 195,342 vs Run-Full 266,345 (saving 26.7%)
- **claude_code** (SWE-bench Verified): Run-Free 63,490 vs Run-Full 166,745 (saving 61.9%)
- **codex** (SWE-bench Verified): Run-Free 539,301 vs Run-Full 543,762 (saving 0.8%)
- **opencode** (SWE-bench Verified): Run-Free 109,313 vs Run-Full 337,273 (saving 67.6%)

### 2. Time Consumption Comparison

- **claude_code** (SWE-bench Lite): Run-Free 531s vs Run-Full 1028s (saving 48.4%)
- **codex** (SWE-bench Lite): Run-Free 570s vs Run-Full 618s (saving 7.8%)
- **opencode** (SWE-bench Lite): Run-Free 585s vs Run-Full 1033s (saving 43.3%)
- **claude_code** (SWE-bench Verified): Run-Free 573s vs Run-Full 1234s (saving 53.6%)
- **codex** (SWE-bench Verified): Run-Free 724s vs Run-Full 723s (saving -0.1%)
- **opencode** (SWE-bench Verified): Run-Free 402s vs Run-Full 1232s (saving 67.4%)

### 3. Cost-Benefit Conclusion

- Average Token saving: **37.8%**
- Average time saving: **36.7%**
- Average Pass Rate difference: **+0.8%**

**Conclusion**: Run-Free mode trades 0.8% performance loss for 38% cost savings, making it the most cost-effective choice.