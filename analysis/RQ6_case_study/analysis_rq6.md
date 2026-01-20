# RQ6: Case Study Analysis and Task Difficulty Stratification

## Comprehensive Multi-Mode Comparison

Comparing performance differences across all 5 execution modes.

### SWE-bench Lite

**claude_code:**

#### Success Rate Comparison

| Mode | Resolved | Pass Rate |
|------|----------|-----------|
| run_free | 63 | 63.0% |
| run_less_k1 | 61 | 61.0% |
| run_less_k3 | 62 | 62.0% |
| run_cost | 63 | 63.0% |
| run_full | 64 | 64.0% |

#### Mode Difference Matrix

Table shows: number of cases where row mode succeeded but column mode failed

| | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|---|---|---|---|---|---|
| run_free | - | 4 | 5 | 6 | 5 |
| run_less_k1 | 2 | - | 3 | 4 | 3 |
| run_less_k3 | 4 | 4 | - | 5 | 2 |
| run_cost | 6 | 6 | 6 | - | 4 |
| run_full | 6 | 6 | 4 | 5 | - |

#### Key Comparisons

**Run-Free vs Run-Less-K1:**
- Both succeeded: 59
- run_free unique: 4
- run_less_k1 unique: 2
- Net difference: -2

**Run-Free vs Run-Less-K3:**
- Both succeeded: 58
- run_free unique: 5
- run_less_k3 unique: 4
- Net difference: -1

**Run-Free vs Run-Cost:**
- Both succeeded: 57
- run_free unique: 6
- run_cost unique: 6
- Net difference: +0

**Run-Free vs Run-Full:**
- Both succeeded: 58
- run_free unique: 5
- run_full unique: 6
- Net difference: +1

**Run-Less-K1 vs Run-Full:**
- Both succeeded: 58
- run_less_k1 unique: 3
- run_full unique: 6
- Net difference: +3

**Run-Less-K3 vs Run-Full:**
- Both succeeded: 60
- run_less_k3 unique: 2
- run_full unique: 4
- Net difference: +2

**Run-Cost vs Run-Full:**
- Both succeeded: 59
- run_cost unique: 4
- run_full unique: 5
- Net difference: +1

**codex:**

#### Success Rate Comparison

| Mode | Resolved | Pass Rate |
|------|----------|-----------|
| run_free | 73 | 73.0% |
| run_less_k1 | 66 | 66.0% |
| run_less_k3 | 68 | 68.0% |
| run_cost | 69 | 69.0% |
| run_full | 72 | 72.0% |

#### Mode Difference Matrix

Table shows: number of cases where row mode succeeded but column mode failed

| | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|---|---|---|---|---|---|
| run_free | - | 9 | 6 | 8 | 4 |
| run_less_k1 | 2 | - | 3 | 5 | 2 |
| run_less_k3 | 1 | 5 | - | 6 | 2 |
| run_cost | 4 | 8 | 7 | - | 5 |
| run_full | 3 | 8 | 6 | 8 | - |

#### Key Comparisons

**Run-Free vs Run-Less-K1:**
- Both succeeded: 64
- run_free unique: 9
- run_less_k1 unique: 2
- Net difference: -7

**Run-Free vs Run-Less-K3:**
- Both succeeded: 67
- run_free unique: 6
- run_less_k3 unique: 1
- Net difference: -5

**Run-Free vs Run-Cost:**
- Both succeeded: 65
- run_free unique: 8
- run_cost unique: 4
- Net difference: -4

**Run-Free vs Run-Full:**
- Both succeeded: 69
- run_free unique: 4
- run_full unique: 3
- Net difference: -1

**Run-Less-K1 vs Run-Full:**
- Both succeeded: 64
- run_less_k1 unique: 2
- run_full unique: 8
- Net difference: +6

**Run-Less-K3 vs Run-Full:**
- Both succeeded: 66
- run_less_k3 unique: 2
- run_full unique: 6
- Net difference: +4

**Run-Cost vs Run-Full:**
- Both succeeded: 64
- run_cost unique: 5
- run_full unique: 8
- Net difference: +3

