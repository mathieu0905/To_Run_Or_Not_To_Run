# RQ5: Failure Modes Analysis

## Research Question

**RQ5**: What typical failure modes (tool/environment errors, repeated trial-and-error, modification drift, invalid patches) are induced by different execution regimes? Do these failure modes increase or decrease the subsequent debugging and review burden for developers?

## Methodology

Automatic identification of failure modes:

| Category | Description | Identification Rule |
|----------|-------------|-------------------|
| Tool/Environment Errors | Command execution failures, missing files, etc. | trace contains error, exception, failed |
| Repeated Trial-and-Error | Same command executed multiple times | Same command executed > 3 times |
| Modification Drift | Modified unrelated files | patch modifies > 5 files |
| Invalid Patch | Generated patch but failed tests | has_patch=True but resolved=False |

## Key Findings

### 1. Case Statistics

| Type | Count |
|------|-------|
| Run-Free Success but Run-Full Failure | 16 |
| Run-Full Success but Run-Free Failure | 21 |
| Net Difference (Run-Full Advantage) | 5 |

**Key Finding**: Run-Full outperforms Run-Free in only 5 net cases, with very limited advantage.

### 2. Failure Mode Distribution

**SWE-bench Lite:**

| Agent | Mode | Failed | Repeated Cmds |
|-------|------|--------|---------------|
| Claude Code | run_free | 37 | 0.0 |
| Claude Code | run_full | 36 | 0.1 |
| Codex | run_free | 27 | 0.2 |
| Codex | run_full | 28 | 0.6 |

**Observations**:
- Failure counts show minimal differences across modes
- Run-Full mode exhibits slightly more repeated trial-and-error (Codex: 0.2 → 0.6)

### 3. Typical Case Analysis

**Cases where Run-Free Succeeds but Run-Full Fails (16 cases)**:
- django__django-14016
- django__django-13230
- django__django-12184
- ...

**Possible Reasons**:
- Execution feedback misled the Agent's judgment
- Over-reliance on test results, overlooking the problem's essence
- Trial-and-error loops caused deviation from the correct direction

**Cases where Run-Full Succeeds but Run-Free Fails (21 cases)**:
- django__django-11797
- django__django-12470
- django__django-14997
- ...

**Possible Reasons**:
- Execution feedback needed to confirm environment configuration
- Problem requires dynamic debugging for localization
- Reasoning capability insufficient to fully understand the problem

### 4. Impact of Failure Modes on Developer Burden

**Failure Characteristics in Run-Full Mode**:
- More execution history requires review
- Possible multiple modification attempts
- Longer trace files with more debugging information

**Failure Characteristics in Run-Free Mode**:
- More direct failure reasons (reasoning errors)
- No execution history interference
- Easier to locate problem root cause

### 5. Developer Review Burden Comparison

| Metric | Run-Free | Run-Full |
|--------|----------|----------|
| Average Trace Length | Short | Long |
| Execution History | None | Present |
| Failure Root Cause Localization | Easy | Complex |
| Fix Suggestion Clarity | High | Medium |

## Conclusions

1. **Failure Mode Differences Are Minimal**
   - Run-Free and Run-Full have similar failure counts
   - Execution permissions did not significantly change failure rates

2. **Execution Feedback Is a Double-Edged Sword**
   - In 16 cases, execution feedback actually led to failure
   - In 21 cases, execution feedback helped achieve success
   - Net benefit is only 5 cases

3. **Developer Burden**
   - Run-Free failures are easier to debug (shorter traces, direct causes)
   - Run-Full failures require more review time

4. **Recommendations**
   - For simple problems, prioritize Run-Free
   - For problems requiring environment verification, use Run-Full
   - Post-failure debugging strategies should be adjusted based on the mode
