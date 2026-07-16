# Usage Examples

Real-world examples for macOS Resource Optimizer using actual UV scripts, covering basic usage, advanced patterns, error handling, and performance optimization.

## Implementation Status

⚠️ **UPDATED**: All examples use **actual UV scripts** (as of 2025-11-30).

**Current Implementation**:
- ✅ All examples use `uv run` commands
- ✅ Real script paths from `.data/scripts/`
- ✅ JSON output patterns from actual scripts
- ✅ Working CLI examples tested

---

## Quick Start Examples

### Example 1: Check System Status

```bash
# Basic system health check
uv run .claude/skills/macos-resource-optimizer/.data/scripts/status.py

# Expected output:
# System Health Status
# ==================
# CPU: OK (45.2%)
# Memory: OK (12.3 GB free)
# Disk: OK (256 GB free)
# Network: OK (Connected)
# Battery: OK (85% charged)
# Thermal: OK (45°C)
```

### Example 2: Analyze Single Category

```bash
# Analyze CPU with JSON output
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --json

# Expected JSON output:
{
  "status": "success",
  "category": "cpu",
  "metrics": {
    "usage_percent": 45.2,
    "user_percent": 30.1,
    "system_percent": 15.1,
    "idle_percent": 54.8,
    "core_count": 8
  },
  "risk_level": "low",
  "recommendations": [
    {
      "description": "CPU usage is within normal range",
      "priority": "low",
      "category": "cpu"
    }
  ]
}
```

### Example 3: Full Parallel Analysis

```bash
# Analyze all 6 categories in parallel (~2.0s)
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_all.py --json

# Expected output structure:
{
  "status": "success",
  "categories": {
    "cpu": { ... },
    "memory": { ... },
    "disk": { ... },
    "network": { ... },
    "battery": { ... },
    "thermal": { ... }
  },
  "execution_time_seconds": 1.98,
  "timestamp": "2025-11-30T10:15:30"
}
```

---

## Category-Specific Analysis

### CPU Analysis

```bash
# Human-readable output
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py

# JSON for automation
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --json

# Custom threshold (exit code 2 if exceeded)
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --threshold 80
```

### Memory Analysis

```bash
# Check memory usage
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_memory.py --json

# Sample output:
{
  "status": "success",
  "category": "memory",
  "metrics": {
    "total_gb": 16.0,
    "used_gb": 12.3,
    "free_gb": 3.7,
    "cached_gb": 2.1,
    "usage_percent": 76.9
  },
  "risk_level": "medium",
  "recommendations": [
    {
      "description": "Memory usage is elevated, consider closing unused applications",
      "priority": "medium",
      "category": "memory"
    }
  ]
}
```

### Disk Analysis

```bash
# Disk I/O and storage analysis
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_disk.py --json

# Sample output:
{
  "status": "success",
  "category": "disk",
  "metrics": {
    "total_gb": 512,
    "used_gb": 256,
    "free_gb": 256,
    "usage_percent": 50.0,
    "read_mb_per_sec": 125.3,
    "write_mb_per_sec": 78.2
  },
  "risk_level": "low"
}
```

### Network Analysis

```bash
# Network performance and connectivity
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_network.py --json
```

### Battery Analysis

```bash
# Battery status and power metrics
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_battery.py --json
```

### Thermal Analysis

```bash
# CPU temperature and thermal state
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_thermal.py --json
```

---

## Optimization Workflow

### Generate Recommendations

```bash
# Dry-run mode (no changes applied)
uv run .claude/skills/macos-resource-optimizer/.data/scripts/optimize.py --json

# Expected output:
{
  "status": "success",
  "mode": "dry_run",
  "recommendations": [
    {
      "category": "cpu",
      "action": "kill_process",
      "target": "Safari (PID 1234)",
      "priority_score": 85,
      "risk": "low",
      "expected_improvement": "15% CPU reduction"
    },
    {
      "category": "memory",
      "action": "clear_cache",
      "target": "system_cache",
      "priority_score": 72,
      "risk": "low",
      "expected_improvement": "2 GB memory freed"
    }
  ],
  "total_recommendations": 2
}
```

### Apply Optimizations (with User Approval)

```bash
# Apply optimizations (shows Korean UI for approval)
uv run .claude/skills/macos-resource-optimizer/.data/scripts/optimize.py --apply

# Interactive workflow:
# 1. Analyze system (analyze_all.py)
# 2. Generate optimization plan
# 3. Display Korean UI with risk assessment
# 4. Request user approval (AskUserQuestion)
# 5. Apply approved optimizations
# 6. Report results
```

### Rollback if Needed

```bash
# Rollback last optimization
uv run .claude/skills/macos-resource-optimizer/.data/scripts/optimize.py --rollback

# Output:
{
  "status": "success",
  "action": "rollback",
  "restored_state": "2025-11-30T10:00:00",
  "changes_reverted": 2
}
```

