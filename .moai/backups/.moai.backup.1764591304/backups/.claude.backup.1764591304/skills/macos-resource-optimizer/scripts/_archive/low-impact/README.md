# Archived Low-Impact Scripts (2025-11-30)

These agents provide minimal resource savings (<0.5 GB) or target niche use cases.

| Script | Impact | Use Case | LOC |
|--------|--------|----------|-----|
| agent_railway_mcp.py | ~0.2 GB | Railway cloud provider only | 172 |
| agent_figma_design_hunter.py | ~0.3 GB | Figma designers only | 257 |
| agent_adobe_daemon_hunter.py | ~0.2 GB | Adobe CC users only | 260 |
| agent_xpc_service_leaks.py | ~0.2 GB | Rare XPC leaks | 366 |
| agent_launchagent_optimizer.py | ~0.1 GB | Advanced/risky | 282 |
| agent_socket_leak_hunter.py | ~0.2 GB | Rare socket leaks | 362 |

Total: 6 scripts, ~1.2 GB max savings, 1,699 LOC

## Rationale

These scripts were archived because:

1. **Low Resource Impact**: Save less than 0.5 GB each (<5% of typical optimization)
2. **Niche Use Cases**: Target specific tools/services not used by most developers
3. **Cost/Benefit Ratio**: Maintenance burden exceeds resource savings
4. **Edge Case Focus**: Address rare issues (socket leaks, XPC leaks)

## Restoration

If specific use case applies:

```bash
cd /Users/rdmtv/Documents/claydev-local/projects-v2/moai-ir-deck/.claude/skills/macos-resource-optimizer

# Copy script back
cp scripts/_archive/low-impact/<script_name>.py scripts/

# Update coordinator.py to re-add agent to appropriate phase
# Add agent import and phase definition
```

## Archived Scripts Details

### agent_railway_mcp.py (172 LOC, ~0.2 GB)
- Purpose: Cleanup Railway MCP server cache
- Impact: 100-300 MB (single cloud provider)
- Reason: Niche use case, minimal impact
- Users: Railway.app cloud platform users only

### agent_figma_design_hunter.py (257 LOC, ~0.3 GB)
- Purpose: Cleanup Figma design tool cache
- Impact: 200-500 MB (design tool cache)
- Reason: Niche use case, designers only
- Users: Figma design tool users only

### agent_adobe_daemon_hunter.py (260 LOC, ~0.2 GB)
- Purpose: Kill Adobe background daemons
- Impact: 150-300 MB RAM + CPU
- Reason: Niche use case, Adobe CC users only
- Users: Adobe Creative Cloud users only

### agent_xpc_service_leaks.py (366 LOC, ~0.2 GB)
- Purpose: Detect and kill leaked XPC services
- Impact: 100-300 MB (rare XPC leaks)
- Reason: Edge case, rare occurrence
- Users: Advanced debugging scenarios

### agent_launchagent_optimizer.py (282 LOC, ~0.1 GB)
- Purpose: Optimize LaunchAgent configurations
- Impact: 50-200 MB (background agents)
- Reason: Advanced/risky, system stability concerns
- Users: Advanced users, manual review required

### agent_socket_leak_hunter.py (362 LOC, ~0.2 GB)
- Purpose: Detect and cleanup socket leaks
- Impact: 100-300 MB (rare socket leaks)
- Reason: Edge case, rare occurrence
- Users: Network debugging scenarios

## Impact Analysis

**Total Potential Savings**: ~1.2 GB (12% of typical 10 GB optimization)

**Comparison to High-Impact Agents**:
- Docker cleanup: 5-20 GB (50x more impact)
- Node modules: 3-15 GB (30x more impact)
- Browser caches: 2-8 GB (20x more impact)

**Decision**: Archive to reduce codebase complexity while maintaining 88% optimization impact.

---

**Archive Date**: 2025-11-30
**Phase**: Phase 3 - Low-Value Script Archival
**Total LOC Archived**: 1,699
**Total Impact Archived**: ~1.2 GB
