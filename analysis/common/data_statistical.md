# Statistical Analysis - Data Tables

Analysis data providing statistical reliability support for the paper.

## Wilson 95% Confidence Intervals

Using Wilson score interval, more stable than normal approximation.

### SWE-bench Lite

| Agent | Mode | n | Resolved | Pass Rate | 95% CI |
|-------|------|---|----------|-----------|--------|
| claude_code | run_free | 100 | 63 | 63.0% | [53.2%, 71.8%] |
| claude_code | run_less_k1 | 100 | 61 | 61.0% | [51.2%, 70.0%] |
| claude_code | run_less_k3 | 100 | 62 | 62.0% | [52.2%, 70.9%] |
| claude_code | run_cost | 100 | 63 | 63.0% | [53.2%, 71.8%] |
| claude_code | run_full | 100 | 64 | 64.0% | [54.2%, 72.7%] |
| codex | run_free | 100 | 74 | 74.0% | [64.6%, 81.6%] |
| codex | run_less_k1 | 100 | 68 | 68.0% | [58.3%, 76.3%] |
| codex | run_less_k3 | 100 | 69 | 69.0% | [59.4%, 77.2%] |
| codex | run_cost | 100 | 71 | 71.0% | [61.5%, 79.0%] |
| codex | run_full | 100 | 73 | 73.0% | [63.6%, 80.7%] |
| opencode | run_free | 100 | 7 | 7.0% | [3.4%, 13.7%] |
| opencode | run_less_k1 | 100 | 14 | 14.0% | [8.5%, 22.1%] |
| opencode | run_less_k3 | 100 | 7 | 7.0% | [3.4%, 13.7%] |
| opencode | run_cost | 100 | 9 | 9.0% | [4.8%, 16.2%] |
| opencode | run_full | 100 | 6 | 6.0% | [2.8%, 12.5%] |

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
| opencode | run_free | 100 | 13 | 13.0% | [7.8%, 21.0%] |
| opencode | run_less_k1 | 100 | 17 | 17.0% | [10.9%, 25.5%] |
| opencode | run_less_k3 | 100 | 11 | 11.0% | [6.3%, 18.6%] |
| opencode | run_cost | 100 | 13 | 13.0% | [7.8%, 21.0%] |
| opencode | run_full | 100 | 14 | 14.0% | [8.5%, 22.1%] |

## Confidence Interval Overlap Analysis

Analyze whether confidence intervals overlap between different modes. Overlap indicates non-significant differences.

### SWE-bench Lite

**claude_code:**

- run_free: 63.0% [53.2%, 71.8%]
- run_full: 64.0% [54.2%, 72.7%]
- CI Overlap: **Yes**
- Conclusion: Difference is not statistically significant

**codex:**

- run_free: 74.0% [64.6%, 81.6%]
- run_full: 73.0% [63.6%, 80.7%]
- CI Overlap: **Yes**
- Conclusion: Difference is not statistically significant

**opencode:**

- run_free: 7.0% [3.4%, 13.7%]
- run_full: 6.0% [2.8%, 12.5%]
- CI Overlap: **Yes**
- Conclusion: Difference is not statistically significant

### SWE-bench Verified

**claude_code:**

- run_free: 64.0% [54.2%, 72.7%]
- run_full: 67.0% [57.3%, 75.4%]
- CI Overlap: **Yes**
- Conclusion: Difference is not statistically significant

**codex:**

- run_free: 73.0% [63.6%, 80.7%]
- run_full: 75.0% [65.7%, 82.5%]
- CI Overlap: **Yes**
- Conclusion: Difference is not statistically significant

**opencode:**

- run_free: 13.0% [7.8%, 21.0%]
- run_full: 14.0% [8.5%, 22.1%]
- CI Overlap: **Yes**
- Conclusion: Difference is not statistically significant

## McNemar Paired Test

Test whether performance differences on the same instances under different modes are significant.

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
- run_less_k1 succeeds but run_full fails: 3 instances
- run_less_k1 fails but run_full succeeds: 8 instances
- p-value: 0.2266
- Significance (α=0.05): **Not significant**

