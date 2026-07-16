# Deployment Guide

Complete step-by-step guide for installing, configuring, validating, and deploying macOS Resource Optimizer in production environments.

## Implementation Status

⚠️ **IMPORTANT**: This document describes **conceptual deployment architecture**. The actual deployment uses **UV scripts** with no complex setup required.

**Current Implementation** (as of 2025-11-30):
- ✅ 12 UV scripts (standalone executables)
- ✅ Zero configuration deployment (UV handles dependencies)
- ✅ Execution: `uv run [script].py`
- ✅ No virtualenv or pip install needed
- 🔄 Production hardening in progress
- 🔄 Monitoring integration pending

**This Document Describes**:
- Conceptual installation procedures
- Wrapper class configuration (not needed for UV scripts)
- Production deployment strategies
- Validation and troubleshooting steps

**For Actual Deployment**:
```bash
# No installation needed - UV handles everything
uv run .claude/skills/macos-resource-optimizer/.data/scripts/status.py
uv run .claude/skills/macos-resource-optimizer/.data/scripts/analyze_all.py --json
```

---

## Prerequisites and System Requirements

### Hardware Requirements

**Minimum**:
- macOS 10.15 (Catalina) or later
- 2GB RAM available
- 100MB disk space for Python engine and scripts

**Recommended**:
- macOS 12.0 (Monterey) or later
- 4GB RAM available
- SSD for faster analysis
- M1/M2/M3 Mac for optimal performance

### Software Requirements

| Component | Minimum | Recommended | Status |
|-----------|---------|-------------|--------|
| macOS | 10.15 | 13.0+ | Required |
| Python | 3.9 | 3.11+ | Required |
| pip/uv | Any | uv latest | Required |
| psutil | 5.7 | 5.9+ | Required |
| numpy | 1.19 | 1.24+ | Recommended |
| Claude Code | Latest | - | Required |

### Permission Requirements

The optimizer requires elevated privileges for certain operations:

```
✓ Read-only metrics: Standard user
✓ Process termination: Admin (sudo)
✓ Memory compression: Admin (sudo)
✓ Disk optimization: Admin (sudo)
✓ Thermal management: Admin (sudo)
✓ Network stats: Standard user
✓ Battery info: Standard user
```

**macOS Security Note**: First run will prompt for password via `sudo`.

## Installation Steps

### Step 1: Install Python Engine

The Python engine provides the core resource analysis functionality.

#### 1.1 Clone or Create Python Engine

```bash
# If cloning from repository:
git clone https://github.com/your-org/macos-optimizer.git .claude/skills/macos-resource-optimizer/.data

# Or create directory structure manually:
mkdir -p .claude/skills/macos-resource-optimizer/.data/scripts/{analyzers,optimizers}
mkdir -p .claude/skills/macos-resource-optimizer/.data/config
mkdir -p .claude/skills/macos-resource-optimizer/.data/logs
```

#### 1.2 Create Virtual Environment

```bash
# Navigate to optimizer directory
cd .claude/skills/macos-resource-optimizer/.data

# Create virtual environment with uv (recommended)
uv venv

# Or with standard Python:
python3 -m venv .venv

# Activate environment
source .venv/bin/activate
```

#### 1.3 Install Python Dependencies

```bash
# If using uv (faster):
uv pip install -r requirements.txt

# Or standard pip:
pip install -r requirements.txt

# Core dependencies:
pip install psutil>=5.9.0
pip install numpy>=1.24.0  # Optional, for advanced analysis
pip install click>=8.0.0   # For CLI
```

#### 1.4 Verify Python Engine

```bash
# Test coordinator.py
uv run scripts/coordinator.py --status

# Expected output:
# { "status": "ready", "categories": 6, "agents": 50 }
```

**Troubleshooting**:

| Error | Cause | Solution |
|-------|-------|----------|
| "Python 3.9+ not found" | Outdated Python | `brew install python@3.11` |
| "psutil not installed" | Missing dependency | `pip install psutil` |
| "Permission denied" | File permissions | `chmod +x scripts/coordinator.py` |

