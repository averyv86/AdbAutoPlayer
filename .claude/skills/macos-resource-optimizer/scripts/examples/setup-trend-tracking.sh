#!/bin/bash
# Example: Set up hourly trend tracking via cron

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Setting Up Hourly Trend Tracking"
echo "=========================================="
echo ""

# 1. Test trend analyzer
echo "1. Testing trend analyzer..."
echo "----------------------------------------"
uv run python3 trend-analyzer.py --log
echo ""

# 2. Check history file
echo "2. Checking history file..."
echo "----------------------------------------"
if [ -f ~/.process_history.json ]; then
    echo "✓ History file exists: ~/.process_history.json"
    ls -lh ~/.process_history.json
else
    echo "✗ History file not created"
    exit 1
fi
echo ""

# 3. Generate cron entry
echo "3. Generating cron entry..."
echo "----------------------------------------"

CRON_COMMAND="0 * * * * cd $SCRIPT_DIR && uv run python3 trend-analyzer.py --log >> /tmp/trend-analyzer.log 2>&1"

echo "Add this line to your crontab:"
echo ""
echo "  $CRON_COMMAND"
echo ""

read -p "Open crontab editor now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if crontab exists
    if ! crontab -l > /dev/null 2>&1; then
        # Create new crontab
        echo "$CRON_COMMAND" | crontab -
        echo "✓ Crontab created with trend tracking"
    else
        # Add to existing crontab
        (crontab -l; echo "$CRON_COMMAND") | crontab -
        echo "✓ Trend tracking added to existing crontab"
    fi
fi

echo ""

# 4. Verify cron entry
echo "4. Verifying cron installation..."
echo "----------------------------------------"
if crontab -l | grep -q "trend-analyzer.py"; then
    echo "✓ Cron entry found:"
    crontab -l | grep "trend-analyzer.py"
else
    echo "✗ Cron entry not found"
    echo "You can add it manually:"
    echo "  crontab -e"
    echo "  Then add: $CRON_COMMAND"
fi

echo ""

# 5. Test manual run
echo "5. Testing manual run..."
echo "----------------------------------------"
echo "Running 3 snapshots (60 second intervals)..."
for i in {1..3}; do
    echo "  Snapshot $i/3..."
    uv run python3 trend-analyzer.py --log
    if [ $i -lt 3 ]; then
        sleep 60
    fi
done

echo ""
uv run python3 trend-analyzer.py --analyze --days 1
echo ""

echo "=========================================="
echo "Trend tracking setup complete!"
echo "=========================================="
echo ""
echo "The system will now log process snapshots hourly."
echo "After 30 days, you'll have meaningful trend data."
echo ""
echo "To check trends:"
echo "  uv run python3 trend-analyzer.py --analyze --days 30"
echo ""
echo "To find idle processes:"
echo "  uv run python3 trend-analyzer.py --idle --days 90"
