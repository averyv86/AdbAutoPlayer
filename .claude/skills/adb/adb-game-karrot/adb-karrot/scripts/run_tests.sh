#!/bin/bash
# Quick test runner for Karrot AI system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Karrot AI Test Runner${NC}"
echo "================================"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check ADB
if ! command -v adb &> /dev/null; then
    echo -e "${RED}✗ ADB not found${NC}"
    exit 1
fi

# Check device connection
DEVICE_COUNT=$(adb devices | grep -v "List" | grep "device$" | wc -l)
if [ "$DEVICE_COUNT" -eq 0 ]; then
    echo -e "${RED}✗ No ADB devices connected${NC}"
    echo "Run: adb connect 127.0.0.1:5555"
    exit 1
fi
echo -e "${GREEN}✓ ADB device connected${NC}"

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}✗ ANTHROPIC_API_KEY not set${NC}"
    echo "Run: export ANTHROPIC_API_KEY='sk-ant-...'"
    exit 1
fi
echo -e "${GREEN}✓ ANTHROPIC_API_KEY set${NC}"

# Check uv
if ! command -v uv &> /dev/null; then
    echo -e "${RED}✗ uv not found${NC}"
    echo "Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo -e "${GREEN}✓ uv installed${NC}"

# Check test script exists
if [ ! -f "karrot_test_ai.py" ]; then
    echo -e "${RED}✗ karrot_test_ai.py not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Test script found${NC}"

# Run tests based on argument
echo -e "\n${YELLOW}Running tests...${NC}\n"

case "${1:-all}" in
    "vision")
        uv run karrot_test_ai.py --test-vision
        ;;
    "detector")
        uv run karrot_test_ai.py --test-detector
        ;;
    "benchmark")
        uv run karrot_test_ai.py --benchmark
        ;;
    "all")
        uv run karrot_test_ai.py --all --report
        ;;
    "quick")
        uv run karrot_test_ai.py --test-detector --quiet
        ;;
    *)
        echo "Usage: $0 [vision|detector|benchmark|all|quick]"
        exit 1
        ;;
esac

EXIT_CODE=$?

# Show report if generated
if [ -f "/tmp/karrot-test-report.json" ]; then
    echo -e "\n${YELLOW}Test report saved to:${NC} /tmp/karrot-test-report.json"
    
    if command -v jq &> /dev/null; then
        echo -e "\n${YELLOW}Summary:${NC}"
        jq .summary /tmp/karrot-test-report.json
    fi
fi

# Exit with test result
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed${NC}"
else
    echo -e "\n${RED}✗ Some tests failed${NC}"
fi

exit $EXIT_CODE
