#!/bin/bash
# Docker image background build script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/build_agent_images_parallel.py"
LOG_FILE="$SCRIPT_DIR/build_output.log"
PID_FILE="$SCRIPT_DIR/build.pid"

usage() {
    echo "Usage: $0 {start|stop|status|logs} [lite|verified]"
    echo ""
    echo "Commands:"
    echo "  start [dataset]  - Start build in background (default: lite)"
    echo "  stop             - Stop build"
    echo "  status           - Check build status"
    echo "  logs             - View build logs in real-time"
    echo ""
    echo "Datasets:"
    echo "  lite             - SWE-bench Lite (300 instances)"
    echo "  verified         - SWE-bench-verified (500 instances)"
    exit 1
}

start_build() {
    local dataset="${1:-lite}"

    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "Error: Build is already running (PID: $pid)"
            exit 1
        else
            rm -f "$PID_FILE"
        fi
    fi

    echo "Starting background build: $dataset dataset"
    echo "Log file: $LOG_FILE"

    nohup python3 -u "$PYTHON_SCRIPT" "$dataset" > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"

    echo "Build started (PID: $pid)"
    echo "Use '$0 status' to check status"
    echo "Use '$0 logs' to view logs"
}

stop_build() {
    if [ ! -f "$PID_FILE" ]; then
        echo "No running build"
        exit 0
    fi

    local pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "Stopping build (PID: $pid)..."
        kill "$pid"
        rm -f "$PID_FILE"
        echo "Build stopped"
    else
        echo "Build process does not exist"
        rm -f "$PID_FILE"
    fi
}

check_status() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Status: Not running"
        exit 0
    fi

    local pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "Status: Running (PID: $pid)"
        echo ""
        if [ -f "$LOG_FILE" ]; then
            echo "Recent output:"
            tail -n 10 "$LOG_FILE"
        fi
    else
        echo "Status: Stopped"
        rm -f "$PID_FILE"
    fi
}

show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "Log file does not exist"
        exit 1
    fi

    tail -f "$LOG_FILE"
}

# Main logic
case "${1:-}" in
    start)
        start_build "${2:-lite}"
        ;;
    stop)
        stop_build
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    *)
        usage
        ;;
esac