### SWE-bench Verified

**claude_code:**

#### Success Rate Comparison

| Mode | Resolved | Pass Rate |
|------|----------|-----------|
| run_free | 64 | 64.0% |
| run_less_k1 | 64 | 64.0% |
| run_less_k3 | 65 | 65.0% |
| run_cost | 67 | 67.0% |
| run_full | 67 | 67.0% |

#### Mode Difference Matrix

Table shows: number of cases where row mode succeeded but column mode failed

| | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|---|---|---|---|---|---|
| run_free | - | 8 | 8 | 4 | 6 |
| run_less_k1 | 8 | - | 2 | 3 | 3 |
| run_less_k3 | 9 | 3 | - | 2 | 2 |
| run_cost | 7 | 6 | 4 | - | 4 |
| run_full | 9 | 6 | 4 | 4 | - |

#### Key Comparisons

**Run-Free vs Run-Less-K1:**
- Both succeeded: 56
- run_free unique: 8
- run_less_k1 unique: 8
- Net difference: +0

**Run-Free vs Run-Less-K3:**
- Both succeeded: 56
- run_free unique: 8
- run_less_k3 unique: 9
- Net difference: +1

**Run-Free vs Run-Cost:**
- Both succeeded: 60
- run_free unique: 4
- run_cost unique: 7
- Net difference: +3

**Run-Free vs Run-Full:**
- Both succeeded: 58
- run_free unique: 6
- run_full unique: 9
- Net difference: +3

**Run-Less-K1 vs Run-Full:**
- Both succeeded: 61
- run_less_k1 unique: 3
- run_full unique: 6
- Net difference: +3

**Run-Less-K3 vs Run-Full:**
- Both succeeded: 63
- run_less_k3 unique: 2
- run_full unique: 4
- Net difference: +2

**Run-Cost vs Run-Full:**
- Both succeeded: 63
- run_cost unique: 4
- run_full unique: 4
- Net difference: +0

**codex:**

#### Success Rate Comparison

| Mode | Resolved | Pass Rate |
|------|----------|-----------|
| run_free | 73 | 73.0% |
| run_less_k1 | 72 | 72.0% |
| run_less_k3 | 73 | 73.0% |
| run_cost | 71 | 71.0% |
| run_full | 75 | 75.0% |

#### Mode Difference Matrix

Table shows: number of cases where row mode succeeded but column mode failed

| | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|---|---|---|---|---|---|
| run_free | - | 5 | 5 | 7 | 1 |
| run_less_k1 | 4 | - | 6 | 7 | 2 |
| run_less_k3 | 5 | 7 | - | 8 | 3 |
| run_cost | 5 | 6 | 6 | - | 2 |
| run_full | 3 | 5 | 5 | 6 | - |

#### Key Comparisons

**Run-Free vs Run-Less-K1:**
- Both succeeded: 68
- run_free unique: 5
- run_less_k1 unique: 4
- Net difference: -1

**Run-Free vs Run-Less-K3:**
- Both succeeded: 68
- run_free unique: 5
- run_less_k3 unique: 5
- Net difference: +0

**Run-Free vs Run-Cost:**
- Both succeeded: 66
- run_free unique: 7
- run_cost unique: 5
- Net difference: -2

**Run-Free vs Run-Full:**
- Both succeeded: 72
- run_free unique: 1
- run_full unique: 3
- Net difference: +2

**Run-Less-K1 vs Run-Full:**
- Both succeeded: 70
- run_less_k1 unique: 2
- run_full unique: 5
- Net difference: +3

**Run-Less-K3 vs Run-Full:**
- Both succeeded: 70
- run_less_k3 unique: 3
- run_full unique: 5
- Net difference: +2

**Run-Cost vs Run-Full:**
- Both succeeded: 69
- run_cost unique: 2
- run_full unique: 6
- Net difference: +4


## Execution Permission Incremental Analysis

Analyzing progressive changes from Run-Free to Run-Full.

### SWE-bench Lite

**claude_code:**

