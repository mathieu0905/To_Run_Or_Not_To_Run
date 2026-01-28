# RQ3: Verification vs Reproduction Execution Analysis

*Generated: 2026-01-28 15:16:14*

## Overview

This analysis distinguishes two types of test execution based on timing:
- **Reproduction**: Test executions BEFORE the first file edit (understanding/locating the bug)
- **Verification**: Test executions AFTER the first file edit (validating the fix)

We compare **Unrestricted** (run_full) vs **Prohibited** (run_free) modes.

---

## Summary Table

| Agent | Mode | Instances | Reproduction Execs | Repro Success | Verification Execs | Verif Success |
|-------|------|-----------|-------------------|---------------|-------------------|---------------|
| Claude Code | Unrestricted | 200 | 69 | 72.5% | 1784 | 70.8% |
| Claude Code | Prohibited | 200 | 3 | 66.7% | 269 | 68.0% |
| Codex | Unrestricted | 200 | 15 | 53.3% | 618 | 52.1% |
| Codex | Prohibited | 200 | 0 | N/A | 1 | 100.0% |

---

## Claude Code Analysis

### Unrestricted Mode

- **Instances analyzed**: 200
- **Instances with file edits**: 200

**Reproduction (before first edit):**
- Total executions: 69
- Success rate: 72.5% (50/69)
- Instances with reproduction: 28 (14.0%)

**Verification (after first edit):**
- Total executions: 1784
- Success rate: 70.8% (1263/1784)
- Instances with verification: 181 (90.5%)

### Prohibited Mode

- **Instances analyzed**: 200
- **Instances with file edits**: 200

**Reproduction (before first edit):**
- Total executions: 3
- Success rate: 66.7% (2/3)
- Instances with reproduction: 3 (1.5%)

**Verification (after first edit):**
- Total executions: 269
- Success rate: 68.0% (183/269)
- Instances with verification: 55 (27.5%)

### Claude Code: Unrestricted vs Prohibited Comparison

| Metric | Unrestricted | Prohibited | Difference |
|--------|-------------|------------|------------|
| Total test executions | 1853 | 272 | +1581 |
| Reproduction executions | 69 | 3 | +66 |
| Verification executions | 1784 | 269 | +1515 |
| Avg executions/instance | 9.3 | 1.4 | +7.9 |

---

## Codex Analysis

### Unrestricted Mode

- **Instances analyzed**: 200
- **Instances with file edits**: 200

**Reproduction (before first edit):**
- Total executions: 15
- Success rate: 53.3% (8/15)
- Instances with reproduction: 8 (4.0%)

**Verification (after first edit):**
- Total executions: 618
- Success rate: 52.1% (322/618)
- Instances with verification: 195 (97.5%)

### Prohibited Mode

- **Instances analyzed**: 200
- **Instances with file edits**: 200

**Reproduction (before first edit):**
- Total executions: 0
- Instances with reproduction: 0 (0.0%)

**Verification (after first edit):**
- Total executions: 1
- Success rate: 100.0% (1/1)
- Instances with verification: 1 (0.5%)

### Codex: Unrestricted vs Prohibited Comparison

| Metric | Unrestricted | Prohibited | Difference |
|--------|-------------|------------|------------|
| Total test executions | 633 | 1 | +632 |
| Reproduction executions | 15 | 0 | +15 |
| Verification executions | 618 | 1 | +617 |
| Avg executions/instance | 3.2 | 0.0 | +3.2 |

---

## Key Findings

### 1. Verification Dominates Execution Patterns

In Unrestricted mode, **96.6%** of test executions occur AFTER the first file edit (verification), 
while only **3.4%** occur before (reproduction).

- Unrestricted: 84 reproduction vs 2402 verification (ratio 1:28)
- Prohibited: 3 reproduction vs 270 verification

### 2. Reproduction is Rare

Very few test executions occur before the first file edit, suggesting agents rely on 
static reasoning from problem descriptions rather than dynamic exploration.

- **Claude Code** (Unrestricted): 28/200 instances (14.0%) had reproduction executions
- **Codex** (Unrestricted): 8/200 instances (4.0%) had reproduction executions

### 3. Implications for RQ3

This analysis supports the paper's argument that **execution has limited impact** because:

1. **Agents rarely use execution for bug reproduction** - they jump straight to making edits based on the problem description
2. **Verification is mostly redundant** - when agents get the fix right, it's not because verification helped them iterate
3. **The execution overhead is substantial** - Unrestricted mode uses significantly more test executions without proportional benefit