### Step 2: Install MoAI Wrapper

The MoAI wrapper provides orchestration and integration with MoAI-ADK.

#### 2.1 Verify MoAI-ADK Installation

```bash
# Check MoAI version
moai --version
# Expected: MoAI-ADK 0.30.2+

# Check Claude Code
claude-code --version
# Expected: Claude Code latest
```

#### 2.2 Install Skill

The moai-system-macos-resource-optimizer skill is auto-included in MoAI-ADK:

```bash
# Verify skill exists
ls -la .claude/skills/moai-system-macos-resource-optimizer/

# Should show:
# - SKILL.md
# - modules/
# - schemas/
```

#### 2.3 Install Wrapper Agents

The 8 wrapper agents should be installed:

```bash
# Verify agent directory
ls -la .claude/agents/macos-resource/

# Should contain:
# - manager-resource-coordinator.md
# - manager-resource-strategy.md
# - expert-cpu-optimizer.md
# - expert-memory-optimizer.md
# - expert-disk-optimizer.md
# - expert-network-optimizer.md
# - expert-battery-optimizer.md
# - expert-thermal-optimizer.md
```

If agents don't exist, create them from templates:

```bash
# Create agents directory
mkdir -p .claude/agents/macos-resource/

# Copy or generate agent files (see templates in skill)
cp .claude/skills/moai-system-macos-resource-optimizer/templates/* \
   .claude/agents/macos-resource/
```

### Step 3: Configuration

#### 3.1 Python Engine Configuration

Edit `.claude/skills/macos-resource-optimizer/.data/config/config.json`:

```json
{
  "engine": {
    "path": ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
    "timeout_seconds": 10,
    "retry_attempts": 3,
    "retry_backoff": 1.0
  },
  "cache": {
    "enabled": true,
    "ttl_seconds": 30,
    "max_size": 50,
    "stale_threshold_seconds": 300
  },
  "performance": {
    "target_seconds": 1.8,
    "parallel_limit": 6,
    "warn_threshold_seconds": 2.5
  },
  "categories": {
    "cpu": {
      "enabled": true,
      "priority": "high",
      "timeout_seconds": 5,
      "critical_threshold": 95.0,
      "warning_threshold": 80.0
    },
    "memory": {
      "enabled": true,
      "priority": "high",
      "timeout_seconds": 5,
      "critical_threshold": 90.0,
      "warning_threshold": 80.0
    },
    "disk": {
      "enabled": true,
      "priority": "medium",
      "timeout_seconds": 10,
      "critical_threshold": 95.0,
      "warning_threshold": 80.0
    },
    "network": {
      "enabled": true,
      "priority": "medium",
      "timeout_seconds": 10
    },
    "battery": {
      "enabled": true,
      "priority": "low",
      "timeout_seconds": 15
    },
    "thermal": {
      "enabled": true,
      "priority": "low",
      "timeout_seconds": 15,
      "critical_threshold": 95.0,
      "warning_threshold": 80.0
    }
  },
  "logging": {
    "enabled": true,
    "level": "INFO",
    "file": ".claude/skills/macos-resource-optimizer/.data/logs/optimizer.log",
    "max_size_mb": 50,
    "retention_days": 30
  },
  "security": {
    "require_approval_for_optimizations": true,
    "sudo_required_operations": ["process_kill", "memory_compress", "disk_cleanup"],
    "enable_rollback": true,
    "rollback_window_hours": 24
  }
}
```

#### 3.2 MoAI Wrapper Configuration

Edit `.moai/config/config.json` (add macOS optimizer section):

```json
{
  "macos_optimizer": {
    "enabled": true,
    "engine_path": ".claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py",
    "cache_ttl_seconds": 30,
    "parallel_execution": true,
    "language": "korean"
  }
}
```

#### 3.3 Threshold Customization

Customize performance thresholds in `.claude/skills/macos-resource-optimizer/.data/config/thresholds.json`:

