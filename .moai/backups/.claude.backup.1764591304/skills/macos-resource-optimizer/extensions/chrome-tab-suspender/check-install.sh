#!/bin/bash
# MoAI Tab Suspender - Installation Check & Auto-Installer
# Version: 1.0.0
# Purpose: Detect existing installation, test connection, auto-install if needed

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
CHROME_MANIFEST="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.moai.tab_suspender.json"
DIA_MANIFEST="$HOME/Library/Application Support/Dia Browser/NativeMessagingHosts/com.moai.tab_suspender.json"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TAB_SUSPENDER_SCRIPT="$SCRIPT_DIR/../../scripts/tab_suspender.py"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  MoAI Tab Suspender - Installation Check${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Check if manifests exist
echo "Step 1: Checking installation status..."
echo ""

CHROME_EXISTS=false
DIA_EXISTS=false

if [ -f "$CHROME_MANIFEST" ]; then
    echo -e "${GREEN}✅ Chrome manifest found${NC}"
    CHROME_EXISTS=true
else
    echo -e "${YELLOW}⚠️  Chrome manifest not found${NC}"
fi

if [ -f "$DIA_MANIFEST" ]; then
    echo -e "${GREEN}✅ Dia Browser manifest found${NC}"
    DIA_EXISTS=true
else
    echo -e "${YELLOW}⚠️  Dia Browser manifest not found${NC}"
fi

# Step 2: Test connection if at least one manifest exists
if [ "$CHROME_EXISTS" = true ] || [ "$DIA_EXISTS" = true ]; then
    echo ""
    echo "Step 2: Testing Native Messaging connection..."
    echo ""

    if command -v uv &> /dev/null; then
        if [ -f "$TAB_SUSPENDER_SCRIPT" ]; then
            # Run connection test
            if uv run "$TAB_SUSPENDER_SCRIPT" --test &> /dev/null; then
                echo -e "${GREEN}✅ Connection test PASSED!${NC}"
                echo ""
                echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
                echo -e "${GREEN}  ✅ Extension fully configured and working!${NC}"
                echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
                echo ""
                echo "Extension is ready to use."
                echo "확장 프로그램이 정상적으로 작동합니다."
                echo ""
                echo "Usage / 사용법:"
                echo "  uv run scripts/tab_suspender.py --suspend --browser=chrome"
                echo "  /macos-resource-optimizer:suspend-tabs"
                echo ""
                exit 0
            else
                echo -e "${RED}❌ Connection test FAILED${NC}"
                echo ""
                echo "Extension is installed but not working properly."
                echo "확장 프로그램이 설치되어 있지만 정상적으로 작동하지 않습니다."
                echo ""
                echo "Running repair installation..."
                echo "복구 설치를 실행합니다..."
                echo ""
            fi
        else
            echo -e "${RED}❌ tab_suspender.py script not found at: $TAB_SUSPENDER_SCRIPT${NC}"
            echo ""
            echo "Script file is missing. Running full installation..."
            echo "스크립트 파일이 없습니다. 전체 설치를 실행합니다..."
            echo ""
        fi
    else
        echo -e "${RED}❌ UV not found. Please install UV first:${NC}"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo ""
        exit 1
    fi
else
    echo ""
    echo "No manifests found. Extension not installed."
    echo "매니페스트를 찾을 수 없습니다. 확장 프로그램이 설치되지 않았습니다."
    echo ""
    echo "Running full installation..."
    echo "전체 설치를 실행합니다..."
    echo ""
fi

# Step 3: Run installation
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Starting Installation / 설치 시작${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

INSTALL_SCRIPT="$SCRIPT_DIR/install.sh"

if [ -f "$INSTALL_SCRIPT" ]; then
    bash "$INSTALL_SCRIPT"

    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  ✅ Installation completed successfully!${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        exit 0
    else
        echo ""
        echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}  ❌ Installation failed${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "Please check the error messages above and try again."
        echo "위의 오류 메시지를 확인하고 다시 시도하세요."
        echo ""
        exit 1
    fi
else
    echo -e "${RED}❌ install.sh not found at: $INSTALL_SCRIPT${NC}"
    echo ""
    echo "Installation script is missing. Please ensure you're in the correct directory."
    echo "설치 스크립트를 찾을 수 없습니다. 올바른 디렉토리에 있는지 확인하세요."
    echo ""
    exit 1
fi
