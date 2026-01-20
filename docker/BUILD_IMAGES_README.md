# Docker Image Build Tool Usage Documentation

## Overview

`build_agent_images_parallel.py` is a tool for building SWE-bench Docker images in parallel, supporting batch construction of enhanced images for Agent experimental environments.

## Features

- Supports two datasets: SWE-bench Lite (300 instances) and SWE-bench-verified (500 instances)
- Parallel building with 16 workers by default
- Automatically skips existing images
- Detailed build logging
- Real-time progress display

## Prerequisites

1. Docker installed and running
2. Sufficient disk space (at least 120GB recommended)
3. Stable network connection (required to pull base images from Docker Hub)
4. Python 3.10+

## Usage

### Basic Syntax

```bash
python build_agent_images_parallel.py [dataset]
```

### Parameter Description

- `dataset`: Optional parameter to specify the dataset to build
  - `lite`: SWE-bench Lite (300 instances, default)
  - `verified`: SWE-bench-verified (500 instances)

### Usage Examples

#### 1. Build SWE-bench Lite Images (Default)

```bash
# Method 1: Without parameters (uses lite by default)
python build_agent_images_parallel.py

# Method 2: Explicitly specify lite
python build_agent_images_parallel.py lite
```

#### 2. Build SWE-bench-verified Images

```bash
python build_agent_images_parallel.py verified
```

## Output Description

### Console Output

```
Building 300 images from lite dataset with 16 workers...
[1/300] ✓ django-11099
[2/300] ✗ pytest-7168: build failed (see swebench_sweb.eval.x86_64.pytest-dev_1776_pytest-7168.log)
[3/300] ✓ sympy-20590
...
Done: 298/300 succeeded
Failed (2):
  swebench/sweb.eval.x86_64.pytest-dev_1776_pytest-7168: build failed (see swebench_sweb.eval.x86_64.pytest-dev_1776_pytest-7168.log)
  swebench/sweb.eval.x86_64.django_1776_django-12345: pull failed (see swebench_sweb.eval.x86_64.django_1776_django-12345.log)
```

### Build Logs

All build logs are saved in the `build_logs/` directory with the filename format:
```
swebench_sweb.eval.x86_64.{repo}_{version}_{issue_id}.log
```

Each log file contains:
- Base image pull process
- Agent overlay build process
- Error messages (if build fails)

## Image Naming Convention

### Base Image
```
swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}:latest
```

### Agent Enhanced Image
```
swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}-agent:latest
```

Examples:
- Base image: `swebench/sweb.eval.x86_64.django_1776_django-11099:latest`
- Agent image: `swebench/sweb.eval.x86_64.django_1776_django-11099-agent:latest`

## Configuration Files

### image_list.txt
Contains the list of 300 images for SWE-bench Lite.

### image_list_verified.txt
Contains the list of 500 images for SWE-bench-verified.

### Dockerfile.agent-overlay
Defines the Dockerfile for the Agent enhancement layer, adding to the base image:
- Tools required for Agent execution
- Environment configuration
- Dependencies

## Performance Tuning

### Adjusting Parallelism

Edit the `MAX_WORKERS` constant in the script:

```python
MAX_WORKERS = 16  # Adjust based on CPU cores and network bandwidth
```

Recommended values:
- 8-core CPU: 8-12 workers
- 16-core CPU: 16-24 workers
- 32-core CPU: 24-32 workers

### Disk Space Management

Regularly clean up unused images:

```bash
# Clean dangling images
docker image prune -f

# Clean all unused images
docker image prune -a -f
```

## Troubleshooting

### Issue 1: Image Pull Failed

**Symptom**: Log shows "pull failed"

**Solution**:
1. Check network connection
2. Check Docker Hub access permissions
3. Re-run the script (will automatically skip successful images)

### Issue 2: Build Failed

**Symptom**: Log shows "build failed"

**Solution**:
1. Check the corresponding log file for detailed errors
2. Verify that Dockerfile.agent-overlay is correct
3. Confirm that the base image is complete

### Issue 3: Insufficient Disk Space

**Symptom**: "no space left on device" error during build

**Solution**:
1. Clean Docker cache: `docker system prune -a`
2. Delete unnecessary images
3. Increase disk space

## Integration with Experiment Workflow

After building is complete, the images can be used to run SWE-bench experiments:

```bash
# Run a single experiment
python experiments/runner.py <instance_id> <mode>

# Example
python experiments/runner.py django__django-11099 run_less 2
```

## Technical Details

### Build Process

1. Read image list from `image_list.txt` or `image_list_verified.txt`
2. For each image:
   - Check if Agent image already exists (skip if exists)
   - Pull base image
   - Build Agent image using Dockerfile.agent-overlay
   - Record build logs
3. Summarize build results

### Concurrency Control

Implemented using Python's `ThreadPoolExecutor`:
- Each worker processes one image independently
- Automatic load balancing
- Thread-safe logging

## Related Files

- `build_agent_images_parallel.py`: Main script
- `Dockerfile.agent-overlay`: Agent enhancement layer definition
- `image_list.txt`: SWE-bench Lite image list
- `image_list_verified.txt`: SWE-bench-verified image list
- `build_logs/`: Build logs directory

## License

This tool is part of the run_free_run_less_run_full research project.