```json
{
  "cpu": {
    "healthy_max": 60.0,
    "warning": 80.0,
    "critical": 95.0,
    "temp_healthy_max": 70.0,
    "temp_warning": 85.0,
    "temp_critical": 100.0
  },
  "memory": {
    "healthy_max": 75.0,
    "warning": 80.0,
    "critical": 90.0
  },
  "disk": {
    "healthy_max": 75.0,
    "warning": 80.0,
    "critical": 95.0,
    "free_gb_warning": 10.0,
    "free_gb_critical": 1.0
  },
  "battery": {
    "warning_threshold": 20.0,
    "critical_threshold": 10.0,
    "health_warning": 80.0
  }
}
```

### Step 4: Validation

#### 4.1 Run Initialization Command

```bash
# Initialize and validate setup
/macos-resource-optimizer:0-init

# Expected output:
# ✅ Python engine: Ready
# ✅ Dependencies: Installed
# ✅ Categories available: 6/6
# ✅ MoAI wrapper: Active
# ✅ Cache: Initialized
```

#### 4.2 Run Test Analysis

```bash
# Execute test analysis
/macos-resource-optimizer:1-analyze

# Should complete in < 3 seconds
# Should return metrics for all 6 categories
```

#### 4.3 Verify Caching

```bash
# Run analysis twice, measure time difference
time /macos-resource-optimizer:1-analyze
# First run: ~2.5s
time /macos-resource-optimizer:1-analyze
# Second run: ~0.5s (cached)
```

#### 4.4 Permission Verification

```bash
# Test sudo requirement
/macos-resource-optimizer:2-optimize --dry-run

# Should prompt for password if applying real optimizations
# Dry-run should complete without password
```

### Step 5: Post-Installation Configuration

#### 5.1 Set Up Logging

```bash
# Create log directory
mkdir -p .claude/skills/macos-resource-optimizer/.data/logs

# Set up log rotation
touch .claude/skills/macos-resource-optimizer/.data/logs/optimizer.log
chmod 644 .claude/skills/macos-resource-optimizer/.data/logs/optimizer.log
```

#### 5.2 Enable Auto-Optimization (Optional)

```bash
# Create launchd plist for periodic optimization
# (requires macOS 10.4+)

cat > ~/Library/LaunchAgents/com.moai.optimizer.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.moai.optimizer</string>
    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>-c</string>
      <string>/macos-resource-optimizer:1-analyze</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>  <!-- Every 5 minutes -->
    <key>StandardOutPath</key>
    <string>.claude/skills/macos-resource-optimizer/.data/logs/scheduled.log</string>
    <key>StandardErrorPath</key>
    <string>.claude/skills/macos-resource-optimizer/.data/logs/scheduled-error.log</string>
  </dict>
</plist>
EOF

# Load the launch agent
launchctl load ~/Library/LaunchAgents/com.moai.optimizer.plist
```

#### 5.3 Configure Notifications (Optional)

```bash
# Enable desktop notifications for alerts
# (Edit .claude/skills/macos-resource-optimizer/.data/config/notifications.json)

cat > .claude/skills/macos-resource-optimizer/.data/config/notifications.json << 'EOF'
{
  "enabled": true,
  "critical_alerts": true,
  "warning_alerts": false,
  "info_alerts": false,
  "sound": true
}
EOF
```

## Production Deployment

### Deployment Checklist

- [ ] Python 3.9+ installed and verified
- [ ] All dependencies installed (psutil, numpy)
- [ ] Python engine tested and functional
- [ ] MoAI-ADK 0.30.2+ installed
- [ ] Wrapper agents installed in `.claude/agents/`
- [ ] Configuration files created and customized
- [ ] Initialization command successful
- [ ] Test analysis command successful
- [ ] Caching performance verified (2x+ speedup)
- [ ] Permissions configured (sudo access for optimizations)
- [ ] Logging directory created
- [ ] Backup strategy defined

### Performance Validation