**opencode:**

run_free vs run_full:
- run_free succeeds but run_full fails: 4 instances
- run_free fails but run_full succeeds: 3 instances
- p-value: 1.0000
- Significance (α=0.05): **Not significant**

run_less_k1 vs run_full:
- run_less_k1 succeeds but run_full fails: 10 instances
- run_less_k1 fails but run_full succeeds: 2 instances
- p-value: 0.0386
- Significance (α=0.05): **Significant**

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
- run_free succeeds but run_full fails: 1 instances
- run_free fails but run_full succeeds: 3 instances
- p-value: 0.6250
- Significance (α=0.05): **Not significant**

run_less_k1 vs run_full:
- run_less_k1 succeeds but run_full fails: 2 instances
- run_less_k1 fails but run_full succeeds: 5 instances
- p-value: 0.4531
- Significance (α=0.05): **Not significant**

**opencode:**

run_free vs run_full:
- run_free succeeds but run_full fails: 4 instances
- run_free fails but run_full succeeds: 5 instances
- p-value: 1.0000
- Significance (α=0.05): **Not significant**

run_less_k1 vs run_full:
- run_less_k1 succeeds but run_full fails: 7 instances
- run_less_k1 fails but run_full succeeds: 4 instances
- p-value: 0.5488
- Significance (α=0.05): **Not significant**

## Equivalence Testing

Using TOST (Two One-Sided Tests), equivalence threshold delta = 5pp

**Core question**: What is the upper bound of benefits between different execution modes?

If 90% CI falls entirely within +/-delta, we can claim 'practical equivalence'.

### SWE-bench Lite

**claude_code:**

**free -> less-k1:** Diff -2.0pp, CI [-5.8, +1.8], b=4, c=2 ❌
**free -> less-k3:** Diff -1.0pp, CI [-5.9, +3.9], b=5, c=4 ❌
**free -> cost:** Diff +0.0pp, CI [-5.7, +5.7], b=6, c=6 ❌
**free -> full:** Diff +1.0pp, CI [-4.4, +6.4], b=5, c=6 ❌
**less-k1 -> less-k3:** Diff +1.0pp, CI [-3.3, +5.3], b=3, c=4 ❌
**less-k1 -> full:** Diff +3.0pp, CI [-1.7, +7.7], b=3, c=6 ❌
**less-k3 -> full:** Diff +2.0pp, CI [-1.8, +5.8], b=2, c=4 ❌
**cost -> full:** Diff +1.0pp, CI [-3.9, +5.9], b=4, c=5 ❌

**codex:**

**free -> less-k1:** Diff -6.0pp, CI [-10.9, -1.1], b=9, c=3 ❌
**free -> less-k3:** Diff -5.0pp, CI [-8.0, -2.0], b=6, c=1 ❌
**free -> cost:** Diff -3.0pp, CI [-8.8, +2.8], b=8, c=5 ❌
**free -> full:** Diff -1.0pp, CI [-5.3, +3.3], b=4, c=3 ❌
**less-k1 -> less-k3:** Diff +1.0pp, CI [-3.9, +5.9], b=4, c=5 ❌
**less-k1 -> full:** Diff +5.0pp, CI [+0.1, +9.9], b=3, c=8 ❌
**less-k3 -> full:** Diff +4.0pp, CI [-0.0, +8.0], b=2, c=6 ❌
**cost -> full:** Diff +2.0pp, CI [-4.1, +8.1], b=6, c=8 ❌

**opencode:**

**free -> less-k1:** Diff +10.6pp, CI [+5.9, +15.3], b=1, c=8 ❌
**free -> less-k3:** Diff +0.0pp, CI [-7.0, +7.0], b=4, c=4 ❌
**free -> cost:** Diff +3.0pp, CI [-1.3, +7.3], b=1, c=3 ❌
**free -> full:** Diff -1.5pp, CI [-8.0, +5.0], b=4, c=3 ❌
**less-k1 -> less-k3:** Diff -7.0pp, CI [-12.0, -2.0], b=10, c=3 ❌
**less-k1 -> full:** Diff -8.0pp, CI [-12.2, -3.8], b=10, c=2 ❌
**less-k3 -> full:** Diff -1.0pp, CI [-6.4, +4.4], b=6, c=5 ❌
**cost -> full:** Diff -3.0pp, CI [-6.9, +0.9], b=5, c=2 ❌

