#!/bin/bash
# Example: Install automated cleanup scheduler

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Installing Automated Cleanup Scheduler"
echo "=========================================="
echo ""

# 1. Check current status
echo "1. Checking current scheduler status..."
echo "----------------------------------------"
uv run python3 scheduler.py --status
echo ""

# 2. Generate cleanup scripts
echo "2. Generating cleanup scripts..."
echo "----------------------------------------"

# Daily cleanup script
cat > /tmp/cleanup-daily.sh << 'EOF'
#!/bin/bash
# Daily cleanup script (3 AM)
echo "[$(date)] Starting daily cleanup"

# Clear system caches
rm -rf ~/Library/Caches/* 2>/dev/null
rm -rf /tmp/* 2>/dev/null

# Clear Python caches
find ~ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Clear npm cache
npm cache clean --force 2>/dev/null

echo "[$(date)] Daily cleanup complete"
EOF

# Weekly cleanup script
cat > /tmp/cleanup-weekly.sh << 'EOF'
#!/bin/bash
# Weekly cleanup script (Sunday 3 AM)
echo "[$(date)] Starting weekly cleanup"

# Run daily cleanup
bash /tmp/cleanup-daily.sh

# Docker cleanup
docker system prune -f 2>/dev/null

# Clear old build artifacts
find ~ -type d -name "node_modules" -mtime +30 -exec rm -rf {} + 2>/dev/null
find ~ -type d -name "dist" -mtime +30 -exec rm -rf {} + 2>/dev/null

# Clear old logs
find ~/Library/Logs -type f -mtime +30 -delete 2>/dev/null

echo "[$(date)] Weekly cleanup complete"
EOF

# Monthly cleanup script
cat > /tmp/cleanup-monthly.sh << 'EOF'
#!/bin/bash
# Monthly cleanup script (1st Sunday 3 AM)
echo "[$(date)] Starting monthly cleanup"

# Run weekly cleanup
bash /tmp/cleanup-weekly.sh

# Full Docker cleanup
docker system prune -a -f --volumes 2>/dev/null

# Generate reports
cd ~/.claude/skills/macos-resource-optimizer/scripts
uv run python3 trend-analyzer.py --analyze --days 90
uv run python3 duplicate-finder.py --report

# Archive logs
tar -czf ~/cleanup-logs-$(date +%Y%m).tar.gz ~/Library/Logs/*.log 2>/dev/null

echo "[$(date)] Monthly cleanup complete"
EOF

chmod +x /tmp/cleanup-*.sh
echo "✓ Cleanup scripts generated in /tmp/"
echo ""

# 3. Install schedules
echo "3. Installing launchd schedules..."
echo "----------------------------------------"
read -p "Install daily cleanup? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    uv run python3 scheduler.py --install daily
fi

read -p "Install weekly cleanup? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    uv run python3 scheduler.py --install weekly
fi

read -p "Install monthly cleanup? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    uv run python3 scheduler.py --install monthly
fi

echo ""

# 4. Verify installation
echo "4. Verifying installation..."
echo "----------------------------------------"
uv run python3 scheduler.py --list
echo ""

# 5. Check launchctl
echo "5. Checking launchctl status..."
echo "----------------------------------------"
launchctl list | grep macos-optimizer
echo ""

echo "=========================================="
echo "Scheduler installation complete!"
echo "=========================================="
echo ""
echo "Logs will be written to:"
echo "  - /tmp/macos-optimizer-daily.log"
echo "  - /tmp/macos-optimizer-weekly.log"
echo "  - /tmp/macos-optimizer-monthly.log"
echo ""
echo "To uninstall:"
echo "  uv run python3 scheduler.py --uninstall all"
