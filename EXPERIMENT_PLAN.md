# Batch Experiment Plan

## Experiment Configuration

### Test Instances (3)
From `test_3_instances.txt`:
1. `django__django-11099`
2. `django__django-11001`
3. `astropy__astropy-12907`

### Agent Types (2)
1. **claude_code** - Claude Code CLI
2. **codex** - OpenAI Codex

### Execution Modes (6 configurations)
1. **run_free** - No code execution, pure reasoning repair
2. **run_less K=1** - Maximum 1 test execution (extreme constraint)
3. **run_less K=2** - Maximum 2 test executions (medium constraint)
4. **run_less K=3** - Maximum 3 test executions (relaxed constraint)
5. **run_cost** - Cost-aware decision making, model decides whether to execute
6. **run_full** - Unlimited execution, trial-and-error loop allowed

### Total Experiments
**3 instances × 2 agents × 6 modes = 36 experiments**

## Output Directory Structure

```
output/
└── swebenchlite/
    ├── claude_code/
    │   ├── run_free/
    │   │   ├── django__django-11099/
    │   │   │   ├── trace.jsonl
    │   │   │   ├── patch.diff
    │   │   │   ├── prompt_run_free.txt
    │   │   │   └── result_run_free.json
    │   │   ├── django__django-11001/
    │   │   └── astropy__astropy-12907/
    │   ├── run_less/
    │   │   ├── django__django-11099/
    │   │   │   ├── trace.jsonl
    │   │   │   ├── patch.diff
    │   │   │   ├── prompt_run_less_k1.txt
    │   │   │   └── result_run_less_k1.json
    │   │   └── ...
    │   ├── run_cost/
    │   └── run_full/
    └── codex/
        ├── run_free/
        ├── run_less/
        ├── run_cost/
        └── run_full/
```

## Execution Methods

### Method 1: Using Batch Script (Recommended)

```bash
# Run from project root directory
./run_all_experiments.sh
```

This script will:
- Automatically iterate through all agent and mode combinations
- Use 8 concurrent workers (adjustable in the script)
- Run batch_runner.py for each configuration
- Display progress and colored output
- Add short delays between configurations to avoid resource conflicts

### Method 2: Manually Run Individual Configurations

```bash
cd experiments

# Claude Code + run_free
python batch_runner.py ../test_3_instances.txt run_free 2 8 claude_code 600

# Claude Code + run_less K=1
python batch_runner.py ../test_3_instances.txt run_less 1 8 claude_code 600

# Claude Code + run_less K=2
python batch_runner.py ../test_3_instances.txt run_less 2 8 claude_code 600

# Claude Code + run_less K=3
python batch_runner.py ../test_3_instances.txt run_less 3 8 claude_code 600

# Claude Code + run_cost
python batch_runner.py ../test_3_instances.txt run_cost 2 8 claude_code 600

# Claude Code + run_full
python batch_runner.py ../test_3_instances.txt run_full 2 8 claude_code 600

# Codex + run_free
python batch_runner.py ../test_3_instances.txt run_free 2 8 codex 600

# Codex + run_less K=1
python batch_runner.py ../test_3_instances.txt run_less 1 8 codex 600

# ... and so on
```

## Docker Container Naming

Since the output directory structure is already organized by `{agent}/{mode}/{instance}`, different configurations will automatically be separated:
- Different agents (claude_code vs codex) use different output directories
- Different modes (run_free vs run_less, etc.) use different output directories
- The same instance with different configurations won't run simultaneously (sequential execution)

Therefore, **there will be no Docker container naming conflicts**.

## Concurrency Settings

- **WORKERS=8**: Each configuration runs 8 instances in parallel internally
- Since there are only 3 instances, the actual concurrency is 3
- Different configurations execute sequentially to avoid resource conflicts

## Estimated Runtime

Assuming each experiment averages 600 seconds (10 minutes):
- 36 experiments × 10 minutes = 360 minutes = **6 hours**

Actual time may be shorter because:
1. run_free mode doesn't execute code, so it's faster
2. run_less mode has limited executions, so it's moderately fast
3. Only run_full mode may take longer

## Monitoring Progress

### View Real-time Output
```bash
# View trace for a specific instance
tail -f output/swebenchlite/claude_code/run_free/django__django-11099/trace.jsonl

# View generated patch
cat output/swebenchlite/claude_code/run_free/django__django-11099/patch.diff

# View result summary
cat output/swebenchlite/claude_code/run_free/django__django-11099/result_run_free.json
```

### Count Completed Experiments
```bash
# Count number of completed experiments
find output/swebenchlite -name "result_*.json" | wc -l

# List all completed experiments
find output/swebenchlite -name "result_*.json" -exec echo {} \;
```

## Result Analysis

Each experiment's result file (`result_*.json`) contains:
- `instance_id`: Instance ID
- `mode`: Execution mode
- `k`: Execution count limit for run_less (if applicable)
- `agent_type`: Agent type
- `tokens_used`: Number of tokens used
- `exec_count`: Actual execution count
- `duration_sec`: Runtime duration (seconds)
- `success`: Whether patch was successfully generated
- `error`: Error message (if any)

## Notes

1. **Environment Variables**: Ensure `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` are set
2. **Docker**: Ensure Docker service is running
3. **Disk Space**: Each experiment generates trace and patch files, ensure sufficient space
4. **Network**: Need access to Hugging Face for dataset downloads and API calls
5. **Checkpoint Resume**: If interrupted, re-running the same command will automatically skip completed experiments

## Troubleshooting

### If a Configuration Fails
```bash
# Re-run that configuration (will automatically skip completed instances)
cd experiments
python batch_runner.py ../test_3_instances.txt <mode> <k> 8 <agent> 600
```

### Clean Checkpoint and Re-run
```bash
# Delete checkpoint file
rm output/swebenchlite/checkpoint.json

# Re-run
./run_all_experiments.sh
```

### View Detailed Errors
```bash
# View complete trace for a specific instance
cat output/swebenchlite/claude_code/run_free/django__django-11099/trace.jsonl | jq .
```
