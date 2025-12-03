#!/bin/bash

# MoAI Tab Suspender - Installation Script
#
# Automates setup of Chrome extension and Native Messaging configuration.
#
# Usage:
#   cd extensions/chrome-tab-suspender
#   ./install.sh
#
# Author: MoAI-ADK
# Version: 1.0.0

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${GREEN}🚀 MoAI Tab Suspender Installation${NC}"
echo "======================================"
echo ""

# Step 1: Verify extension files
echo -e "${YELLOW}Step 1: Verifying extension files...${NC}"

if [ ! -f "$SCRIPT_DIR/manifest.json" ]; then
    echo -e "${RED}❌ manifest.json not found${NC}"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/background.js" ]; then
    echo -e "${RED}❌ background.js not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Extension files verified${NC}"
echo ""

# Step 2: Verify Native Messaging host script
echo -e "${YELLOW}Step 2: Verifying Native Messaging host...${NC}"

HOST_SCRIPT="$PROJECT_ROOT/scripts/tab_suspender.py"

if [ ! -f "$HOST_SCRIPT" ]; then
    echo -e "${RED}❌ tab_suspender.py not found at: $HOST_SCRIPT${NC}"
    exit 1
fi

# Make script executable
chmod +x "$HOST_SCRIPT"
echo -e "${GREEN}✅ Native Messaging host verified${NC}"
echo ""

# Step 3: Install extension in Chrome
echo -e "${YELLOW}Step 3: Installing Chrome extension...${NC}"
echo ""
echo "Please follow these steps to install the extension:"
echo ""
echo "1. Open Chrome and navigate to: chrome://extensions/"
echo "2. Enable 'Developer mode' (toggle in top-right)"
echo "3. Click 'Load unpacked'"
echo "4. Select this directory: $SCRIPT_DIR"
echo "5. Copy the Extension ID (looks like: abcdefghijklmnopqrstuvwxyzabcdef)"
echo ""
read -p "Press ENTER once you've completed steps 1-4 and have the Extension ID ready..."
echo ""
read -p "Paste the Extension ID here: " EXTENSION_ID

# Validate Extension ID format
if [[ ! "$EXTENSION_ID" =~ ^[a-z]{32}$ ]]; then
    echo -e "${YELLOW}⚠️  Extension ID format looks unusual. Expected 32 lowercase letters.${NC}"
    read -p "Continue anyway? (y/n): " confirm
    if [[ "$confirm" != "y" ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

echo -e "${GREEN}✅ Extension ID: $EXTENSION_ID${NC}"
echo ""

# Step 4: Create Native Messaging manifest
echo -e "${YELLOW}Step 4: Creating Native Messaging manifest...${NC}"

# Create ~/.moai/bin directory
mkdir -p ~/.moai/bin

# Create Native Messaging manifest
MANIFEST_PATH="$HOME/.moai/bin/com.moai.tab_suspender.json"

cat > "$MANIFEST_PATH" << EOF
{
  "name": "com.moai.tab_suspender",
  "description": "MoAI Tab Suspender Native Messaging Host",
  "path": "$HOST_SCRIPT",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://$EXTENSION_ID/"
  ]
}
EOF

echo -e "${GREEN}✅ Created manifest: $MANIFEST_PATH${NC}"
echo ""

# Step 5: Register with Chrome
echo -e "${YELLOW}Step 5: Registering with Chrome...${NC}"

CHROME_HOST_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
mkdir -p "$CHROME_HOST_DIR"

ln -sf "$MANIFEST_PATH" "$CHROME_HOST_DIR/com.moai.tab_suspender.json"

echo -e "${GREEN}✅ Registered with Chrome${NC}"
echo ""

# Step 6: Register with Dia Browser (if exists)
DIA_HOST_DIR="$HOME/Library/Application Support/Dia Browser/NativeMessagingHosts"

if [ -d "$HOME/Library/Application Support/Dia Browser" ]; then
    echo -e "${YELLOW}Step 6: Registering with Dia Browser...${NC}"

    mkdir -p "$DIA_HOST_DIR"
    ln -sf "$MANIFEST_PATH" "$DIA_HOST_DIR/com.moai.tab_suspender.json"

    echo -e "${GREEN}✅ Registered with Dia Browser${NC}"
    echo ""
else
    echo -e "${YELLOW}Step 6: Dia Browser not found (skipping)${NC}"
    echo ""
fi

# Step 7: Test connection
echo -e "${YELLOW}Step 7: Testing Native Messaging connection...${NC}"
echo ""

# Give user time to verify extension is installed
echo "Please verify in Chrome that:"
echo "  - Extension is enabled (chrome://extensions/)"
echo "  - No errors shown"
echo ""
read -p "Press ENTER to test connection..."
echo ""

# Run test
if uv run "$HOST_SCRIPT" --test; then
    echo ""
    echo -e "${GREEN}✅ Installation successful!${NC}"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠️  Connection test had issues${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Restart Chrome completely"
    echo "  2. Check extension is enabled at chrome://extensions/"
    echo "  3. Check for errors in extension's background page"
    echo "  4. Run: uv run $HOST_SCRIPT --test"
    echo ""
fi

# Print summary
echo "======================================"
echo -e "${GREEN}Installation Summary${NC}"
echo "======================================"
echo ""
echo "Extension Directory: $SCRIPT_DIR"
echo "Extension ID: $EXTENSION_ID"
echo "Native Messaging Manifest: $MANIFEST_PATH"
echo "Host Script: $HOST_SCRIPT"
echo ""
echo "Next Steps:"
echo "  1. Test tab suspension:"
echo "     uv run scripts/tab_suspender.py --suspend --browser=chrome"
echo ""
echo "  2. Integrate with memory optimizer:"
echo "     /macos-resource-optimizer:quick-optimize"
echo ""
echo -e "${GREEN}✨ Ready to use!${NC}"
