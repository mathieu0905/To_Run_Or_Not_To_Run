# Patch Complexity Stratification

For each (agent, benchmark) cell we group the 100 instances by ground-truth patch complexity (files touched / hunk count / total added+removed lines) and report resolve rate under Prohibited and Unrestricted plus the difference. Cells with $N < 5$ are noisy and flagged.

## Stratified by files

| Benchmark | Agent | Bucket | $N$ | Prohibited | Unrestricted | Gap |
|-----------|-------|--------|----:|-----------:|-------------:|----:|
| Lite | Claude Code | single-file | 100 | 63/100 (63.0\%) | 64/100 (64.0\%) | -1.0 |
| Lite | Codex | single-file | 100 | 74/100 (74.0\%) | 73/100 (73.0\%) | +1.0 |
| Lite | OpenCode | single-file | 66 | 7/66 (10.6\%) | 5/66 (7.6\%) | +3.0 |
| Verified | Claude Code | single-file | 85 | 58/85 (68.2\%) | 63/85 (74.1\%) | -5.9 |
| Verified | Claude Code | 2-file | 9 | 4/9 (44.4\%) | 4/9 (44.4\%) | +0.0 |
| Verified | Claude Code | multi-file ($\geq 3$) | 6 | 2/6 (33.3\%) | 0/6 (0.0\%) | +33.3 |
| Verified | Codex | single-file | 85 | 66/85 (77.6\%) | 68/85 (80.0\%) | -2.4 |
| Verified | Codex | 2-file | 9 | 4/9 (44.4\%) | 4/9 (44.4\%) | +0.0 |
| Verified | Codex | multi-file ($\geq 3$) | 6 | 3/6 (50.0\%) | 3/6 (50.0\%) | +0.0 |
| Verified | OpenCode | single-file | 65 | 12/65 (18.5\%) | 11/65 (16.9\%) | +1.5 |
| Verified | OpenCode | 2-file | 9 | 1/9 (11.1\%) | 1/9 (11.1\%) | +0.0 |
| Verified | OpenCode | multi-file ($\geq 3$) | 3 $\star$ | 0/3 (0.0\%) | 0/3 (0.0\%) | +0.0 |

## Stratified by hunks

| Benchmark | Agent | Bucket | $N$ | Prohibited | Unrestricted | Gap |
|-----------|-------|--------|----:|-----------:|-------------:|----:|
| Lite | Claude Code | 1 hunk | 71 | 50/71 (70.4\%) | 51/71 (71.8\%) | -1.4 |
| Lite | Claude Code | 2--3 hunks | 29 | 13/29 (44.8\%) | 13/29 (44.8\%) | +0.0 |
| Lite | Codex | 1 hunk | 71 | 57/71 (80.3\%) | 57/71 (80.3\%) | +0.0 |
| Lite | Codex | 2--3 hunks | 29 | 17/29 (58.6\%) | 16/29 (55.2\%) | +3.4 |
| Lite | OpenCode | 1 hunk | 47 | 6/47 (12.8\%) | 3/47 (6.4\%) | +6.4 |
| Lite | OpenCode | 2--3 hunks | 19 | 1/19 (5.3\%) | 2/19 (10.5\%) | -5.3 |
| Verified | Claude Code | 1 hunk | 62 | 45/62 (72.6\%) | 49/62 (79.0\%) | -6.5 |
| Verified | Claude Code | 2--3 hunks | 25 | 13/25 (52.0\%) | 15/25 (60.0\%) | -8.0 |
| Verified | Claude Code | $\geq 4$ hunks | 13 | 6/13 (46.2\%) | 3/13 (23.1\%) | +23.1 |
| Verified | Codex | 1 hunk | 62 | 50/62 (80.6\%) | 52/62 (83.9\%) | -3.2 |
| Verified | Codex | 2--3 hunks | 25 | 15/25 (60.0\%) | 15/25 (60.0\%) | +0.0 |
| Verified | Codex | $\geq 4$ hunks | 13 | 8/13 (61.5\%) | 8/13 (61.5\%) | +0.0 |
| Verified | OpenCode | 1 hunk | 44 | 8/44 (18.2\%) | 8/44 (18.2\%) | +0.0 |
| Verified | OpenCode | 2--3 hunks | 23 | 3/23 (13.0\%) | 3/23 (13.0\%) | +0.0 |
| Verified | OpenCode | $\geq 4$ hunks | 10 | 2/10 (20.0\%) | 1/10 (10.0\%) | +10.0 |

## Stratified by delta_lines

| Benchmark | Agent | Bucket | $N$ | Prohibited | Unrestricted | Gap |
|-----------|-------|--------|----:|-----------:|-------------:|----:|
| Lite | Claude Code | small ($\leq 5$) | 47 | 35/47 (74.5\%) | 32/47 (68.1\%) | +6.4 |
| Lite | Claude Code | medium (6--20) | 47 | 27/47 (57.4\%) | 31/47 (66.0\%) | -8.5 |
| Lite | Claude Code | large ($> 20$) | 6 | 1/6 (16.7\%) | 1/6 (16.7\%) | +0.0 |
| Lite | Codex | small ($\leq 5$) | 47 | 40/47 (85.1\%) | 40/47 (85.1\%) | +0.0 |
| Lite | Codex | medium (6--20) | 47 | 32/47 (68.1\%) | 31/47 (66.0\%) | +2.1 |
| Lite | Codex | large ($> 20$) | 6 | 2/6 (33.3\%) | 2/6 (33.3\%) | +0.0 |
| Lite | OpenCode | small ($\leq 5$) | 27 | 5/27 (18.5\%) | 3/27 (11.1\%) | +7.4 |
| Lite | OpenCode | medium (6--20) | 34 | 2/34 (5.9\%) | 2/34 (5.9\%) | +0.0 |
| Lite | OpenCode | large ($> 20$) | 5 | 0/5 (0.0\%) | 0/5 (0.0\%) | +0.0 |
| Verified | Claude Code | small ($\leq 5$) | 45 | 36/45 (80.0\%) | 37/45 (82.2\%) | -2.2 |
| Verified | Claude Code | medium (6--20) | 36 | 19/36 (52.8\%) | 23/36 (63.9\%) | -11.1 |
| Verified | Claude Code | large ($> 20$) | 19 | 9/19 (47.4\%) | 7/19 (36.8\%) | +10.5 |
| Verified | Codex | small ($\leq 5$) | 45 | 38/45 (84.4\%) | 40/45 (88.9\%) | -4.4 |
| Verified | Codex | medium (6--20) | 36 | 23/36 (63.9\%) | 24/36 (66.7\%) | -2.8 |
| Verified | Codex | large ($> 20$) | 19 | 12/19 (63.2\%) | 11/19 (57.9\%) | +5.3 |
| Verified | OpenCode | small ($\leq 5$) | 32 | 11/32 (34.4\%) | 9/32 (28.1\%) | +6.2 |
| Verified | OpenCode | medium (6--20) | 30 | 0/30 (0.0\%) | 1/30 (3.3\%) | -3.3 |
| Verified | OpenCode | large ($> 20$) | 15 | 2/15 (13.3\%) | 2/15 (13.3\%) | +0.0 |