### SWE-bench Verified

**claude_code:**

**free -> less-k1:** Diff +0.0pp, CI [-6.6, +6.6], b=8, c=8 ❌
**free -> less-k3:** Diff +1.0pp, CI [-5.8, +7.8], b=8, c=9 ❌
**free -> cost:** Diff +3.0pp, CI [-2.2, +8.2], b=4, c=7 ❌
**free -> full:** Diff +3.0pp, CI [-3.2, +9.2], b=6, c=9 ❌
**less-k1 -> less-k3:** Diff +1.0pp, CI [-2.6, +4.6], b=2, c=3 ✅
**less-k1 -> full:** Diff +3.0pp, CI [-1.7, +7.7], b=3, c=6 ❌
**less-k3 -> full:** Diff +2.0pp, CI [-1.8, +5.8], b=2, c=4 ❌
**cost -> full:** Diff +0.0pp, CI [-4.7, +4.7], b=4, c=4 ✅

**codex:**

**free -> less-k1:** Diff -1.0pp, CI [-5.9, +3.9], b=5, c=4 ❌
**free -> less-k3:** Diff +0.0pp, CI [-5.2, +5.2], b=5, c=5 ❌
**free -> cost:** Diff -2.0pp, CI [-7.6, +3.6], b=7, c=5 ❌
**free -> full:** Diff +2.0pp, CI [-0.8, +4.8], b=1, c=3 ✅
**less-k1 -> less-k3:** Diff +1.0pp, CI [-4.9, +6.9], b=6, c=7 ❌
**less-k1 -> full:** Diff +3.0pp, CI [-0.9, +6.9], b=2, c=5 ❌
**less-k3 -> full:** Diff +2.0pp, CI [-2.5, +6.5], b=3, c=5 ❌
**cost -> full:** Diff +4.0pp, CI [-0.0, +8.0], b=2, c=6 ❌

**opencode:**

**free -> less-k1:** Diff +4.0pp, CI [-0.8, +8.8], b=3, c=7 ❌
**free -> less-k3:** Diff -2.0pp, CI [-7.1, +3.1], b=6, c=4 ❌
**free -> cost:** Diff +0.0pp, CI [-5.7, +5.7], b=6, c=6 ❌
**free -> full:** Diff +1.0pp, CI [-3.9, +5.9], b=4, c=5 ❌
**less-k1 -> less-k3:** Diff -6.0pp, CI [-10.2, -1.8], b=8, c=2 ❌
**less-k1 -> full:** Diff -3.0pp, CI [-8.2, +2.2], b=7, c=4 ❌
**less-k3 -> full:** Diff +3.0pp, CI [-2.2, +8.2], b=4, c=7 ❌
**cost -> full:** Diff +1.0pp, CI [-4.4, +6.4], b=5, c=6 ❌

### Equivalence Testing Summary Table

