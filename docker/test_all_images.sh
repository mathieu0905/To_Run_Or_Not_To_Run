#!/bin/bash
# Batch test all SWE-bench Docker images

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default parameters
TEST_AGENT=false
MAX_TESTS=5

# Parse command line arguments
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
            echo "Unknown parameter: $1"
            echo "Usage: $0 [--agent] [--max N] [--all]"
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
echo -e "${YELLOW}Batch Testing SWE-bench Docker Environment${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "Test Agent Image: ${TEST_AGENT}"
echo -e "Maximum Test Count: ${MAX_TESTS}"
echo ""

PASSED=0
FAILED=0
COUNT=0

while IFS= read -r image || [ -n "$image" ]; do
    # Skip empty lines and comments
    [[ -z "$image" || "$image" =~ ^# ]] && continue

    COUNT=$((COUNT + 1))
    if [ $COUNT -gt $MAX_TESTS ]; then
        break
    fi

    echo -e "\n${YELLOW}[${COUNT}/${MAX_TESTS}] Testing image: ${image}${NC}"

    if [ "$TEST_AGENT" = true ]; then
        ./docker/test_docker_env.sh --image "$image" --agent
    else
        ./docker/test_docker_env.sh --image "$image"
    fi

    if [ $? -eq 0 ]; then
        PASSED=$((PASSED + 1))
        echo -e "${GREEN}✓ Test passed${NC}"
    else
        FAILED=$((FAILED + 1))
        echo -e "${RED}✗ Test failed${NC}"
    fi
done < "$IMAGE_LIST"

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "Total: ${COUNT}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed${NC}"
    exit 1
fi
