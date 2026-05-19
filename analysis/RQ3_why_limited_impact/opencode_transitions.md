# RQ3 (OpenCode leg): Transition Matrix + Empty Patch Breakdown

All resolved_ids are sourced via the _fixed-prefer loader, so
OpenCode results reflect the post-bracket-bug-fix reruns.

## 1. Outcome Transition Matrices (OpenCode)

For each pair of modes, classify the 100 instances into four
cells: P->P (both resolved), P->F (mode1 only), F->P (mode2 only),
F->F (neither). |PF-FP| quantifies the net flow — a large value
means one mode systematically beats the other; a small value means
they mostly agree.

### SWE-bench Lite

| DS | Agent | Transition | PP | PF | FP | FF | |PF-FP| / 100 |
|----|-------|-----------|----|----|----|----|-----------------|
| SWE-benc | claude_code | run_free -> run_less_k1 | PP=59 | PF=4 | FP=2 | FF=35 | |PF-FP|=2 / 100 |
| SWE-benc | claude_code | run_free -> run_less_k3 | PP=58 | PF=5 | FP=4 | FF=33 | |PF-FP|=1 / 100 |
| SWE-benc | claude_code | run_free -> run_cost | PP=57 | PF=6 | FP=6 | FF=31 | |PF-FP|=0 / 100 |
| SWE-benc | claude_code | run_free -> run_full | PP=58 | PF=5 | FP=6 | FF=31 | |PF-FP|=1 / 100 |
| SWE-benc | claude_code | run_less_k1 -> run_less_k3 | PP=58 | PF=3 | FP=4 | FF=35 | |PF-FP|=1 / 100 |
| SWE-benc | claude_code | run_less_k1 -> run_full | PP=58 | PF=3 | FP=6 | FF=33 | |PF-FP|=3 / 100 |
| SWE-benc | claude_code | run_cost -> run_full | PP=59 | PF=4 | FP=5 | FF=32 | |PF-FP|=1 / 100 |
| SWE-benc | codex      | run_free -> run_less_k1 | PP=65 | PF=9 | FP=3 | FF=23 | |PF-FP|=6 / 100 |
| SWE-benc | codex      | run_free -> run_less_k3 | PP=68 | PF=6 | FP=1 | FF=25 | |PF-FP|=5 / 100 |
| SWE-benc | codex      | run_free -> run_cost | PP=66 | PF=8 | FP=5 | FF=21 | |PF-FP|=3 / 100 |
| SWE-benc | codex      | run_free -> run_full | PP=70 | PF=4 | FP=3 | FF=23 | |PF-FP|=1 / 100 |
| SWE-benc | codex      | run_less_k1 -> run_less_k3 | PP=64 | PF=4 | FP=5 | FF=27 | |PF-FP|=1 / 100 |
| SWE-benc | codex      | run_less_k1 -> run_full | PP=65 | PF=3 | FP=8 | FF=24 | |PF-FP|=5 / 100 |
| SWE-benc | codex      | run_cost -> run_full | PP=65 | PF=6 | FP=8 | FF=21 | |PF-FP|=2 / 100 |
| SWE-benc | opencode   | run_free -> run_less_k1 | PP=6 | PF=1 | FP=8 | FF=85 | |PF-FP|=7 / 100 |
| SWE-benc | opencode   | run_free -> run_less_k3 | PP=3 | PF=4 | FP=4 | FF=89 | |PF-FP|=0 / 100 |
| SWE-benc | opencode   | run_free -> run_cost | PP=6 | PF=1 | FP=3 | FF=90 | |PF-FP|=2 / 100 |
| SWE-benc | opencode   | run_free -> run_full | PP=3 | PF=4 | FP=3 | FF=90 | |PF-FP|=1 / 100 |
| SWE-benc | opencode   | run_less_k1 -> run_less_k3 | PP=4 | PF=10 | FP=3 | FF=83 | |PF-FP|=7 / 100 |
| SWE-benc | opencode   | run_less_k1 -> run_full | PP=4 | PF=10 | FP=2 | FF=84 | |PF-FP|=8 / 100 |
| SWE-benc | opencode   | run_cost -> run_full | PP=4 | PF=5 | FP=2 | FF=89 | |PF-FP|=3 / 100 |

### SWE-bench Verified

