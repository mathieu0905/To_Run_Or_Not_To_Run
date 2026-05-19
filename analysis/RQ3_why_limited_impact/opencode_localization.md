# OpenCode localization Hit/Recall

Computed from output/{dataset}/opencode/{mode}/{instance}/patch.diff
using the same `extract_files_from_patch` helper as the main RQ3 analysis.

## Pass->Pass cases (Prohibited AND Unrestricted resolved)

| Dataset | Mode | n | Hit | Recall |
|---------|------|---|-----|--------|
| swebenchlite | run_full | 3 | 100.0% | 100.0% |
| swebenchlite | run_free | 3 | 100.0% | 100.0% |
| swebenchverified | run_full | 9 | 100.0% | 94.4% |
| swebenchverified | run_free | 9 | 100.0% | 94.4% |

## Fail->Fail cases (neither mode resolved)

| Dataset | Mode | n | Hit | Recall |
|---------|------|---|-----|--------|
| swebenchlite | run_full | 90 | 35.6% | 35.6% |
| swebenchlite | run_free | 90 | 47.8% | 47.8% |
| swebenchverified | run_full | 82 | 29.3% | 27.1% |
| swebenchverified | run_free | 82 | 61.0% | 55.2% |

## Combined (Lite + Verified, matching tab:localization-pp format)

| Mode | n_PP | Hit_PP | Recall_PP | n_FF | Hit_FF | Recall_FF |
|------|------|--------|-----------|------|--------|-----------|
| run_full | 12 | 100.0% | 95.8% | 172 | 32.6% | 31.5% |
| run_free | 12 | 100.0% | 95.8% | 172 | 54.1% | 51.3% |
