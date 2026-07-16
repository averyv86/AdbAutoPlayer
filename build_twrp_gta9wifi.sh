#!/bin/bash
# =============================================================================
# build_twrp_gta9wifi.sh — Build TWRP for Samsung Galaxy Tab A9 (SM-X110)
# =============================================================================
# Run this on Ubuntu 20.04+ or Debian 11+ (native, WSL2, or Google Colab)
# Requires ~120GB disk space, 8GB+ RAM, and a few hours of build time.
#
# Usage:
#   chmod +x build_twrp_gta9wifi.sh
#   ./build_twrp_gta9wifi.sh
#
# Output: out/target/product/gta9wifi/recovery.img
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$HOME/twrp_build"
JOBS=$(nproc --all 2>/dev/null || echo 4)

echo "=========================================="
echo " TWRP Builder for SM-X110 (gta9wifi)"
echo " Script dir: $SCRIPT_DIR"
echo " Build dir:  $BUILD_DIR"
echo " CPU cores:  $JOBS"
echo "=========================================="

# --- Step 1: Install dependencies ---
echo ""
echo "[1/7] Installing dependencies..."
sudo apt update -y
sudo apt install -y \
    bc bison build-essential ccache curl flex g++-multilib gcc-multilib \
    git gnupg gperf imagemagick lib32ncurses5-dev lib32readline-dev \
    lib32z1-dev liblz4-tool libncurses5 libncurses5-dev libsdl1.2-dev \
    libssl-dev libxml2 libxml2-utils lz4 lzop pngcrush \
    rsync schedtool squashfs-tools xsltproc zip zlib1g-dev \
    python3 python3-pip openjdk-11-jdk android-sdk-libsparse-utils \
    erofs-utils device-tree-compiler

# --- Step 2: Set up repo tool ---
echo ""
echo "[2/7] Installing repo..."
if ! command -v repo &>/dev/null; then
    mkdir -p "$HOME/bin"
    curl https://storage.googleapis.com/git-repo-downloads/repo > "$HOME/bin/repo"
    chmod a+x "$HOME/bin/repo"
    export PATH="$HOME/bin:$PATH"
fi

# --- Step 3: Initialize TWRP source tree ---
echo ""
echo "[3/7] Initializing TWRP minimal manifest..."
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

if [ ! -d ".repo" ]; then
    repo init --depth=1 -u https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp.git -b twrp-12.1
fi

# --- Step 4: Sync sources ---
echo ""
echo "[4/7] Syncing TWRP source (this will take a while)..."
repo sync -c --no-clone-bundle --no-tags -j"$JOBS" 2>&1 | tail -5

# --- Step 5: Copy device tree ---
echo ""
echo "[5/7] Installing device tree..."
mkdir -p "$BUILD_DIR/device/samsung/gta9wifi"

if [ -d "$SCRIPT_DIR/device_tree" ]; then
    cp -rv "$SCRIPT_DIR/device_tree/"* "$BUILD_DIR/device/samsung/gta9wifi/"
    echo "    Device tree copied from $SCRIPT_DIR/device_tree/"
else
    echo "    ERROR: No device_tree/ folder found at $SCRIPT_DIR/device_tree/"
    echo "    Place the device tree files there and rerun."
    exit 1
fi

# --- Step 6: Build recovery image ---
echo ""
echo "[6/7] Building TWRP recovery image..."
cd "$BUILD_DIR"
source build/envsetup.sh
lunch twrp_gta9wifi-eng
mka recoveryimage -j"$JOBS" 2>&1 | tee build.log

# --- Step 7: Post-build ---
echo ""
echo "[7/7] Build complete!"
OUTPUT="$BUILD_DIR/out/target/product/gta9wifi/recovery.img"
if [ -f "$OUTPUT" ]; then
    FILESIZE=$(stat -c%s "$OUTPUT")
    echo ""
    echo "=========================================="
    echo " SUCCESS! TWRP built successfully."
    echo " Output: $OUTPUT"
    echo " Size: $((FILESIZE / 1024 / 1024)) MB"
    echo ""
    echo " To flash with Odin:"
    echo "   1. Copy recovery.img to your PC"
    echo "   2. Open Odin, click AP, select recovery.img"
    echo "   3. Disable 'Auto Reboot' in Options"
    echo "   4. Flash, then manually boot to recovery:"
    echo "      Volume Up + Power (with USB disconnected)"
    echo ""
    echo " To flash with fastboot:"
    echo "   fastboot flash recovery recovery.img"
    echo "   fastboot reboot"
    echo ""
    echo " To patch for fastbootd:"
    echo "   Run: ./patch-recovery.sh $OUTPUT SM-X110"
    echo "   (from patch-recovery-revived directory)"
    echo "=========================================="
else
    echo ""
    echo " BUILD FAILED. Check build.log in $BUILD_DIR"
    exit 1
fi
