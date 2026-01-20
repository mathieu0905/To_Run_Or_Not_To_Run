# Analysis of Run-Less Mode Advantages

Although overall data shows Run-Less is not as good as Run-Free, moderate execution does help in certain specific scenarios.

## 1. Cases with Unique Success in Run-Less

In these cases, both Run-Free and Run-Full failed, but Run-Less succeeded.

### SWE-bench Lite

**claude_code:**

- Run-Less-K1 unique success: 1
- Run-Less-K3 unique success: 0
- Any Run-Less unique success: 1

**Case list:**
- `django__django-11964` (K1)

**codex:**

- Run-Less-K1 unique success: 1
- Run-Less-K3 unique success: 1
- Any Run-Less unique success: 1

**Case list:**
- `django__django-15213` (K1, K3)

### SWE-bench Verified

**claude_code:**

- Run-Less-K1 unique success: 2
- Run-Less-K3 unique success: 2
- Any Run-Less unique success: 3

**Case list:**
- `astropy__astropy-14369` (K3)
- `django__django-11433` (K1, K3)
- `django__django-12193` (K1)

**codex:**

- Run-Less-K1 unique success: 2
- Run-Less-K3 unique success: 3
- Any Run-Less unique success: 5

**Case list:**
- `astropy__astropy-14369` (K1)
- `django__django-11149` (K3)
- `django__django-11433` (K3)
- `django__django-12273` (K3)
- `django__django-12308` (K1)

## 2. Detailed Analysis of Run-Less Unique Success Cases

### `django__django-11964` (claude_code, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 264,394 | 107 | 7 | Failed |
| run_less_k1 | 279,901 | 91 | 6 | **Success** |
| run_less_k3 | 286,153 | 92 | 5 | Failed |
| run_cost | 371,806 | 110 | 6 | Failed |
| run_full | 454,826 | 148 | 11 | Failed |

**Analysis**: Moderate execution (1-3 times) helps verify fixes, but excessive execution is harmful.

### `django__django-15213` (codex, SWE-bench Lite)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 773,892 | 52 | 0 | Failed |
| run_less_k1 | 497,171 | 42 | 0 | **Success** |
| run_less_k3 | 648,812 | 55 | 6 | **Success** |
| run_cost | 1,194,744 | 86 | 10 | **Success** |
| run_full | 664,227 | 54 | 4 | Failed |

**Analysis**: Moderate execution (1-3 times) helps verify fixes, but excessive execution is harmful.

### `astropy__astropy-14369` (claude_code, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 23,182 | 36 | 0 | Failed |
| run_less_k1 | 662,637 | 94 | 3 | Failed |
| run_less_k3 | 202,229 | 55 | 5 | **Success** |
| run_cost | 172,953 | 64 | 4 | **Success** |
| run_full | 159,775 | 62 | 3 | Failed |

**Analysis**: Moderate execution (1-3 times) helps verify fixes, but excessive execution is harmful.

### `django__django-11433` (claude_code, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 17,216 | 17 | 0 | Failed |
| run_less_k1 | 143,606 | 71 | 6 | **Success** |
| run_less_k3 | 152,186 | 70 | 2 | **Success** |
| run_cost | 243,147 | 83 | 6 | Failed |
| run_full | 197,423 | 89 | 2 | Failed |

**Analysis**: Moderate execution (1-3 times) helps verify fixes, but excessive execution is harmful.

### `django__django-12193` (claude_code, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 10,860 | 11 | 0 | Failed |
| run_less_k1 | 83,166 | 44 | 2 | **Success** |
| run_less_k3 | 89,103 | 50 | 4 | Failed |
| run_cost | 92,623 | 56 | 4 | Failed |
| run_full | 60,372 | 43 | 1 | Failed |

**Analysis**: Moderate execution (1-3 times) helps verify fixes, but excessive execution is harmful.

### `astropy__astropy-14369` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 476,795 | 44 | 0 | Failed |
| run_less_k1 | 465,523 | 46 | 0 | **Success** |
| run_less_k3 | 863,774 | 67 | 2 | Failed |
| run_cost | 799,612 | 66 | 2 | Failed |
| run_full | 1,023,689 | 67 | 2 | Failed |

**Analysis**: Moderate execution (1-3 times) helps verify fixes, but excessive execution is harmful.

### `django__django-11149` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 887,761 | 77 | 0 | Failed |
| run_less_k1 | 1,666,811 | 87 | 4 | Failed |
| run_less_k3 | 1,745,265 | 76 | 6 | **Success** |
| run_cost | 1,617,609 | 74 | 4 | Failed |
| run_full | 1,249,548 | 78 | 2 | Failed |

