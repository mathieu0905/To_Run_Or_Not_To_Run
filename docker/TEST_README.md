# Docker Environment Test Scripts

These scripts are used to verify that the SWE-bench Docker environment is working properly.

## Script Description

### test_docker_env.sh

Tests the environment configuration of a single Docker image.

**Functionality Checks:**
1. Whether the image exists
2. Whether the container can start normally
3. Whether the Conda environment is configured correctly
4. Whether the working directory `/testbed` exists
5. Whether the test framework is available (auto-detects Django/pytest/unittest)

**Usage:**

```bash
# Test base image
./docker/test_docker_env.sh --image swebench/sweb.eval.x86_64.django_1776_django-11099

# Test Agent image
./docker/test_docker_env.sh --image swebench/sweb.eval.x86_64.django_1776_django-11099 --agent
```

### test_all_images.sh

Batch test multiple Docker images.

**Usage:**

```bash
# Test first 5 images (default)
./docker/test_all_images.sh

# Test first 3 images
./docker/test_all_images.sh --max 3

# Test all images
./docker/test_all_images.sh --all

# Test Agent version images
./docker/test_all_images.sh --agent --max 3
```

## Environment Requirements

- Docker installed and running
- SWE-bench images built (refer to `image_list.txt`)
- Bash shell environment

## Test Output

The scripts output colored test results:
- ✓ Green: Test passed
- ✗ Red: Test failed
- ⚠ Yellow: Warning message

## Image List

All available images are listed in the `docker/image_list.txt` file.

## Environment Configuration

Each SWE-bench container contains:
- **Working Directory**: `/testbed` - Contains project source code
- **Conda Environment**: `testbed` - Located at `/opt/miniconda3/envs/testbed`
- **Test Framework**: Automatically configured based on project type (Django/pytest/unittest)

## Examples

```bash
# Quick test Django project
./docker/test_docker_env.sh --image swebench/sweb.eval.x86_64.django_1776_django-11099

# Quick test pytest project
./docker/test_docker_env.sh --image swebench/sweb.eval.x86_64.pytest-dev_1776_pytest-7168

# Batch test first 10 images
./docker/test_all_images.sh --max 10
```

## Troubleshooting

If tests fail, check:
1. Whether Docker service is running: `docker ps`
2. Whether images exist: `docker images | grep swebench`
3. Whether disk space is sufficient: `df -h`
4. Container logs: Check the `docker/build_logs/` directory
