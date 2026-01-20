#!/bin/bash
# Script to test SWE-bench Docker environment

set -e

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default parameters
IMAGE_NAME=""
USE_AGENT=false

# Parse command line arguments
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
            echo "Unknown parameter: $1"
            echo "Usage: $0 --image <image_name> [--agent]"
            exit 1
            ;;
    esac
done

# Check if image name is provided
if [ -z "$IMAGE_NAME" ]; then
    echo -e "${RED}Error: Image name must be provided${NC}"
    echo "Usage: $0 --image <image_name> [--agent]"
    echo ""
    echo "Examples:"
    echo "  $0 --image swebench/sweb.eval.x86_64.django_1776_django-11099"
    echo "  $0 --image swebench/sweb.eval.x86_64.django_1776_django-11099 --agent"
    exit 1
fi

# If using agent version, add suffix
if [ "$USE_AGENT" = true ]; then
    FULL_IMAGE_NAME="${IMAGE_NAME}-agent:latest"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}:latest"
fi

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Testing Docker Environment${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "Image: ${GREEN}${FULL_IMAGE_NAME}${NC}"
echo ""

# Check if image exists
echo -e "${YELLOW}[1/5] Checking if image exists...${NC}"
if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${FULL_IMAGE_NAME}$"; then
    echo -e "${GREEN}✓ Image exists${NC}"
else
    echo -e "${RED}✗ Image does not exist${NC}"
    exit 1
fi

# Test container startup
echo -e "\n${YELLOW}[2/5] Testing container startup...${NC}"
if docker run --rm "${FULL_IMAGE_NAME}" echo "Container started successfully"; then
    echo -e "${GREEN}✓ Container can start normally${NC}"
else
    echo -e "${RED}✗ Container startup failed${NC}"
    exit 1
fi

# Check conda environment
echo -e "\n${YELLOW}[3/5] Checking conda environment...${NC}"
docker run --rm "${FULL_IMAGE_NAME}" bash -c "conda env list"
if docker run --rm "${FULL_IMAGE_NAME}" bash -c "conda env list | grep -q testbed"; then
    echo -e "${GREEN}✓ testbed environment exists${NC}"
else
    echo -e "${RED}✗ testbed environment does not exist${NC}"
    exit 1
fi

# Check working directory
echo -e "\n${YELLOW}[4/5] Checking working directory...${NC}"
docker run --rm "${FULL_IMAGE_NAME}" bash -c "ls -la /testbed | head -10"
if docker run --rm "${FULL_IMAGE_NAME}" bash -c "[ -d /testbed ]"; then
    echo -e "${GREEN}✓ /testbed directory exists${NC}"
else
    echo -e "${RED}✗ /testbed directory does not exist${NC}"
    exit 1
fi

# Test testing framework
echo -e "\n${YELLOW}[5/5] Detecting and testing testing framework...${NC}"

# Try to detect project type
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

echo -e "Detected project type: ${PROJECT_TYPE}"

case "$PROJECT_TYPE" in
    django)
        if docker run --rm "${FULL_IMAGE_NAME}" bash -c "source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed && python -m django --version" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Django testing framework is available${NC}"
        else
            echo -e "${RED}✗ Django testing framework is not available${NC}"
            exit 1
        fi
        ;;
    pytest)
        if docker run --rm "${FULL_IMAGE_NAME}" bash -c "source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed && python -m pytest --version" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ pytest is available${NC}"
        else
            echo -e "${RED}✗ pytest is not available${NC}"
            exit 1
        fi
        ;;
    unittest)
        echo -e "${GREEN}✓ unittest is available${NC}"
        ;;
    *)
        echo -e "${YELLOW}⚠ Unable to detect testing framework, but environment may still be usable${NC}"
        ;;
esac

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}All tests passed!${NC}"
echo -e "${GREEN}========================================${NC}"