---

## Monitoring Examples

### Continuous Monitoring

```bash
# Monitor for 30 seconds
uv run .claude/skills/macos-resource-optimizer/.data/scripts/monitor.py --duration 30

# Real-time output (Rich table):
# Iteration 1/6  [5s interval]
# ┏━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┓
# ┃ Category┃ Status ┃ Value    ┃ Risk  ┃
# ┡━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━┩
# │ CPU     │ OK     │ 45.2%    │ low   │
# │ Memory  │ WARN   │ 12.3 GB  │ medium│
# │ Disk    │ OK     │ 256 GB   │ low   │
# └─────────┴────────┴──────────┴───────┘
```

### Custom Monitoring Interval

```bash
# Monitor with 10-second interval for 60 seconds
uv run .claude/skills/macos-resource-optimizer/.data/scripts/monitor.py --interval 10 --duration 60
```

### JSON Monitoring Output

```bash
# Output JSON samples for automation
uv run .claude/skills/macos-resource-optimizer/.data/scripts/monitor.py --duration 30 --json

# Sample output:
[
  {
    "iteration": 1,
    "timestamp": "2025-11-30T10:15:30",
    "categories": {
      "cpu": {"status": "ok", "value": 45.2, "risk": "low"},
      "memory": {"status": "warning", "value": 76.9, "risk": "medium"}
    },
    "alerts": [
      {"category": "memory", "message": "Memory usage elevated"}
    ]
  }
]
```

### Monitor Indefinitely (Ctrl+C to Stop)

```bash
# Monitor with 5-second interval until stopped
uv run .claude/skills/macos-resource-optimizer/.data/scripts/monitor.py --interval 5

# Press Ctrl+C to gracefully terminate
# Final state saved to: ~/.moai/resource-optimizer/monitor/state.json
```

---

## Report Generation

### Generate Markdown Report

```bash
# Default markdown format
uv run .claude/skills/macos-resource-optimizer/.data/scripts/report.py --format markdown

# Output:
# macOS Resource Optimization Report
# ==================================
#
# ## Executive Summary
# - Overall Health: Good
# - Total Issues: 2 (1 medium, 1 low)
# - Critical Issues: 0
#
# ## Category Analysis
# ...
```

### Generate JSON Report

```bash
# JSON export for automation
uv run .claude/skills/macos-resource-optimizer/.data/scripts/report.py --format json --output /tmp/report.json

# File contents:
{
  "report_type": "system_analysis",
  "timestamp": "2025-11-30T10:15:30",
  "summary": {
    "overall_health": "good",
    "total_issues": 2,
    "critical_issues": 0
  },
  "categories": { ... },
  "recommendations": [ ... ]
}
```

### Generate HTML Report

```bash
# Professional HTML report (browser-ready)
uv run .claude/skills/macos-resource-optimizer/.data/scripts/report.py --format html --output /tmp/system-report.html

# Open in browser:
open /tmp/system-report.html

# Features:
# - Modern Apple-inspired design
# - Color-coded status indicators
# - Responsive layout
# - Interactive tables
# - Gradient accents
```

---

## Cache Operations

### Set Cache Entry

```bash
# Store analysis result with 60-second TTL
uv run .claude/skills/macos-resource-optimizer/.data/scripts/cache.py \
  --operation set \
  --key cpu_analysis \
  --value '{"usage": 45.2, "status": "ok"}' \
  --ttl 60
```

### Get Cache Entry

```bash
# Retrieve cached value
uv run .claude/skills/macos-resource-optimizer/.data/scripts/cache.py \
  --operation get \
  --key cpu_analysis

# Output (if hit):
{
  "data": {"usage": 45.2, "status": "ok"},
  "timestamp": "2025-11-30T10:15:30",
  "age_seconds": 15,
  "ttl_remaining": 45
}

# Exit code 0: Cache hit
# Exit code 1: Cache miss
```

### Cache Statistics

```bash
# Get cache performance metrics
uv run .claude/skills/macos-resource-optimizer/.data/scripts/cache.py --operation stats

# Output:
{
  "size": 6,
  "max_size": 50,
  "hits": 42,
  "misses": 8,
  "hit_rate": 0.84,
  "utilization": 0.12,
  "average_staleness": 0.15
}
```

### Invalidate Cache Entry

```bash
# Remove specific cache entry
uv run .claude/skills/macos-resource-optimizer/.data/scripts/cache.py \
  --operation invalidate \
  --key cpu_analysis
```

### Clear All Cache

```bash
# Remove all cache entries
uv run .claude/skills/macos-resource-optimizer/.data/scripts/cache.py --operation clear
```

### Cleanup Expired Entries

```bash
# Remove expired TTL entries
uv run .claude/skills/macos-resource-optimizer/.data/scripts/cache.py --operation cleanup
```

---

## Integration Patterns

### MoAI Agent Integration

