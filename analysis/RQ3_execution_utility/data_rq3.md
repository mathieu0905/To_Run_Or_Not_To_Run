# RQ3: Execution Utility - Data Tables

Analysis data on the purpose of execution behavior.

## Execution Purpose Classification Distribution

### SWE-bench Lite

| Agent | Mode | Total | Verification | Localization | Environment | Exploration | Other |
|-------|------|-------|--------------|--------------|-------------|-------------|-------|
| claude_code | run_free | 693 | 59 (8.5%) | 16 (2.3%) | 44 (6.3%) | 493 (71.1%) | 81 (11.7%) |
| claude_code | run_less_k1 | 1064 | 395 (37.1%) | 235 (22.1%) | 92 (8.6%) | 257 (24.2%) | 85 (8.0%) |
| claude_code | run_less_k3 | 1372 | 516 (37.6%) | 310 (22.6%) | 122 (8.9%) | 299 (21.8%) | 125 (9.1%) |
| claude_code | run_cost | 1450 | 541 (37.3%) | 254 (17.5%) | 175 (12.1%) | 355 (24.5%) | 125 (8.6%) |
| claude_code | run_full | 1804 | 703 (39.0%) | 239 (13.2%) | 342 (19.0%) | 375 (20.8%) | 145 (8.0%) |
| codex | run_free | 4324 | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 2372 (54.9%) | 1952 (45.1%) |
| codex | run_less_k1 | 4040 | 226 (5.6%) | 22 (0.5%) | 26 (0.6%) | 1064 (26.3%) | 2702 (66.9%) |
| codex | run_less_k3 | 4760 | 488 (10.3%) | 37 (0.8%) | 168 (3.5%) | 1246 (26.2%) | 2821 (59.3%) |
| codex | run_cost | 4562 | 442 (9.7%) | 42 (0.9%) | 82 (1.8%) | 1072 (23.5%) | 2924 (64.1%) |
| codex | run_full | 4636 | 634 (13.7%) | 44 (0.9%) | 80 (1.7%) | 1090 (23.5%) | 2788 (60.1%) |

### SWE-bench Verified

| Agent | Mode | Total | Verification | Localization | Environment | Exploration | Other |
|-------|------|-------|--------------|--------------|-------------|-------------|-------|
| claude_code | run_free | 640 | 46 (7.2%) | 21 (3.3%) | 3 (0.5%) | 462 (72.2%) | 108 (16.9%) |
| claude_code | run_less_k1 | 1086 | 374 (34.4%) | 227 (20.9%) | 125 (11.5%) | 259 (23.8%) | 101 (9.3%) |
| claude_code | run_less_k3 | 1226 | 444 (36.2%) | 287 (23.4%) | 102 (8.3%) | 304 (24.8%) | 89 (7.3%) |
| claude_code | run_cost | 1322 | 451 (34.1%) | 224 (16.9%) | 209 (15.8%) | 329 (24.9%) | 109 (8.2%) |
| claude_code | run_full | 1758 | 633 (36.0%) | 220 (12.5%) | 385 (21.9%) | 353 (20.1%) | 167 (9.5%) |
| codex | run_free | 5034 | 2 (0.0%) | 0 (0.0%) | 0 (0.0%) | 2612 (51.9%) | 2420 (48.1%) |
| codex | run_less_k1 | 4130 | 220 (5.3%) | 18 (0.4%) | 62 (1.5%) | 928 (22.5%) | 2902 (70.3%) |
| codex | run_less_k3 | 5008 | 448 (8.9%) | 30 (0.6%) | 164 (3.3%) | 1200 (24.0%) | 3166 (63.2%) |
| codex | run_cost | 4544 | 378 (8.3%) | 38 (0.8%) | 112 (2.5%) | 1080 (23.8%) | 2936 (64.6%) |
| codex | run_full | 4864 | 594 (12.2%) | 40 (0.8%) | 94 (1.9%) | 1114 (22.9%) | 3022 (62.1%) |

## Execution Purpose Comparison Across Modes

Comparing execution behavior differences across different execution modes.

### SWE-bench Lite

**claude_code:**

- Run-Free total executions: 693
- Run-Full total executions: 1804
- Run-Free verification executions: 59
- Run-Full verification executions: 703
- Execution count difference: +1111 (160.3% increase)

**codex:**

- Run-Free total executions: 4324
- Run-Full total executions: 4636
- Run-Free verification executions: 0
- Run-Full verification executions: 634
- Execution count difference: +312 (7.2% increase)

### SWE-bench Verified

**claude_code:**

- Run-Free total executions: 640
- Run-Full total executions: 1758
- Run-Free verification executions: 46
- Run-Full verification executions: 633
- Execution count difference: +1118 (174.7% increase)

**codex:**

- Run-Free total executions: 5034
- Run-Full total executions: 4864
- Run-Free verification executions: 2
- Run-Full verification executions: 594
- Execution count difference: -170 (-3.4% decrease)

## Trial-and-Error Loop Analysis

Statistics on repeated execution of the same command, reflecting trial-and-error behavior.

### SWE-bench Lite

| Agent | Mode | Repeated Commands | Trial-Error Instances |
|-------|------|------------|------------|
| claude_code | run_free | 8 | 8 |
| claude_code | run_less_k1 | 86 | 86 |
| claude_code | run_less_k3 | 119 | 119 |
| claude_code | run_cost | 120 | 120 |
| claude_code | run_full | 124 | 124 |
| codex | run_free | 2041 | 2041 |
| codex | run_less_k1 | 1896 | 1896 |
| codex | run_less_k3 | 2220 | 2220 |
| codex | run_cost | 2151 | 2151 |
| codex | run_full | 2122 | 2122 |

### SWE-bench Verified

| Agent | Mode | Repeated Commands | Trial-Error Instances |
|-------|------|------------|------------|
| claude_code | run_free | 9 | 9 |
| claude_code | run_less_k1 | 94 | 94 |
| claude_code | run_less_k3 | 113 | 113 |
| claude_code | run_cost | 94 | 94 |
| claude_code | run_full | 115 | 115 |
| codex | run_free | 2394 | 2394 |
| codex | run_less_k1 | 1946 | 1946 |
| codex | run_less_k3 | 2334 | 2334 |
| codex | run_cost | 2169 | 2169 |
| codex | run_full | 2241 | 2241 |

## Key Findings

### 1. Execution Purpose Classification

| Category | Description | Typical Commands |
|------|------|----------|
| Verification | Run test frameworks to validate fixes | pytest, python -m pytest, python -m unittest |
| Localization | Run scripts to locate problems | python script.py |
| Environment | Confirm environment configuration | python --version, pip list, pip show |
| Exploration | Explore file system and code | ls, find, cat |

### 2. Main Findings

**Average execution count per mode:**

- run_free: Average 2673 executions, including 27 verification executions
- run_less_k1: Average 2580 executions, including 304 verification executions
- run_less_k3: Average 3092 executions, including 474 verification executions
- run_cost: Average 2970 executions, including 453 verification executions
- run_full: Average 3266 executions, including 641 verification executions

### 3. Conclusion

- **Run-Free mode executes almost no commands**: Verification execution count close to 0
- **Run-Full mode executes the most**: Heavily used for verification and exploration
- **Verification is the primary execution purpose**: In modes with execution privileges, verification has the highest proportion
- **Trial-and-error loops are prevalent**: Repeated execution of the same command is common in Run-Full mode
