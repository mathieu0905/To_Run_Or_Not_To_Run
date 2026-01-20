# SWE-bench Submission Guide

## Environment Setup

1. Install sb-cli:
```bash
conda activate swebench
pip install -e sb-cli/
```

2. Configure API Key (already saved in `.env` file):
```bash
# .env file content
SWEBENCH_API_KEY=swb_xxx...
```

## Check Quota

```bash
conda activate swebench
export SWEBENCH_API_KEY=swb_xxx...
sb-cli get-quotas
```

## Using submit_to_swebench.sh

### List All Available Combinations

```bash
./submit_to_swebench.sh --list
```

Example output:
```
Dataset              Agent           Mode            Instances  Patches
----------------------------------------------------------------------
swebenchlite         codex           run_free        100        100
swebenchverified     claude_code     run_free        33         33
swebenchverified     codex           run_free        99         99
...
```

### Generate predictions file (without submission)

```bash
./submit_to_swebench.sh --dataset swebenchverified --agent codex --mode run_free --gen-only
```

Generated files are saved in the `predictions/` directory.

### Submit to SWE-bench

```bash
# Use default run_id (agent_mode)
./submit_to_swebench.sh --dataset swebenchverified --agent codex --mode run_free

# Custom run_id
./submit_to_swebench.sh --dataset swebenchverified --agent codex --mode run_free --run-id my_experiment_v1
```

### Generate All predictions Files

```bash
./submit_to_swebench.sh --all --gen-only
```

## Using sb-cli Directly

### Submission Command Format

```bash
sb-cli submit <subset> <split> --predictions_path <file> --run_id <id>
```

Parameter explanation:
- `subset`: `swe-bench_lite` | `swe-bench_verified` | `swe-bench-m`
- `split`: `test` | `dev`
- `--predictions_path`: predictions JSON file path
- `--run_id`: run identifier

### Examples

```bash
# Submit to SWE-bench Verified test set
sb-cli submit swe-bench_verified test \
    --predictions_path predictions/swebenchverified_codex_run_free.json \
    --run_id codex_run_free

# Submit to SWE-bench Lite test set
sb-cli submit swe-bench_lite test \
    --predictions_path predictions/swebenchlite_codex_run_free.json \
    --run_id codex_run_free
```

### View Results

```bash
# Get report
sb-cli get-report swe-bench_verified test <run_id>

# List all runs
sb-cli list-runs swe-bench_verified test
```

## Predictions File Format

```json
[
    {
        "instance_id": "django__django-11099",
        "model_patch": "diff --git a/...",
        "model_name_or_path": "codex_run_free"
    },
    ...
]
```

## Dataset Mapping

| Local Directory Name | sb-cli subset Name |
|-----------|-------------------|
| swebenchlite | swe-bench_lite |
| swebenchverified | swe-bench_verified |

## Notes

- Test set submissions have quota limits, please use carefully
- Recommend using `--gen-only` to check generated predictions file before submission
- Each submission's run_id should be unique for easy result tracking

./submit_to_swebench.sh --dataset swebenchverified --agent codex --mode run_free
