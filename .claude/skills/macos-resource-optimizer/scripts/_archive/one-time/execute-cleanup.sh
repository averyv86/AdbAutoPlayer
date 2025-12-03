#!/bin/bash

################################################################################
# macOS Resource Optimizer - Cleanup Execution Script
# Generated: 2025-11-24
# Estimated Recovery: 30-75 GB
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Disk usage before cleanup
get_disk_usage() {
    df -h / | tail -1 | awk '{print $3}'
}

BEFORE_USAGE=$(get_disk_usage)

echo "================================================================================"
echo "🎯 macOS Resource Optimizer - Cleanup Execution"
echo "================================================================================"
echo "Start Time: $(date)"
echo "Disk Usage Before: $BEFORE_USAGE"
echo ""

################################################################################
# PHASE 1: IMMEDIATE & SAFE CLEANUP (10-25 GB)
################################################################################

echo "================================================================================"
echo "⚡ PHASE 1: IMMEDIATE & SAFE CLEANUP"
echo "================================================================================"
echo ""

# Check if running in dry-run mode
DRY_RUN=${DRY_RUN:-false}
if [ "$DRY_RUN" = true ]; then
    warning "Running in DRY-RUN mode - no changes will be made"
    echo ""
fi

################################################################################
# 1. Docker Cleanup
################################################################################

log "Step 1/3: Docker Cleanup"
if command -v docker &> /dev/null; then
    if [ "$DRY_RUN" = false ]; then
        echo "  Stopping unused containers..."
        docker container prune -f || warning "Failed to prune containers"

        echo "  Removing unused images..."
        docker image prune -af || warning "Failed to prune images"

        echo "  Removing unused volumes..."
        docker volume prune -f || warning "Failed to prune volumes"

        echo "  Removing unused networks..."
        docker network prune -f || warning "Failed to prune networks"

        echo "  Running system-wide prune..."
        docker system prune -af --volumes || warning "Failed to run system prune"

        success "Docker cleanup complete"
    else
        echo "  [DRY-RUN] Would run: docker system prune -af --volumes"
    fi
else
    warning "Docker not installed - skipping"
fi
echo ""

################################################################################
# 2. Cache Cleanup
################################################################################

log "Step 2/3: Cache Cleanup"

# Yarn cache
if [ -d ~/Library/Caches/Yarn ]; then
    YARN_SIZE=$(du -sh ~/Library/Caches/Yarn 2>/dev/null | cut -f1)
    echo "  Yarn cache size: $YARN_SIZE"
    if [ "$DRY_RUN" = false ]; then
        rm -rf ~/Library/Caches/Yarn/*
        success "Cleared Yarn cache"
    else
        echo "  [DRY-RUN] Would clear ~/Library/Caches/Yarn"
    fi
fi

# Claude CLI cache
if [ -d ~/Library/Caches/claude-cli-nodejs ]; then
    CLAUDE_SIZE=$(du -sh ~/Library/Caches/claude-cli-nodejs 2>/dev/null | cut -f1)
    echo "  Claude CLI cache size: $CLAUDE_SIZE"
    if [ "$DRY_RUN" = false ]; then
        rm -rf ~/Library/Caches/claude-cli-nodejs/*
        success "Cleared Claude CLI cache"
    else
        echo "  [DRY-RUN] Would clear ~/Library/Caches/claude-cli-nodejs"
    fi
fi

# Homebrew cleanup
if command -v brew &> /dev/null; then
    echo "  Running Homebrew cleanup..."
    if [ "$DRY_RUN" = false ]; then
        brew cleanup --prune=all -s || warning "Homebrew cleanup had warnings"
        success "Homebrew cleanup complete"
    else
        echo "  [DRY-RUN] Would run: brew cleanup --prune=all -s"
    fi
fi

# npm cache
if command -v npm &> /dev/null; then
    echo "  Cleaning npm cache..."
    if [ "$DRY_RUN" = false ]; then
        npm cache clean --force || warning "npm cache clean had warnings"
        success "npm cache cleaned"
    else
        echo "  [DRY-RUN] Would run: npm cache clean --force"
    fi
fi

# pnpm cache (if installed)
if command -v pnpm &> /dev/null; then
    echo "  Cleaning pnpm cache..."
    if [ "$DRY_RUN" = false ]; then
        pnpm store prune || warning "pnpm store prune had warnings"
        success "pnpm cache cleaned"
    else
        echo "  [DRY-RUN] Would run: pnpm store prune"
    fi
fi

echo ""

################################################################################
# 3. System Cache Cleanup
################################################################################

log "Step 3/3: System Cache Cleanup"

# Python cache
if [ -d ~/Library/Caches/com.apple.python ]; then
    PYTHON_SIZE=$(du -sh ~/Library/Caches/com.apple.python 2>/dev/null | cut -f1)
    echo "  Python cache size: $PYTHON_SIZE"
    if [ "$DRY_RUN" = false ]; then
        rm -rf ~/Library/Caches/com.apple.python/*
        success "Cleared Python cache"
    else
        echo "  [DRY-RUN] Would clear ~/Library/Caches/com.apple.python"
    fi
fi

# Electron cache
if [ -d ~/Library/Caches/electron ]; then
    ELECTRON_SIZE=$(du -sh ~/Library/Caches/electron 2>/dev/null | cut -f1)
    echo "  Electron cache size: $ELECTRON_SIZE"
    if [ "$DRY_RUN" = false ]; then
        rm -rf ~/Library/Caches/electron/*
        success "Cleared Electron cache"
    else
        echo "  [DRY-RUN] Would clear ~/Library/Caches/electron"
    fi
fi

echo ""
success "Phase 1 cleanup complete!"
echo ""

################################################################################
# FINAL REPORT
################################################################################

AFTER_USAGE=$(get_disk_usage)

echo "================================================================================"
echo "📊 CLEANUP SUMMARY"
echo "================================================================================"
echo "End Time: $(date)"
echo "Disk Usage Before: $BEFORE_USAGE"
echo "Disk Usage After:  $AFTER_USAGE"
echo ""

if [ "$DRY_RUN" = false ]; then
    success "Cleanup completed successfully!"
    echo ""
    echo "🎯 Recommended Next Steps:"
    echo "  1. Review node_modules directories (139 found, 10-30 GB potential)"
    echo "  2. Archive old projects (no commits in 6+ months)"
    echo "  3. Set up automated weekly cleanup"
    echo "  4. Configure Time Machine exclusions"
    echo ""
    echo "📋 Full Report: ./reports/CLEANUP_SUMMARY.md"
else
    warning "Dry-run complete - no changes were made"
    echo ""
    echo "To execute cleanup, run:"
    echo "  bash execute-cleanup.sh"
fi

echo "================================================================================"
