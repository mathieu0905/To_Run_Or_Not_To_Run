#!/bin/bash
# 批量运行所有实验配置 - 完全并行版本
# 3个实例 × 2个agent × 6个模式 = 36个实验，所有配置并行运行

set -e

# 配置
INSTANCES_FILE="test_3_instances.txt"
WORKERS=3  # 每个配置内部的并发数（因为只有3个实例）
TIMEOUT=600
DATASET="princeton-nlp/SWE-bench_Lite"

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

# 启动 Docker 容器（如果还没启动）
echo "检查 Docker 容器状态..."
if ! docker-compose ps swebench-batch | grep -q "Up"; then
    echo "启动 Docker 容器..."
    docker-compose up -d swebench-batch
    sleep 5
fi

# 创建日志目录（按 agent 分层）
LOG_DIR="../logs"
mkdir -p "$LOG_DIR"

# Agent 列表
AGENTS=("claude_code" "codex")

# 模式配置列表
# 格式: "mode k_value"
CONFIGS=(
    "run_free 0"
    "run_less 2"
    "run_less 5"
    "run_less 10"
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

        # 在 Docker 容器内运行批量实验
        if [ "$mode" = "run_less" ]; then
            (docker-compose exec -T swebench-batch bash -c "cd /workspace/experiments && python -u batch_runner.py /workspace/${INSTANCES_FILE} $mode $k $WORKERS $agent $TIMEOUT $DATASET" > "$LOG_FILE" 2>&1) &
        else
            (docker-compose exec -T swebench-batch bash -c "cd /workspace/experiments && python -u batch_runner.py /workspace/${INSTANCES_FILE} $mode 2 $WORKERS $agent $TIMEOUT $DATASET" > "$LOG_FILE" 2>&1) &
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
