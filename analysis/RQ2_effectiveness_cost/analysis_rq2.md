# RQ2: Efficiency - Pareto Frontier of Cost and Efficiency

## Research Question

**RQ2**: How much do different execution regimes impact cost (Avg Total tokens), interaction rounds (Avg Turns), and runtime (Avg Time)? Can Run-Less achieve success rates close to Run-Full at significantly lower cost (i.e., form a Pareto-optimal tradeoff)?

## Method

- Calculate average token consumption, interaction rounds, and runtime for each mode
- Use run_full as baseline, calculate relative change percentages (ΔCost%, ΔTurns%, ΔTime%)
- Plot Pareto frontier of Pass Rate vs Avg Total Tokens

## Main Findings

### 1. Claude Code Shows Significant Cost Savings

| Dataset | Mode | Avg Tokens | vs run_full |
|---------|------|------------|-------------|
| Lite | run_free | 69,046 | -56.4% |
| Lite | run_full | 158,417 | - |
| Verified | run_free | 63,490 | -61.9% |
| Verified | run_full | 166,745 | - |

Claude Code in Run-Free mode can save approximately **56-62%** of token consumption.

### 2. Codex Shows Smaller Cost Savings

| Dataset | Mode | Avg Tokens | vs run_full |
|---------|------|------------|-------------|
| Lite | run_free | 409,354 | -13.4% |
| Lite | run_full | 472,776 | - |
| Verified | run_free | 539,301 | -0.8% |
| Verified | run_full | 543,762 | - |

Codex in Run-Free mode only saves approximately **0.8-13.4%** of token consumption, far less than Claude Code.

### 3. Time Consumption Comparison

| Agent | Dataset | Run-Free | Run-Full | Savings |
|-------|---------|----------|----------|------|
| Claude Code | Lite | 531s | 1028s | 48.4% |
| Claude Code | Verified | 573s | 1234s | 53.6% |
| Codex | Lite | 570s | 618s | 7.8% |
| Codex | Verified | 724s | 723s | -0.1% |

Claude Code's time savings are proportional to token savings, while Codex shows almost no time difference.

### 4. Pareto Frontier Analysis

**Pareto optimal points on SWE-bench Lite**:
- Claude Code run_free (63.0%, 69K tokens) ✓
- Claude Code run_full (64.0%, 158K tokens) ✓
- Codex run_free (74.5%, 409K tokens) ✓
- Codex run_less_k1 (67.3%, 375K tokens) ✓

**Key Findings**:
- Claude Code run_free is the most cost-effective choice (lowest cost, near-highest performance)
- Codex run_free is Pareto optimal in the high-performance region

### 5. Efficiency Ratio Analysis

Efficiency Ratio = Token Savings / Pass Rate Difference

| Agent | Dataset | Token Savings | Pass Difference | Efficiency Ratio |
|-------|---------|------------|-----------|--------|
| Claude Code | Lite | 56.4% | +1.0% | 56.4 |
| Claude Code | Verified | 61.9% | +3.0% | 20.6 |
| Codex | Lite | 13.4% | -1.0% | 13.1 |
| Codex | Verified | 0.8% | +2.0% | 0.4 |

Claude Code's efficiency ratio is far higher than Codex, indicating Claude Code is more suitable for use in Run-Free mode.

## Conclusion

1. **Run-Free is the most cost-effective choice**
   - Average 33% token savings with only 1.2% Pass Rate loss
   - For Claude Code, savings are even more significant (56-62%)

2. **No clear Pareto frontier exists**
   - Run-Less mode fails to form an effective Pareto frontier
   - In most cases, Run-Free or Run-Full are the optimal choices

3. **Significant agent differences**
   - Claude Code shows significant cost savings in Run-Free mode
   - Codex's cost is almost unaffected by execution mode

4. **Green AI perspective**
   - Run-Free mode can significantly reduce computational cost and carbon emissions
   - For cost-sensitive application scenarios, Run-Free is the preferred choice
