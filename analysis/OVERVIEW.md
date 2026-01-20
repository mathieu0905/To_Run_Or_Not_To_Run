# Experimental Analysis Overview

## Research Background

This study explores the impact of **Execution Regimes** on LLM Agents in software engineering tasks. We compared 5 execution modes:

| Mode | Description |
|------|------|
| Run-Free | No code execution at all |
| Run-Less-K1 | Limited to 1 execution |
| Run-Less-K3 | Limited to 3 executions |
| Run-Cost | Execution with cost constraints |
| Run-Full | Unrestricted execution |

**Experimental Setup**:
- Agent: Claude Code, Codex
- Dataset: SWE-bench Lite (100 instances), SWE-bench Verified (100 instances)
- Evaluation Metrics: Pass Rate, Token Consumption, Execution Count, Runtime

---

## Core Findings Summary

### One-Sentence Conclusion

> **Execution primarily affects efficiency and trajectory quality, while its marginal benefit on correctness is limited.**

---

## RQ1: Effectiveness - Impact of Execution Regimes on Success Rate

**Research Question**: What impact do Run-Free, Run-Less, and Run-Full have on repair success rate?

### Core Data

| Agent | Dataset | Run-Free | Run-Full | ΔPass |
|-------|---------|----------|----------|-------|
| Claude Code | Lite | 63.0% | 64.0% | +1.0% |
| Claude Code | Verified | 64.0% | 67.0% | +3.0% |
| Codex | Lite | 74.5% | 73.5% | -1.0% |
| Codex | Verified | 73.0% | 75.0% | +2.0% |

**Average Difference**: Run-Full improves over Run-Free by only **1.2%**

### Key Findings

1. **Execution regimes have minimal impact on success rate** - Differences are within statistical noise
2. **No monotonic "more execution = better" relationship** - Only 1 out of 4 experiments showed monotonic increase
3. **Run-Less mode underperforms expectations** - Limiting execution count generally performs worse than Run-Free
4. **Codex Run-Free performs exceptionally well** - Even slightly better than Run-Full (74.5% vs 73.5%)

### Conclusion

> Execution environment is not a necessary condition; Run-Free already achieves near-optimal performance (gap < 5%)

---

## RQ2: Efficiency - Pareto Frontier of Cost and Efficiency

**Research Question**: How much do different execution regimes impact cost?

### Core Data

| Agent | Dataset | Run-Free Tokens | Run-Full Tokens | Savings |
|-------|---------|-----------------|-----------------|------|
| Claude Code | Lite | 69K | 158K | **56.4%** |
| Claude Code | Verified | 63K | 167K | **61.9%** |
| Codex | Lite | 409K | 473K | 13.4% |
| Codex | Verified | 539K | 544K | 0.8% |

### Key Findings

1. **Run-Free is the most cost-effective choice** - Average 33% token savings with only 1.2% Pass Rate loss
2. **Claude Code shows significant cost savings** - 56-62% token savings
3. **Codex cost is nearly unaffected by execution mode** - Only 0.8-13% variation
4. **Time savings proportional to token savings** - Claude Code saves 48-54% time

### Conclusion

> Run-Free mode can significantly reduce computational cost and carbon emissions, making it the preferred choice for cost-sensitive scenarios

---

## RQ3: Execution Utility - Purpose Analysis of Execution Behavior

**Research Question**: What are executions primarily used for? Which are high-value executions?

### Core Data

**Claude Code Execution Distribution (Lite):**

| Mode | Total Exec | Validation | Localization | Environment | Exploration |
|------|--------|------|------|------|------|
| run_free | 693 | 8.5% | 2.3% | 6.3% | **71.1%** |
| run_full | 1804 | **39.0%** | 13.2% | 19.0% | 20.8% |

### Key Findings

1. **Validation is the primary execution purpose** - 35-40% of executions in Run-Full mode
2. **Exploration executions are high in proportion but low in value** - Can be replaced by static analysis
3. **Trial-and-error loops are prevalent** - Codex has ~2000 repeated commands
4. **Execution efficiency is extremely low** - Each validation execution brings < 0.01% Pass Rate improvement

### Conclusion

> Most executions are "low-value overhead"; validation executions have value but extremely low marginal benefit

---

## RQ4: Agent Sensitivity - Sensitivity Differences Across Agents

**Research Question**: Is the impact of execution regimes consistent across different agents?

### Core Data