```bash
# Run performance benchmark
echo "Testing performance..."

# Cold start (no cache)
time /macos-resource-optimizer:1-analyze --no-cache
# Expected: 2-3 seconds

# Warm start (with cache)
time /macos-resource-optimizer:1-analyze
# Expected: 0.5-1.5 seconds

# Parallel execution test
time /macos-resource-optimizer:1-analyze --categories=cpu,memory,disk
# Expected: 2-3 seconds (not 7.5s sequential)

echo "Performance validation complete!"
```

### Security Hardening

```bash
# Set proper file permissions
chmod 700 .claude/skills/macos-resource-optimizer/.data/scripts/
chmod 700 .claude/skills/macos-resource-optimizer/.data/config/
chmod 600 .claude/skills/macos-resource-optimizer/.data/config/*.json

# Restrict log access
chmod 600 .claude/skills/macos-resource-optimizer/.data/logs/*

# Enable file integrity monitoring
sudo fsactl monitor .claude/skills/macos-resource-optimizer/.data/scripts/
```

### Monitoring Setup

```bash
# Start continuous monitoring
/macos-resource-optimizer:3-monitor \
  --interval=300 \
  --duration=86400 \
  --alert-threshold=warning \
  --log-file=.claude/skills/macos-resource-optimizer/.data/logs/monitor.log

# Monitor process
tail -f .claude/skills/macos-resource-optimizer/.data/logs/monitor.log
```

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Async Tests Failing

**Error**: `RuntimeError: no running event loop`

**Solution**:
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Configure pytest.ini
cat > pytest.ini << 'EOF'
[pytest]
asyncio_mode = auto
EOF
```

#### Issue 2: Subprocess Timeout

**Error**: `AnalysisTimeoutError: CPU analysis exceeded 10s timeout`

**Solution**:
```bash
# Increase timeout in config.json
"timeout_seconds": 15,  # Increase from 10

# Or rebuild coordinator.py for efficiency
# Check .claude/skills/macos-resource-optimizer/.data/scripts/cpu_analyzer.py for bottlenecks
```

#### Issue 3: Cache Not Working

**Error**: `Cache hit rate: 0.0%`

**Solution**:
```bash
# Check cache settings in config.json
"cache": {
  "enabled": true,
  "ttl_seconds": 30,  # Ensure TTL is reasonable
  "max_size": 50
}

# Verify cache is being used
/macos-resource-optimizer:1-analyze --verbose
# Should show "cached: true" for subsequent runs
```

#### Issue 4: Permission Denied on Optimizations

**Error**: `PermissionError: Operation requires elevated privileges`

**Solution**:
```bash
# Grant sudo access for optimization commands
# Add to sudoers (use visudo, not direct edit)
sudo visudo

# Add this line:
# %admin ALL=(ALL) NOPASSWD: /path/to/.claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py
```

#### Issue 5: Python Engine Not Found

**Error**: `FileNotFoundError: Engine not found at .claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py`

**Solution**:
```bash
# Verify engine path
ls -la .claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py

# If missing, clone or create:
git clone https://github.com/your-org/macos-optimizer.git .claude/skills/macos-resource-optimizer/.data

# Or create stub coordinator.py
touch .claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py
chmod +x .claude/skills/macos-resource-optimizer/.data/scripts/coordinator.py
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Set debug level in config.json
"logging": {
  "level": "DEBUG"
}

# Run command with verbose flag
/macos-resource-optimizer:1-analyze --verbose

# Check detailed logs
tail -f .claude/skills/macos-resource-optimizer/.data/logs/optimizer.log
```

## Upgrade Procedure

### Upgrading Python Engine

```bash
# Backup current configuration
cp -r .claude/skills/macos-resource-optimizer/.data/ .claude/skills/macos-resource-optimizer/.data.backup

# Pull latest changes
cd .claude/skills/macos-resource-optimizer/.data
git pull origin main

# Install new dependencies (if any)
uv pip install -r requirements.txt

# Validate upgrade
/macos-resource-optimizer:0-init

