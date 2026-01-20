# RQ3: Execution Utility - Purpose Analysis of Execution Behavior

## Research Question

**RQ3**: Under different regimes, what are execution behaviors primarily used for (verification, localization, environment confirmation, trial-and-error loops)? Which types of executions bring actual benefits, and which are low-value overhead?

## Method

Automatically classify execution commands based on rules:

| Category | Description | Typical Commands |
|------|------|----------|
| Verification | Run test frameworks to validate fixes | pytest, unittest, manage.py test |
| Localization | Run scripts to locate problems | python script.py |
| Environment | Confirm environment configuration | python --version, pip list |
| Exploration | Explore file system and code | ls, find, cat, grep |

## Main Findings

### 1. Claude Code Execution Behavior Analysis

**SWE-bench Lite:**

| Mode | Total Exec | Verification | Localization | Environment | Exploration |
|------|--------|------|------|------|------|
| run_free | 693 | 59 (8.5%) | 16 (2.3%) | 44 (6.3%) | 493 (71.1%) |
| run_less_k1 | 1064 | 395 (37.1%) | 235 (22.1%) | 92 (8.6%) | 257 (24.2%) |
| run_full | 1804 | 703 (39.0%) | 239 (13.2%) | 342 (19.0%) | 375 (20.8%) |

**Key Observations**:
- Run-Free mode still has 693 "executions", but mainly exploration (ls, cat, etc.), with only 59 verification executions
- Run-Full mode has the highest proportion of verification executions (39%), indicating execution is primarily used for validating fixes
- From Run-Free to Run-Full, execution count increases by 160% (693 → 1804)

### 2. Codex Execution Behavior Analysis

**SWE-bench Lite:**

| Mode | Total Exec | Verification | Localization | Environment | Exploration | Other |
|------|--------|------|------|------|------|-------|
| run_free | 4324 | 0 (0%) | 0 (0%) | 0 (0%) | 2372 (54.9%) | 1952 (45.1%) |
| run_full | 4636 | 634 (13.7%) | 44 (0.9%) | 80 (1.7%) | 1090 (23.5%) | 2788 (60.1%) |

**Key Observations**:
- Codex has absolutely no verification executions in Run-Free mode (0 times)
- Codex's total execution count is far higher than Claude Code (4324 vs 693)
- Codex's "Other" category has a high proportion (45-60%), indicating more diverse execution behavior

### 3. Trial-and-Error Loop Analysis

| Agent | Mode | Repeated Commands |
|-------|------|------------|
| Claude Code | run_free | 8 |
| Claude Code | run_full | 124 |
| Codex | run_free | 2041 |
| Codex | run_full | 2122 |

**Key Observations**:
- Claude Code's trial-and-error loops increase with execution privileges (8 → 124)
- Codex's trial-and-error loops are high across all modes (~2000) with little variation
- This indicates Codex's execution behavior is more "blind", while Claude Code is more "purposeful"

### 4. Execution Efficiency Comparison

**Pass Rate improvement per verification execution**:

| Agent | Dataset | Verification Exec Increase | Pass Rate Increase | Efficiency |
|-------|---------|--------------|----------------|------|
| Claude Code | Lite | +644 | +1.0% | 0.0016%/exec |
| Claude Code | Verified | +587 | +3.0% | 0.0051%/exec |
| Codex | Lite | +634 | -1.0% | -0.0016%/exec |
| Codex | Verified | +592 | +2.0% | 0.0034%/exec |

**Conclusion**: The marginal benefit of each verification execution is extremely low (< 0.01%)

## Conclusion

1. **Verification is the primary execution purpose**
   - In modes with execution privileges, verification executions account for 35-40% (Claude Code)
   - Verification executions are used to confirm whether fixes are correct

2. **Exploration executions have high proportion but low value**
   - Exploration executions (ls, cat, grep) account for 20-70%
   - These executions can be replaced by static analysis

3. **Trial-and-error loops are prevalent**
   - Codex's trial-and-error loops are particularly severe (~2000 repeated commands)
   - This indicates execution feedback is not being effectively utilized

4. **Execution efficiency is extremely low**
   - Each verification execution brings < 0.01% Pass Rate improvement
   - Most executions are "low-value overhead"

5. **Significant agent differences**
   - Claude Code's executions are more purposeful (high verification proportion)
   - Codex's executions are more blind (high Other proportion, more trial-and-error)

## Impact on Research Hypothesis

Data indicates:
- Most executions are "low-value overhead" (exploration, trial-and-error)
- Verification executions have value but extremely low marginal benefit
- This supports the view that "execution environment is an engineering shortcut rather than a necessary capability"
