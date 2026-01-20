# RQ4: Agent Sensitivity - Data Tables

Sensitivity analysis data for different agents regarding execution permissions.

## ΔCost% vs ΔPass Comparison Table

Calculate the changes of each mode relative to run_free using run_free as the baseline.

### SWE-bench Lite

| Agent | Mode | Pass Rate | ΔPass | Avg Tokens | ΔTokens | Avg Time | ΔTime |
|-------|------|-----------|-------|------------|---------|----------|-------|
| claude_code | run_free | 63.0% | - | 69,046 | - | 531s | - |
| claude_code | run_less_k1 | 61.0% | -2.0% | 105,399 | +52.7% | 845s | +59.1% |
| claude_code | run_less_k3 | 62.0% | -1.0% | 139,240 | +101.7% | 851s | +60.4% |
| claude_code | run_cost | 63.0% | +0.0% | 143,595 | +108.0% | 889s | +67.5% |
| claude_code | run_full | 64.0% | +1.0% | 158,417 | +129.4% | 1028s | +93.7% |
| codex | run_free | 74.5% | - | 409,354 | - | 570s | - |
| codex | run_less_k1 | 67.3% | -7.1% | 375,407 | -8.3% | 585s | +2.5% |
| codex | run_less_k3 | 69.4% | -5.1% | 524,471 | +28.1% | 592s | +3.9% |
| codex | run_cost | 70.4% | -4.1% | 499,336 | +22.0% | 610s | +7.0% |
| codex | run_full | 73.5% | -1.0% | 472,776 | +15.5% | 618s | +8.5% |

### SWE-bench Verified

| Agent | Mode | Pass Rate | ΔPass | Avg Tokens | ΔTokens | Avg Time | ΔTime |
|-------|------|-----------|-------|------------|---------|----------|-------|
| claude_code | run_free | 64.0% | - | 63,490 | - | 573s | - |
| claude_code | run_less_k1 | 64.0% | +0.0% | 125,338 | +97.4% | 878s | +53.4% |
| claude_code | run_less_k3 | 65.0% | +1.0% | 125,776 | +98.1% | 957s | +67.2% |
| claude_code | run_cost | 67.0% | +3.0% | 134,374 | +111.6% | 1013s | +76.9% |
| claude_code | run_full | 67.0% | +3.0% | 166,745 | +162.6% | 1234s | +115.4% |
| codex | run_free | 73.0% | - | 539,301 | - | 724s | - |
| codex | run_less_k1 | 72.0% | -1.0% | 409,696 | -24.0% | 695s | -4.0% |
| codex | run_less_k3 | 73.0% | +0.0% | 578,573 | +7.3% | 725s | +0.3% |
| codex | run_cost | 71.0% | -2.0% | 491,096 | -8.9% | 690s | -4.7% |
| codex | run_full | 75.0% | +2.0% | 543,762 | +0.8% | 723s | -0.1% |

## Agent Characteristics Comparison Table

### SWE-bench Lite

| Metric | claude_code | codex |
|------|------|------|
| Run-Free Pass Rate | 63.0% | 74.5% |
| Run-Full Pass Rate | 64.0% | 73.5% |
| ΔPass (Full-Free) | +1.0% | -1.0% |
| Run-Free Tokens | 69,046 | 409,354 |
| Run-Full Tokens | 158,417 | 472,776 |
| ΔTokens (Full-Free) | +129.4% | +15.5% |
| Run-Free Time | 531s | 570s |
| Run-Full Time | 1028s | 618s |
| ΔTime (Full-Free) | +93.7% | +8.5% |
| Free Input Token % | 97.0% | 97.9% |
| Full Input Token % | 98.3% | 98.2% |

### SWE-bench Verified

| Metric | claude_code | codex |
|------|------|------|
| Run-Free Pass Rate | 64.0% | 73.0% |
| Run-Full Pass Rate | 67.0% | 75.0% |
| ΔPass (Full-Free) | +3.0% | +2.0% |
| Run-Free Tokens | 63,490 | 539,301 |
| Run-Full Tokens | 166,745 | 543,762 |
| ΔTokens (Full-Free) | +162.6% | +0.8% |
| Run-Free Time | 573s | 724s |
| Run-Full Time | 1234s | 723s |
| ΔTime (Full-Free) | +115.4% | +-0.1% |
| Free Input Token % | 97.0% | 98.1% |
| Full Input Token % | 98.4% | 98.3% |

## Token Consumption Breakdown