| Category | Count | Description |
|------|------|------|
| Always Succeed | 52 | All modes can resolve |
| Always Fail | 0 | All modes cannot resolve |
| Improve with Execution | 4 | More execution permission helps |
| Degrade with Execution | 5 | More execution permission is harmful |
| Inconsistent | 11 | Performance is unstable |

**Cases that degrade with execution (Run-Free succeeds but Run-Full fails):**
- `django__django-12184`
- `django__django-12908`
- `django__django-13230`
- `django__django-14016`
- `django__django-15695`

**codex:**

| Category | Count | Description |
|------|------|------|
| Always Succeed | 59 | All modes can resolve |
| Always Fail | 0 | All modes cannot resolve |
| Improve with Execution | 2 | More execution permission helps |
| Degrade with Execution | 4 | More execution permission is harmful |
| Inconsistent | 14 | Performance is unstable |

**Cases that degrade with execution (Run-Free succeeds but Run-Full fails):**
- `django__django-11848`
- `django__django-11964`
- `django__django-12497`
- `django__django-12747`

### SWE-bench Verified

**claude_code:**

| Category | Count | Description |
|------|------|------|
| Always Succeed | 55 | All modes can resolve |
| Always Fail | 0 | All modes cannot resolve |
| Improve with Execution | 8 | More execution permission helps |
| Degrade with Execution | 6 | More execution permission is harmful |
| Inconsistent | 7 | Performance is unstable |

**Cases that degrade with execution (Run-Free succeeds but Run-Full fails):**
- `astropy__astropy-14365`
- `django__django-11532`
- `django__django-11555`
- `django__django-11728`
- `django__django-11790`
- ... 6 total

**codex:**

| Category | Count | Description |
|------|------|------|
| Always Succeed | 59 | All modes can resolve |
| Always Fail | 0 | All modes cannot resolve |
| Improve with Execution | 3 | More execution permission helps |
| Degrade with Execution | 1 | More execution permission is harmful |
| Inconsistent | 19 | Performance is unstable |

**Cases that degrade with execution (Run-Free succeeds but Run-Full fails):**
- `django__django-10973`


## Typical Case Full-Mode Analysis

### `django__django-10973` (codex, SWE-bench Verified)

**Type**: Run-Free succeeds but Run-Full fails

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 232,585 | 47 | 0 | **Success** |
| run_less_k1 | 149,535 | 29 | 2 | Failed |
| run_less_k3 | 166,599 | 27 | 0 | Failed |
| run_cost | 162,007 | 24 | 8 | Failed |
| run_full | 278,583 | 44 | 12 | Failed |

**Analysis**: Execution feedback may cause the agent to fall into trial-and-error loops or deviate from the correct direction.

### `django__django-12304` (codex, SWE-bench Verified)

**Type**: Run-Full succeeds but Run-Free fails

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 157,322 | 25 | 0 | Failed |
| run_less_k1 | 191,904 | 31 | 4 | **Success** |
| run_less_k3 | 259,846 | 40 | 4 | **Success** |
| run_cost | 234,968 | 33 | 4 | **Success** |
| run_full | 200,265 | 27 | 4 | **Success** |

**Analysis**: This problem may require execution feedback to verify fixes or locate issues.

### `django__django-11490` (codex, SWE-bench Verified)

**Type**: Run-Full succeeds but Run-Free fails

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 252,469 | 32 | 0 | Failed |
| run_less_k1 | 202,265 | 19 | 2 | **Success** |
| run_less_k3 | 411,288 | 47 | 6 | **Success** |
| run_cost | 345,046 | 47 | 4 | **Success** |
| run_full | 305,072 | 38 | 4 | **Success** |

**Analysis**: This problem may require execution feedback to verify fixes or locate issues.

### `django__django-11265` (codex, SWE-bench Verified)

**Type**: Run-Full succeeds but Run-Free fails

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 409,485 | 29 | 0 | Failed |
| run_less_k1 | 585,511 | 39 | 2 | Failed |
| run_less_k3 | 745,455 | 45 | 8 | Failed |
| run_cost | 1,087,114 | 61 | 12 | **Success** |
| run_full | 858,408 | 54 | 16 | **Success** |

