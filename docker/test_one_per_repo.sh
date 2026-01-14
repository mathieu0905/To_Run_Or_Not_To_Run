#!/bin/bash
# 为每个 repo 测试一个镜像

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 默认参数
TEST_AGENT=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent)
            TEST_AGENT=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--agent]"
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
echo -e "${YELLOW}为每个 repo 测试一个镜像${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "测试 Agent 镜像: ${TEST_AGENT}"
echo ""

# 提取唯一的 repo 名称并为每个 repo 选择第一个镜像
declare -A repo_images

while IFS= read -r image || [ -n "$image" ]; do
    # 跳过空行和注释
    [[ -z "$image" || "$image" =~ ^# ]] && continue

    # 提取 repo 名称（格式：swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}）
    repo=$(echo "$image" | sed 's/swebench\/sweb\.eval\.x86_64\.\([^_]*\)_.*/\1/')

    # 如果这个 repo 还没有镜像，就记录下来
    if [ -z "${repo_images[$repo]}" ]; then
        repo_images[$repo]="$image"
    fi
done < "$IMAGE_LIST"

echo -e "${YELLOW}找到 ${#repo_images[@]} 个不同的 repo${NC}"
echo ""

PASSED=0
FAILED=0
COUNT=0

for repo in "${!repo_images[@]}"; do
    COUNT=$((COUNT + 1))
    image="${repo_images[$repo]}"

    echo -e "\n${YELLOW}[${COUNT}/${#repo_images[@]}] 测试 repo: ${repo}${NC}"
    echo -e "镜像: ${image}"

    if [ "$TEST_AGENT" = true ]; then
        ./docker/test_docker_env.sh --image "$image" --agent
    else
        ./docker/test_docker_env.sh --image "$image"
    fi

    if [ $? -eq 0 ]; then
        PASSED=$((PASSED + 1))
        echo -e "${GREEN}✓ ${repo} 测试通过${NC}"
    else
        FAILED=$((FAILED + 1))
        echo -e "${RED}✗ ${repo} 测试失败${NC}"
    fi
done

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}测试总结${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "总计 repo: ${COUNT}"
echo -e "${GREEN}通过: ${PASSED}${NC}"
echo -e "${RED}失败: ${FAILED}${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}所有 repo 测试通过！${NC}"
    exit 0
else
    echo -e "\n${RED}部分 repo 测试失败${NC}"
    exit 1
fi
