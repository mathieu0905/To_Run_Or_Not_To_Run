#!/bin/bash
# 实验运行脚本 - 支持单个实例或批量运行

set -e

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 显示使用说明
show_usage() {
    echo "用法: $0 <mode> [options]"
    echo ""
    echo "模式:"
    echo "  single <instance_id> <mode> [k] [agent_type] [timeout] [dataset]"
    echo "      运行单个实例"
    echo ""
    echo "  batch <instances_file> <mode> [k] [workers] [agent_type] [timeout] [dataset]"
    echo "      批量运行多个实例"
    echo ""
    echo "执行模式 (mode):"
    echo "  run_free    - 不执行代码，纯推理"
    echo "  run_less    - 限制执行次数（需要指定 k）"
    echo "  run_cost    - 成本意识决策"
    echo "  run_full    - 无限制执行"
    echo ""
    echo "示例:"
    echo "  # 运行单个实例"
    echo "  $0 single django__django-11099 run_free"
    echo "  $0 single django__django-11099 run_less 2"
    echo "  $0 single django__django-11099 run_full claude_code 600"
    echo ""
    echo "  # 批量运行"
    echo "  $0 batch instances.txt run_less 2 4"
    echo "  $0 batch instances.txt run_free 2 8 claude_code 600"
    echo ""
    exit 1
}

# 检查参数
if [ $# -lt 2 ]; then
    show_usage
fi

MODE=$1
shift

# 切换到 experiments 目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/experiments"

case "$MODE" in
    single)
        # 运行单个实例
        if [ $# -lt 2 ]; then
            echo -e "${RED}错误: single 模式需要至少 2 个参数${NC}"
            show_usage
        fi

        INSTANCE_ID=$1
        EXEC_MODE=$2
        K=${3:-2}
        AGENT_TYPE=${4:-claude_code}
        TIMEOUT=${5:-600}
        DATASET=${6:-princeton-nlp/SWE-bench_Lite}

        echo -e "${YELLOW}========================================${NC}"
        echo -e "${YELLOW}运行单个实例${NC}"
        echo -e "${YELLOW}========================================${NC}"
        echo -e "实例 ID:    ${GREEN}${INSTANCE_ID}${NC}"
        echo -e "执行模式:   ${GREEN}${EXEC_MODE}${NC}"
        if [ "$EXEC_MODE" = "run_less" ]; then
            echo -e "执行次数:   ${GREEN}${K}${NC}"
        fi
        echo -e "Agent:      ${GREEN}${AGENT_TYPE}${NC}"
        echo -e "超时:       ${GREEN}${TIMEOUT}s${NC}"
        echo -e "数据集:     ${GREEN}${DATASET}${NC}"
        echo ""

        # 运行实验
        python runner.py "$INSTANCE_ID" "$EXEC_MODE" "$K" "$AGENT_TYPE" "$TIMEOUT" "$DATASET"
        EXIT_CODE=$?

        if [ $EXIT_CODE -eq 0 ]; then
            echo ""
            echo -e "${GREEN}========================================${NC}"
            echo -e "${GREEN}实验完成！${NC}"
            echo -e "${GREEN}========================================${NC}"

            # 确定数据集目录
            if [[ "$DATASET" == *"Lite"* ]]; then
                DATASET_DIR="swebenchlite"
            else
                DATASET_DIR="swebenchverified"
            fi

            echo -e "输出目录: ${GREEN}output/${DATASET_DIR}/${AGENT_TYPE}/${EXEC_MODE}/${INSTANCE_ID}/${NC}"
        else
            echo ""
            echo -e "${RED}========================================${NC}"
            echo -e "${RED}实验失败！${NC}"
            echo -e "${RED}========================================${NC}"
        fi

        exit $EXIT_CODE
        ;;

    batch)
        # 批量运行
        if [ $# -lt 2 ]; then
            echo -e "${RED}错误: batch 模式需要至少 2 个参数${NC}"
            show_usage
        fi

        INSTANCES_FILE=$1
        EXEC_MODE=$2
        K=${3:-2}
        WORKERS=${4:-4}
        AGENT_TYPE=${5:-claude_code}
        TIMEOUT=${6:-600}
        DATASET=${7:-princeton-nlp/SWE-bench_Lite}

        # 检查实例文件是否存在
        if [ ! -f "../$INSTANCES_FILE" ]; then
            echo -e "${RED}错误: 实例文件不存在: $INSTANCES_FILE${NC}"
            exit 1
        fi

        # 统计实例数量
        INSTANCE_COUNT=$(grep -v '^#' "../$INSTANCES_FILE" | grep -v '^$' | wc -l)

        echo -e "${YELLOW}========================================${NC}"
        echo -e "${YELLOW}批量运行实验${NC}"
        echo -e "${YELLOW}========================================${NC}"
        echo -e "实例文件:   ${GREEN}${INSTANCES_FILE}${NC}"
        echo -e "实例数量:   ${GREEN}${INSTANCE_COUNT}${NC}"
        echo -e "执行模式:   ${GREEN}${EXEC_MODE}${NC}"
        if [ "$EXEC_MODE" = "run_less" ]; then
            echo -e "执行次数:   ${GREEN}${K}${NC}"
        fi
        echo -e "并发数:     ${GREEN}${WORKERS}${NC}"
        echo -e "Agent:      ${GREEN}${AGENT_TYPE}${NC}"
        echo -e "超时:       ${GREEN}${TIMEOUT}s${NC}"
        echo -e "数据集:     ${GREEN}${DATASET}${NC}"
        echo ""

        # 运行批量实验
        python batch_runner.py "../$INSTANCES_FILE" "$EXEC_MODE" "$K" "$WORKERS" "$AGENT_TYPE" "$TIMEOUT" "$DATASET"
        EXIT_CODE=$?

        if [ $EXIT_CODE -eq 0 ]; then
            echo ""
            echo -e "${GREEN}========================================${NC}"
            echo -e "${GREEN}批量实验完成！${NC}"
            echo -e "${GREEN}========================================${NC}"
        else
            echo ""
            echo -e "${YELLOW}========================================${NC}"
            echo -e "${YELLOW}批量实验完成（部分失败）${NC}"
            echo -e "${YELLOW}========================================${NC}"
            echo -e "${YELLOW}提示: 重新运行相同命令可以从断点继续${NC}"
        fi

        # 确定数据集目录
        if [[ "$DATASET" == *"Lite"* ]]; then
            DATASET_DIR="swebenchlite"
        else
            DATASET_DIR="swebenchverified"
        fi

        echo -e "输出目录: ${GREEN}output/${DATASET_DIR}/${AGENT_TYPE}/${EXEC_MODE}/${NC}"
        echo -e "Checkpoint: ${GREEN}output/${DATASET_DIR}/${AGENT_TYPE}/${EXEC_MODE}/checkpoint.json${NC}"

        exit $EXIT_CODE
        ;;

    *)
        echo -e "${RED}错误: 未知模式 '$MODE'${NC}"
        show_usage
        ;;
esac