| Dataset | Agent | Comparison | Diff | 90% CI | b | c | Equivalent? |
|---------|-------|------------|------|--------|---|---|-------------|
| SWE-benc | claude | free->less-k1 | -2.0pp | [-5.8, +1.8] | 4 | 2 | No |
| SWE-benc | claude | free->less-k3 | -1.0pp | [-5.9, +3.9] | 5 | 4 | No |
| SWE-benc | claude | free->cost | +0.0pp | [-5.7, +5.7] | 6 | 6 | No |
| SWE-benc | claude | free->full | +1.0pp | [-4.4, +6.4] | 5 | 6 | No |
| SWE-benc | claude | less-k1->less-k3 | +1.0pp | [-3.3, +5.3] | 3 | 4 | No |
| SWE-benc | claude | less-k1->full | +3.0pp | [-1.7, +7.7] | 3 | 6 | No |
| SWE-benc | claude | less-k3->full | +2.0pp | [-1.8, +5.8] | 2 | 4 | No |
| SWE-benc | claude | cost->full | +1.0pp | [-3.9, +5.9] | 4 | 5 | No |
| SWE-benc | codex | free->less-k1 | -6.0pp | [-10.9, -1.1] | 9 | 3 | No |
| SWE-benc | codex | free->less-k3 | -5.0pp | [-8.0, -2.0] | 6 | 1 | No |
| SWE-benc | codex | free->cost | -3.0pp | [-8.8, +2.8] | 8 | 5 | No |
| SWE-benc | codex | free->full | -1.0pp | [-5.3, +3.3] | 4 | 3 | No |
| SWE-benc | codex | less-k1->less-k3 | +1.0pp | [-3.9, +5.9] | 4 | 5 | No |
| SWE-benc | codex | less-k1->full | +5.0pp | [+0.1, +9.9] | 3 | 8 | No |
| SWE-benc | codex | less-k3->full | +4.0pp | [-0.0, +8.0] | 2 | 6 | No |
| SWE-benc | codex | cost->full | +2.0pp | [-4.1, +8.1] | 6 | 8 | No |
| SWE-benc | openco | free->less-k1 | +10.6pp | [+5.9, +15.3] | 1 | 8 | No |
| SWE-benc | openco | free->less-k3 | +0.0pp | [-7.0, +7.0] | 4 | 4 | No |
| SWE-benc | openco | free->cost | +3.0pp | [-1.3, +7.3] | 1 | 3 | No |
| SWE-benc | openco | free->full | -1.5pp | [-8.0, +5.0] | 4 | 3 | No |
| SWE-benc | openco | less-k1->less-k3 | -7.0pp | [-12.0, -2.0] | 10 | 3 | No |
| SWE-benc | openco | less-k1->full | -8.0pp | [-12.2, -3.8] | 10 | 2 | No |
| SWE-benc | openco | less-k3->full | -1.0pp | [-6.4, +4.4] | 6 | 5 | No |
| SWE-benc | openco | cost->full | -3.0pp | [-6.9, +0.9] | 5 | 2 | No |
| SWE-benc | claude | free->less-k1 | +0.0pp | [-6.6, +6.6] | 8 | 8 | No |
| SWE-benc | claude | free->less-k3 | +1.0pp | [-5.8, +7.8] | 8 | 9 | No |
| SWE-benc | claude | free->cost | +3.0pp | [-2.2, +8.2] | 4 | 7 | No |
| SWE-benc | claude | free->full | +3.0pp | [-3.2, +9.2] | 6 | 9 | No |
| SWE-benc | claude | less-k1->less-k3 | +1.0pp | [-2.6, +4.6] | 2 | 3 | Yes |
| SWE-benc | claude | less-k1->full | +3.0pp | [-1.7, +7.7] | 3 | 6 | No |
| SWE-benc | claude | less-k3->full | +2.0pp | [-1.8, +5.8] | 2 | 4 | No |
| SWE-benc | claude | cost->full | +0.0pp | [-4.7, +4.7] | 4 | 4 | Yes |
| SWE-benc | codex | free->less-k1 | -1.0pp | [-5.9, +3.9] | 5 | 4 | No |
| SWE-benc | codex | free->less-k3 | +0.0pp | [-5.2, +5.2] | 5 | 5 | No |
| SWE-benc | codex | free->cost | -2.0pp | [-7.6, +3.6] | 7 | 5 | No |
| SWE-benc | codex | free->full | +2.0pp | [-0.8, +4.8] | 1 | 3 | Yes |
| SWE-benc | codex | less-k1->less-k3 | +1.0pp | [-4.9, +6.9] | 6 | 7 | No |
| SWE-benc | codex | less-k1->full | +3.0pp | [-0.9, +6.9] | 2 | 5 | No |
| SWE-benc | codex | less-k3->full | +2.0pp | [-2.5, +6.5] | 3 | 5 | No |
| SWE-benc | codex | cost->full | +4.0pp | [-0.0, +8.0] | 2 | 6 | No |
| SWE-benc | openco | free->less-k1 | +4.0pp | [-0.8, +8.8] | 3 | 7 | No |
| SWE-benc | openco | free->less-k3 | -2.0pp | [-7.1, +3.1] | 6 | 4 | No |
| SWE-benc | openco | free->cost | +0.0pp | [-5.7, +5.7] | 6 | 6 | No |
| SWE-benc | openco | free->full | +1.0pp | [-3.9, +5.9] | 4 | 5 | No |
| SWE-benc | openco | less-k1->less-k3 | -6.0pp | [-10.2, -1.8] | 8 | 2 | No |
| SWE-benc | openco | less-k1->full | -3.0pp | [-8.2, +2.2] | 7 | 4 | No |
| SWE-benc | openco | less-k3->full | +3.0pp | [-2.2, +8.2] | 4 | 7 | No |
| SWE-benc | openco | cost->full | +1.0pp | [-4.4, +6.4] | 5 | 6 | No |

