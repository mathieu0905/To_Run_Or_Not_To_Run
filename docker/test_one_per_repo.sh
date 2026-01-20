#!/bin/bash
# Test one image per repo

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default parameters
TEST_AGENT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent)
            TEST_AGENT=true
            shift
            ;;
        *)
            echo "Unknown parameter: $1"
            echo "Usage: $0 [--agent]"
            exit 1
            ;;
    esac
done

IMAGE_LIST="docker/image_list.txt"

if [ ! -f "$IMAGE_LIST" ]; then
    echo -e "${RED}Error: Cannot find image list file $IMAGE_LIST${NC}"
    exit 1
fi

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Test one image per repo${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "Test Agent image: ${TEST_AGENT}"
echo ""

# Extract unique repo names and select the first image for each repo
declare -A repo_images

while IFS= read -r image || [ -n "$image" ]; do
    # Skip empty lines and comments
    [[ -z "$image" || "$image" =~ ^# ]] && continue

    # Extract repo name (format: swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id})
    repo=$(echo "$image" | sed 's/swebench\/sweb\.eval\.x86_64\.\([^_]*\)_.*/\1/')

    # If this repo doesn't have an image yet, record it
    if [ -z "${repo_images[$repo]}" ]; then
        repo_images[$repo]="$image"
    fi
done < "$IMAGE_LIST"

echo -e "${YELLOW}Found ${#repo_images[@]} different repos${NC}"
echo ""

PASSED=0
FAILED=0
COUNT=0

for repo in "${!repo_images[@]}"; do
    COUNT=$((COUNT + 1))
    image="${repo_images[$repo]}"

    echo -e "\n${YELLOW}[${COUNT}/${#repo_images[@]}] Testing repo: ${repo}${NC}"
    echo -e "Image: ${image}"

    if [ "$TEST_AGENT" = true ]; then
        ./docker/test_docker_env.sh --image "$image" --agent
    else
        ./docker/test_docker_env.sh --image "$image"
    fi

    if [ $? -eq 0 ]; then
        PASSED=$((PASSED + 1))
        echo -e "${GREEN}✓ ${repo} test passed${NC}"
    else
        FAILED=$((FAILED + 1))
        echo -e "${RED}✗ ${repo} test failed${NC}"
    fi
done

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "Total repos: ${COUNT}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All repo tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some repo tests failed${NC}"
    exit 1
fi
