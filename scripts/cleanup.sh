#!/bin/bash
# Cleanup script: Clean up residual processes and Docker containers

echo "=========================================="
echo "Cleaning up residual resources"
echo "=========================================="

# 1. Kill all batch_runner.py processes
echo "Searching for batch_runner.py processes..."
BATCH_PIDS=$(ps aux | grep -E "python.*batch_runner\.py" | grep -v grep | awk '{print $2}')
if [ -n "$BATCH_PIDS" ]; then
    echo "Found the following processes:"
    ps aux | grep -E "python.*batch_runner\.py" | grep -v grep
    echo ""
    echo "Terminating processes..."
    echo "$BATCH_PIDS" | xargs kill -9 2>/dev/null
    echo "✓ Terminated batch_runner.py processes"
else
    echo "✓ No batch_runner.py processes found"
fi
echo ""

# 2. Kill all runner.py processes
echo "Searching for runner.py processes..."
RUNNER_PIDS=$(ps aux | grep -E "python.*runner\.py" | grep -v grep | awk '{print $2}')
if [ -n "$RUNNER_PIDS" ]; then
    echo "Found the following processes:"
    ps aux | grep -E "python.*runner\.py" | grep -v grep
    echo ""
    echo "Terminating processes..."
    echo "$RUNNER_PIDS" | xargs kill -9 2>/dev/null
    echo "✓ Terminated runner.py processes"
else
    echo "✓ No runner.py processes found"
fi
echo ""

# 3. Kill Docker run processes (experiment-running containers)
echo "Searching for Docker run processes..."
DOCKER_RUN_PIDS=$(ps aux | grep -E "docker run.*swebench" | grep -v grep | awk '{print $2}')
if [ -n "$DOCKER_RUN_PIDS" ]; then
    echo "Found $(echo "$DOCKER_RUN_PIDS" | wc -l) Docker run processes"
    echo "Terminating processes..."
    echo "$DOCKER_RUN_PIDS" | xargs kill -9 2>/dev/null
    echo "✓ Terminated Docker run processes"
else
    echo "✓ No Docker run processes found"
fi
echo ""

# 4. Clean up SWE-bench Docker containers (only clean up experiment-generated containers, not those being built)
echo "Searching for SWE-bench Docker containers..."
SWEBENCH_CONTAINERS=$(docker ps -a | grep swebench | awk '{print $1}')
if [ -n "$SWEBENCH_CONTAINERS" ]; then
    CONTAINER_COUNT=$(echo "$SWEBENCH_CONTAINERS" | wc -l)
    echo "Found $CONTAINER_COUNT SWE-bench containers"
    echo "Stopping and removing containers..."
    echo "$SWEBENCH_CONTAINERS" | xargs docker rm -f 2>/dev/null
    echo "✓ Cleaned up SWE-bench containers"
else
    echo "✓ No SWE-bench containers found"
fi
echo ""

# 5. Kill codex/claude processes (running inside containers)
echo "Searching for codex/claude processes..."
AGENT_PIDS=$(ps aux | grep -E "(codex|claude).*exec" | grep -v grep | awk '{print $2}')
if [ -n "$AGENT_PIDS" ]; then
    echo "Found $(echo "$AGENT_PIDS" | wc -l) agent processes"
    echo "Terminating processes..."
    echo "$AGENT_PIDS" | xargs kill -9 2>/dev/null
    echo "✓ Terminated agent processes"
else
    echo "✓ No agent processes found"
fi
echo ""

# 6. Clean up temporary files
echo "Cleaning up temporary files..."
TEMP_FILES=$(find /tmp -name "tmp*" -user $(whoami) -mmin -60 2>/dev/null | grep -E "(instances|trace)" | head -20)
if [ -n "$TEMP_FILES" ]; then
    echo "Found the following temporary files:"
    echo "$TEMP_FILES"
    echo "$TEMP_FILES" | xargs rm -f 2>/dev/null
    echo "✓ Cleaned up temporary files"
else
    echo "✓ No related temporary files found"
fi
echo ""

echo "=========================================="
echo "Cleanup complete!"
echo "=========================================="
echo ""
echo "Current status:"
echo "- Python processes: $(ps aux | grep -E "python.*(batch_runner|runner)\.py" | grep -v grep | wc -l) processes"
echo "- Docker run processes: $(ps aux | grep -E "docker run.*swebench" | grep -v grep | wc -l) processes"
echo "- SWE-bench containers: $(docker ps -a | grep swebench | wc -l) containers"
echo "- Agent processes: $(ps aux | grep -E "(codex|claude).*exec" | grep -v grep | wc -l) processes"
echo ""
echo "Note: Docker build processes will not be cleaned up, they are normal image build tasks"
echo ""
