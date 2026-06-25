#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment variables
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

# Check if API key is set
if [ -z "$SWEBENCH_API_KEY" ]; then
    echo "Error: SWEBENCH_API_KEY is not set"
    exit 1
fi

if [ -n "${CONDA_EXE:-}" ]; then
    CONDA_BASE="$("$CONDA_EXE" info --base)"
    # shellcheck disable=SC1091
    source "$CONDA_BASE/etc/profile.d/conda.sh"
fi
if command -v conda >/dev/null 2>&1; then
    conda activate "${SWEBENCH_CONDA_ENV:-swebench}" || true
fi

# Show help
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --list                    List all available dataset/agent/mode combinations"
    echo "  --dataset <name>          Dataset name (swebenchlite, swebenchverified)"
    echo "  --agent <name>            Agent name (claude_code, codex)"
    echo "  --mode <name>             Mode name (run_free, run_less_k1, run_less_k3, run_cost, run_full)"
    echo "  --run-id <id>             Run ID (optional, defaults to agent_mode)"
    echo "  --all                     Generate and submit all combinations"
    echo "  --gen-only                Only generate predictions file, do not submit"
    echo "  --help                    Show help"
    echo ""
    echo "Examples:"
    echo "  $0 --list"
    echo "  $0 --dataset swebenchverified --agent codex --mode run_free"
    echo "  $0 --dataset swebenchverified --agent codex --mode run_free --run-id my_run_001"
}

# Parse arguments
LIST=false
GEN_ONLY=false
ALL=false
DATASET=""
AGENT=""
MODE=""
RUN_ID=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --list)
            LIST=true
            shift
            ;;
        --dataset)
            DATASET="$2"
            shift 2
            ;;
        --agent)
            AGENT="$2"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --run-id)
            RUN_ID="$2"
            shift 2
            ;;
        --all)
            ALL=true
            shift
            ;;
        --gen-only)
            GEN_ONLY=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# List all combinations
if [ "$LIST" = true ]; then
    python3 scripts/generate_predictions.py --list
    exit 0
fi

# Map dataset name to sb-cli format
map_dataset() {
    case $1 in
        swebenchlite)
            echo "swe-bench_lite"
            ;;
        swebenchverified)
            echo "swe-bench_verified"
            ;;
        *)
            echo "$1"
            ;;
    esac
}

# Submit single combination
submit_one() {
    local dataset=$1
    local agent=$2
    local mode=$3
    local run_id=$4

    # Generate predictions file
    echo "Generating predictions file: ${dataset}/${agent}/${mode}"
    python3 scripts/generate_predictions.py --dataset "$dataset" --agent "$agent" --mode "$mode"

    if [ "$GEN_ONLY" = true ]; then
        echo "Only generating file, skipping submission"
        return 0
    fi

    # Determine predictions file path
    local predictions_file="predictions/${dataset}_${agent}_${mode}.json"

    if [ ! -f "$predictions_file" ]; then
        echo "Error: predictions file does not exist: $predictions_file"
        return 1
    fi

    # Determine run_id
    if [ -z "$run_id" ]; then
        run_id="${dataset}_${agent}_${mode}"
    fi

    # Map dataset name
    local sb_dataset=$(map_dataset "$dataset")

    echo ""
    echo "Submitting to SWE-bench..."
    echo "  Dataset: $sb_dataset"
    echo "  Split: test"
    echo "  Run ID: $run_id"
    echo "  File: $predictions_file"
    echo ""

    # Submit
    sb-cli submit "$sb_dataset" test \
        --predictions_path "$predictions_file" \
        --run_id "$run_id"

    if [ $? -eq 0 ]; then
        echo ""
        echo "Submission successful!"
        echo "Use the following command to view results:"
        echo "  sb-cli get-report $sb_dataset test $run_id"
    else
        echo ""
        echo "Submission failed"
        return 1
    fi
}

# Main logic
if [ "$ALL" = true ]; then
    echo "Generating all predictions files..."
    python3 scripts/generate_predictions.py --all

    if [ "$GEN_ONLY" = true ]; then
        echo "Only generating files, skipping submission"
        exit 0
    fi

    echo ""
    echo "Note: --all mode only generates files, does not auto-submit"
    echo "Please manually select combinations to submit"
    exit 0
fi

# Check required parameters
if [ -z "$DATASET" ] || [ -z "$AGENT" ] || [ -z "$MODE" ]; then
    echo "Error: must specify --dataset, --agent, --mode"
    echo ""
    show_help
    exit 1
fi

submit_one "$DATASET" "$AGENT" "$MODE" "$RUN_ID"