**Analysis**: This problem may require execution feedback to verify fixes or locate issues.

### `django__django-11790` (claude_code, SWE-bench Verified)

**Type**: Run-Free succeeds but Run-Full fails

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 132,602 | 59 | 0 | **Success** |
| run_less_k1 | 233,202 | 87 | 6 | Failed |
| run_less_k3 | 198,961 | 80 | 6 | Failed |
| run_cost | 189,346 | 80 | 4 | Failed |
| run_full | 176,459 | 75 | 5 | Failed |

**Analysis**: Execution feedback may cause the agent to fall into trial-and-error loops or deviate from the correct direction.

### `astropy__astropy-14365` (claude_code, SWE-bench Verified)

**Type**: Run-Free succeeds but Run-Full fails

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 15,768 | 14 | 0 | **Success** |
| run_less_k1 | 15,657 | 12 | 0 | Failed |
| run_less_k3 | 53,159 | 29 | 2 | Failed |
| run_cost | 70,629 | 38 | 3 | Failed |
| run_full | 39,176 | 32 | 3 | Failed |

**Analysis**: Execution feedback may cause the agent to fall into trial-and-error loops or deviate from the correct direction.

### `django__django-11532` (claude_code, SWE-bench Verified)

**Type**: Run-Free succeeds but Run-Full fails

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 11,961 | 7 | 0 | **Success** |
| run_less_k1 | 101,566 | 42 | 3 | **Success** |
| run_less_k3 | 94,802 | 40 | 5 | Failed |
| run_cost | 129,260 | 54 | 4 | **Success** |
| run_full | 124,953 | 56 | 6 | Failed |

**Analysis**: Execution feedback may cause the agent to fall into trial-and-error loops or deviate from the correct direction.

### `django__django-12965` (claude_code, SWE-bench Verified)

**Type**: Run-Full succeeds but Run-Free fails

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 191,095 | 69 | 0 | Failed |
| run_less_k1 | 182,385 | 67 | 4 | **Success** |
| run_less_k3 | 182,567 | 69 | 3 | **Success** |
| run_cost | 188,172 | 71 | 5 | **Success** |
| run_full | 225,064 | 84 | 5 | **Success** |

**Analysis**: This problem may require execution feedback to verify fixes or locate issues.

### `django__django-12663` (claude_code, SWE-bench Verified)

**Type**: Run-Full succeeds but Run-Free fails

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 85,546 | 40 | 0 | Failed |
| run_less_k1 | 185,420 | 64 | 3 | Failed |
| run_less_k3 | 301,056 | 83 | 2 | **Success** |
| run_cost | 483,717 | 116 | 5 | **Success** |
| run_full | 440,663 | 118 | 5 | **Success** |

**Analysis**: This problem may require execution feedback to verify fixes or locate issues.

### `django__django-10973` (claude_code, SWE-bench Verified)

**Type**: Run-Full succeeds but Run-Free fails

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 8,643 | 15 | 0 | Failed |
| run_less_k1 | 32,236 | 28 | 3 | Failed |
| run_less_k3 | 25,522 | 23 | 3 | Failed |
| run_cost | 22,523 | 20 | 3 | Failed |
| run_full | 51,807 | 41 | 3 | **Success** |

**Analysis**: This problem may require execution feedback to verify fixes or locate issues.


## Task Difficulty Stratification Analysis

Analyzing the impact of execution permissions by task difficulty. Difficulty is defined based on success rate in Run-Full mode.

### Difficulty Distribution

- Easy (all agents succeed in Run-Full): 141 cases
- Medium (some agents succeed): 15 cases
- Hard (all agents fail): 12 cases

### Full-Mode Comparison by Difficulty

#### Easy Tasks (141 cases)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 79.4% | 81.6% | 84.4% | 83.0% | 88.7% |
| codex | 93.6% | 89.4% | 90.8% | 89.4% | 97.9% |