# If successful, remove backup
rm -rf .claude/skills/macos-resource-optimizer/.data.backup
```

### Upgrading MoAI Wrapper

```bash
# Update MoAI-ADK
moai-adk update

# Update skill
moai-adk skills install moai-system-macos-resource-optimizer

# Verify upgrade
/macos-resource-optimizer:0-init
```

## Uninstallation

To completely remove macOS Resource Optimizer:

```bash
# Stop any running monitors
pkill -f "macos-resource-optimizer"

# Remove Python engine
rm -rf .claude/skills/macos-resource-optimizer/.data/

# Remove wrapper agents
rm -rf .claude/agents/macos-resource/

# Remove skill
rm -rf .claude/skills/moai-system-macos-resource-optimizer/

# Clean up launchd agents (if installed)
launchctl unload ~/Library/LaunchAgents/com.moai.optimizer.plist
rm ~/Library/LaunchAgents/com.moai.optimizer.plist

# Verify removal
/macos-resource-optimizer:0-init
# Should error: "Skill not found"
```

## Performance Tuning

### Optimize Cache TTL

```json
{
  "cache": {
    "ttl_seconds": 60,  // Increase for longer cache validity
    "max_size": 100,    // Increase for more entries
    "stale_threshold_seconds": 600  // Allow older cache as fallback
  }
}
```

### Optimize Timeouts Per Category

```json
{
  "categories": {
    "cpu": { "timeout_seconds": 3 },      // Fast analysis
    "memory": { "timeout_seconds": 3 },   // Fast analysis
    "disk": { "timeout_seconds": 10 },    // Slower analysis
    "network": { "timeout_seconds": 10 }, // Can be slow
    "battery": { "timeout_seconds": 5 },  // Usually fast
    "thermal": { "timeout_seconds": 5 }   // Usually fast
  }
}
```

### Connection Pooling (Advanced)

```python
# In coordinator.py, add subprocess pooling:
class SubprocessPool:
    def __init__(self, size=3):
        self.pool = [spawn_process() for _ in range(size)]

    async def execute(self, cmd):
        proc = self.pool.pop()
        try:
            result = await run_command(proc, cmd)
        finally:
            self.pool.append(proc)
```

## Backup and Recovery

### Backup Procedure

```bash
# Back up configuration and results
backup_dir="backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup_dir"

# Backup config
cp -r .claude/skills/macos-resource-optimizer/.data/config/ "$backup_dir/config/"

# Backup logs
cp -r .claude/skills/macos-resource-optimizer/.data/logs/ "$backup_dir/logs/"

# Backup reports
cp -r .claude/skills/macos-resource-optimizer/.data/reports/ "$backup_dir/reports/"

echo "Backup complete: $backup_dir"
```

### Recovery Procedure

```bash
# Restore from backup
backup_dir="backups/2024-01-01-100000"

# Stop running processes
/macos-resource-optimizer:3-monitor --stop

# Restore config
cp -r "$backup_dir/config/"/* .claude/skills/macos-resource-optimizer/.data/config/

# Verify restoration
/macos-resource-optimizer:0-init
```

## Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| Status check | Daily | `/macos-resource-optimizer:0-init` |
| Performance analysis | Weekly | `/macos-resource-optimizer:1-analyze` |
| Optimization review | Monthly | `/macos-resource-optimizer:4-report --days=30` |
| Log rotation | Monthly | `logrotate .claude/skills/macos-resource-optimizer/.data/logs/` |
| Dependency update | Quarterly | `pip install --upgrade -r requirements.txt` |
| Backup verification | Monthly | Test recovery procedure |

## Support and Contact

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `.claude/skills/macos-resource-optimizer/.data/logs/optimizer.log`
3. Run debug mode: `/macos-resource-optimizer:0-init --verbose`
4. Submit feedback: `/macos-resource-optimizer:9-feedback`

---

**Deployment Version**: 1.0.0
**Last Updated**: 2025-11-29
**Tested On**: macOS 12.0+, Python 3.9+, MoAI-ADK 0.30.2+
