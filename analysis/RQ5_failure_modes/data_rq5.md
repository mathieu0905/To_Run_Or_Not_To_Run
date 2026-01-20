# RQ5: Failure Modes - Data Tables

Failure mode analysis data.

## Failure Type Analysis

### Failure Mode Classification

| Category | Description | Identification Rule |
|------|------|----------|
| Tool/Environment Error | Command execution failure, file not found, etc. | trace contains error, exception, failed |
| Trial-and-Error Loop | Same command executed multiple times | Same command executed > 3 times |
| Drift | Modified unrelated files | patch modified files > 5 |
| Invalid Patch | Generated patch but failed tests | has_patch=True but resolved=False |

## Failure Mode Distribution

### SWE-bench Lite

| Agent | Mode | Total | Resolved | Failed | Tool Errors | Repeated Cmds |
|-------|------|-------|----------|--------|-------------|---------------|
| claude_code | run_free | 100 | 63 | 37 | 0.0 | 0.0 |
| claude_code | run_less_k1 | 100 | 61 | 39 | 0.0 | 0.1 |
| claude_code | run_less_k3 | 100 | 62 | 38 | 0.0 | 0.1 |
| claude_code | run_cost | 100 | 63 | 37 | 0.0 | 0.1 |
| claude_code | run_full | 100 | 64 | 36 | 0.0 | 0.1 |
| codex | run_free | 100 | 73 | 27 | 0.0 | 0.2 |
| codex | run_less_k1 | 100 | 66 | 34 | 0.0 | 0.2 |
| codex | run_less_k3 | 100 | 68 | 32 | 0.0 | 0.3 |
| codex | run_cost | 100 | 69 | 31 | 0.0 | 0.2 |
| codex | run_full | 100 | 72 | 28 | 0.0 | 0.6 |

### SWE-bench Verified

| Agent | Mode | Total | Resolved | Failed | Tool Errors | Repeated Cmds |
|-------|------|-------|----------|--------|-------------|---------------|
| claude_code | run_free | 100 | 64 | 36 | 0.0 | 0.0 |
| claude_code | run_less_k1 | 100 | 64 | 36 | 0.0 | 0.1 |
| claude_code | run_less_k3 | 100 | 65 | 35 | 0.0 | 0.1 |
| claude_code | run_cost | 100 | 67 | 33 | 0.0 | 0.1 |
| claude_code | run_full | 100 | 67 | 33 | 0.0 | 0.1 |
| codex | run_free | 100 | 73 | 27 | 0.0 | 0.2 |
| codex | run_less_k1 | 100 | 72 | 28 | 0.0 | 0.2 |
| codex | run_less_k3 | 100 | 73 | 27 | 0.0 | 0.2 |
| codex | run_cost | 100 | 71 | 29 | 0.0 | 0.1 |
| codex | run_full | 100 | 75 | 25 | 0.0 | 0.5 |

## Typical Case Comparison

### Cases Where Run-Free Succeeded but Run-Full Failed

| Dataset | Agent | Instance ID |
|---------|-------|-------------|
| swebenchlite | claude_code | django__django-14016 |
| swebenchlite | claude_code | django__django-13230 |
| swebenchlite | claude_code | django__django-12184 |
| swebenchlite | claude_code | django__django-12908 |
| swebenchlite | claude_code | django__django-15695 |
| swebenchlite | codex | django__django-12747 |
| swebenchlite | codex | django__django-12497 |
| swebenchlite | codex | django__django-11964 |
| swebenchlite | codex | django__django-11848 |
| swebenchverified | claude_code | django__django-11532 |

共 16 个案例

### Cases Where Run-Full Succeeded but Run-Free Failed

| Dataset | Agent | Instance ID |
|---------|-------|-------------|
| swebenchlite | claude_code | django__django-11797 |
| swebenchlite | claude_code | django__django-12470 |
| swebenchlite | claude_code | django__django-14997 |
| swebenchlite | claude_code | django__django-11620 |
| swebenchlite | claude_code | django__django-12284 |
| swebenchlite | claude_code | django__django-15498 |
| swebenchlite | codex | django__django-15781 |
| swebenchlite | codex | django__django-15202 |
| swebenchlite | codex | django__django-15252 |
| swebenchverified | claude_code | astropy__astropy-7166 |

Total: 21 cases

## Key Findings

### 1. Case Statistics

- Run-Free succeeded but Run-Full failed: **16** cases
- Run-Full succeeded but Run-Free failed: **21** cases
- Net difference: **5** cases (Run-Full advantage)

### 2. Failure Mode Analysis

**Typical failure modes in Run-Full mode:**
- Trial-and-error loop: Repeatedly executing the same test command, expecting different results
- Over-modification: Modified unnecessary files, introducing new issues
- Tool errors: Encountered environment issues during execution

**Typical failure modes in Run-Free mode:**
- Reasoning errors: Inaccurate understanding of the problem
- Lack of verification: Unable to confirm if the fix is correct
- Environment assumptions: Incorrect assumptions about the runtime environment

### 3. Conclusion

- Run-Full mode outperforms Run-Free in **5** cases
- Execution feedback is indeed helpful in some situations
- Different failure modes require different response strategies
- Developer review burden depends on the type of failure mode