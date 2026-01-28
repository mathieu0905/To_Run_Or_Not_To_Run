# Cross-Agent Execution Analysis on SWE-bench

## Summary Table

| Agent | Model | Dataset | Instances | Avg Bash | Avg Test | Test Ratio |
|-------|-------|---------|-----------|----------|----------|------------|
| GRU | unknown | verified | 1000 | 0.1 | 0.1 | 47.2% |
| Honeycomb | unknown | verified | 500 | 65.1 | 19.1 | 29.3% |
| Moatless | GPT-4 | lite | 300 | 0.0 | 0.0 | 0.0% |
| Moatless | claude35sonnet | lite | 300 | 0.0 | 0.0 | 0.0% |
| OpenHands | CodeAct-2.1-sonnet-2 | lite | 300 | 11.2 | 5.8 | 52.1% |
| OpenHands | CodeAct-2.1-sonnet-2 | verified | 500 | 11.6 | 6.6 | 56.9% |
| OpenHands | claude-4-sonnet | verified | 500 | 38.2 | 19.0 | 49.8% |
| OpenHands | claude-opus-4-5 | verified | 489 | 0.0 | 0.0 | 0.0% |
| OpenHands | devstral-small | verified | 500 | 0.0 | 0.0 | 0.0% |
| OpenHands | gpt5 | verified | 500 | 25.7 | 5.0 | 19.5% |
| OpenHands | kimi-k2 | verified | 500 | 27.8 | 15.5 | 55.7% |
| OpenHands | qwen3-30b | verified | 500 | 34.7 | 15.4 | 44.5% |
| OpenHands | qwen3-480b | verified | 500 | 41.0 | 18.7 | 45.7% |
| OpenHands | unknown | verified | 500 | 21.0 | 9.2 | 43.7% |
| SWE-agent | Claude-3-Opus | lite | 300 | 6.5 | 2.5 | 38.1% |
| SWE-agent | Claude-3-Opus | verified | 443 | 7.0 | 2.9 | 41.9% |
| SWE-agent | Claude-3.5-Sonnet | lite | 289 | 12.9 | 5.3 | 41.4% |
| SWE-agent | Claude-3.5-Sonnet | verified | 500 | 13.9 | 5.8 | 41.7% |
| SWE-agent | GPT-4 | lite | 578 | 9.7 | 4.5 | 46.3% |
| SWE-agent | GPT-4 | verified | 961 | 9.3 | 4.4 | 47.0% |
| SuperCoder | 2.0 | lite | 300 | 0.0 | 0.0 | 0.0% |

## By Agent Type (Aggregated)

| Agent Type | Total Instances | Avg Bash | Avg Test | Test Ratio |
|------------|-----------------|----------|----------|------------|
| GRU | 1000 | 0.1 | 0.1 | 47.2% |
| Honeycomb | 500 | 65.1 | 19.1 | 29.3% |
| Moatless | 600 | 0.0 | 0.0 | 0.0% |
| OpenHands | 4789 | 21.6 | 9.7 | 45.0% |
| SWE-agent | 3071 | 9.9 | 4.3 | 43.9% |
| SuperCoder | 300 | 0.0 | 0.0 | 0.0% |