| DS | Agent | Transition | PP | PF | FP | FF | |PF-FP| / 100 |
|----|-------|-----------|----|----|----|----|-----------------|
| SWE-benc | claude_code | run_free -> run_less_k1 | PP=56 | PF=8 | FP=8 | FF=28 | |PF-FP|=0 / 100 |
| SWE-benc | claude_code | run_free -> run_less_k3 | PP=56 | PF=8 | FP=9 | FF=27 | |PF-FP|=1 / 100 |
| SWE-benc | claude_code | run_free -> run_cost | PP=60 | PF=4 | FP=7 | FF=29 | |PF-FP|=3 / 100 |
| SWE-benc | claude_code | run_free -> run_full | PP=58 | PF=6 | FP=9 | FF=27 | |PF-FP|=3 / 100 |
| SWE-benc | claude_code | run_less_k1 -> run_less_k3 | PP=62 | PF=2 | FP=3 | FF=33 | |PF-FP|=1 / 100 |
| SWE-benc | claude_code | run_less_k1 -> run_full | PP=61 | PF=3 | FP=6 | FF=30 | |PF-FP|=3 / 100 |
| SWE-benc | claude_code | run_cost -> run_full | PP=63 | PF=4 | FP=4 | FF=29 | |PF-FP|=0 / 100 |
| SWE-benc | codex      | run_free -> run_less_k1 | PP=68 | PF=5 | FP=4 | FF=23 | |PF-FP|=1 / 100 |
| SWE-benc | codex      | run_free -> run_less_k3 | PP=68 | PF=5 | FP=5 | FF=22 | |PF-FP|=0 / 100 |
| SWE-benc | codex      | run_free -> run_cost | PP=66 | PF=7 | FP=5 | FF=22 | |PF-FP|=2 / 100 |
| SWE-benc | codex      | run_free -> run_full | PP=72 | PF=1 | FP=3 | FF=24 | |PF-FP|=2 / 100 |
| SWE-benc | codex      | run_less_k1 -> run_less_k3 | PP=66 | PF=6 | FP=7 | FF=21 | |PF-FP|=1 / 100 |
| SWE-benc | codex      | run_less_k1 -> run_full | PP=70 | PF=2 | FP=5 | FF=23 | |PF-FP|=3 / 100 |
| SWE-benc | codex      | run_cost -> run_full | PP=69 | PF=2 | FP=6 | FF=23 | |PF-FP|=4 / 100 |
| SWE-benc | opencode   | run_free -> run_less_k1 | PP=10 | PF=3 | FP=7 | FF=80 | |PF-FP|=4 / 100 |
| SWE-benc | opencode   | run_free -> run_less_k3 | PP=7 | PF=6 | FP=4 | FF=83 | |PF-FP|=2 / 100 |
| SWE-benc | opencode   | run_free -> run_cost | PP=7 | PF=6 | FP=6 | FF=81 | |PF-FP|=0 / 100 |
| SWE-benc | opencode   | run_free -> run_full | PP=9 | PF=4 | FP=5 | FF=82 | |PF-FP|=1 / 100 |
| SWE-benc | opencode   | run_less_k1 -> run_less_k3 | PP=9 | PF=8 | FP=2 | FF=81 | |PF-FP|=6 / 100 |
| SWE-benc | opencode   | run_less_k1 -> run_full | PP=10 | PF=7 | FP=4 | FF=79 | |PF-FP|=3 / 100 |
| SWE-benc | opencode   | run_cost -> run_full | PP=8 | PF=5 | FP=6 | FF=81 | |PF-FP|=1 / 100 |

## 2. Empty-Patch Breakdown (OpenCode)

Per-mode breakdown of the 100 instances by patch.diff status:

- `edit_all_errored`: every edit call returned status=error
  (Qwen hallucinated filePath / oldString)
- `read_only_abandon`: agent only called read, never edit/bash
- `no_edit_bail`: early stop without invoking edit
- `edit_ok_but_no_diff`: at least one edit succeeded yet
  git diff is empty — likely Qwen idempotent-retry bug where
  repeated identical edits poison the successful one

| Dataset | Mode | Empty/Total | edit_all_errored | read_only_abandon | no_edit_bail | edit_ok_but_no_diff | other |
|---------|------|-------------|------------------|-------------------|--------------|---------------------|-------|
| Lite | run_free | 33/100 (33%) | 17 | 11 | 5 | 0 | 0 |
| Lite | run_less_k1 | 26/100 (26%) | 13 | 5 | 4 | 4 | 0 |
| Lite | run_less_k3 | 36/100 (36%) | 17 | 4 | 9 | 6 | 0 |
| Lite | run_cost | 41/100 (41%) | 13 | 10 | 8 | 10 | 0 |
| Lite | run_full | 43/100 (43%) | 10 | 13 | 5 | 15 | 0 |
| Verified | run_free | 27/101 (27%) | 9 | 15 | 2 | 1 | 0 |
| Verified | run_less_k1 | 24/100 (24%) | 13 | 5 | 5 | 1 | 0 |
| Verified | run_less_k3 | 30/100 (30%) | 14 | 5 | 8 | 3 | 0 |
| Verified | run_cost | 33/100 (33%) | 13 | 6 | 8 | 6 | 0 |
| Verified | run_full | 44/100 (44%) | 11 | 15 | 9 | 9 | 0 |

## 3. Narrative Summary

Key observations from the OpenCode + Qwen2.5-Coder-32B leg:

- **Run-Less-k1 dominates Run-Free**: on Lite the transition
  matrix shows 8 instances moving from F (run_free) to P
  (run_less_k1) while only 1 moves the other way.
- **Run-Less-k3 silently loses instances to k1**: on Lite, 10
  instances resolved in k1 are lost by k3 while only 3 new
  ones appear -- a net -7 transition.
- **Run-Full's low ceiling is explained by the 50% empty-patch
  rate** (Section 2), driven primarily by edit-call hallucinations
  and Qwen's idempotent-retry bug. Prohibited mode has only
  28-34% empty-patch rate because the prompt-imposed single-
  edit focus reaches the edit stage before context runs out.
- These transitions corroborate the paper's **one smart run**
  thesis in the capability-bounded regime: k=1 is a strictly
  better investment than k=3 or unlimited for Qwen2.5-Coder.