#### Medium Tasks (15 cases)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 80.0% | 53.3% | 40.0% | 66.7% | 40.0% |
| codex | 80.0% | 60.0% | 66.7% | 73.3% | 60.0% |

#### Hard Tasks (12 cases)

| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |
|-------|----------|-------------|-------------|----------|----------|
| claude_code | 25.0% | 16.7% | 16.7% | 25.0% | 0.0% |
| codex | 16.7% | 25.0% | 25.0% | 25.0% | 0.0% |


## Full-Mode Cost Analysis

### SWE-bench Lite

**claude_code:**

| Mode | Avg Tokens | Avg Turns | Avg High-Cost Exec | vs Run-Free |
|------|------------|-----------|--------------------| ------------|
| run_free | 69,047 | 35.2 | 0.6 | - |
| run_less_k1 | 105,400 | 48.5 | 4.0 | +52.6% |
| run_less_k3 | 139,240 | 59.6 | 5.2 | +101.7% |
| run_cost | 143,596 | 61.3 | 5.4 | +108.0% |
| run_full | 158,417 | 69.7 | 7.0 | +129.4% |

**codex:**

| Mode | Avg Tokens | Avg Turns | Avg High-Cost Exec | vs Run-Free |
|------|------------|-----------|--------------------| ------------|
| run_free | 409,355 | 41.0 | 0.0 | - |
| run_less_k1 | 375,408 | 40.1 | 2.3 | +-8.3% |
| run_less_k3 | 524,471 | 46.8 | 4.9 | +28.1% |
| run_cost | 499,337 | 44.9 | 4.4 | +22.0% |
| run_full | 472,777 | 44.1 | 6.3 | +15.5% |

### SWE-bench Verified

**claude_code:**

| Mode | Avg Tokens | Avg Turns | Avg High-Cost Exec | vs Run-Free |
|------|------------|-----------|--------------------| ------------|
| run_free | 63,490 | 32.7 | 0.5 | - |
| run_less_k1 | 125,338 | 52.6 | 3.7 | +97.4% |
| run_less_k3 | 125,777 | 53.6 | 4.4 | +98.1% |
| run_cost | 134,374 | 56.6 | 4.5 | +111.6% |
| run_full | 166,746 | 68.7 | 6.3 | +162.6% |

**codex:**

| Mode | Avg Tokens | Avg Turns | Avg High-Cost Exec | vs Run-Free |
|------|------------|-----------|--------------------| ------------|
| run_free | 539,302 | 46.5 | 0.0 | - |
| run_less_k1 | 409,696 | 41.3 | 2.2 | +-24.0% |
| run_less_k3 | 578,573 | 50.3 | 4.5 | +7.3% |
| run_cost | 491,096 | 44.9 | 3.8 | +-8.9% |
| run_full | 543,763 | 46.3 | 5.9 | +0.8% |


## Case Study Summary

### Core Findings

1. **Execution feedback is a double-edged sword**
   - In some cases, execution feedback helps agents verify fixes
   - In other cases, execution feedback misleads agents away from the correct direction
   - Net benefit is limited (typically < 5 cases)

2. **Run-Less mode shows unstable performance**
   - Run-Less-K1 and Run-Less-K3 do not perform better than Run-Free
   - Restricting execution count does not force agents to execute more intelligently
   - May instead fail to complete verification due to insufficient execution budget

3. **Task difficulty determines execution value**
   - Easy tasks: execution permission has almost no impact
   - Medium tasks: execution permission provides some help
   - Hard tasks: execution permission cannot solve fundamental problems

4. **Cost increases monotonically with execution permission**
   - Run-Free < Run-Less-K1 < Run-Less-K3 < Run-Cost < Run-Full
   - But Pass Rate does not increase monotonically

### Practical Recommendations

1. **Use Run-Free by default** - Best cost-benefit ratio
2. **Do not recommend Run-Less mode** - Performs worse than Run-Free with higher cost
3. **Enable Run-Full only when necessary** - When reasoning cannot determine fix correctness
4. **Run-Cost is a compromise choice** - Alternative when cost constraints exist
