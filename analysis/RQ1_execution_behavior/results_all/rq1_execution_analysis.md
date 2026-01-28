# RQ1: Execution Frequency Analysis on SWE-bench

## Overview

This report analyzes **execution patterns** of execution-based agents on SWE-bench.
Pure-reasoning agents (Moatless, SuperCoder, etc.) are excluded.

**Total traces analyzed:** 2628

---

## Summary by Submission

| Split | Agent | Model | Instances | Avg Bash | Avg Test | Test Ratio |
|-------|-------|-------|-----------|----------|----------|------------|
| lite | sweagent | gpt-4 | 300 | 6.5 | 2.6 | 39.6% |
| lite | sweagent | claude-3.5-sonnet | 289 | 12.6 | 5.2 | 41.4% |
| lite | sweagent | gpt-4o | 278 | 12.9 | 6.5 | 50.0% |
| lite | openhands | claude-3.5-sonnet | 300 | 11.2 | 5.9 | 52.4% |
| verified | sweagent | gpt-4 | 496 | 6.0 | 2.5 | 42.4% |
| verified | sweagent | claude-3.5-sonnet | 500 | 13.6 | 5.6 | 41.1% |
| verified | sweagent | gpt-4o | 465 | 12.8 | 6.3 | 49.5% |

---

## Summary by Agent Type

| Agent | Total Instances | Avg Bash/Instance | Avg Test/Instance | Test Ratio |
|-------|-----------------|-------------------|-------------------|------------|
| openhands | 300 | 11.2 | 5.9 | 52.4% |
| sweagent | 2328 | 10.7 | 4.8 | 44.5% |

---

## Summary by Model

| Model | Total Instances | Avg Bash/Instance | Avg Test/Instance | Test Ratio |
|-------|-----------------|-------------------|-------------------|------------|
| claude-3.5-sonnet | 1089 | 12.7 | 5.6 | 43.9% |
| gpt-4 | 796 | 6.2 | 2.6 | 41.3% |
| gpt-4o | 743 | 12.8 | 6.4 | 49.7% |

---

## Distribution Statistics

### Bash Commands per Instance

- **Min:** 0
- **Max:** 80
- **Mean:** 10.7
- **Median:** 8.0
- **Std Dev:** 9.1

### Test Executions per Instance

- **Min:** 0
- **Max:** 37
- **Mean:** 4.9
- **Median:** 3.0
- **Std Dev:** 5.5

---

## Key Findings

1. **Overall Test Execution Ratio:** 45.4% of bash commands are test executions

2. **Average Bash Commands:** 10.7 per instance

3. **Average Test Executions:** 4.9 per instance

4. **SWE-agent:** 44.5% test ratio (2328 instances)
5. **OpenHands:** 52.4% test ratio (300 instances)