| Agent | ΔTokens% (Free→Full) | ΔPass% | Sensitivity Ratio |
|-------|----------------------|--------|----------|
| Claude Code | +129% ~ +163% | +1% ~ +3% | **54-129** |
| Codex | +0.8% ~ +15% | -1% ~ +2% | **0.4-15** |

### Key Findings

1. **Claude Code is cost-sensitive** - Execution regimes significantly increase cost (+146%)
2. **Codex is cost-stable** - Execution regimes have minimal cost impact (+8%)
3. **Base cost determines sensitivity** - Claude Code has low base cost (65K), Codex has high base cost (470K)
4. **Different agents need different execution strategies** - "One size fits all" doesn't apply

### Conclusion

> For cost-effectiveness, Claude Code + Run-Free is the optimal choice

---

## RQ5: Failure Modes - Failure Mode Analysis

**Research Question**: What typical failure modes are induced by different execution regimes?

### Core Data

| Type | Count |
|------|------|
| Run-Free succeeds but Run-Full fails | 16 |
| Run-Full succeeds but Run-Free fails | 21 |
| **Net difference (Run-Full advantage)** | **5** |

### Key Findings

1. **Failure mode differences are minimal** - Run-Free and Run-Full have similar failure counts
2. **Execution feedback is a double-edged sword** - In 16 cases, execution feedback actually led to failure
3. **Net benefit is only 5 cases** - Run-Full's advantage is very limited
4. **Run-Free failures are easier to debug** - Shorter traces, more direct causes

### Conclusion

> Execution feedback is not always beneficial; Run-Free failures have lower debugging burden

---

## Statistical Reliability

### Wilson 95% Confidence Intervals

For all agents across all datasets, the 95% confidence intervals of Run-Free and Run-Full **highly overlap**:

| Agent | Dataset | Run-Free CI | Run-Full CI | Overlap |
|-------|---------|-------------|-------------|------|
| Claude Code | Lite | [53.2%, 71.8%] | [54.2%, 72.7%] | ✓ |
| Codex | Verified | [63.6%, 80.7%] | [65.7%, 82.5%] | ✓ |

### McNemar's Paired Test

All comparisons have p-value > 0.05, differences are **not significant**:

| Agent | Dataset | b (Free wins) | c (Full wins) | p-value |
|-------|---------|------------|------------|---------|
| Claude Code | Lite | 5 | 6 | 1.0000 |
| Codex | Verified | 1 | 3 | 0.6250 |

### Cross-Dataset Consistency

Main trends are **consistent** across both Lite and Verified datasets, supporting the robustness of conclusions.

---

## Summary and Recommendations

### Core Conclusions

| Dimension | Finding |
|------|------|
| **Correctness** | Execution regimes have minimal impact on Pass Rate (< 5%) |
| **Cost** | Run-Free can save 33-62% tokens |
| **Efficiency** | Most executions are low-value overhead |
| **Agent Differences** | Claude Code is cost-sensitive, Codex is cost-stable |
| **Failure Modes** | Execution feedback is a double-edged sword with limited net benefit |
| **Task Difficulty** | Execution has no impact on simple tasks, cannot solve difficult tasks |

### Practical Recommendations

1. **Use Run-Free by default** - Highest cost-effectiveness
2. **Claude Code + Run-Free** - Optimal cost-effectiveness combination
3. **Use Run-Full only when necessary** - Complex problems requiring environment validation
4. **Run-Less not recommended** - Performs worse than Run-Free

### Academic Contribution

> **Correctness appears robust to execution access, whereas cost is highly sensitive to it.**

This study demonstrates that current LLM reasoning capabilities are sufficiently powerful; execution environments are more of an "engineering shortcut" than a "necessary capability."

---

## File Index

| File | Description |
|------|------|
| [RQ1_effectiveness/](./RQ1_effectiveness/) | Impact of execution regimes on success rate |
| [RQ2_efficiency/](./RQ2_efficiency/) | Pareto frontier of cost and efficiency |
| [RQ3_execution_utility/](./RQ3_execution_utility/) | Purpose analysis of execution behavior |
| [RQ4_agent_sensitivity/](./RQ4_agent_sensitivity/) | Sensitivity differences across agents |
| [RQ5_failure_modes/](./RQ5_failure_modes/) | Failure mode analysis |
| [RQ6_case_study/](./RQ6_case_study/) | Case studies and task difficulty stratification |
| [common/data_statistical.md](./common/data_statistical.md) | Statistical analysis data |
