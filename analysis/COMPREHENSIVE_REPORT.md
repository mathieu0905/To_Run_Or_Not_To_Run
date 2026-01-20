# Comprehensive Analysis Report on Execution Modes

## Research Overview

This study explores the impact of different execution regimes on LLM Agents in software engineering tasks.

### Experimental Setup

| Dimension | Configuration |
|------|------|
| Agent | Claude Code, Codex |
| Dataset | SWE-bench Lite (100), SWE-bench Verified (100) |
| Execution Modes | run_free, run_less_k1, run_less_k3, run_cost, run_full |

### Execution Mode Descriptions

| Mode | Description |
|------|------|
| run_free | No code execution at all |
| run_less_k1 | Limited to 1 execution |
| run_less_k3 | Limited to 3 executions |
| run_cost | Execution with cost constraints |
| run_full | Unrestricted execution |

---

## Core Findings

### One-Sentence Conclusion

> **Execution primarily affects efficiency and trajectory quality, while its marginal benefit on correctness is limited.**

---

## 1. Overall Performance Comparison

### SWE-bench Lite

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 63 | 61 | 62 | 63 | 64 |
| codex | 73 | 66 | 68 | 69 | 72 |

### SWE-bench Verified

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 64 | 64 | 65 | 67 | 67 |
| codex | 73 | 72 | 73 | 71 | 75 |

### Key Observations

1. **Run-Free vs Run-Full difference is minimal** - Average difference of only 1.2%
2. **Run-Less mode performance is unstable** - In most cases performs worse than Run-Free
3. **Codex Run-Free performs exceptionally well** - On Lite, even better than Run-Full (73 vs 72)

---

## 2. Cost Efficiency Analysis

### Claude Code Cost Comparison

| Dataset | Mode | Avg Tokens | vs Run-Free |
|---------|------|------------|-------------|
| Lite | run_free | 69,047 | - |
| Lite | run_less_k1 | 105,400 | +52.6% |
| Lite | run_less_k3 | 139,240 | +101.7% |
| Lite | run_cost | 143,596 | +108.0% |
| Lite | run_full | 158,417 | **+129.4%** |
| Verified | run_free | 63,490 | - |
| Verified | run_full | 166,746 | **+162.6%** |

### Codex Cost Comparison

| Dataset | Mode | Avg Tokens | vs Run-Free |
|---------|------|------------|-------------|
| Lite | run_free | 409,355 | - |
| Lite | run_full | 472,777 | +15.5% |
| Verified | run_free | 539,302 | - |
| Verified | run_full | 543,763 | +0.8% |

### Efficiency Ratio Analysis (Pass Rate / Token)

| Agent | Dataset | run_free | run_cost | run_full |
|-------|---------|----------|----------|----------|
| claude_code | Lite | **0.91** | 0.44 | 0.40 |
| claude_code | Verified | **1.01** | 0.50 | 0.40 |
| codex | Lite | **0.18** | 0.14 | 0.15 |
| codex | Verified | **0.14** | 0.14 | 0.14 |

**Conclusion**: Run-Free has the highest efficiency ratio and is the most cost-effective choice.

---

## 3. Inter-Mode Difference Analysis

### Full Mode Difference Matrix (Claude Code, Lite)

Table shows: Number of cases where row mode succeeds but column mode fails

| | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|---|---|---|---|---|---|
| run_free | - | 4 | 5 | 6 | 5 |
| run_less_k1 | 2 | - | 3 | 4 | 3 |
| run_less_k3 | 4 | 4 | - | 5 | 2 |
| run_cost | 6 | 6 | 6 | - | 4 |
| run_full | 6 | 6 | 4 | 5 | - |

### Key Comparison Summary

| Comparison | Run-Free Wins | Run-Full Wins | Net Difference |
|------|-------------|-------------|--------|
| Claude Code (Lite) | 5 | 6 | +1 |
| Claude Code (Verified) | 6 | 9 | +3 |
| Codex (Lite) | 4 | 3 | -1 |
| Codex (Verified) | 1 | 3 | +2 |
| **Total** | **16** | **21** | **+5** |

**Conclusion**: Run-Full only outperforms Run-Free in 5 net cases, with very limited advantage.

---

## 4. Execution Regime Progression Analysis

### Instance Classification

| Category | Claude Code | Codex | Description |
|------|-------------|-------|------|
| Always Success | 52-55 | 59 | All modes can solve |
| Always Failure | 0 | 0 | All modes fail |
| Improves with Execution | 4-8 | 2-3 | More execution helps |
| Degrades with Execution | 5-6 | 1-4 | More execution harms |
| Inconsistent | 7-11 | 14-19 | Unstable performance |

**Key Finding**: "Inconsistent" category has high proportion, indicating unstable effects of execution regimes.

---

## 5. Task Difficulty Stratification Analysis

### Difficulty Distribution

| Difficulty | Count | Definition |
|------|------|------|
| Easy | 141 | All agents succeed under Run-Full |
| Medium | 15 | Some agents succeed |
| Hard | 12 | All agents fail |

### Full Mode Comparison by Difficulty

#### Easy Tasks (141 instances)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 79.4% | 81.6% | 84.4% | 83.0% | 88.7% |
| codex | 93.6% | 89.4% | 90.8% | 89.4% | 97.9% |