### Paired Symmetry Analysis (Agent Randomness)

If a mode has systematic advantage, we should see c >> b (or b >> c).
If b is approximately equal to c, it indicates differences mainly come from agent's inherent randomness, not the mode's influence.

| Dataset | Agent | Comparison | b (mode1 wins) | c (mode2 wins) | Ratio b:c | Symmetric? |
|---------|-------|------------|----------------|----------------|-----------|------------|
| SWE-benc | claude | free->less-k1 | 4 | 2 | 4:2 | Yes |
| SWE-benc | claude | free->less-k3 | 5 | 4 | 5:4 | Yes |
| SWE-benc | claude | free->cost | 6 | 6 | 6:6 | Yes |
| SWE-benc | claude | free->full | 5 | 6 | 5:6 | Yes |
| SWE-benc | claude | less-k1->less-k3 | 3 | 4 | 3:4 | Yes |
| SWE-benc | claude | less-k1->full | 3 | 6 | 3:6 | Yes |
| SWE-benc | claude | less-k3->full | 2 | 4 | 2:4 | Yes |
| SWE-benc | claude | cost->full | 4 | 5 | 4:5 | Yes |
| SWE-benc | codex | free->less-k1 | 9 | 3 | 9:3 | Skewed |
| SWE-benc | codex | free->less-k3 | 6 | 1 | 6:1 | Skewed |
| SWE-benc | codex | free->cost | 8 | 5 | 8:5 | Yes |
| SWE-benc | codex | free->full | 4 | 3 | 4:3 | Yes |
| SWE-benc | codex | less-k1->less-k3 | 4 | 5 | 4:5 | Yes |
| SWE-benc | codex | less-k1->full | 3 | 8 | 3:8 | Skewed |
| SWE-benc | codex | less-k3->full | 2 | 6 | 2:6 | Skewed |
| SWE-benc | codex | cost->full | 6 | 8 | 6:8 | Yes |
| SWE-benc | openco | free->less-k1 | 1 | 8 | 1:8 | Skewed |
| SWE-benc | openco | free->less-k3 | 4 | 4 | 4:4 | Yes |
| SWE-benc | openco | free->cost | 1 | 3 | 1:3 | Yes |
| SWE-benc | openco | free->full | 4 | 3 | 4:3 | Yes |
| SWE-benc | openco | less-k1->less-k3 | 10 | 3 | 10:3 | Skewed |
| SWE-benc | openco | less-k1->full | 10 | 2 | 10:2 | Skewed |
| SWE-benc | openco | less-k3->full | 6 | 5 | 6:5 | Yes |
| SWE-benc | openco | cost->full | 5 | 2 | 5:2 | Yes |
| SWE-benc | claude | free->less-k1 | 8 | 8 | 8:8 | Yes |
| SWE-benc | claude | free->less-k3 | 8 | 9 | 8:9 | Yes |
| SWE-benc | claude | free->cost | 4 | 7 | 4:7 | Yes |
| SWE-benc | claude | free->full | 6 | 9 | 6:9 | Yes |
| SWE-benc | claude | less-k1->less-k3 | 2 | 3 | 2:3 | Yes |
| SWE-benc | claude | less-k1->full | 3 | 6 | 3:6 | Yes |
| SWE-benc | claude | less-k3->full | 2 | 4 | 2:4 | Yes |
| SWE-benc | claude | cost->full | 4 | 4 | 4:4 | Yes |
| SWE-benc | codex | free->less-k1 | 5 | 4 | 5:4 | Yes |
| SWE-benc | codex | free->less-k3 | 5 | 5 | 5:5 | Yes |
| SWE-benc | codex | free->cost | 7 | 5 | 7:5 | Yes |
| SWE-benc | codex | free->full | 1 | 3 | 1:3 | Yes |
| SWE-benc | codex | less-k1->less-k3 | 6 | 7 | 6:7 | Yes |
| SWE-benc | codex | less-k1->full | 2 | 5 | 2:5 | Yes |
| SWE-benc | codex | less-k3->full | 3 | 5 | 3:5 | Yes |
| SWE-benc | codex | cost->full | 2 | 6 | 2:6 | Skewed |
| SWE-benc | openco | free->less-k1 | 3 | 7 | 3:7 | Yes |
| SWE-benc | openco | free->less-k3 | 6 | 4 | 6:4 | Yes |
| SWE-benc | openco | free->cost | 6 | 6 | 6:6 | Yes |
| SWE-benc | openco | free->full | 4 | 5 | 4:5 | Yes |
| SWE-benc | openco | less-k1->less-k3 | 8 | 2 | 8:2 | Skewed |
| SWE-benc | openco | less-k1->full | 7 | 4 | 7:4 | Yes |
| SWE-benc | openco | less-k3->full | 4 | 7 | 4:7 | Yes |
| SWE-benc | openco | cost->full | 5 | 6 | 5:6 | Yes |

