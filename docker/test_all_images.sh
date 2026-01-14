#!/bin/bash
# 批量测试所有 SWE-bench Docker 镜像

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 默认参数
TEST_AGENT=false
MAX_TESTS=5

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent)
            TEST_AGENT=true
            shift
            ;;
        --max)
            MAX_TESTS="$2"
            shift 2
            ;;
        --all)
            MAX_TESTS=999999
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--agent] [--max N] [--all]"
            exit 1
            ;;
    esac
done

IMAGE_LIST="docker/image_list.txt"

if [ ! -f "$IMAGE_LIST" ]; then
    echo -e "${RED}错误: 找不到镜像列表文件 $IMAGE_LIST${NC}"
    exit 1
fi

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}批量测试 SWE-bench Docker 环境${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "测试 Agent 镜像: ${TEST_AGENT}"
echo -e "最大测试数量: ${MAX_TESTS}"
echo ""

PASSED=0
FAILED=0
COUNT=0

while IFS= read -r image || [ -n "$image" ]; do
    # 跳过空行和注释
    [[ -z "$image" || "$image" =~ ^# ]] && continue

    COUNT=$((COUNT + 1))
    if [ $COUNT -gt $MAX_TESTS ]; then
        break
    fi

    echo -e "\n${YELLOW}[${COUNT}/${MAX_TESTS}] 测试镜像: ${image}${NC}"

    if [ "$TEST_AGENT" = true ]; then
        ./docker/test_docker_env.sh --image "$image" --agent
    else
        ./docker/test_docker_env.sh --image "$image"
    fi

    if [ $? -eq 0 ]; then
        PASSED=$((PASSED + 1))
        echo -e "${GREEN}✓ 测试通过${NC}"
    else
        FAILED=$((FAILED + 1))
        echo -e "${RED}✗ 测试失败${NC}"
    fi
done < "$IMAGE_LIST"

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}测试总结${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "总计: ${COUNT}"
echo -e "${GREEN}通过: ${PASSED}${NC}"
echo -e "${RED}失败: ${FAILED}${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}所有测试通过！${NC}"
    exit 0
else
    echo -e "\n${RED}部分测试失败${NC}"
    exit 1
fi
