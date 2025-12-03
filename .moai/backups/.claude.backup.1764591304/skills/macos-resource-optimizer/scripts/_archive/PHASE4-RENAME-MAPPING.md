# Phase 4: Agent Naming Standardization (2025-11-30)

## Renaming Summary

**Total Renames**: 8 agents
**Total Archives**: 2 utilities
**Script Count**: 65 → 63

## Naming Convention Applied

- `_hunter` suffix: Agents that only **detect/identify** resources
- `_cleaner` suffix: Agents that **actively cleanup/remove** resources
- `_scanner` suffix: Agents that **scan and analyze** processes
- `_optimizer` suffix: Agents that **optimize settings/configurations**

## Renamed Agents

| # | Old Name | New Name | Reason |
|---|----------|----------|--------|
| 1 | agent_slack_discord_hunter.py | agent_messaging_app_hunter.py | Generic domain (not just Slack/Discord) |
| 2 | agent_dns_network_hunter.py | agent_dns_connection_scanner.py | Clearer action (scanner, not hunter) |
| 3 | agent_ssh_session_leaks.py | agent_ssh_connection_scanner.py | Consistency with other scanners |
| 4 | agent_gradle_maven_hunter.py | agent_build_cache_cleaner.py | Accurate action (cleaner, not hunter) |
| 5 | agent_developer_cache_hunter.py | agent_developer_cache_cleaner.py | Accurate action (cleaner, not hunter) |
| 6 | agent_system_log_hunter.py | agent_system_log_cleaner.py | Accurate action (cleaner, not hunter) |
| 7 | agent_xcode_artifact_hunter.py | agent_xcode_cache_cleaner.py | Accurate action (cleaner, not hunter) |
| 8 | agent_timemachine_snapshot_hunter.py | agent_timemachine_snapshot_cleaner.py | Accurate action (cleaner, not hunter) |

## Archived Utilities

| # | Script | Replacement | Reason |
|---|--------|-------------|--------|
| 1 | kill_zombies.py | kill_zombies_parallel.py | Parallel version is faster |
| 2 | docker-analyzer.py | agent_docker_deep_cleanup.py | Functionality integrated |

## Updated References

- `coordinator.py`: Updated 8 agent references (lines 497-501, 658-660)
- All renamed agents verified with syntax check
- No internal filename references required updates

## Verification

✅ All 8 agents renamed successfully
✅ All 2 utilities archived
✅ coordinator.py updated with new names
✅ Syntax validation passed for all agents
✅ Archive documentation created
✅ Final script count: 63

