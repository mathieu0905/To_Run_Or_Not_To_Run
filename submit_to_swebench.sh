#!/bin/bash

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

# 参数说明
# $1: predictions 文件路径
# $2: run ID (可选)
# $3: 数据集名称 (可选，默认为 SWE-bench_Lite)

PREDICTIONS_PATH=$1
RUN_ID=${2:-"run_$(date +%Y%m%d_%H%M%S)"}
DATASET=${3:-"princeton-nlp/SWE-bench_Lite"}

if [ -z "$PREDICTIONS_PATH" ]; then
    echo "用法: $0 <predictions_path> [run_id] [dataset]"
    echo "示例: $0 output/predictions.json my_run_001"
    exit 1
fi

if [ ! -f "$PREDICTIONS_PATH" ]; then
    echo "错误: 文件不存在: $PREDICTIONS_PATH"
    exit 1
fi

echo "提交预测结果到 SWE-bench..."
echo "  文件: $PREDICTIONS_PATH"
echo "  Run ID: $RUN_ID"
echo "  数据集: $DATASET"
echo ""

# 提交到 SWE-bench
sb-cli submit \
    --predictions "$PREDICTIONS_PATH" \
    --run-id "$RUN_ID" \
    --dataset "$DATASET"

if [ $? -eq 0 ]; then
    echo ""
    echo "提交成功！"
    echo "使用以下命令查看结果:"
    echo "  sb-cli get-report $RUN_ID"
else
    echo ""
    echo "提交失败，请检查错误信息"
    exit 1
fi
