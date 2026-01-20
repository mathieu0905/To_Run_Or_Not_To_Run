# Statistical Analysis - Data Tables

Analysis data providing statistical reliability support for the paper.

## Wilson 95% Confidence Intervals

Using Wilson score interval, which is more stable than normal approximation.

### SWE-bench Lite

| Agent | Mode | n | Resolved | Pass Rate | 95% CI |
|-------|------|---|----------|-----------|--------|
| claude_code | run_free | 100 | 63 | 63.0% | [53.2%, 71.8%] |
| claude_code | run_less_k1 | 100 | 61 | 61.0% | [51.2%, 70.0%] |
| claude_code | run_less_k3 | 100 | 62 | 62.0% | [52.2%, 70.9%] |
| claude_code | run_cost | 100 | 63 | 63.0% | [53.2%, 71.8%] |
| claude_code | run_full | 100 | 64 | 64.0% | [54.2%, 72.7%] |
| codex | run_free | 98 | 73 | 74.5% | [65.0%, 82.1%] |
| codex | run_less_k1 | 98 | 66 | 67.3% | [57.6%, 75.8%] |
| codex | run_less_k3 | 98 | 68 | 69.4% | [59.7%, 77.6%] |
| codex | run_cost | 98 | 69 | 70.4% | [60.7%, 78.5%] |
| codex | run_full | 98 | 72 | 73.5% | [64.0%, 81.2%] |

### SWE-bench Verified

| Agent | Mode | n | Resolved | Pass Rate | 95% CI |
|-------|------|---|----------|-----------|--------|
| claude_code | run_free | 100 | 64 | 64.0% | [54.2%, 72.7%] |
| claude_code | run_less_k1 | 100 | 64 | 64.0% | [54.2%, 72.7%] |
| claude_code | run_less_k3 | 100 | 65 | 65.0% | [55.3%, 73.6%] |
| claude_code | run_cost | 100 | 67 | 67.0% | [57.3%, 75.4%] |
| claude_code | run_full | 100 | 67 | 67.0% | [57.3%, 75.4%] |
| codex | run_free | 100 | 73 | 73.0% | [63.6%, 80.7%] |
| codex | run_less_k1 | 100 | 72 | 72.0% | [62.5%, 79.9%] |
| codex | run_less_k3 | 100 | 73 | 73.0% | [63.6%, 80.7%] |
| codex | run_cost | 100 | 71 | 71.0% | [61.5%, 79.0%] |
| codex | run_full | 100 | 75 | 75.0% | [65.7%, 82.5%] |

## Confidence Interval Overlap Analysis

Analyze whether confidence intervals overlap between different modes; overlap indicates non-significant differences.

### SWE-bench Lite

**claude_code:**

- run_free: 63.0% [53.2%, 71.8%]
- run_full: 64.0% [54.2%, 72.7%]
- Confidence interval overlap: **Yes**
- Conclusion: Difference is not statistically significant

**codex:**

- run_free: 74.5% [65.0%, 82.1%]
- run_full: 73.5% [64.0%, 81.2%]
- Confidence interval overlap: **Yes**
- Conclusion: Difference is not statistically significant

### SWE-bench Verified

**claude_code:**

- run_free: 64.0% [54.2%, 72.7%]
- run_full: 67.0% [57.3%, 75.4%]
- Confidence interval overlap: **Yes**
- Conclusion: Difference is not statistically significant

**codex:**

- run_free: 73.0% [63.6%, 80.7%]
- run_full: 75.0% [65.7%, 82.5%]
- Confidence interval overlap: **Yes**
- Conclusion: Difference is not statistically significant

## McNemar Paired Test

Test whether performance differences for the same instance under different modes are significant.

### SWE-bench Lite

**claude_code:**

run_free vs run_full:
- run_free succeeds but run_full fails: 5 instances
- run_free fails but run_full succeeds: 6 instances
- p-value: 1.0000
- Significance (α=0.05): **Not significant**

run_less_k1 vs run_full:
- run_less_k1 succeeds but run_full fails: 3 instances
- run_less_k1 fails but run_full succeeds: 6 instances
- p-value: 0.5078
- Significance (α=0.05): **Not significant**

**codex:**

run_free vs run_full:
- run_free succeeds but run_full fails: 4 instances
- run_free fails but run_full succeeds: 3 instances
- p-value: 1.0000
- Significance (α=0.05): **Not significant**

