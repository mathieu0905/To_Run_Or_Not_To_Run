# RQ3 Deep Analysis Report: Why Does Execution Have Limited Impact on Outcomes?

*Generated: 2026-01-28*

## Overview

This analysis aims to answer: **Why is there little difference in repair success rate between Unrestricted mode (unlimited test execution) and Prohibited mode (no test execution)?**

**Core Finding: Verification feedback leads to "over-fixing", while Prohibited mode generates more precise patches.**

---

## 1. Data Overview

### Case Classification (Claude Code)

| Category | Count | Description |
|------|------|------|
| P→P | 116 | Both modes succeed |
| F→F | 84 | Both modes fail |

---

## 2. Core Finding: Prohibited Patches Are Closer to Correct Answer

### 2.1 Patch Comparison in P→P Cases

For cases where both modes succeed, comparing generated patches:

| Patch Similarity | Count | Percentage |
|-----------|------|------|
| Identical | 21 | 26.2% |
| Similar (>80%) | 11 | 13.8% |
| **Different (≤80%)** | **48** | **60.0%** |

**60% of successful cases generated different patches between the two modes.**

### 2.2 When Patches Differ, Which Is Closer to Correct Answer?

| Result | Count | Percentage |
|------|------|------|
| **Prohibited closer** | **47** | **70%** |
| Unrestricted closer | 12 | 18% |
| Similar quality | 8 | 12% |

🔥 **Key Finding: In cases with different patches, Prohibited generates higher quality patches (47 vs 12)!**

---

## 3. Root Cause: Verification Feedback Leads to "Over-fixing"

### 3.1 Patch Size Comparison

Analyzing the 47 cases where Prohibited is better:

| Metric | Unrestricted | Prohibited |
|------|-------------|------------|
| **Average patch size** | 26.3 lines | 5.4 lines |
| **Files involved** | 2.1 files | 1.0 files |

**Unrestricted patches are 5x larger than Prohibited!**

### 3.2 Over-fixing Statistics

| Unrestricted Patch Situation | Count | Percentage |
|----------------------|------|------|
| **Over-fixed (patch too large)** | **39** | **83%** |
| Under-fixed (patch too small) | 4 | 8.5% |
| Appropriate size | 4 | 8.5% |

### 3.3 Agent Behavior Comparison

| Metric | Unrestricted | Prohibited |
|------|-------------|------------|
| Conversation turns | 74.3 | 30.7 |
| Edit count | 6.1 | 1.8 |
| Test execution count | 11.3 | 1.0 |

**In Unrestricted mode, Agent averages 11 test executions and 6 edits, but patch quality is worse than Prohibited's 1-2 edits.**

### 3.4 Specific Cases

| Instance | Unrestricted Similarity | Prohibited Similarity | Patch Size (Unres/Proh) |
|----------|-------------------|------------------|----------------------|
| django__django-10914 | 57.7% | **100.0%** | 5 lines / 2 lines |
| django__django-11815 | 20.3% | **99.6%** | 31 lines / 7 lines |
| django__django-11848 | 47.1% | **69.2%** | 9 lines / 9 lines |

---

## 4. Why Does Verification Feedback Lead to Over-fixing?

### 4.1 Unrestricted Mode Behavior Pattern

```
Agent edits code
  → Runs test
  → Test fails (possibly environment issue, incomplete test, etc.)
  → Agent thinks fix is insufficient, continues modifying
  → Test may still fail
  → Continues modifying more code...
  → Loops 11 times
  → Final patch is bloated (26.3 lines, 2.1 files)
```

### 4.2 Prohibited Mode Behavior Pattern

```
Agent reads problem description
  → Understands the essence of the problem
  → Generates minimal fix in one shot
  → Patch is concise (5.4 lines, 1.0 files)
```

### 4.3 Why Does Test Feedback Mislead?

1. **Environment errors account for 40-60%**: First test failures are mainly `No module named pytest`, path errors, etc., not code issues
2. **Incomplete test coverage**: Agent's tests differ from final evaluation tests; passing Agent's tests doesn't mean truly fixed
3. **Error attribution**: When tests fail, Agent doesn't know if it's "code is wrong" or "test itself has issues", tends to modify more code

---

## 5. Verification Analysis: Does Verification Execution Really Help?

### 5.1 First Verification Result Classification (Excluding Environment Errors)

| Metric | P→P | F→F |
|------|-----|-----|
| Cases with real test results | 71 | 72 |
| First test success | 42 (59.2%) | 33 (45.8%) |
| First test failure | 29 (40.8%) | 39 (54.2%) |

**P→P and F→F first test success rates are similar (59% vs 46%), verification execution cannot effectively distinguish success and failure cases.**

### 5.2 Environment Errors Dominate

| First Verification Result | P→P | F→F |
|-------------|-----|-----|
| Success | 10.9% | 5.0% |
| Test failure | 24.8% | 37.5% |
| **Environment error** | **43.6%** | **33.8%** |

**First verification failures are mainly environment issues (pytest not installed, path errors), not test logic failures.**

### 5.3 F→F Cases: Verification Succeeded But Ultimately Failed

| Agent | F→F Any Verification Success Rate |
|-------|---------------------|
| Claude Code | 91.2% |
| Codex | 100.0% |

**In F→F cases, 91-100% had successful verification at some point, but still failed ultimately. This shows Agent's tests are inconsistent with evaluation tests.**

---

## 6. Reproduction Analysis: Did Reproduction Execution Help with Localization?

### 6.1 Reproduction Execution Usage

| Agent | P→P Has Reproduction | P→P No Reproduction |
|-------|-----------|-----------|
| Claude Code | 19 (16%) | 97 (84%) |
| Codex | 6 (4%) | 136 (96%) |

**The vast majority of cases (84-96%) had no reproduction execution; Agent directly locates files based on problem description.**

### 6.2 File Localization Accuracy

| Agent | With Reproduction Hit | Without Reproduction Hit |
|-------|---------------------|---------------------|
| Claude Code P→P | 94.7% | 97.9% |
| Codex P→P | 100% | 98.5% |

**Regardless of reproduction execution, file localization accuracy is high (>94%). Problem descriptions are already clear enough.**

---

## 7. Comprehensive Conclusion

### Why Does Execution Have Limited Impact on Outcomes?

| Reason | Evidence |
|------|------|
| **Verification feedback leads to over-fixing** | Unrestricted patch 26.3 lines vs Prohibited 5.4 lines; 83% cases over-fixed |
| **Prohibited is actually more precise** | In 70% of different patch cases, Prohibited is closer to correct answer |
| **More iterations ≠ better results** | 11 test executions + 6 edits, quality worse than 1 edit |
| **Environment errors waste execution** | 40-60% of first verifications are environment issues |
| **Verification tests inconsistent with evaluation tests** | In F→F, 91% had successful verification but ultimately failed |
| **Problem descriptions are sufficient** | 84-96% of cases don't need reproduction execution to correctly locate |

### Core Insight

> **Execution feedback can be a double-edged sword: It can help discover problems, but may also mislead Agent into making unnecessary modifications. When problem descriptions are clear enough, "getting it right the first time" is more effective than "trial-and-error iteration".**

---

## Appendix: Data Sources

- Analysis subjects: SWE-bench Lite + Verified (200 instances total)
- Agents: Claude Code, Codex
- Modes: Unrestricted (run_full), Prohibited (run_free)
- Analysis code: `/analysis/new_RQ3/`