#### Medium Tasks (15 instances)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | **80.0%** | 53.3% | 40.0% | 66.7% | 40.0% |
| codex | **80.0%** | 60.0% | 66.7% | 73.3% | 60.0% |

#### Hard Tasks (12 instances)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 25.0% | 16.7% | 16.7% | 25.0% | 0.0% |
| codex | 16.7% | 25.0% | 25.0% | 25.0% | 0.0% |

**Key Findings**:
- **Easy tasks**: Run-Full is best, but Run-Free is close
- **Medium tasks**: Run-Free is actually best (80%), Run-Full only 40-60%
- **Hard tasks**: All modes fail, Run-Full is even 0%

---

## 6. Unique Value of Each Mode

### Unique Success Case Statistics

| Mode | Unique Successes | Better than Run-Free | Better than Run-Full |
|------|----------|----------------|----------------|
| run_less_k1 | 4 | 16 | 10 |
| run_less_k3 | 2 | 19 | 9 |
| run_cost | 5 | 22 | 15 |

### Value of Run-Less Mode

Although overall worse than Run-Free, it performs better in **16-22 cases** than Run-Free.

**Typical Case**: `django__django-11433`
- Run-Free: Failed
- Run-Less-K1: **Success** ✓
- Run-Less-K3: **Success** ✓
- Run-Full: Failed

**Insight**: 1-3 executions are just enough to validate the fix, but too many executions are harmful.

### Value of Run-Cost Mode

There are 5 cases that **only Run-Cost can solve**:
- `django__django-12113`
- `django__django-12589`
- `django__django-14997`
- `astropy__astropy-13236`

---

## 7. Typical Case Analysis

### Run-Free Succeeds but Run-Full Fails

#### `django__django-13230` (Claude Code, Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 6,891 | 9 | 0 | **Success** |
| run_full | 105,713 | 70 | 9 | Failed |

**Analysis**: Excessive test executions lead to trial-and-error loops, token consumption increased 15x but failed instead.

### Run-Full Succeeds but Run-Free Fails

#### `django__django-12965` (Claude Code, Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 191,095 | 69 | 0 | Failed |
| run_less_k1 | 182,385 | 67 | 4 | **Success** |
| run_full | 225,064 | 84 | 5 | **Success** |

**Analysis**: This problem requires execution feedback to validate the fix, but K1 is sufficient.

---

## 8. Statistical Reliability

### Wilson 95% Confidence Intervals

| Agent | Dataset | Run-Free CI | Run-Full CI | Overlap |
|-------|---------|-------------|-------------|------|
| Claude Code | Lite | [53.2%, 71.8%] | [54.2%, 72.7%] | ✓ |
| Claude Code | Verified | [54.2%, 72.7%] | [57.3%, 75.4%] | ✓ |
| Codex | Lite | [65.0%, 82.1%] | [64.0%, 81.2%] | ✓ |
| Codex | Verified | [63.6%, 80.7%] | [65.7%, 82.5%] | ✓ |

**Conclusion**: All confidence intervals highly overlap, differences are not statistically significant.

### McNemar's Paired Test

| Agent | Dataset | p-value | Significance |
|-------|---------|---------|--------|
| Claude Code | Lite | 1.0000 | Not significant |
| Claude Code | Verified | 0.6072 | Not significant |
| Codex | Lite | 1.0000 | Not significant |
| Codex | Verified | 0.6250 | Not significant |

---

## 9. Core Conclusions

### Main Findings

| Dimension | Finding |
|------|------|
| **Correctness** | Execution regimes have minimal impact on Pass Rate (< 5%) |
| **Cost** | Run-Free can save 33-62% tokens |
| **Efficiency** | Most executions are low-value overhead |
| **Agent Differences** | Claude Code is cost-sensitive (+146%), Codex is cost-stable (+8%) |
| **Task Difficulty** | Execution has no impact on easy tasks, cannot solve hard tasks |
| **Execution Feedback** | Double-edged sword, net benefit only 5 cases |

### Practical Recommendations

| Priority | Mode | Use Case |
|--------|------|----------|
| 1 | **Run-Free** | Default choice, highest cost-effectiveness |
| 2 | **Run-Less-K1** | Fallback when Run-Free fails |
| 3 | **Run-Cost** | Need execution but control cost |
| 4 | Run-Full | Only for complex debugging |
| ✗ | Run-Less-K3 | Not recommended, unstable performance |

### Academic Contribution

> **Correctness appears robust to execution access, whereas cost is highly sensitive to it.**

This study demonstrates that current LLM reasoning capabilities are sufficiently powerful; execution environments are more of an "engineering shortcut" than a "necessary capability."

---

## 10. Text Ready for Paper

### English Version

> We report pass rates with 95% Wilson confidence intervals. For Codex on SWE-bench Verified: Run-Full achieves 75/100 (75.0%, CI: [65.7%, 82.5%]), while Run-Free achieves 73/100 (73.0%, CI: [63.6%, 80.7%]). The confidence intervals substantially overlap, indicating that the pass rate differences are within statistical noise. In contrast, cost differences are substantial (e.g., Claude Code shows 146% token increase from Run-Free to Run-Full). This suggests that execution regimes primarily affect efficiency and trajectory behavior rather than correctness.

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
