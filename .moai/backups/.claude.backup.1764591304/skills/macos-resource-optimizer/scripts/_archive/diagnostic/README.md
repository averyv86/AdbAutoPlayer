# Archived Diagnostic-Only Scripts (2025-11-30)

These agents provide analysis/reporting but no cleanup capability.

| Script | Reason | LOC |
|--------|--------|-----|
| agent_system_analyzer.py | System info only | 217 |
| agent_kernel_extension_analyzer.py | Analysis only | 610 |
| agent_app_memory_profiler.py | Diagnostic only | 393 |
| agent_temp_file_analyzer.py | Analysis only | 390 |
| agent_log_rotation_optimizer.py | Analysis only | 372 |
| context-detector.py | Unclear purpose | 445 |

Total: 6 scripts, 2,427 LOC

## Rationale

These scripts were archived because:

1. **No Resource Cleanup**: They only analyze and report, but don't free any resources
2. **Redundant Analysis**: Their analysis capabilities are covered by other active agents
3. **Low Integration**: Not integrated into the main coordinator workflow
4. **Maintenance Burden**: Additional code to maintain without resource optimization benefit

## Restoration

If analysis capability needed:

```bash
cd /Users/rdmtv/Documents/claydev-local/projects-v2/moai-ir-deck/.claude/skills/macos-resource-optimizer

# Copy script back
cp scripts/_archive/diagnostic/<script_name>.py scripts/

# Update coordinator.py to re-add agent to appropriate phase
# Add agent import and phase definition
```

## Archived Scripts Details

### agent_system_analyzer.py (217 LOC)
- Purpose: System information gathering
- Capability: Read-only system info
- Reason: No cleanup, info available via `system_profiler`

### agent_kernel_extension_analyzer.py (610 LOC)
- Purpose: Analyze loaded kernel extensions
- Capability: Report loaded kexts
- Reason: Analysis only, no cleanup capability

### agent_app_memory_profiler.py (393 LOC)
- Purpose: Profile application memory usage
- Capability: Memory usage reporting
- Reason: Diagnostic only, covered by Activity Monitor

### agent_temp_file_analyzer.py (390 LOC)
- Purpose: Analyze temporary files
- Capability: Temp file discovery
- Reason: Cleanup handled by `agent_temp_file_cleanup.py`

### agent_log_rotation_optimizer.py (372 LOC)
- Purpose: Analyze log rotation settings
- Capability: Log config reporting
- Reason: No cleanup, macOS handles rotation

### context-detector.py (445 LOC)
- Purpose: Unclear, possibly context detection
- Capability: Unknown integration
- Reason: Not integrated, unclear purpose

---

**Archive Date**: 2025-11-30
**Phase**: Phase 3 - Low-Value Script Archival
**Total LOC Archived**: 2,427
