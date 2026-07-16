# Archived Duplicate Agents (2025-11-30)

These agents were duplicates of existing functionality and have been consolidated to reduce maintenance overhead.

## Archived Files

| Archived File | Primary Replacement | Reason |
|---------------|---------------------|---------|
| agent_chrome_helper_detector.py | agent_browser_helpers.py | Chrome-specific detection consolidated into general browser helpers |
| agent_docker_container_zombies.py | agent_docker_container_scanner.py | Docker zombie detection included in container scanner |
| agent_db_connection_leaks.py | agent_database_connection_pooler.py | Database leak detection merged into connection pooler |
| agent_jvm_zombies.py | agent_jvm_memory_hog_detector.py | JVM zombie detection included in memory hog detector |
| agent_windowserver_hunter.py | agent_window_server_optimizer.py | WindowServer hunting merged into optimizer |
| agent_memory_growth_detector.py | agent_memory_leak_hunter.py | Memory growth detection is subset of leak hunting |
| agent_node_zombies.py | agent_node_process_scanner.py | Node zombie detection included in process scanner |
| agent_git_credential_helpers.py | agent_ssh_git_process_zombies.py | Git credential helper detection merged into SSH/Git zombies |

**Total Files Archived**: 8
**Space Saved**: ~73.4 KB
**Scripts Reduced**: 85 → 77 (-8 scripts)

## Archive Details

- **Archive Date**: 2025-11-30
- **Phase**: Phase 2 - Duplicate Agent Consolidation
- **Archive Location**: `scripts/_archive/duplicates/`
- **Backup Available**: Yes (all files preserved in archive)

## Restoration Instructions

If you need to restore any archived agent:

```bash
# Navigate to scripts directory
cd scripts/

# Copy the archived agent back
cp _archive/duplicates/<agent_name>.py ./

# Update coordinator.py to reference the restored agent
# Example: Add ("chrome_helper_detector", "agent_chrome_helper_detector.py") to agents list

# Test the restoration
python coordinator.py --dry-run
```

## Impact Assessment

### Before Consolidation
- Total Scripts: 85
- Duplicate Agents: 8
- Maintenance Burden: High (duplicate logic across files)

### After Consolidation
- Total Scripts: 77
- Duplicate Agents: 0
- Maintenance Burden: Reduced (single source of truth per function)

### Coordinator.py Changes
- Updated 4 agent references to use primary agents
- Reduced parallel agent count from 20 to 18
- Removed duplicate entries from agent lists

## Verification

To verify all duplicates are properly archived:

```bash
# Check archive directory
ls -la scripts/_archive/duplicates/

# Verify coordinator.py has no references to duplicates
grep -E "chrome_helper_detector|docker_container_zombies|db_connection_leaks|jvm_zombies|windowserver_hunter|memory_growth_detector|node_zombies|git_credential_helpers" scripts/coordinator.py

# Should return no matches
```

## Notes

- All archived agents were functionally redundant with their primary replacements
- Primary agents provide equal or superior functionality
- Archive preserves all code for reference or emergency restoration
- This consolidation aligns with the broader refactoring plan to reduce script count from 85 to ~65

---

**Phase 2 Status**: ✅ Complete
**Next Phase**: Phase 3 - Framework Unification (Day 4)
