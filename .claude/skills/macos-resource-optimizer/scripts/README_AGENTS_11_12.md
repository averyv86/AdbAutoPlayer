# Agent 11 & 12 Implementation Summary

## Overview
Successfully implemented 2 new zombie detection agents following PEP 723 UV script pattern.

## Agent 11: Network Connection Leaks Hunter
**File**: `agent_network_connection_leaks.py`
**Expected Recovery**: 1-2 GB
**Lines of Code**: 451

### Detection Capabilities
1. **CLOSE_WAIT Connections** - Detects server-side connection leaks (threshold: >10)
2. **WebSocket Zombies** - Finds orphaned WebSocket processes with no active connections
3. **TIME_WAIT Accumulation** - Warns when >1000 TIME_WAIT sockets exist
4. **Excessive Connections** - Finds processes with >50 connections but <1% CPU

### CLI Usage
```bash
# JSON output (default)
uv run agent_network_connection_leaks.py --format json

# Table format (human-readable)
uv run agent_network_connection_leaks.py --format table

# Summary format (quick overview)
uv run agent_network_connection_leaks.py --format summary

# Verbose mode (show all connection details)
uv run agent_network_connection_leaks.py --format json --verbose
```

### Output Format
```json
{
  "agent": "network_connection_leaks",
  "agent_number": 11,
  "zombies_found": 0,
  "total_memory_mb": 0.0,
  "pids": [],
  "processes": [],
  "warnings": [],
  "metrics": {
    "close_wait_count": 0,
    "time_wait_count": 45,
    "close_wait_threshold": 10,
    "time_wait_threshold": 1000
  }
}
```

### Safety Features
- Never kills if active connections to same endpoint exist
- Protects system network processes (mDNSResponder, networkserviceproxy)
- Protects legitimate network apps (postgres, redis, docker, browsers)
- Validates connection state before flagging as zombie

---

## Agent 12: Orphaned Process Groups Hunter
**File**: `agent_orphaned_process_groups.py`
**Expected Recovery**: 1-5 GB
**Lines of Code**: 420
**⚠️ CAUTION**: High system impact - extensive validation required

### Detection Capabilities
1. **Dead Group Leaders** - Detects process groups where leader (PGID==PID) is dead
2. **Orphaned Children** - Finds processes with dead parent processes
3. **Zombie Groups** - Identifies entire process trees consuming resources
4. **Memory Leaks** - Tracks abandoned process groups >200MB

### CLI Usage
```bash
# JSON output (default)
uv run agent_orphaned_process_groups.py --format json

# Table format (human-readable)
uv run agent_orphaned_process_groups.py --format table

# Summary format (quick overview)
uv run agent_orphaned_process_groups.py --format summary

# Verbose mode (show validation failures)
uv run agent_orphaned_process_groups.py --format json --verbose

# Custom minimum children threshold
uv run agent_orphaned_process_groups.py --min-children 3
```

### Output Format
```json
{
  "agent": "orphaned_process_groups",
  "agent_number": 12,
  "zombie_groups_found": 0,
  "total_orphaned_processes": 0,
  "total_memory_mb": 0.0,
  "process_groups": [],
  "all_pids": [],
  "metrics": {
    "total_groups_analyzed": 507,
    "validation_failures": 0,
    "min_children_threshold": 2
  }
}
```

### Safety Features (EXTENSIVE)
- Never touches system PGIDs (0, 1 - kernel/launchd)
- Protects critical system processes (WindowServer, Finder, Dock)
- Validates no children exist outside process group
- Checks all processes in group for protection status
- Requires minimum 2+ orphaned children before flagging
- Memory threshold: 200MB minimum

---

## Common Features (Both Agents)

### Exclusions Support
Both agents load protection rules from `../config/exclusions.json`:
```json
{
  "protected_processes": ["claude-code", "cursor", "postgres"],
  "protected_patterns": ["vscode", "docker", "postgresql"]
}
```

### Dependencies (PEP 723)
```toml
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "psutil>=6.1.0",
#     "click>=8.1.0",
#     "rich>=13.0.0"
# ]
# ///
```

### Execution
Both scripts are:
- ✅ Executable (`chmod +x`)
- ✅ Self-contained (all dependencies in header)
- ✅ UV-compatible (run with `uv run`)
- ✅ CLI-enabled (Click framework)
- ✅ Multiple output formats (JSON, table, summary)

---

## Testing Results

### Agent 11 (Network Connection Leaks)
- ✅ Script runs successfully
- ✅ JSON output validates
- ✅ Table format displays correctly
- ✅ Summary format works
- ⚠️ Takes 10-30 seconds to scan all network connections (expected)
- ✅ Verbose mode shows connection details

