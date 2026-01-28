# RQ3 Comprehensive Analysis: Why Does Execution Have Limited Impact on Outcomes?

*Generated: 2026-01-28 16:46:08*

## Table of Contents

1. [Data Overview](#1-data-overview)
2. [RQ3.1 Verification Analysis](#2-rq31-verification-analysis)
3. [RQ3.2 File Localization Analysis](#3-rq32-file-localization-analysis)
4. [Agent Behavior Comparison](#4-agent-behavior-comparison)
5. [Key Findings and Conclusions](#5-key-findings-and-conclusions)

---

## 1. Data Overview

### Case Distribution

| Agent | P→P (Both Succeed) | F→F (Both Fail) |
|-------|-----------------|-----------------|
| Claude Code | 116 | 84 |
| Codex | 142 | 55 |

---

## 2. RQ3.1 Verification Analysis

**Question**: What are the results of verification execution after the first edit? Can it demonstrate that verification is redundant?

### Claude Code

#### P→P Cases (Both Modes Succeed)

| Metric | Unrestricted | Prohibited |
|------|-------------|------------|
| Instances with verification | 101 (87.1%) | 32 (27.6%) |
| First verification success | 6 (5.9%) | 5 (15.6%) |
| First verification fail (test) | 53 (52.5%) | 23 (71.9%) |
| First verification fail (env) | 42 (41.6%) | 4 (12.5%) |

#### F→F Cases (Both Modes Fail)

| Metric | Unrestricted | Prohibited |
|------|-------------|------------|
| Instances with verification | 80 (95.2%) | 23 (27.4%) |
| Any verification succeeded | 65 (81.2%) | N/A |

**Interpretation**:

- In P→P cases, first verification success rate is only 5.9%, indicating Agent needs multiple iterations to pass verification
- 41.6% of first verification failures are environment errors (pytest not installed, etc.), not code issues
- In F→F cases, 81.2% had successful verification at some point, but still failed ultimately → Agent's tests are inconsistent with evaluation tests

### Codex

#### P→P Cases (Both Modes Succeed)

| Metric | Unrestricted | Prohibited |
|------|-------------|------------|
| Instances with verification | 140 (98.6%) | 0 (0.0%) |
| First verification success | 48 (34.3%) | 0 (0.0%) |
| First verification fail (test) | 92 (65.7%) | 0 (0.0%) |
| First verification fail (env) | 0 (0.0%) | 0 (0.0%) |

#### F→F Cases (Both Modes Fail)

| Metric | Unrestricted | Prohibited |
|------|-------------|------------|
| Instances with verification | 52 (94.5%) | 1 (1.8%) |
| Any verification succeeded | 52 (100.0%) | N/A |

**Interpretation**:

- In P→P cases, first verification success rate is 34.3%
- In F→F cases, 100.0% had successful verification at some point, but still failed ultimately → Agent's tests are inconsistent with evaluation tests

---

## 3. RQ3.2 File Localization Analysis

**Question**: Can Agent accurately locate the files that need modification? Does execution help with localization?

### Claude Code

#### P→P Cases

| Metric | Unrestricted | Prohibited |
|------|-------------|------------|
| First edit is test file | 52 (44.8%) | 3 (2.6%) |
| First edit hits GT | 64 (55.2%) | 111 (95.7%) |
| Final edit hits GT | 113 (97.4%) | 114 (98.3%) |
| Average recall | 96.6% | 97.4% |
| Uses Reproduction | 19 (16.4%) | 1 (0.9%) |

**Interpretation**:

- Unrestricted mode has 44.8% first edits on test files (vs Prohibited 2.6%)
  - This explains the difference in first edit hit rate: Unrestricted writes tests first to reproduce the issue
- Final edit hit rates are both high (97.4% vs 98.3%), indicating comparable localization ability
- Only 16.4% use Reproduction, suggesting problem descriptions are clear enough

### Codex

#### P→P Cases

| Metric | Unrestricted | Prohibited |
|------|-------------|------------|
| First edit is test file | 3 (2.1%) | 2 (1.4%) |
| First edit hits GT | 137 (96.5%) | 136 (95.8%) |
| Final edit hits GT | 140 (98.6%) | 136 (95.8%) |
| Average recall | 96.4% | 93.6% |
| Uses Reproduction | 6 (4.2%) | 0 (0.0%) |

**Interpretation**:

- Final edit hit rates are both high (98.6% vs 95.8%), indicating comparable localization ability
- Only 4.2% use Reproduction, suggesting problem descriptions are clear enough

---

## 4. Agent Behavior Comparison

### P→P Case Behavior Statistics

| Agent | Mode | Avg Conversation Turns | Avg Edit Count | Avg Test Count |
|-------|------|------------|------------|------------|
| Claude Code | Unrestricted | 93.7 | 5.0 | 8.8 |
| Claude Code | Prohibited | 44.5 | 1.8 | 1.1 |
| Codex | Unrestricted | 70.7 | 3.1 | 3.3 |
| Codex | Prohibited | 68.3 | 3.2 | 0.0 |

### Behavior Difference Analysis

**Claude Code**:
- Unrestricted averages 8.8 test executions vs Prohibited 1.1
- Unrestricted averages 5.0 edits vs Prohibited 1.8
- **More iterations did not lead to better results**: Both succeed, but Unrestricted consumes more resources

---

## 5. Key Findings and Conclusions

### Key Findings

| # | Finding | Evidence |
|---|------|------|
| 1 | **Claude Code: Limited value of verification feedback** | P→P first verification success rate only 5.9% |
| 2 | **Codex: Limited value of verification feedback** | P→P first verification success rate only 34.3% |
| 3 | **Claude Code: Environment errors interfere with verification** | 41.6% of first verifications are environment errors |
| 4 | **Claude Code: Verification inconsistent with evaluation** | In F→F, 81.2% had successful verification but ultimately failed |
| 5 | **Codex: Verification inconsistent with evaluation** | In F→F, 100.0% had successful verification but ultimately failed |
| 6 | **Claude Code: Localization doesn't need execution** | Only 16.4% used Reproduction, but 97.4% hit GT |
| 7 | **Codex: Localization doesn't need execution** | Only 4.2% used Reproduction, but 98.6% hit GT |
| 8 | **Claude Code: More iterations ≠ better** | Unrestricted 8.8 tests vs Prohibited 1.1 |
| 9 | **Codex: More iterations ≠ better** | Unrestricted 3.3 tests vs Prohibited 0.0 |

### Conclusions

**Why does execution have limited impact on outcomes?**

1. **Problem descriptions are clear enough**: Agent can locate files through static analysis without dynamic execution for reproduction
2. **Verification feedback is noisy**: Environment errors and test inconsistencies reduce the value of verification
3. **Iteration may lead to over-fixing**: More edits may introduce unnecessary changes
4. **Core capability is understanding**: Regardless of execution, Agent's code comprehension ability is the key to success

> **Execution feedback is a double-edged sword**: It can help discover problems, but may also mislead Agent into making unnecessary modifications.
> When problem descriptions are clear enough, "getting it right the first time" is more effective than "trial-and-error iteration".
