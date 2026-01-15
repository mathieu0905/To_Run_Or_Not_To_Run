#!/bin/bash
# 清理脚本：清理残留的进程和 Docker 容器

echo "=========================================="
echo "清理残留资源"
echo "=========================================="

# 1. 杀死所有 batch_runner.py 进程
echo "正在查找 batch_runner.py 进程..."
BATCH_PIDS=$(ps aux | grep -E "python.*batch_runner\.py" | grep -v grep | awk '{print $2}')
if [ -n "$BATCH_PIDS" ]; then
    echo "找到以下进程："
    ps aux | grep -E "python.*batch_runner\.py" | grep -v grep
    echo ""
    echo "正在终止进程..."
    echo "$BATCH_PIDS" | xargs kill -9 2>/dev/null
    echo "✓ 已终止 batch_runner.py 进程"
else
    echo "✓ 没有找到 batch_runner.py 进程"
fi
echo ""

# 2. 杀死所有 runner.py 进程
echo "正在查找 runner.py 进程..."
RUNNER_PIDS=$(ps aux | grep -E "python.*runner\.py" | grep -v grep | awk '{print $2}')
if [ -n "$RUNNER_PIDS" ]; then
    echo "找到以下进程："
    ps aux | grep -E "python.*runner\.py" | grep -v grep
    echo ""
    echo "正在终止进程..."
    echo "$RUNNER_PIDS" | xargs kill -9 2>/dev/null
    echo "✓ 已终止 runner.py 进程"
else
    echo "✓ 没有找到 runner.py 进程"
fi
echo ""

# 3. 杀死 Docker run 进程（实验运行的容器）
echo "正在查找 Docker run 进程..."
DOCKER_RUN_PIDS=$(ps aux | grep -E "docker run.*swebench" | grep -v grep | awk '{print $2}')
if [ -n "$DOCKER_RUN_PIDS" ]; then
    echo "找到 $(echo "$DOCKER_RUN_PIDS" | wc -l) 个 Docker run 进程"
    echo "正在终止进程..."
    echo "$DOCKER_RUN_PIDS" | xargs kill -9 2>/dev/null
    echo "✓ 已终止 Docker run 进程"
else
    echo "✓ 没有找到 Docker run 进程"
fi
echo ""

# 4. 清理 SWE-bench Docker 容器（只清理实验运行产生的容器，不清理构建中的）
echo "正在查找 SWE-bench Docker 容器..."
SWEBENCH_CONTAINERS=$(docker ps -a | grep swebench | awk '{print $1}')
if [ -n "$SWEBENCH_CONTAINERS" ]; then
    CONTAINER_COUNT=$(echo "$SWEBENCH_CONTAINERS" | wc -l)
    echo "找到 $CONTAINER_COUNT 个 SWE-bench 容器"
    echo "正在停止并删除容器..."
    echo "$SWEBENCH_CONTAINERS" | xargs docker rm -f 2>/dev/null
    echo "✓ 已清理 SWE-bench 容器"
else
    echo "✓ 没有找到 SWE-bench 容器"
fi
echo ""

# 5. 杀死 codex/claude 进程（在容器内运行的）
echo "正在查找 codex/claude 进程..."
AGENT_PIDS=$(ps aux | grep -E "(codex|claude).*exec" | grep -v grep | awk '{print $2}')
if [ -n "$AGENT_PIDS" ]; then
    echo "找到 $(echo "$AGENT_PIDS" | wc -l) 个 agent 进程"
    echo "正在终止进程..."
    echo "$AGENT_PIDS" | xargs kill -9 2>/dev/null
    echo "✓ 已终止 agent 进程"
else
    echo "✓ 没有找到 agent 进程"
fi
echo ""

# 6. 清理临时文件
echo "正在清理临时文件..."
TEMP_FILES=$(find /tmp -name "tmp*" -user $(whoami) -mmin -60 2>/dev/null | grep -E "(instances|trace)" | head -20)
if [ -n "$TEMP_FILES" ]; then
    echo "找到以下临时文件："
    echo "$TEMP_FILES"
    echo "$TEMP_FILES" | xargs rm -f 2>/dev/null
    echo "✓ 已清理临时文件"
else
    echo "✓ 没有找到相关临时文件"
fi
echo ""

echo "=========================================="
echo "清理完成！"
echo "=========================================="
echo ""
echo "当前状态："
echo "- Python 进程: $(ps aux | grep -E "python.*(batch_runner|runner)\.py" | grep -v grep | wc -l) 个"
echo "- Docker run 进程: $(ps aux | grep -E "docker run.*swebench" | grep -v grep | wc -l) 个"
echo "- SWE-bench 容器: $(docker ps -a | grep swebench | wc -l) 个"
echo "- Agent 进程: $(ps aux | grep -E "(codex|claude).*exec" | grep -v grep | wc -l) 个"
echo ""
echo "注意：Docker 构建进程不会被清理，它们是正常的镜像构建任务"
echo ""
