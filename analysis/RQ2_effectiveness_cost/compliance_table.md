# Execution Compliance by Mode

For each (dataset, agent, mode) cell: **Attempted** = test-framework invocations launched by the agent (pytest / unittest / manage.py test / tox / nose / direct `.py` script); **Env-Error** = blocked by import / missing-module / dependency errors before reaching the test stage; **Completed** = reached the test stage (i.e. not blocked by env errors) and produced non-empty output; **Actionable** = produced a concrete pass/fail test signal the agent could use to guide the next edit (subset of Completed). Counts are totals across 100 instances; per-task averages are in parentheses.

## SWE-bench Lite

| Agent | Mode | Instances (with exec) | Attempted | Env-Error | Completed | Actionable |
|-------|------|----------------------:|----------:|----------:|----------:|-----------:|
| Claude Code | Prohibited | 100 (18) | 79 (0.79) | 22 (0.22) | 55 (0.55) | 39 (0.39) |
| Claude Code | Quota-1 | 100 (89) | 639 (6.39) | 182 (1.82) | 452 (4.52) | 269 (2.69) |
| Claude Code | Quota-3 | 100 (98) | 844 (8.44) | 210 (2.10) | 625 (6.25) | 391 (3.91) |
| Claude Code | Budget-Guided | 100 (84) | 803 (8.03) | 181 (1.81) | 617 (6.17) | 396 (3.96) |
| Claude Code | Unrestricted | 100 (94) | 952 (9.52) | 197 (1.97) | 741 (7.41) | 530 (5.30) |
| Claude Code | run_hard_free | 1 (0) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| Codex | Prohibited | 100 (0) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| Codex | Quota-1 | 100 (97) | 124 (1.24) | 55 (0.55) | 54 (0.54) | 47 (0.47) |
| Codex | Quota-3 | 100 (90) | 265 (2.65) | 48 (0.48) | 190 (1.90) | 172 (1.72) |
| Codex | Budget-Guided | 100 (86) | 243 (2.43) | 52 (0.52) | 158 (1.58) | 141 (1.41) |
| Codex | Unrestricted | 100 (100) | 343 (3.43) | 54 (0.54) | 263 (2.63) | 234 (2.34) |
| OpenCode+Qwen2.5-Coder | Prohibited | 100 (7) | 77 (0.77) | 6 (0.06) | 71 (0.71) | 14 (0.14) |
| OpenCode+Qwen2.5-Coder | Quota-1 | 100 (71) | 1293 (12.93) | 58 (0.58) | 1219 (12.19) | 549 (5.49) |
| OpenCode+Qwen2.5-Coder | Quota-3 | 100 (71) | 1207 (12.07) | 135 (1.35) | 1054 (10.54) | 301 (3.01) |
| OpenCode+Qwen2.5-Coder | Budget-Guided | 100 (63) | 1130 (11.30) | 73 (0.73) | 1033 (10.33) | 331 (3.31) |
| OpenCode+Qwen2.5-Coder | Unrestricted | 100 (58) | 1066 (10.66) | 91 (0.91) | 951 (9.51) | 222 (2.22) |

## SWE-bench Verified

| Agent | Mode | Instances (with exec) | Attempted | Env-Error | Completed | Actionable |
|-------|------|----------------------:|----------:|----------:|----------:|-----------:|
| Claude Code | Prohibited | 100 (16) | 76 (0.76) | 17 (0.17) | 59 (0.59) | 36 (0.36) |
| Claude Code | Quota-1 | 100 (81) | 611 (6.11) | 153 (1.53) | 452 (4.52) | 290 (2.90) |
| Claude Code | Quota-3 | 100 (91) | 734 (7.34) | 157 (1.57) | 573 (5.73) | 325 (3.25) |
| Claude Code | Budget-Guided | 100 (80) | 678 (6.78) | 145 (1.45) | 530 (5.30) | 365 (3.65) |
| Claude Code | Unrestricted | 100 (89) | 860 (8.60) | 152 (1.52) | 700 (7.00) | 498 (4.98) |
| Claude Code | run_hard_free | 100 (0) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| Codex | Prohibited | 100 (1) | 1 (0.01) | 0 (0.00) | 1 (0.01) | 0 (0.00) |
| Codex | Quota-1 | 100 (89) | 119 (1.19) | 43 (0.43) | 59 (0.59) | 50 (0.50) |
| Codex | Quota-3 | 100 (95) | 240 (2.40) | 30 (0.30) | 193 (1.93) | 169 (1.69) |
| Codex | Budget-Guided | 100 (90) | 209 (2.09) | 38 (0.38) | 144 (1.44) | 125 (1.25) |
| Codex | Unrestricted | 100 (100) | 319 (3.19) | 30 (0.30) | 264 (2.64) | 229 (2.29) |
| OpenCode+Qwen2.5-Coder | Prohibited | 100 (0) | 0 (0.00) | 0 (0.00) | 0 (0.00) | 0 (0.00) |
| OpenCode+Qwen2.5-Coder | Quota-1 | 100 (75) | 1101 (11.01) | 55 (0.55) | 1035 (10.35) | 410 (4.10) |
| OpenCode+Qwen2.5-Coder | Quota-3 | 100 (74) | 950 (9.50) | 91 (0.91) | 855 (8.55) | 141 (1.41) |
| OpenCode+Qwen2.5-Coder | Budget-Guided | 100 (68) | 1042 (10.42) | 90 (0.90) | 943 (9.43) | 286 (2.86) |
| OpenCode+Qwen2.5-Coder | Unrestricted | 100 (59) | 1147 (11.47) | 66 (0.66) | 1074 (10.74) | 299 (2.99) |