Analysis of the distribution of Input Tokens and Output Tokens.

### SWE-bench Lite

| Agent | Mode | Input Tokens | Output Tokens | Total | Input % | Output % |
|-------|------|--------------|---------------|-------|---------|----------|
| claude_code | run_free | 66,942 | 2,103 | 69,046 | 97.0% | 3.0% |
| claude_code | run_less_k1 | 103,090 | 2,308 | 105,399 | 97.8% | 2.2% |
| claude_code | run_less_k3 | 136,680 | 2,559 | 139,240 | 98.2% | 1.8% |
| claude_code | run_cost | 141,132 | 2,463 | 143,595 | 98.3% | 1.7% |
| claude_code | run_full | 155,760 | 2,656 | 158,417 | 98.3% | 1.7% |
| codex | run_free | 400,764 | 8,589 | 409,354 | 97.9% | 2.1% |
| codex | run_less_k1 | 366,649 | 8,758 | 375,407 | 97.7% | 2.3% |
| codex | run_less_k3 | 514,425 | 10,045 | 524,471 | 98.1% | 1.9% |
| codex | run_cost | 489,971 | 9,365 | 499,336 | 98.1% | 1.9% |
| codex | run_full | 464,132 | 8,644 | 472,776 | 98.2% | 1.8% |

### SWE-bench Verified

| Agent | Mode | Input Tokens | Output Tokens | Total | Input % | Output % |
|-------|------|--------------|---------------|-------|---------|----------|
| claude_code | run_free | 61,614 | 1,876 | 63,490 | 97.0% | 3.0% |
| claude_code | run_less_k1 | 122,820 | 2,517 | 125,338 | 98.0% | 2.0% |
| claude_code | run_less_k3 | 123,146 | 2,630 | 125,776 | 97.9% | 2.1% |
| claude_code | run_cost | 131,919 | 2,455 | 134,374 | 98.2% | 1.8% |
| claude_code | run_full | 164,053 | 2,691 | 166,745 | 98.4% | 1.6% |
| codex | run_free | 529,305 | 9,996 | 539,301 | 98.1% | 1.9% |
| codex | run_less_k1 | 400,660 | 9,035 | 409,696 | 97.8% | 2.2% |
| codex | run_less_k3 | 567,645 | 10,927 | 578,573 | 98.1% | 1.9% |
| codex | run_cost | 481,301 | 9,795 | 491,096 | 98.0% | 2.0% |
| codex | run_full | 534,277 | 9,485 | 543,762 | 98.3% | 1.7% |

## Sensitivity Analysis

### Cost Sensitivity Comparison

| Agent | Dataset | ΔTokens% | ΔPass% | Sensitivity (ΔTokens/ΔPass) |
|-------|---------|----------|--------|------------------------|
| claude_code | SWE-bench Lite | +129.4% | +1.0% | 129.4 |
| codex | SWE-bench Lite | +15.5% | -1.0% | 15.2 |
| claude_code | SWE-bench Verified | +162.6% | +3.0% | 54.2 |
| codex | SWE-bench Verified | +0.8% | +2.0% | 0.4 |

## Key Findings

### 1. Claude Code Characteristics

- Average Token Growth (Free→Full): **+146.0%**
- Average Pass Rate Change: **+2.0%**
- Average Run-Free Token Consumption: **66,268**
- Characteristic: **Cost-Sensitive** - Execution permissions significantly increase costs, but benefits are limited

### 2. Codex Characteristics

- Average Token Growth (Free→Full): **+8.2%**
- Average Pass Rate Change: **+0.5%**
- Average Run-Free Token Consumption: **474,328**
- Characteristic: **Cost-Stable** - Execution permissions have minimal impact on costs

### 3. Analysis of Differences

**Reasons for Claude Code's Cost Sensitivity:**
- Token consumption in Run-Free mode is relatively low (~65K), indicating concise reasoning process
- Execution feedback leads to more interaction rounds and context accumulation
- Execution results need to be parsed and processed, increasing Input Tokens

**Reasons for Codex's Cost Stability:**
- Token consumption in Run-Free mode is already very high (~400-500K)
- The model's reasoning process is inherently verbose
- Marginal impact of execution feedback on overall Token consumption is small

### 4. Conclusion

- **Impact of execution permissions varies across different agents**
- Claude Code is more sensitive to execution permissions (large cost changes)
- Codex is less sensitive to execution permissions (small cost changes)
- Cost sensitivity should be considered when selecting an agent