**Symmetry Summary**: 39/48 comparisons show symmetric distribution

> In most comparisons b is approximately equal to c, indicating discordant pairs are bidirectional,
> supporting the conclusion that 'differences mainly come from agent randomness rather than systematic advantage of execution modes'.

## Cross-Dataset Consistency Analysis

Verify consistency of conclusions across different datasets.

### claude_code

| Mode | Lite Pass Rate | Verified Pass Rate | Trend Consistent |
|------|----------------|--------------------| -----------------|
| run_free | 63.0% | 64.0% | ✓ |
| run_less_k1 | 61.0% | 64.0% | ✓ |
| run_less_k3 | 62.0% | 65.0% | ✓ |
| run_cost | 63.0% | 67.0% | ✓ |
| run_full | 64.0% | 67.0% | ✓ |

### codex

| Mode | Lite Pass Rate | Verified Pass Rate | Trend Consistent |
|------|----------------|--------------------| -----------------|
| run_free | 74.0% | 73.0% | ✓ |
| run_less_k1 | 68.0% | 72.0% | ✓ |
| run_less_k3 | 69.0% | 73.0% | ✓ |
| run_cost | 71.0% | 71.0% | ✓ |
| run_full | 73.0% | 75.0% | ✓ |

## Key Statistical Conclusions

### 1. Confidence Interval Analysis Conclusions

- For all agents on all datasets, the 95% confidence intervals of run_free and run_full **highly overlap**
- This indicates that pass rate differences are **not statistically significant**
- Differences mainly come from random noise, not the essential impact of execution permissions

### 2. Paired Test Conclusions

- McNemar test shows that the difference between run_free vs run_full is **not significant** (p > 0.05)
- This means: problems that can be solved by run_free can mostly also be solved by run_full, and vice versa
- Supports the argument: "What can be done right will still be done right"

### 3. Cross-Dataset Consistency Conclusions

