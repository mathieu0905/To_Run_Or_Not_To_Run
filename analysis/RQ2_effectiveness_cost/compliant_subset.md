# Prohibited vs. Unrestricted Resolve Rates on Compliant Subsets

For each (dataset, agent) pair we compute three subsets and report the Prohibited and Unrestricted resolve rates on each. "All" is the full 100 instances. "Env-clean" keeps only instances whose executions never hit an environment error in any of the five modes---so Prohibited vs. Unrestricted comparisons on this subset are not affected by env-error noise. "Prohibit-strict" keeps only instances where the agent produced zero actionable executions in Prohibited mode, i.e. the subset that strictly obeyed the prompt-level restriction.

| Dataset | Agent | Subset | N | Prohibited | Unrestricted | Gap (pp) |
|---------|-------|--------|--:|-----------:|-------------:|---------:|
| Lite | Claude Code | All (100) | 100 | 63/100 (63.0\%) | 64/100 (64.0\%) | -1.0 |
| Lite | Claude Code | Env-clean | 7 | 3/7 (42.9\%) | 3/7 (42.9\%) | +0.0 |
| Lite | Claude Code | Prohibit-strict | 82 | 53/82 (64.6\%) | 54/82 (65.9\%) | -1.2 |
| Lite | Codex | All (100) | 100 | 74/100 (74.0\%) | 73/100 (73.0\%) | +1.0 |
| Lite | Codex | Env-clean | 17 | 13/17 (76.5\%) | 12/17 (70.6\%) | +5.9 |
| Lite | Codex | Prohibit-strict | 100 | 74/100 (74.0\%) | 73/100 (73.0\%) | +1.0 |
| Lite | OpenCode+Qwen2.5-Coder | All (100) | 100 | 7/100 (7.0\%) | 6/100 (6.0\%) | +1.0 |
| Lite | OpenCode+Qwen2.5-Coder | Env-clean | 51 | 2/51 (3.9\%) | 3/51 (5.9\%) | -2.0 |
| Lite | OpenCode+Qwen2.5-Coder | Prohibit-strict | 93 | 7/93 (7.5\%) | 6/93 (6.5\%) | +1.1 |
| Verified | Claude Code | All (100) | 100 | 64/100 (64.0\%) | 67/100 (67.0\%) | -3.0 |
| Verified | Claude Code | Env-clean | 22 | 10/22 (45.5\%) | 11/22 (50.0\%) | -4.5 |
| Verified | Claude Code | Prohibit-strict | 84 | 52/84 (61.9\%) | 56/84 (66.7\%) | -4.8 |
| Verified | Codex | All (100) | 100 | 73/100 (73.0\%) | 75/100 (75.0\%) | -2.0 |
| Verified | Codex | Env-clean | 34 | 27/34 (79.4\%) | 28/34 (82.4\%) | -2.9 |
| Verified | Codex | Prohibit-strict | 99 | 73/99 (73.7\%) | 75/99 (75.8\%) | -2.0 |
| Verified | OpenCode+Qwen2.5-Coder | All (100) | 100 | 13/100 (13.0\%) | 14/100 (14.0\%) | -1.0 |
| Verified | OpenCode+Qwen2.5-Coder | Env-clean | 46 | 6/46 (13.0\%) | 6/46 (13.0\%) | +0.0 |
| Verified | OpenCode+Qwen2.5-Coder | Prohibit-strict | 100 | 13/100 (13.0\%) | 14/100 (14.0\%) | -1.0 |
