# Guide to Running Experiments in Docker Containers

## Architecture Overview

All experiment scripts run inside Docker containers, with output synchronized to the host machine in real-time through volume mounting.

**Output Directory Structure**:
```
output/
├── swebenchlite/          # SWE-bench Lite dataset
│   └── {instance_id}/     # Instance ID (e.g., django__django-11099)
│       ├── trace.jsonl    # Agent execution trace
│       ├── patch.diff     # Generated patch
│       ├── prompt_{mode}.txt  # Prompt used
│       └── result_{mode}.json # Experiment result summary
└── swebenchverified/      # SWE-bench Verified dataset
    └── {instance_id}/
        └── ...
```

## Prerequisites

### 1. Set Environment Variables

Create a `.env` file (or export in shell):

```bash
# Claude Code authentication
export ANTHROPIC_API_KEY="your-api-key"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # Optional

# Codex authentication (if using)
export OPENAI_API_KEY="your-api-key"

# Proxy settings (if needed)
export http_proxy="http://127.0.0.1:15732"
export https_proxy="http://127.0.0.1:15732"
```

### 2. Build or Pull Docker Image

```bash
# If using official base image
docker pull swebench/sweb.eval.x86_64.base:latest

# Or use your own built Agent-enhanced image
# docker pull swebench/sweb.eval.x86_64.{repo}_{version}_{issue}-agent:latest
```

## Usage

### Method 1: Using Docker Compose (Recommended)

#### Start Container

```bash
# Start interactive container
docker-compose up -d swebench-runner

# Enter container
docker-compose exec swebench-runner bash
```

#### Run Experiments Inside Container

```bash
# Navigate to experiments directory
cd /workspace/experiments

# Run single experiment
python runner.py django__django-11099 run_free
python runner.py django__django-11099 run_less 2
python runner.py django__django-11099 run_full

# Specify dataset
python runner.py django__django-11099 run_less 2 claude_code 600 princeton-nlp/SWE-bench_Verified
```

#### View Output (On Host Machine)

```bash
# Output is synchronized to host's output/ directory in real-time
ls output/swebenchlite/django__django-11099/
# Output: trace.jsonl  patch.diff  prompt_run_free.txt  result_run_free.json
```

#### Stop Container

```bash
docker-compose down
```

### Method 2: Direct Docker Commands

```bash
# Start container and mount directories
docker run -it --rm \
  --name swebench-runner \
  -v $(pwd):/workspace \
  -v $(pwd)/output:/workspace/output \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  --network host \
  swebench/sweb.eval.x86_64.base:latest \
  bash

# Run experiments inside container
cd /workspace/experiments
python runner.py django__django-11099 run_free
```

## Batch Running Experiments

### Create Instance List File

```bash
# Create instance list on host machine
cat > instances.txt <<EOF
django__django-11099
django__django-11001
astropy__astropy-12907
EOF
```

### Run Batch Experiments Inside Container

```bash
# Enter container
docker-compose exec swebench-runner bash

# Run batch experiments
cd /workspace/experiments
python batch_runner.py ../instances.txt run_less 2 4

# Parameter explanation:
# - ../instances.txt: Instance list file
# - run_less: Execution mode
# - 2: Execution count limit for run_less
# - 4: Concurrency (run 4 instances simultaneously)
```

## FAQ

### Q1: How to view real-time output?

Output is synchronized to the host's `output/` directory in real-time, you can view it on the host machine:

```bash
# View trace
tail -f output/swebenchlite/django__django-11099/trace.jsonl

# View patch
cat output/swebenchlite/django__django-11099/patch.diff
```

### Q2: How to install additional dependencies inside the container?

```bash
# Enter container
docker-compose exec swebench-runner bash

# Install Python packages
pip install some-package

# Or modify Dockerfile and rebuild the image
```

### Q3: How to use different datasets?

```bash
# SWE-bench Lite (default)
python runner.py instance_id run_free

# SWE-bench Verified
python runner.py instance_id run_free claude_code 600 princeton-nlp/SWE-bench_Verified
```

### Q4: How to debug failed experiments?

```bash
# View result JSON
cat output/swebenchlite/instance_id/result_run_free.json

# View complete trace
cat output/swebenchlite/instance_id/trace.jsonl

# View prompt
cat output/swebenchlite/instance_id/prompt_run_free.txt
```

### Q5: Will modifications inside the container be lost?

- **Code modifications**: Through volume mounting, modifications to `/workspace` inside the container are synchronized to the host machine
- **Output files**: Through volume mounting, output is synchronized to the host's `output/` directory in real-time
- **System-level modifications** (e.g., apt install): Will be lost after container restart, recommend modifying Dockerfile

## Performance Optimization Recommendations

### 1. Concurrency Control

```bash
# Adjust concurrency based on machine resources
# Recommended: 50-75% of CPU cores
python batch_runner.py instances.txt run_less 2 4  # 4 concurrent
```

### 2. Resource Limits

Add resource limits in `docker-compose.yml`:

```yaml
services:
  swebench-runner:
    # ...
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
        reservations:
          cpus: '4.0'
          memory: 8G
```

### 3. Use SSD Storage

Ensure the `output/` directory is on SSD to improve I/O performance.

## Next Steps

1. **Test single instance**: First run one instance to verify environment configuration is correct
2. **Small batch test**: Run 3-5 instances to test batch running functionality
3. **Full experiment**: Run complete SWE-bench Lite (300 instances)

## Related Files

- `docker-compose.yml` - Docker Compose configuration
- `experiments/runner.py` - Single experiment runner
- `experiments/batch_runner.py` - Batch experiment runner (to be implemented)
- `experiments/prompt_builder.py` - Prompt builder
- `experiments/agent_caller.py` - Agent caller
