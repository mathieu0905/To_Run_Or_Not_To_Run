# RQ1: Cross-Agent Execution Analysis on SWE-bench

## Overview

This report analyzes execution patterns across different agent+model combinations
on SWE-bench Lite/Verified.

---

## Summary Table

| Submission | Agent | Model | Instances | Resolved | Resolve Rate | Avg Actions | Avg Bash | Avg Test | Test Ratio |
|------------|-------|-------|-----------|----------|--------------|-------------|----------|----------|------------|
| 20240402_sweagent_gpt4 | sweagent | gpt4 | 300 | 298 | 99.3% | 21.4 | 6.5 | 2.6 | 39.5% |
| 20240617_moatless_gpt4o | moatless | gpt4o | 300 | 290 | 96.7% | 9.3 | 0.0 | 0.0 | 0.0% |
| 20240620_sweagent_claude3.5sonnet | sweagent | claude3.5sonnet | 289 | 289 | 100.0% | 32.7 | 12.5 | 4.9 | 39.6% |
| 20240623_moatless_claude35sonnet | moatless | claude35sonnet | 300 | 286 | 95.3% | 8.6 | 0.0 | 0.0 | 0.0% |
| 20240728_sweagent_gpt4o | sweagent | gpt4o | 278 | 268 | 96.4% | 39.1 | 12.9 | 6.3 | 49.0% |
| 20240806_SuperCoder2.0 | supercoder | 2.0 | 300 | 0 | 0.0% | 5.0 | 0.0 | 0.0 | 0.0% |
| 20241025_OpenHands-CodeAct-2.1-sonnet-20 | openhands | CodeAct-2.1-sonnet-2 | 300 | 300 | 100.0% | 52.6 | 11.2 | 5.8 | 52.1% |

---

## By Agent Type

| Agent Type | Instances | Avg Bash | Avg Test | Test Ratio |
|------------|-----------|----------|----------|------------|
| moatless | 600 | 0.0 | 0.0 | 0.0% |
| openhands | 300 | 11.2 | 5.8 | 52.1% |
| supercoder | 300 | 0.0 | 0.0 | 0.0% |
| sweagent | 867 | 10.5 | 4.6 | 43.3% |