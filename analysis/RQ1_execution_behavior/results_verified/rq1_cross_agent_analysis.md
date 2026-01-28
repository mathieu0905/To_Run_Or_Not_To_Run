# RQ1: Cross-Agent Execution Analysis on SWE-bench

## Overview

This report analyzes execution patterns across different agent+model combinations
on SWE-bench Lite/Verified.

---

## Summary Table

| Submission | Agent | Model | Instances | Resolved | Resolve Rate | Avg Actions | Avg Bash | Avg Test | Test Ratio |
|------------|-------|-------|-----------|----------|--------------|-------------|----------|----------|------------|
| 20240402_sweagent_gpt4 | sweagent | gpt4 | 496 | 490 | 98.8% | 20.8 | 6.0 | 2.5 | 42.2% |
| 20240620_sweagent_claude3.5sonnet | sweagent | claude3.5sonnet | 500 | 492 | 98.4% | 33.6 | 13.5 | 5.4 | 39.9% |
| 20240728_sweagent_gpt4o | sweagent | gpt4o | 465 | 453 | 97.4% | 38.9 | 12.7 | 6.2 | 48.7% |
| 20241208_gru | other | gru | 500 | 0 | 0.0% | 5.0 | 0.0 | 0.0 | 0.0% |

---

## By Agent Type

| Agent Type | Instances | Avg Bash | Avg Test | Test Ratio |
|------------|-----------|----------|----------|------------|
| other | 500 | 0.0 | 0.0 | 0.0% |
| sweagent | 1461 | 10.7 | 4.7 | 43.7% |