```python
# Manager agent using Bash(uv run) pattern
Bash(
    command='uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --json',
    description='Analyze CPU usage',
    timeout=5000
)

# Parse JSON output
result = json.loads(stdout)
cpu_usage = result['metrics']['usage_percent']
```

### Workflow Example: Analyze → Optimize → Report

```bash
# Step 1: Analyze all categories
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_all.py --json > /tmp/analysis.json

# Step 2: Generate optimization plan
uv run .claude/skills/macos-resource-optimizer/.data/scripts/optimize.py --json > /tmp/plan.json

# Step 3: Generate HTML report
uv run .claude/skills/macos-resource-optimizer/.data/scripts/report.py --format html --output /tmp/report.html

# Step 4: Open report
open /tmp/report.html
```

### Scheduled Monitoring (cron example)

```bash
# Add to crontab: Monitor every 5 minutes
*/5 * * * * uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_all.py --json >> ~/.moai/logs/monitoring.jsonl
```

---

## Error Handling Examples

### Handle Script Failures

```bash
# Check exit codes
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --json
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "Success"
elif [ $EXIT_CODE -eq 1 ]; then
  echo "No issues detected"
elif [ $EXIT_CODE -eq 2 ]; then
  echo "Threshold exceeded (warning)"
elif [ $EXIT_CODE -eq 3 ]; then
  echo "Critical error"
fi
```

### Timeout Protection

```bash
# Use timeout command (macOS)
timeout 10 uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_all.py --json

# Exit code 124 indicates timeout
```

### Fallback to Cache

```bash
# Try analysis, fallback to cache on failure
if ! uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --json > /tmp/result.json 2>/dev/null; then
  echo "Analysis failed, using cache..."
  uv run .claude/skills/macos-resource-optimizer/.data/scripts/cache.py --operation get --key cpu_analysis
fi
```

---

## Performance Optimization Tips

### 1. Use Parallel Analysis

```bash
# Always use analyze_all.py for multiple categories
# ✅ Parallel (1.5-2.0s)
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_all.py --json

# ❌ Serial (6 × 0.5s = 3.0s)
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --json
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_memory.py --json
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_disk.py --json
# ... (3 more)
```

### 2. Cache Frequently Accessed Data

```bash
# Cache analysis results for 30 seconds
RESULT=$(uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --json)
uv run .claude/skills/macos-resource-optimizer/.data/scripts/cache.py \
  --operation set \
  --key cpu_analysis \
  --value "$RESULT" \
  --ttl 30
```

### 3. Use JSON Output for Automation

```bash
# JSON is faster than human-readable output
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --json  # Fast
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py         # Slower (Rich rendering)
```

### 4. Batch Cache Operations

```bash
# Get all cached categories at once
for category in cpu memory disk network battery thermal; do
  uv run .claude/skills/macos-resource-optimizer/.data/scripts/cache.py \
    --operation get \
    --key "${category}_analysis"
done
```

---

## Advanced Patterns

### Custom Monitoring Dashboard

```bash
#!/bin/bash
# monitor-dashboard.sh - Custom monitoring script

while true; do
  clear
  echo "=== System Monitor Dashboard ==="
  echo "Updated: $(date)"
  echo ""

  # Run analysis
  uv run .claude/skills/macos-resource-optimizer/.data/scripts/status.py

  # Wait 5 seconds
  sleep 5
done
```

### Alert on Threshold Breach

```bash
#!/bin/bash
# alert-on-breach.sh - Send alert when threshold exceeded

uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --threshold 80
if [ $? -eq 2 ]; then
  # Send notification (macOS)
  osascript -e 'display notification "CPU usage exceeded 80%" with title "Resource Alert"'
fi
```

### Historical Data Collection

```bash
#!/bin/bash
# collect-historical-data.sh - Log analysis results

TIMESTAMP=$(date +%s)
RESULT=$(uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_all.py --json)

# Append to JSONL file
echo "{\"timestamp\": $TIMESTAMP, \"data\": $RESULT}" >> ~/.moai/logs/historical.jsonl
```

---

## Troubleshooting Examples

### Debug Mode

```bash
# Run with verbose output (not all scripts support --verbose yet)
uv run .claude/skills/macos-resource-optimizer/.data/scripts/status.py --verbose
```

### Check Script Health

```bash
# Verify all scripts are executable
ls -la .claude/skills/macos-resource-optimizer/.data/scripts/*.py

# Test each script
for script in .claude/skills/macos-resource-optimizer/.data/scripts/*.py; do
  echo "Testing $script..."
  uv run "$script" --help
done
```

### Validate JSON Output

```bash
# Verify JSON is valid
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_cpu.py --json | jq .

# Expected: Pretty-printed JSON
# Error: jq parse error if invalid JSON
```

---

**Version**: 2.0.0 (UV Scripts)
**Last Updated**: 2025-11-30
**Status**: ✅ Production Examples with Real Scripts