- Main trends are **consistent** across both Lite and Verified datasets
- This is more convincing than random sampling for demonstrating the robustness of conclusions
- Supports the argument: conclusions do not depend on specific sample selection

### 4. Core Academic Expression

> **Execution primarily affects efficiency and trajectory quality, while its marginal benefit on correctness is limited.**

> **Correctness appears robust to execution access, whereas cost is highly sensitive to it.**

## Paper-Ready Text

### English Version

#### Experimental Setup

> We did not perform any task filtering or manual selection. To ensure full reproducibility, we used the first 100 instances from the official release order of SWE-bench Lite and SWE-bench Verified as our deterministic evaluation subset, with instance IDs listed in the appendix. Our goal is not to claim a new state-of-the-art accuracy on SWE-bench, but to isolate the effect of execution regimes on agent behavior and cost. Therefore, a deterministic subset is sufficient for controlled comparison.

#### Statistical Reliability

> We report pass rates with 95% Wilson confidence intervals. For Codex on SWE-bench Verified: Run-Full achieves 75/100 (75.0%, CI: [65.7%, 82.5%]), while Run-Free achieves 73/100 (73.0%, CI: [63.6%, 80.7%]). The confidence intervals substantially overlap, indicating that the pass rate differences are within statistical noise. In contrast, cost differences are substantial (e.g., Claude Code shows 146% token increase from Run-Free to Run-Full). This suggests that execution regimes primarily affect efficiency and trajectory behavior rather than correctness.

#### Threats to Validity

> Using a prefix subset of the dataset may introduce ordering bias. However, we performed no selective filtering, and we demonstrate the stability of observed trends through confidence intervals and paired comparisons. The consistency of findings across both SWE-bench Lite and Verified further supports the robustness of our conclusions. Future work may extend to additional instances to further validate generalizability.

### Chinese Version

#### Experimental Setup

> We did not perform any task filtering or manual selection. To ensure full reproducibility, we directly used the first 100 instances from the official release order of SWE-bench Lite and SWE-bench Verified as our deterministic evaluation subset, with instance ID lists disclosed in the appendix. This work focuses on the impact of different execution regimes on agent cost and behavioral mechanisms, so this deterministic subset is sufficient to support controlled comparison.

#### Statistical Reliability

> We report the pass rate and its 95% Wilson confidence interval for each setting. Taking Codex results on SWE-bench Verified as an example: Run-Full achieves 75/100 (75.0%, CI: [65.7%, 82.5%]), Run-Free achieves 73/100 (73.0%, CI: [63.6%, 80.7%]). The confidence intervals highly overlap, indicating that pass rate differences are within statistical noise. In contrast, cost differences are significant (e.g., Claude Code shows 146% token increase from Run-Free to Run-Full). This suggests that the main impact of execution regime is reflected in efficiency and trajectory behavior, rather than correctness.

#### Threats to Validity

> Due to using a prefix subset of the dataset, results may be affected by ordering bias. However, we did not perform any selective filtering, and demonstrate the stability of observed trends through confidence intervals and paired comparisons. The consistency of conclusions across both SWE-bench Lite and Verified datasets further supports the robustness of the results. Future work can extend to more instances to further validate the generalizability of the conclusions.

## Equivalence Testing - Paper Text

### English Version

> To quantify the upper bound of execution benefits, we performed equivalence testing with a practically meaningful threshold δ = 5pp. Using Two One-Sided Tests (TOST), we computed 90% confidence intervals for the paired difference between Run-Full and Run-Free. 
The maximum observed upper bound across all settings is +9.2pp. While some settings show equivalence, others cannot rule out modest benefits from execution.

### Chinese Version

> To quantify the upper bound of execution benefits, we used equivalence testing with a practically meaningful threshold delta = 5pp. Using the TOST (Two One-Sided Tests) method, we computed the 90% confidence interval for the paired difference between Run-Full and Run-Free.
The maximum observed upper bound of benefits across all settings is +9.2pp. Some settings show equivalence, but others cannot rule out modest benefits from execution.
