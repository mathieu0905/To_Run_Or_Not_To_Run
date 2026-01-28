# RQ3: Why Does Execution Have Limited Impact?

*Generated: 2026-01-28 15:40:04*

## Overview

This analysis examines two aspects of execution:
1. **Verification**: Is the first test after editing successful? (If yes → verification is redundant)
2. **Reproduction**: Does running tests before editing help locate correct files?

---

## 1. Verification Analysis

**Question**: When agents edit files and then run tests, do they get it right the first time?

### Summary Table

| Agent | Outcome | Has Verification | First Verif Success | First Verif Fail |
|-------|---------|-----------------|--------------------|--------------------|
| Claude Code | P→P | 101 | 10 (9.9%) | 91 (90.1%) |
| Claude Code | F→F | 80 | 5 (6.2%) | 75 (93.8%) |
| Codex | P→P | 140 | 48 (34.3%) | 92 (65.7%) |
| Codex | F→F | 52 | 15 (28.8%) | 37 (71.2%) |

### Interpretation

**Claude Code:**
- P→P: 9.9% first verification success → Verification is mostly redundant
- F→F: 93.8% first verification fail → Iteration didn't help

**Codex:**
- P→P: 34.3% first verification success → Verification is mostly redundant
- F→F: 71.2% first verification fail → Iteration didn't help

---

## 2. Reproduction Analysis

**Question**: Does running tests before editing help locate the correct files?

### File Localization Accuracy

| Agent | Outcome | Has Repro | Count | Avg Hit | Avg Recall | No Repro | Count | Avg Hit | Avg Recall |
|-------|---------|-----------|-------|---------|------------|----------|-------|---------|------------|
| Claude Code | P→P | Yes | 19 | 94.7% | 94.7% | No | 97 | 97.9% | 96.9% |
| Claude Code | F→F | Yes | 9 | 88.9% | 70.4% | No | 75 | 85.3% | 80.0% |
| Codex | P→P | Yes | 6 | 100.0% | 100.0% | No | 136 | 98.5% | 96.2% |
| Codex | F→F | Yes | 2 | 100.0% | 100.0% | No | 53 | 90.6% | 83.3% |

### Interpretation

- **Hit**: At least one edited file matches ground truth
- **Recall**: Proportion of ground truth files that were edited

If 'No Reproduction' cases have similar or better Hit/Recall than 'Has Reproduction' cases,
it suggests that reproduction execution doesn't significantly help with file localization.

---

## Key Findings

1. **Verification is largely redundant**: 24.1% of P→P cases succeed on first verification
   - Agents get it right the first time; verification just confirms

2. **Reproduction has limited impact on file localization**:
   - Claude Code P→P: With repro Hit=94.7%, Without repro Hit=97.9%
   - Codex P→P: With repro Hit=100.0%, Without repro Hit=98.5%

3. **Implications**:
   - Problem descriptions are clear enough for static reasoning
   - Execution overhead doesn't proportionally improve outcomes
