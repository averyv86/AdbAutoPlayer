#!/bin/bash
# Example: Weekly cleanup workflow using advanced features

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Weekly macOS Resource Cleanup Workflow"
echo "=========================================="
echo ""

# 1. Check current context
echo "1. Detecting work context..."
echo "----------------------------------------"
uv run python3 context-detector.py --report
echo ""

# 2. Find duplicates
echo "2. Finding duplicate services..."
echo "----------------------------------------"
uv run python3 duplicate-finder.py --report
echo ""

# 3. Check trend data
echo "3. Analyzing usage trends (30 days)..."
echo "----------------------------------------"
uv run python3 trend-analyzer.py --analyze --days 30
echo ""

# 4. Find truly idle processes
echo "4. Finding idle processes (90 days)..."
echo "----------------------------------------"
uv run python3 trend-analyzer.py --idle --days 90
echo ""

# 5. Generate recommendations
echo "5. Generating cleanup recommendations..."
echo "----------------------------------------"

# Save reports to temporary files
CONTEXT_JSON="/tmp/context-report.json"
DUPLICATES_JSON="/tmp/duplicates-report.json"
TRENDS_JSON="/tmp/trends-report.json"

uv run python3 context-detector.py --report --format json > "$CONTEXT_JSON"
uv run python3 duplicate-finder.py --report --format json > "$DUPLICATES_JSON"
uv run python3 trend-analyzer.py --analyze --format json > "$TRENDS_JSON"

echo "Recommendations:"
echo ""

# Parse and display recommendations
echo "SAFE TO KILL (not in active workspace):"
python3 -c "
import json
with open('$CONTEXT_JSON') as f:
    data = json.load(f)
    safe = data.get('classification', {}).get('safe', [])
    for proc in safe[:10]:
        print(f\"  - PID {proc['pid']}: {proc['name']}\")
    if len(safe) > 10:
        print(f\"  ... and {len(safe) - 10} more\")
"

echo ""
echo "DUPLICATE PROCESSES TO CONSOLIDATE:"
python3 -c "
import json
with open('$DUPLICATES_JSON') as f:
    data = json.load(f)
    procs = data.get('processes', [])
    for proc in procs[:5]:
        print(f\"  - {proc['name']}: {proc['count']} instances\")
        print(f\"    → {proc['recommendation']}\")
"

echo ""
echo "TRULY IDLE PROCESSES (consider removing):"
python3 -c "
import json
with open('$TRENDS_JSON') as f:
    data = json.load(f)
    idle = data.get('90_day_trends', {}).get('idle', [])
    for proc in idle[:10]:
        print(f\"  - {proc['name']}: Last seen {proc.get('days_since', 'N/A')} days ago\")
"

echo ""
echo "=========================================="
echo "Cleanup workflow complete!"
echo "=========================================="

# Cleanup temp files
rm -f "$CONTEXT_JSON" "$DUPLICATES_JSON" "$TRENDS_JSON"