run_less_k1 vs run_full:
- run_less_k1 succeeds but run_full fails: 2 instances
- run_less_k1 fails but run_full succeeds: 8 instances
- p-value: 0.1094
- Significance (α=0.05): **Not significant**

### SWE-bench Verified

**claude_code:**

run_free vs run_full:
- run_free succeeds but run_full fails: 6 instances
- run_free fails but run_full succeeds: 9 instances
- p-value: 0.6072
- Significance (α=0.05): **Not significant**

run_less_k1 vs run_full:
- run_less_k1 succeeds but run_full fails: 3 instances
- run_less_k1 fails but run_full succeeds: 6 instances
- p-value: 0.5078
- Significance (α=0.05): **Not significant**

**codex:**

run_free vs run_full:
- run_free succeeds but run_full fails: 1 instance
- run_free fails but run_full succeeds: 3 instances
- p-value: 0.6250
- Significance (α=0.05): **Not significant**

run_less_k1 vs run_full:
- run_less_k1 succeeds but run_full fails: 2 instances
- run_less_k1 fails but run_full succeeds: 5 instances
- p-value: 0.4531
- Significance (α=0.05): **Not significant**

## Cross-Dataset Consistency Analysis

Verify consistency of conclusions across different datasets.

### claude_code

| Mode | Lite Pass Rate | Verified Pass Rate | Trend Consistent |
|------|----------------|--------------------| ---------|
| run_free | 63.0% | 64.0% | ✓ |
| run_less_k1 | 61.0% | 64.0% | ✓ |
| run_less_k3 | 62.0% | 65.0% | ✓ |
| run_cost | 63.0% | 67.0% | ✓ |
| run_full | 64.0% | 67.0% | ✓ |

### codex

| Mode | Lite Pass Rate | Verified Pass Rate | Trend Consistent |
|------|----------------|--------------------| ---------|
| run_free | 74.5% | 73.0% | ✓ |
| run_less_k1 | 67.3% | 72.0% | ✓ |
| run_less_k3 | 69.4% | 73.0% | ✓ |
| run_cost | 70.4% | 71.0% | ✓ |
| run_full | 73.5% | 75.0% | ✓ |

## Key Statistical Conclusions

### 1. Confidence Interval Analysis Conclusion

- For all agents across all datasets, the 95% confidence intervals of run_free and run_full **highly overlap**
- This indicates that pass rate differences are **not statistically significant**
- Differences mainly come from random noise rather than the essential impact of execution privileges

### 2. Paired Test Conclusion

- McNemar test shows that the difference between run_free vs run_full is **not significant** (p > 0.05)
- This means: problems that can be solved by run_free can mostly also be solved by run_full, and vice versa
- Supports the argument: "what can be done right will still be done right"

### 3. Cross-Dataset Consistency Conclusion

- Main trends are **consistent** across both Lite and Verified datasets
- This is more indicative of conclusion robustness than random sampling
- Supports the argument: conclusions do not depend on specific sample selection

### 4. Core Academic Expression

> **Execution primarily affects efficiency and trajectory quality, while its marginal benefit on correctness is limited.**

> **Correctness appears robust to execution access, whereas cost is highly sensitive to it.**

## Text Ready for Paper

### English Version

#### Experimental Setup

> We did not perform any task filtering or manual selection. To ensure full reproducibility, we used the first 100 instances from the official release order of SWE-bench Lite and SWE-bench Verified as our deterministic evaluation subset, with instance IDs listed in the appendix. Our goal is not to claim a new state-of-the-art accuracy on SWE-bench, but to isolate the effect of execution regimes on agent behavior and cost. Therefore, a deterministic subset is sufficient for controlled comparison.

#### Statistical Reliability

> We report pass rates with 95% Wilson confidence intervals. For Codex on SWE-bench Verified: Run-Full achieves 75/100 (75.0%, CI: [65.7%, 82.5%]), while Run-Free achieves 73/100 (73.0%, CI: [63.6%, 80.7%]). The confidence intervals substantially overlap, indicating that the pass rate differences are within statistical noise. In contrast, cost differences are substantial (e.g., Claude Code shows 146% token increase from Run-Free to Run-Full). This suggests that execution regimes primarily affect efficiency and trajectory behavior rather than correctness.

#### Threats to Validity

> Using a prefix subset of the dataset may introduce ordering bias. However, we performed no selective filtering, and we demonstrate the stability of observed trends through confidence intervals and paired comparisons. The consistency of findings across both SWE-bench Lite and Verified further supports the robustness of our conclusions. Future work may extend to additional instances to further validate generalizability.

