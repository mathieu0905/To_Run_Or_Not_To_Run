# RQ1: Cross-Agent Execution Analysis on SWE-bench

## Overview

This report analyzes execution patterns across different agent+model combinations
on SWE-bench Lite/Verified.

---

## Summary Table

| Submission | Agent | Model | Instances | Resolved | Resolve Rate | Avg Actions | Avg Bash | Avg Test | Test Ratio |
|------------|-------|-------|-----------|----------|--------------|-------------|----------|----------|------------|
| lite_20240402_sweagent_gpt4 | sweagent | gpt4 | 300 | 298 | 99.3% | 21.4 | 6.5 | 2.6 | 39.5% |
| lite_20240617_moatless_gpt4o | moatless | gpt4o | 300 | 296 | 98.7% | 9.3 | 0.0 | 0.0 | 0.0% |
| lite_20240620_sweagent_claude3.5sonnet | sweagent | claude3.5sonnet | 289 | 289 | 100.0% | 32.7 | 12.5 | 4.9 | 39.6% |
| lite_20240623_moatless_claude35sonnet | moatless | claude35sonnet | 300 | 295 | 98.3% | 8.6 | 0.0 | 0.0 | 0.0% |
| lite_20240728_sweagent_gpt4o | sweagent | gpt4o | 278 | 268 | 96.4% | 39.1 | 12.9 | 6.3 | 49.0% |
| lite_20240806_SuperCoder2.0 | supercoder | 2.0 | 300 | 0 | 0.0% | 5.0 | 0.0 | 0.0 | 0.0% |
| lite_20241025_OpenHands-CodeAct-2.1-sonn | openhands | CodeAct-2.1-sonnet-2 | 300 | 300 | 100.0% | 52.6 | 11.2 | 5.8 | 52.1% |
| verified_20240402_sweagent_claude3opus | sweagent | claude3opus | 443 | 423 | 95.5% | 18.8 | 6.8 | 2.8 | 41.0% |
| verified_20240402_sweagent_gpt4 | sweagent | gpt4 | 496 | 490 | 98.8% | 20.8 | 6.0 | 2.5 | 42.2% |
| verified_20240620_sweagent_claude3.5sonn | sweagent | claude3.5sonnet | 500 | 492 | 98.4% | 33.6 | 13.5 | 5.4 | 39.9% |
| verified_20240728_sweagent_gpt4o | sweagent | gpt4o | 465 | 453 | 97.4% | 38.9 | 12.7 | 6.2 | 48.7% |
| verified_20240820_honeycomb | other | honeycomb | 500 | 0 | 0.0% | 229.4 | 0.0 | 0.0 | 0.0% |
| verified_20241029_OpenHands-CodeAct-2.1- | openhands | CodeAct-2.1-sonnet-2 | 500 | 500 | 100.0% | 54.4 | 11.6 | 6.6 | 56.9% |
| verified_20241208_gru | other | gru | 500 | 0 | 0.0% | 5.0 | 0.0 | 0.0 | 0.0% |

---

## By Agent Type

| Agent Type | Instances | Avg Bash | Avg Test | Test Ratio |
|------------|-----------|----------|----------|------------|
| moatless | 600 | 0.0 | 0.0 | 0.0% |
| openhands | 800 | 11.4 | 6.3 | 55.1% |
| other | 1000 | 0.0 | 0.0 | 0.0% |
| supercoder | 300 | 0.0 | 0.0 | 0.0% |
| sweagent | 2771 | 10.0 | 4.3 | 43.2% |