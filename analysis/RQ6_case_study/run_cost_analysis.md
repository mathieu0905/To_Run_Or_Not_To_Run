# Run-Cost Mode In-Depth Analysis

Run-Cost is a cost-constrained execution mode that seeks a balance between execution frequency and cost.

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

## 2. Run-Cost Comparison with Other Modes

### SWE-bench Lite

**claude_code:**

| Comparison | Run-Cost Wins | Other Wins | Net Difference |
|------|-------------|--------|--------|
| vs Run-Free | 6 | 6 | +0 |
| vs Run-Less-K1 | 6 | 4 | +2 |
| vs Run-Less-K3 | 6 | 5 | +1 |
| vs Run-Full | 4 | 5 | -1 |

**Run-Cost Unique Successes (2):**
- `django__django-12113`
- `django__django-12589`

**codex:**

| Comparison | Run-Cost Wins | Other Wins | Net Difference |
|------|-------------|--------|--------|
| vs Run-Free | 4 | 8 | -4 |
| vs Run-Less-K1 | 8 | 5 | +3 |
| vs Run-Less-K3 | 7 | 6 | +1 |
| vs Run-Full | 5 | 8 | -3 |

**Run-Cost Unique Successes (2):**
- `django__django-12589`
- `django__django-14997`

### SWE-bench Verified

**claude_code:**

| Comparison | Run-Cost Wins | Other Wins | Net Difference |
|------|-------------|--------|--------|
| vs Run-Free | 7 | 4 | +3 |
| vs Run-Less-K1 | 6 | 3 | +3 |
| vs Run-Less-K3 | 4 | 2 | +2 |
| vs Run-Full | 4 | 4 | +0 |

**codex:**

| Comparison | Run-Cost Wins | Other Wins | Net Difference |
|------|-------------|--------|--------|
| vs Run-Free | 5 | 7 | -2 |
| vs Run-Less-K1 | 6 | 7 | -1 |
| vs Run-Less-K3 | 6 | 8 | -2 |
| vs Run-Full | 2 | 6 | -4 |

**Run-Cost Unique Successes (1):**
- `astropy__astropy-13236`

## 3. Summary Statistics

| Metric | Count |
|------|------|
| Run-Cost Unique Successes | 5 |
| Run-Cost Better than Run-Free | 22 |
| Run-Cost Better than Run-Full | 15 |
| Run-Free Better than Run-Cost | 25 |
| Run-Full Better than Run-Cost | 23 |

## 4. Detailed Analysis of Run-Cost Unique Success Cases

### `astropy__astropy-13236` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 1,115,511 | 72 | 2 | Failed |
| run_less_k1 | 263,515 | 37 | 2 | Failed |
| run_less_k3 | 678,205 | 60 | 8 | Failed |
| run_cost | 594,006 | 61 | 2 | **Success** |
| run_full | 564,008 | 55 | 10 | Failed |

### `django__django-12113` (claude_code, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 91,157 | 34 | 0 | Failed |
| run_less_k1 | 104,128 | 34 | 1 | Failed |
| run_less_k3 | 330,868 | 83 | 7 | Failed |
| run_cost | 443,799 | 112 | 0 | **Success** |
| run_full | 103,905 | 34 | 0 | Failed |

### `django__django-12589` (claude_code, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 506,993 | 107 | 9 | Failed |
| run_less_k1 | 115,450 | 45 | 2 | Failed |
| run_less_k3 | 154,816 | 59 | 3 | Failed |
| run_cost | 570,922 | 157 | 11 | **Success** |
| run_full | 294,978 | 108 | 8 | Failed |

### `django__django-14997` (codex, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 905,040 | 58 | 0 | Failed |
| run_less_k1 | 926,072 | 56 | 2 | Failed |
| run_less_k3 | 609,736 | 49 | 2 | Failed |
| run_cost | 1,362,485 | 78 | 6 | **Success** |
| run_full | 564,813 | 53 | 2 | Failed |

### `django__django-12589` (codex, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 1,056,172 | 67 | 0 | Failed |
| run_less_k1 | 1,304,099 | 78 | 2 | Failed |
| run_less_k3 | 1,195,104 | 77 | 4 | Failed |
| run_cost | 1,547,467 | 81 | 2 | **Success** |
| run_full | 554,197 | 57 | 2 | Failed |

## 5. Cost Efficiency Analysis

Run-Cost's cost position relative to other modes.

### SWE-bench Lite

**claude_code:**

| Mode | Avg Tokens | Pass Rate | Efficiency Ratio (Pass/Token) |
|------|------------|-----------|---------------------|
| run_free | 69,047 | 63 | 0.91 |
| run_less_k1 | 105,400 | 61 | 0.58 |
| run_less_k3 | 139,240 | 62 | 0.45 |
| run_cost | 143,596 | 63 | 0.44 |
| run_full | 158,417 | 64 | 0.40 |

**codex:**

| Mode | Avg Tokens | Pass Rate | Efficiency Ratio (Pass/Token) |
|------|------------|-----------|---------------------|
| run_free | 409,355 | 73 | 0.18 |
| run_less_k1 | 375,408 | 66 | 0.18 |
| run_less_k3 | 524,471 | 68 | 0.13 |
| run_cost | 499,337 | 69 | 0.14 |
| run_full | 472,777 | 72 | 0.15 |

### SWE-bench Verified

**claude_code:**

| Mode | Avg Tokens | Pass Rate | Efficiency Ratio (Pass/Token) |
|------|------------|-----------|---------------------|
| run_free | 63,490 | 64 | 1.01 |
| run_less_k1 | 125,338 | 64 | 0.51 |
| run_less_k3 | 125,777 | 65 | 0.52 |
| run_cost | 134,374 | 67 | 0.50 |
| run_full | 166,746 | 67 | 0.40 |

**codex:**

| Mode | Avg Tokens | Pass Rate | Efficiency Ratio (Pass/Token) |
|------|------------|-----------|---------------------|
| run_free | 539,302 | 73 | 0.14 |
| run_less_k1 | 409,696 | 72 | 0.18 |
| run_less_k3 | 578,573 | 73 | 0.13 |
| run_cost | 491,096 | 71 | 0.14 |
| run_full | 543,763 | 75 | 0.14 |

## 6. Value of Run-Cost Mode

### Advantages

1. **Cost Control** - Clear cost ceiling prevents unlimited consumption
2. **Stable Performance** - In most cases approaches Run-Full effectiveness
3. **Unique Success Cases** - Some problems can only be solved by Run-Cost
4. **More Flexible than Run-Less** - Not simply limiting execution count, but limiting total cost

### Applicable Scenarios

1. **Limited Budget but Execution Feedback Needed** - More verification capability than Run-Free
2. **Avoid Over-Execution** - More restrained than Run-Full
3. **Production Environment** - Predictable costs suitable for large-scale deployment

### Practical Recommendations

1. **Run-Free** - Default first choice, lowest cost
2. **Run-Cost** - Best choice when execution is needed but cost must be controlled
3. **Run-Full** - Use only when debugging complex problems
4. **Run-Less** - Not recommended, unstable performance
