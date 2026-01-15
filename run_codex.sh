#!/bin/bash
# 批量运行所有实验配置 - 完全并行版本
# 3个实例 × 2个agent × 6个模式 = 36个实验，所有配置并行运行

set -e

# 默认后台执行，-f 前台执行
if [ "$1" != "-f" ] && [ "$1" != "--foreground" ]; then
    SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
    LOG_FILE="$(cd "$(dirname "$0")" && pwd)/logs/run_codex_$(date +%Y%m%d_%H%M%S).log"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "后台运行中，日志: $LOG_FILE"
    nohup bash "$SCRIPT_PATH" -f > "$LOG_FILE" 2>&1 &
    echo "PID: $!"
    exit 0
fi

# 切换到脚本所在目录
cd "$(dirname "$0")"
SCRIPT_DIR="$(pwd)"

# 切换到 experiments 目录运行
cd experiments

# ========== 配置区域 ==========
# 实验配置
NUM_INSTANCES=100  # 取前 n 个实例
WORKERS=30  # 每个配置内部的并发数
TIMEOUT=1200
DATASET="princeton-nlp/SWE-bench_Lite"

# Claude Code 配置
export CLAUDE_MODEL="${CLAUDE_MODEL:-sonnet}"  # 可选: opus, sonnet, haiku
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-http://39.96.176.191:60660}"

# Codex 配置
export CODEX_MODEL="${CODEX_MODEL:-gpt-5.2}"
export CODEX_REASONING_EFFORT="${CODEX_REASONING_EFFORT:-xhigh}"
# ==============================

# 根据 DATASET 选择对应的 JSON 数据文件
if [ "$DATASET" = "princeton-nlp/SWE-bench_Lite" ]; then
    DATA_FILE="${SCRIPT_DIR}/data/swe_bench_lite.json"
elif [ "$DATASET" = "princeton-nlp/SWE-bench_Verified" ]; then
    DATA_FILE="${SCRIPT_DIR}/data/swe_bench_verified.json"
else
    echo "未知数据集: $DATASET"
    exit 1
fi

# 检查数据文件是否存在
if [ ! -f "$DATA_FILE" ]; then
    echo "数据文件不存在: $DATA_FILE"
    exit 1
fi

# 从 JSON 文件提取 instance_id 并生成临时实例文件（取前 n 个）
INSTANCES_FILE=$(mktemp)
python3 -c "import json; data = json.load(open('$DATA_FILE')); print('\n'.join([d['instance_id'] for d in data[:$NUM_INSTANCES]]))" > "$INSTANCES_FILE"
trap "rm -f $INSTANCES_FILE" EXIT

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "批量实验运行脚本 - 完全并行模式"
echo "=========================================="
echo "实例文件: $INSTANCES_FILE"
echo "每个配置并发数: $WORKERS"
echo "超时时间: ${TIMEOUT}s"
echo "数据集: $DATASET"
echo "=========================================="
echo ""

# 创建日志目录（在项目根目录，按 agent 分层）
LOG_DIR="${SCRIPT_DIR}/logs"
mkdir -p "$LOG_DIR"

# Agent 列表
# AGENTS=("claude_code" "codex")
AGENTS=("codex")

# 模式配置列表
# 格式: "mode k_value"
CONFIGS=(
    "run_free 0"
    "run_less 1"
    # "run_less 2"
    "run_less 3"
    "run_cost 0"
    "run_full 0"
)

# 统计
TOTAL_CONFIGS=$((${#AGENTS[@]} * ${#CONFIGS[@]}))
echo -e "${YELLOW}总共将启动 ${TOTAL_CONFIGS} 个并行任务${NC}"
echo ""

# 存储后台任务的 PID
declare -a PIDS=()
declare -a TASK_NAMES=()

# 遍历所有 agent
for agent in "${AGENTS[@]}"; do
    # 遍历所有模式配置
    for config in "${CONFIGS[@]}"; do
        # 解析配置
        read -r mode k <<< "$config"

        # 构建模式描述
        if [ "$mode" = "run_less" ]; then
            MODE_DESC="${mode}_k${k}"
            TASK_NAME="${agent}_${MODE_DESC}"
        else
            MODE_DESC="${mode}"
            TASK_NAME="${agent}_${mode}"
        fi

        # 创建分层日志目录
        AGENT_LOG_DIR="${LOG_DIR}/${agent}"
        mkdir -p "$AGENT_LOG_DIR"

        # 日志文件
        LOG_FILE="${AGENT_LOG_DIR}/${MODE_DESC}.log"

        echo -e "${BLUE}启动任务:${NC} ${GREEN}${TASK_NAME}${NC} (日志: ${LOG_FILE})"

        # 直接在宿主机运行，agent_caller.py 会为每个实例启动对应的 Docker 容器
        if [ "$mode" = "run_less" ]; then
            (python -u batch_runner.py "${INSTANCES_FILE}" $mode $k $WORKERS $agent $TIMEOUT $DATASET > "$LOG_FILE" 2>&1) &
        else
            (python -u batch_runner.py "${INSTANCES_FILE}" $mode 2 $WORKERS $agent $TIMEOUT $DATASET > "$LOG_FILE" 2>&1) &
        fi

        # 记录 PID 和任务名
        PIDS+=($!)
        TASK_NAMES+=("$TASK_NAME")
    done
done

echo ""
echo "=========================================="
echo -e "${YELLOW}所有 ${TOTAL_CONFIGS} 个任务已启动！${NC}"
echo "=========================================="
echo ""
echo "监控进度："
echo "  - 查看所有日志: ls -lh ${LOG_DIR}/"
echo "  - 实时查看某个日志: tail -f ${LOG_DIR}/<task_name>.log"
echo "  - 查看进程: ps aux | grep batch_runner"
echo ""
echo "等待所有任务完成..."
echo ""

# 等待所有后台任务完成
COMPLETED=0
FAILED=0

for i in "${!PIDS[@]}"; do
    PID=${PIDS[$i]}
    TASK_NAME=${TASK_NAMES[$i]}

    # 等待进程完成
    if wait $PID; then
        echo -e "${GREEN}✓${NC} 任务完成: ${TASK_NAME}"
        COMPLETED=$((COMPLETED + 1))
    else
        echo -e "\033[0;31m✗${NC} 任务失败: ${TASK_NAME} (查看日志: ${LOG_DIR}/${TASK_NAME}.log)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "=========================================="
echo "所有任务执行完毕！"
echo "=========================================="
echo -e "完成: ${GREEN}${COMPLETED}${NC} / 失败: ${FAILED} / 总计: ${TOTAL_CONFIGS}"
echo ""
echo "结果保存在: output/swebenchlite/{agent}/{mode}/{instance_id}/"
echo "日志保存在: ${LOG_DIR}/"
echo ""

# 返回状态码
if [ $FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
