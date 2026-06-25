#!/bin/bash
# Batch run all experiment configurations - fully parallel version
# 3 instances × 2 agents × 6 modes = 36 experiments, all configurations run in parallel

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default background execution, -f for foreground execution
if [ "$1" != "-f" ] && [ "$1" != "--foreground" ]; then
    SCRIPT_PATH="${SCRIPT_DIR}/$(basename "$0")"
    LOG_FILE="${PROJECT_ROOT}/logs/run_codex_$(date +%Y%m%d_%H%M%S).log"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "Running in background, log: $LOG_FILE"
    nohup bash "$SCRIPT_PATH" -f > "$LOG_FILE" 2>&1 &
    echo "PID: $!"
    exit 0
fi

# Switch to experiments directory to run
cd "$PROJECT_ROOT/experiments"

# Cleanup function: terminate all child processes and Docker containers
cleanup() {
    echo ""
    echo "=========================================="
    echo "Received termination signal, cleaning up resources..."
    echo "=========================================="

    # Terminate all child processes
    if [ ${#PIDS[@]} -gt 0 ]; then
        echo "Terminating ${#PIDS[@]} background processes..."
        for pid in "${PIDS[@]}"; do
            kill -TERM "$pid" 2>/dev/null || true
        done
        sleep 2
        for pid in "${PIDS[@]}"; do
            kill -KILL "$pid" 2>/dev/null || true
        done
        echo "✓ All background processes terminated"
    fi

    # Clean up SWE-bench Docker containers
    echo "Cleaning up Docker containers..."
    CONTAINERS=$(docker ps -aq --filter "ancestor=swebench" 2>/dev/null || true)
    if [ -n "$CONTAINERS" ]; then
        echo "$CONTAINERS" | xargs docker rm -f 2>/dev/null || true
        echo "✓ Docker containers cleaned up"
    fi

    echo "Cleanup complete!"
    exit 1
}

# Register signal handler
trap cleanup SIGINT SIGTERM

# ========== Configuration Section ==========
# Experiment configuration
NUM_INSTANCES=100  # Take first n instances
WORKERS=30  # Concurrency within each configuration
TIMEOUT=1200
DATASET="princeton-nlp/SWE-bench_Lite"

# Claude Code configuration
export CLAUDE_MODEL="${CLAUDE_MODEL:-sonnet}"  # Options: opus, sonnet, haiku
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.anthropic.com}"

# Codex configuration
export CODEX_MODEL="${CODEX_MODEL:-gpt-5.2}"
export CODEX_REASONING_EFFORT="${CODEX_REASONING_EFFORT:-xhigh}"
# ==============================

# Select corresponding JSON data file based on DATASET
if [ "$DATASET" = "princeton-nlp/SWE-bench_Lite" ]; then
    DATA_FILE="${PROJECT_ROOT}/data/swe_bench_lite.json"
elif [ "$DATASET" = "princeton-nlp/SWE-bench_Verified" ]; then
    DATA_FILE="${PROJECT_ROOT}/data/swe_bench_verified.json"
else
    echo "Unknown dataset: $DATASET"
    exit 1
fi

# Check if data file exists
if [ ! -f "$DATA_FILE" ]; then
    echo "Data file does not exist: $DATA_FILE"
    exit 1
fi

# Extract instance_id from JSON file and generate temporary instance file (take first n instances)
INSTANCES_FILE=$(mktemp)
python3 -c "import json; data = json.load(open('$DATA_FILE')); print('\n'.join([d['instance_id'] for d in data[:$NUM_INSTANCES]]))" > "$INSTANCES_FILE"
trap "rm -f $INSTANCES_FILE" EXIT

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Batch Experiment Runner - Fully Parallel Mode"
echo "=========================================="
echo "Instance file: $INSTANCES_FILE"
echo "Concurrency per configuration: $WORKERS"
echo "Timeout: ${TIMEOUT}s"
echo "Dataset: $DATASET"
echo "=========================================="
echo ""

# Create log directory (in project root, organized by agent)
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "$LOG_DIR"

# Agent list
# AGENTS=("claude_code" "codex")
AGENTS=("codex")

# Mode configuration list
# Format: "mode k_value"
CONFIGS=(
    "run_free 0"
    "run_less 1"
    # "run_less 2"
    "run_less 3"
    "run_cost 0"
    "run_full 0"
)

# Statistics
TOTAL_CONFIGS=$((${#AGENTS[@]} * ${#CONFIGS[@]}))
echo -e "${YELLOW}Total ${TOTAL_CONFIGS} parallel tasks will be launched${NC}"
echo ""

# Store background task PIDs
declare -a PIDS=()
declare -a TASK_NAMES=()

# Iterate through all agents
for agent in "${AGENTS[@]}"; do
    # Iterate through all mode configurations
    for config in "${CONFIGS[@]}"; do
        # Parse configuration
        read -r mode k <<< "$config"

        # Build mode description
        if [ "$mode" = "run_less" ]; then
            MODE_DESC="${mode}_k${k}"
            TASK_NAME="${agent}_${MODE_DESC}"
        else
            MODE_DESC="${mode}"
            TASK_NAME="${agent}_${mode}"
        fi

        # Create hierarchical log directory
        AGENT_LOG_DIR="${LOG_DIR}/${agent}"
        mkdir -p "$AGENT_LOG_DIR"

        # Log file
        LOG_FILE="${AGENT_LOG_DIR}/${MODE_DESC}.log"

        echo -e "${BLUE}Starting task:${NC} ${GREEN}${TASK_NAME}${NC} (log: ${LOG_FILE})"

        # Run directly on host machine, agent_caller.py will start corresponding Docker container for each instance
        if [ "$mode" = "run_less" ]; then
            (python -u batch_runner.py "${INSTANCES_FILE}" $mode $k $WORKERS $agent $TIMEOUT $DATASET > "$LOG_FILE" 2>&1) &
        else
            (python -u batch_runner.py "${INSTANCES_FILE}" $mode 2 $WORKERS $agent $TIMEOUT $DATASET > "$LOG_FILE" 2>&1) &
        fi

        # Record PID and task name
        PIDS+=($!)
        TASK_NAMES+=("$TASK_NAME")
    done
done

echo ""
echo "=========================================="
echo -e "${YELLOW}All ${TOTAL_CONFIGS} tasks have been launched!${NC}"
echo "=========================================="
echo ""
echo "Monitor progress:"
echo "  - View all logs: ls -lh ${LOG_DIR}/"
echo "  - View a specific log in real-time: tail -f ${LOG_DIR}/<task_name>.log"
echo "  - View processes: ps aux | grep batch_runner"
echo ""
echo "Waiting for all tasks to complete..."
echo ""

# Wait for all background tasks to complete
COMPLETED=0
FAILED=0

for i in "${!PIDS[@]}"; do
    PID=${PIDS[$i]}
    TASK_NAME=${TASK_NAMES[$i]}

    # Wait for process to complete
    if wait $PID; then
        echo -e "${GREEN}✓${NC} Task completed: ${TASK_NAME}"
        COMPLETED=$((COMPLETED + 1))
    else
        echo -e "\033[0;31m✗${NC} Task failed: ${TASK_NAME} (view log: ${LOG_DIR}/${TASK_NAME}.log)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=========================================="
echo "All tasks completed!"
echo "=========================================="
echo -e "Completed: ${GREEN}${COMPLETED}${NC} / Failed: ${FAILED} / Total: ${TOTAL_CONFIGS}"
echo ""
echo "Results saved in: output/swebenchlite/{agent}/{mode}/{instance_id}/"
echo "Logs saved in: ${LOG_DIR}/"
echo ""

# Return status code
if [ $FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
