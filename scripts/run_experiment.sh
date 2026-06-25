#!/bin/bash
# Experiment runner script - supports single instance or batch execution

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Display usage instructions
show_usage() {
    echo "Usage: $0 <mode> [options]"
    echo ""
    echo "Modes:"
    echo "  single <instance_id> <mode> [k] [agent_type] [timeout] [dataset]"
    echo "      Run a single instance"
    echo ""
    echo "  batch <instances_file> <mode> [k] [workers] [agent_type] [timeout] [dataset]"
    echo "      Run multiple instances in batch"
    echo ""
    echo "Execution modes (mode):"
    echo "  run_free    - No code execution, pure reasoning"
    echo "  run_less    - Limited execution count (requires k parameter)"
    echo "  run_cost    - Cost-aware decision making"
    echo "  run_full    - Unrestricted execution"
    echo ""
    echo "Examples:"
    echo "  # Run a single instance"
    echo "  $0 single django__django-11099 run_free"
    echo "  $0 single django__django-11099 run_less 2"
    echo "  $0 single django__django-11099 run_full claude_code 600"
    echo ""
    echo "  # Batch execution"
    echo "  $0 batch instances.txt run_less 2 4"
    echo "  $0 batch instances.txt run_free 2 8 claude_code 600"
    echo ""
    exit 1
}

# Check parameters
if [ $# -lt 2 ]; then
    show_usage
fi

MODE=$1
shift

# Switch to experiments directory
cd "$PROJECT_ROOT/experiments"

case "$MODE" in
    single)
        # Run single instance
        if [ $# -lt 2 ]; then
            echo -e "${RED}Error: single mode requires at least 2 parameters${NC}"
            show_usage
        fi

        INSTANCE_ID=$1
        EXEC_MODE=$2
        K=${3:-2}
        AGENT_TYPE=${4:-claude_code}
        TIMEOUT=${5:-600}
        DATASET=${6:-princeton-nlp/SWE-bench_Lite}

        echo -e "${YELLOW}========================================${NC}"
        echo -e "${YELLOW}Running Single Instance${NC}"
        echo -e "${YELLOW}========================================${NC}"
        echo -e "Instance ID:    ${GREEN}${INSTANCE_ID}${NC}"
        echo -e "Exec Mode:      ${GREEN}${EXEC_MODE}${NC}"
        if [ "$EXEC_MODE" = "run_less" ]; then
            echo -e "Exec Count:     ${GREEN}${K}${NC}"
        fi
        echo -e "Agent:          ${GREEN}${AGENT_TYPE}${NC}"
        echo -e "Timeout:        ${GREEN}${TIMEOUT}s${NC}"
        echo -e "Dataset:        ${GREEN}${DATASET}${NC}"
        echo ""

        # Run experiment
        python runner.py "$INSTANCE_ID" "$EXEC_MODE" "$K" "$AGENT_TYPE" "$TIMEOUT" "$DATASET"
        EXIT_CODE=$?

        if [ $EXIT_CODE -eq 0 ]; then
            echo ""
            echo -e "${GREEN}========================================${NC}"
            echo -e "${GREEN}Experiment Completed!${NC}"
            echo -e "${GREEN}========================================${NC}"

            # Determine dataset directory
            if [[ "$DATASET" == *"Lite"* ]]; then
                DATASET_DIR="swebenchlite"
            else
                DATASET_DIR="swebenchverified"
            fi

            echo -e "Output Directory: ${GREEN}output/${DATASET_DIR}/${AGENT_TYPE}/${EXEC_MODE}/${INSTANCE_ID}/${NC}"
        else
            echo ""
            echo -e "${RED}========================================${NC}"
            echo -e "${RED}Experiment Failed!${NC}"
            echo -e "${RED}========================================${NC}"
        fi

        exit $EXIT_CODE
        ;;

    batch)
        # Batch execution
        if [ $# -lt 2 ]; then
            echo -e "${RED}Error: batch mode requires at least 2 parameters${NC}"
            show_usage
        fi

        INSTANCES_FILE=$1
        EXEC_MODE=$2
        K=${3:-2}
        WORKERS=${4:-4}
        AGENT_TYPE=${5:-claude_code}
        TIMEOUT=${6:-600}
        DATASET=${7:-princeton-nlp/SWE-bench_Lite}

        # Check if instances file exists
        if [[ "$INSTANCES_FILE" = /* ]]; then
            INSTANCE_PATH="$INSTANCES_FILE"
        else
            INSTANCE_PATH="$PROJECT_ROOT/$INSTANCES_FILE"
        fi

        if [ ! -f "$INSTANCE_PATH" ]; then
            echo -e "${RED}Error: Instances file does not exist: $INSTANCES_FILE${NC}"
            exit 1
        fi

        # Count number of instances
        INSTANCE_COUNT=$(grep -v '^#' "$INSTANCE_PATH" | grep -v '^$' | wc -l)

        echo -e "${YELLOW}========================================${NC}"
        echo -e "${YELLOW}Running Batch Experiments${NC}"
        echo -e "${YELLOW}========================================${NC}"
        echo -e "Instances File: ${GREEN}${INSTANCES_FILE}${NC}"
        echo -e "Instance Count: ${GREEN}${INSTANCE_COUNT}${NC}"
        echo -e "Exec Mode:      ${GREEN}${EXEC_MODE}${NC}"
        if [ "$EXEC_MODE" = "run_less" ]; then
            echo -e "Exec Count:     ${GREEN}${K}${NC}"
        fi
        echo -e "Workers:        ${GREEN}${WORKERS}${NC}"
        echo -e "Agent:          ${GREEN}${AGENT_TYPE}${NC}"
        echo -e "Timeout:        ${GREEN}${TIMEOUT}s${NC}"
        echo -e "Dataset:        ${GREEN}${DATASET}${NC}"
        echo ""

        # Run batch experiments
        python batch_runner.py "$INSTANCE_PATH" "$EXEC_MODE" "$K" "$WORKERS" "$AGENT_TYPE" "$TIMEOUT" "$DATASET"
        EXIT_CODE=$?

        if [ $EXIT_CODE -eq 0 ]; then
            echo ""
            echo -e "${GREEN}========================================${NC}"
            echo -e "${GREEN}Batch Experiments Completed!${NC}"
            echo -e "${GREEN}========================================${NC}"
        else
            echo ""
            echo -e "${YELLOW}========================================${NC}"
            echo -e "${YELLOW}Batch Experiments Completed (Partial Failures)${NC}"
            echo -e "${YELLOW}========================================${NC}"
            echo -e "${YELLOW}Tip: Re-run the same command to resume from checkpoint${NC}"
        fi

        # Determine dataset directory
        if [[ "$DATASET" == *"Lite"* ]]; then
            DATASET_DIR="swebenchlite"
        else
            DATASET_DIR="swebenchverified"
        fi

        echo -e "Output Directory: ${GREEN}output/${DATASET_DIR}/${AGENT_TYPE}/${EXEC_MODE}/${NC}"
        echo -e "Checkpoint: ${GREEN}output/${DATASET_DIR}/${AGENT_TYPE}/${EXEC_MODE}/checkpoint.json${NC}"

        exit $EXIT_CODE
        ;;

    *)
        echo -e "${RED}Error: Unknown mode '$MODE'${NC}"
        show_usage
        ;;
esac
