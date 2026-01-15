#!/bin/bash

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "错误: .env 文件不存在"
    exit 1
fi

# 检查 API key 是否设置
if [ -z "$SWEBENCH_API_KEY" ]; then
    echo "错误: SWEBENCH_API_KEY 未设置"
    exit 1
fi

# 激活 conda 环境
source /data/zhihao/miniconda3/etc/profile.d/conda.sh
conda activate swebench

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --list                    列出所有可用的 dataset/agent/mode 组合"
    echo "  --dataset <name>          数据集名称 (swebenchlite, swebenchverified)"
    echo "  --agent <name>            agent 名称 (claude_code, codex)"
    echo "  --mode <name>             模式名称 (run_free, run_less_k1, run_less_k3, run_cost, run_full)"
    echo "  --run-id <id>             运行 ID (可选，默认为 agent_mode)"
    echo "  --all                     生成并提交所有组合"
    echo "  --gen-only                只生成 predictions 文件，不提交"
    echo "  --help                    显示帮助"
    echo ""
    echo "示例:"
    echo "  $0 --list"
    echo "  $0 --dataset swebenchverified --agent codex --mode run_free"
    echo "  $0 --dataset swebenchverified --agent codex --mode run_free --run-id my_run_001"
}

# 解析参数
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
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 列出所有组合
if [ "$LIST" = true ]; then
    python3 generate_predictions.py --list
    exit 0
fi

# 映射数据集名称到 sb-cli 格式
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

# 提交单个组合
submit_one() {
    local dataset=$1
    local agent=$2
    local mode=$3
    local run_id=$4

    # 生成 predictions 文件
    echo "生成 predictions 文件: ${dataset}/${agent}/${mode}"
    python3 generate_predictions.py --dataset "$dataset" --agent "$agent" --mode "$mode"

    if [ "$GEN_ONLY" = true ]; then
        echo "只生成文件，跳过提交"
        return 0
    fi

    # 确定 predictions 文件路径
    local predictions_file="predictions/${dataset}_${agent}_${mode}.json"

    if [ ! -f "$predictions_file" ]; then
        echo "错误: predictions 文件不存在: $predictions_file"
        return 1
    fi

    # 确定 run_id
    if [ -z "$run_id" ]; then
        run_id="${dataset}_${agent}_${mode}"
    fi

    # 映射数据集名称
    local sb_dataset=$(map_dataset "$dataset")

    echo ""
    echo "提交到 SWE-bench..."
    echo "  数据集: $sb_dataset"
    echo "  Split: test"
    echo "  Run ID: $run_id"
    echo "  文件: $predictions_file"
    echo ""

    # 提交
    sb-cli submit "$sb_dataset" test \
        --predictions_path "$predictions_file" \
        --run_id "$run_id"

    if [ $? -eq 0 ]; then
        echo ""
        echo "提交成功！"
        echo "使用以下命令查看结果:"
        echo "  sb-cli get-report $sb_dataset test $run_id"
    else
        echo ""
        echo "提交失败"
        return 1
    fi
}

# 主逻辑
if [ "$ALL" = true ]; then
    echo "生成所有 predictions 文件..."
    python3 generate_predictions.py --all

    if [ "$GEN_ONLY" = true ]; then
        echo "只生成文件，跳过提交"
        exit 0
    fi

    echo ""
    echo "注意: --all 模式只生成文件，不自动提交"
    echo "请手动选择要提交的组合"
    exit 0
fi

# 检查必要参数
if [ -z "$DATASET" ] || [ -z "$AGENT" ] || [ -z "$MODE" ]; then
    echo "错误: 需要指定 --dataset, --agent, --mode"
    echo ""
    show_help
    exit 1
fi

submit_one "$DATASET" "$AGENT" "$MODE" "$RUN_ID"
