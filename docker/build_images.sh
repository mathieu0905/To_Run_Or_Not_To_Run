#!/bin/bash
# Docker 镜像后台构建脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/build_agent_images_parallel.py"
LOG_FILE="$SCRIPT_DIR/build_output.log"
PID_FILE="$SCRIPT_DIR/build.pid"

usage() {
    echo "用法: $0 {start|stop|status|logs} [lite|verified]"
    echo ""
    echo "命令:"
    echo "  start [dataset]  - 后台启动构建 (默认: lite)"
    echo "  stop             - 停止构建"
    echo "  status           - 查看构建状态"
    echo "  logs             - 实时查看构建日志"
    echo ""
    echo "数据集:"
    echo "  lite             - SWE-bench Lite (300 实例)"
    echo "  verified         - SWE-bench-verified (500 实例)"
    exit 1
}

start_build() {
    local dataset="${1:-lite}"

    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "错误: 构建已在运行 (PID: $pid)"
            exit 1
        else
            rm -f "$PID_FILE"
        fi
    fi

    echo "启动后台构建: $dataset 数据集"
    echo "日志文件: $LOG_FILE"

    nohup python3 -u "$PYTHON_SCRIPT" "$dataset" > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"

    echo "构建已启动 (PID: $pid)"
    echo "使用 '$0 status' 查看状态"
    echo "使用 '$0 logs' 查看日志"
}

stop_build() {
    if [ ! -f "$PID_FILE" ]; then
        echo "没有运行中的构建"
        exit 0
    fi

    local pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "停止构建 (PID: $pid)..."
        kill "$pid"
        rm -f "$PID_FILE"
        echo "构建已停止"
    else
        echo "构建进程不存在"
        rm -f "$PID_FILE"
    fi
}

check_status() {
    if [ ! -f "$PID_FILE" ]; then
        echo "状态: 未运行"
        exit 0
    fi

    local pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "状态: 运行中 (PID: $pid)"
        echo ""
        if [ -f "$LOG_FILE" ]; then
            echo "最近输出:"
            tail -n 10 "$LOG_FILE"
        fi
    else
        echo "状态: 已停止"
        rm -f "$PID_FILE"
    fi
}

show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "日志文件不存在"
        exit 1
    fi

    tail -f "$LOG_FILE"
}

# 主逻辑
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
