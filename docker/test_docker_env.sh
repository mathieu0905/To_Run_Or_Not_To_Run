#!/bin/bash
# 测试 SWE-bench Docker 环境的脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 默认参数
IMAGE_NAME=""
USE_AGENT=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --agent)
            USE_AGENT=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 --image <镜像名称> [--agent]"
            exit 1
            ;;
    esac
done

# 检查是否提供了镜像名称
if [ -z "$IMAGE_NAME" ]; then
    echo -e "${RED}错误: 必须提供镜像名称${NC}"
    echo "用法: $0 --image <镜像名称> [--agent]"
    echo ""
    echo "示例:"
    echo "  $0 --image swebench/sweb.eval.x86_64.django_1776_django-11099"
    echo "  $0 --image swebench/sweb.eval.x86_64.django_1776_django-11099 --agent"
    exit 1
fi

# 如果使用 agent 版本，添加后缀
if [ "$USE_AGENT" = true ]; then
    FULL_IMAGE_NAME="${IMAGE_NAME}-agent:latest"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}:latest"
fi

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}测试 Docker 环境${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "镜像: ${GREEN}${FULL_IMAGE_NAME}${NC}"
echo ""

# 检查镜像是否存在
echo -e "${YELLOW}[1/5] 检查镜像是否存在...${NC}"
if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${FULL_IMAGE_NAME}$"; then
    echo -e "${GREEN}✓ 镜像存在${NC}"
else
    echo -e "${RED}✗ 镜像不存在${NC}"
    exit 1
fi

# 测试容器启动
echo -e "\n${YELLOW}[2/5] 测试容器启动...${NC}"
if docker run --rm "${FULL_IMAGE_NAME}" echo "容器启动成功"; then
    echo -e "${GREEN}✓ 容器可以正常启动${NC}"
else
    echo -e "${RED}✗ 容器启动失败${NC}"
    exit 1
fi

# 检查 conda 环境
echo -e "\n${YELLOW}[3/5] 检查 conda 环境...${NC}"
docker run --rm "${FULL_IMAGE_NAME}" bash -c "conda env list"
if docker run --rm "${FULL_IMAGE_NAME}" bash -c "conda env list | grep -q testbed"; then
    echo -e "${GREEN}✓ testbed 环境存在${NC}"
else
    echo -e "${RED}✗ testbed 环境不存在${NC}"
    exit 1
fi

# 检查工作目录
echo -e "\n${YELLOW}[4/5] 检查工作目录...${NC}"
docker run --rm "${FULL_IMAGE_NAME}" bash -c "ls -la /testbed | head -10"
if docker run --rm "${FULL_IMAGE_NAME}" bash -c "[ -d /testbed ]"; then
    echo -e "${GREEN}✓ /testbed 目录存在${NC}"
else
    echo -e "${RED}✗ /testbed 目录不存在${NC}"
    exit 1
fi

# 测试测试框架
echo -e "\n${YELLOW}[5/5] 检测并测试测试框架...${NC}"

# 尝试检测项目类型
PROJECT_TYPE=$(docker run --rm "${FULL_IMAGE_NAME}" bash -c "
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed
if python -c 'import django' 2>/dev/null; then
    echo 'django'
elif python -m pytest --version 2>/dev/null; then
    echo 'pytest'
elif python -c 'import unittest' 2>/dev/null; then
    echo 'unittest'
else
    echo 'unknown'
fi
")

echo -e "检测到项目类型: ${PROJECT_TYPE}"

case "$PROJECT_TYPE" in
    django)
        if docker run --rm "${FULL_IMAGE_NAME}" bash -c "source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed && python -m django --version" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Django 测试框架可用${NC}"
        else
            echo -e "${RED}✗ Django 测试框架不可用${NC}"
            exit 1
        fi
        ;;
    pytest)
        if docker run --rm "${FULL_IMAGE_NAME}" bash -c "source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed && python -m pytest --version" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ pytest 可用${NC}"
        else
            echo -e "${RED}✗ pytest 不可用${NC}"
            exit 1
        fi
        ;;
    unittest)
        echo -e "${GREEN}✓ unittest 可用${NC}"
        ;;
    *)
        echo -e "${YELLOW}⚠ 无法检测测试框架，但环境可能仍然可用${NC}"
        ;;
esac

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}所有测试通过！${NC}"
echo -e "${GREEN}========================================${NC}"