**Analysis**: Moderate execution (1-3 times) helps verify fixes, but excessive execution is harmful.

### `django__django-11433` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 290,823 | 33 | 0 | Failed |
| run_less_k1 | 457,464 | 43 | 4 | Failed |
| run_less_k3 | 326,728 | 39 | 6 | **Success** |
| run_cost | 565,026 | 62 | 6 | **Success** |
| run_full | 655,146 | 55 | 8 | Failed |

**Analysis**: Moderate execution (1-3 times) helps verify fixes, but excessive execution is harmful.

### `django__django-12273` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 460,123 | 52 | 0 | Failed |
| run_less_k1 | 288,012 | 36 | 2 | Failed |
| run_less_k3 | 779,584 | 66 | 4 | **Success** |
| run_cost | 306,596 | 41 | 0 | Failed |
| run_full | 342,668 | 27 | 4 | Failed |

**Analysis**: Moderate execution (1-3 times) helps verify fixes, but excessive execution is harmful.

### `django__django-12308` (codex, SWE-bench Verified)

| Mode | Tokens | Turns | High-Cost Exec | Result |
|------|--------|-------|----------------|--------|
| run_free | 264,021 | 32 | 0 | Failed |
| run_less_k1 | 348,176 | 40 | 2 | **Success** |
| run_less_k3 | 235,008 | 33 | 6 | Failed |
| run_cost | 295,168 | 42 | 4 | Failed |
| run_full | 209,938 | 29 | 6 | Failed |

**Analysis**: Moderate execution (1-3 times) helps verify fixes, but excessive execution is harmful.

## 3. Cases Where Run-Less Outperforms Run-Free

In these cases, Run-Free failed but Run-Less succeeded.

### SWE-bench Lite

**claude_code:**

- Run-Less-K1 success while Run-Free failed: 2
- Run-Less-K3 success while Run-Free failed: 4

**Cases:**
- `django__django-11964` (K1 success)
- `django__django-15498` (K1 success)
- `django__django-11620` (K3 success)
- `django__django-11797` (K3 success)
- `django__django-12284` (K3 success)

**codex:**

- Run-Less-K1 success while Run-Free failed: 2
- Run-Less-K3 success while Run-Free failed: 1

**Cases:**
- `django__django-15202` (K1 success)
- `django__django-15213` (K1 success)

### SWE-bench Verified

**claude_code:**

- Run-Less-K1 success while Run-Free failed: 8
- Run-Less-K3 success while Run-Free failed: 9

**Cases:**
- `astropy__astropy-14096` (K1 success)
- `astropy__astropy-7166` (K1 success)
- `django__django-11206` (K1 success)
- `django__django-11433` (K1 success)
- `django__django-11490` (K1 success)
- `astropy__astropy-14369` (K3 success)
- `django__django-12663` (K3 success)

**codex:**

- Run-Less-K1 success while Run-Free failed: 4
- Run-Less-K3 success while Run-Free failed: 5

**Cases:**
- `astropy__astropy-14369` (K1 success)
- `django__django-11490` (K1 success)
- `django__django-12304` (K1 success)
- `django__django-12308` (K1 success)
- `django__django-11149` (K3 success)
- `django__django-11433` (K3 success)
- `django__django-12273` (K3 success)

## 4. Value Analysis of Moderate Execution

| Mode | Unique Success | Better than Run-Free | Better than Run-Full |
|------|----------|----------------|----------------|
| run_less_k1 | 4 | 16 | 10 |
| run_less_k3 | 2 | 19 | 9 |
| run_cost | 5 | 22 | 15 |

## 5. Key Findings: Value of Moderate Execution

### Scenarios Where Moderate Execution Helps

1. **Problems requiring verification but not iteration**
   - 1-3 executions are sufficient to verify if fixes are correct
   - More executions introduce noise and interference

2. **Problems where Run-Free reasoning is insufficient**
   - Pure reasoning cannot determine the correct answer
   - But limited execution feedback can point the way

3. **Problems where Run-Full excessive execution is harmful**
   - Excessive execution leads to trial-and-error loops
   - Moderate execution avoids this problem

### Practical Recommendations

1. **Run-Free remains the default choice** - Lowest cost, near-optimal results
2. **Run-Less-K1 can serve as a fallback** - When Run-Free fails, try 1 execution
3. **Avoid Run-Full** - Unless significant iterative debugging is truly needed
4. **The value of moderate execution lies in verification** - Not exploration, but confirmation