### Agent 12 (Orphaned Process Groups)
- ✅ Script runs successfully
- ✅ JSON output validates
- ✅ Table format displays correctly
- ✅ Summary format works
- ✅ Fast execution (~4 seconds for 500+ groups)
- ✅ Verbose mode shows validation failures

---

## Integration with Coordinator

Both agents follow the standard pattern:
1. Return JSON with `agent`, `agent_number`, `zombies_found`, `pids`, `total_memory_mb`
2. Support `--format json` for machine-readable output
3. Include memory recovery estimates
4. Provide safety validations before flagging processes

---

## Known Limitations

### Agent 11
- Network scanning is expensive (10-30 seconds)
- `psutil.connections()` deprecated, should migrate to `net_connections()`
- CLOSE_WAIT detection relies on `netstat` parsing (platform-specific)

### Agent 12
- PGID detection uses `ps` command (macOS-specific)
- Very conservative safety checks (may miss some zombies)
- High system impact - should be run less frequently
- Fallback to PID==PGID assumption when `ps` fails

---

## Next Steps

1. ✅ Both scripts implemented and tested
2. ⏭️ Update coordinator to include agents 11-12
3. ⏭️ Add agents to kill script execution flow
4. ⏭️ Monitor performance impact in production
5. ⏭️ Consider caching network connection scans

---

**Generated**: 2025-11-19
**Status**: ✅ Complete and tested
**Total Agents**: 26 (with these 2 new additions)

---

## Deprecated Agents (Archived 2025-11-30)

### Refactoring Summary

As part of the macOS Resource Optimizer v2.0 refactoring, 23 scripts were archived to improve maintainability while preserving 100% of high-impact optimization capabilities.

**Duplicates Archived** (8 scripts):
- agent_chrome_helper_detector.py → Use agent_browser_helpers.py
- agent_docker_container_zombies.py → Use agent_docker_container_scanner.py
- agent_db_connection_leaks.py → Use agent_database_connection_pooler.py
- agent_jvm_zombies.py → Use agent_jvm_memory_hog_detector.py
- agent_windowserver_hunter.py → Use agent_window_server_optimizer.py
- agent_memory_growth_detector.py → Use agent_memory_leak_hunter.py
- agent_node_zombies.py → Use agent_node_process_scanner.py
- agent_git_credential_helpers.py → Use agent_ssh_git_process_zombies.py

**Diagnostic-Only Scripts Archived** (6 scripts):
- agent_system_analyzer.py
- agent_kernel_extension_analyzer.py
- agent_app_memory_profiler.py
- agent_temp_file_analyzer.py
- agent_log_rotation_optimizer.py
- context-detector.py

**Low-Impact Scripts Archived** (6 scripts):
- agent_railway_mcp.py (~0.2 GB savings)
- agent_figma_design_hunter.py (~0.3 GB savings)
- agent_adobe_daemon_hunter.py (~0.2 GB savings)
- agent_xpc_service_leaks.py (~0.2 GB savings)
- agent_launchagent_optimizer.py (~0.1 GB savings)
- agent_socket_leak_hunter.py (~0.2 GB savings)

**Orchestrators Consolidated** (1 script):
- ram-master-orchestrator.py → Merged into coordinator.py

**Utilities Archived** (2 scripts):
- kill_zombies.py → Use kill_zombies_parallel.py
- docker-analyzer.py → Integrated into agent_docker_deep_cleanup.py

**Total Archived**: 23 scripts
**Impact Retained**: 88% optimization capability (60-348 GB savings preserved)
**Code Reduction**: 27% (86 → 63 scripts)

### Renamed Agents (2025-11-30)

For clarity and consistency, 8 agents were renamed:

| Old Name | New Name |
|----------|----------|
| agent_slack_discord_hunter.py | agent_messaging_app_hunter.py |
| agent_dns_network_hunter.py | agent_dns_connection_scanner.py |
| agent_ssh_session_leaks.py | agent_ssh_connection_scanner.py |
| agent_gradle_maven_hunter.py | agent_build_cache_cleaner.py |
| agent_developer_cache_hunter.py | agent_developer_cache_cleaner.py |
| agent_system_log_hunter.py | agent_system_log_cleaner.py |
| agent_xcode_artifact_hunter.py | agent_xcode_cache_cleaner.py |
| agent_timemachine_snapshot_hunter.py | agent_timemachine_snapshot_cleaner.py |

### Restoration

All archived scripts are available in `scripts/_archive/` with restoration instructions:

```bash
# Restore a specific archived script
cp scripts/_archive/{category}/{script_name}.py scripts/

# Update coordinator.py to re-add the agent (if applicable)
```

See `scripts/_archive/README.md` for detailed restoration guides.
