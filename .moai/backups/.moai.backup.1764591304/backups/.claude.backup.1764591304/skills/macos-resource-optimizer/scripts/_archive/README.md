# Script Archive - macOS Resource Optimizer

**Purpose**: Archive of unused, legacy, and superseded scripts
**Last Updated**: 2025-12-01
**Total Archived**: 67 scripts across 6 archival phases
**Active Scripts**: 12 (82% reduction from original 74)

---

## Archive History

### Phase 1: Agent Scripts Archive (2025-11-30)
- **Archived**: 41 agent-specific scripts
- **Reason**: Replaced by 8 category-based analysis scripts (cpu, memory, disk, network, battery, thermal)
- **Location**: `_archive/agent_scripts/`

### Phase 2: Hyphenated Scripts (2025-11-30)
- **Archived**: 11 scripts with old naming convention
- **Reason**: Not referenced by agents/commands
- **Location**: `_archive/hyphenated_scripts/`

### Phase 3: Legacy Scripts (2025-11-30)
- **Archived**: 4 superseded implementations
- **Reason**: Replaced by newer implementations
- **Location**: `_archive/legacy_scripts/`

### Phase 4: Workflow Consolidation (2025-12-01)
- **Archived**: 11 additional scripts
- **Reason**: Workflow consolidation (9 agents → 3 agents, 23 → 12 essential scripts)
- **Categories**: Legacy (3), Utilities (4), Tests (1), One-time (3)
- **Location**: `_archive/legacy/`, `_archive/utilities/`, `_archive/tests/`, `_archive/one-time/`

---

## Current Archive Structure

```
_archive/
├── agent_scripts/         # 41 scripts - Old micro-agent architecture
├── hyphenated_scripts/    # 11 scripts - Old naming convention
├── legacy_scripts/        # 4 scripts - Superseded implementations
├── legacy/                # 3 scripts - Phase 4: Replaced scripts
├── utilities/             # 4 scripts - Phase 4: Unused helpers
├── tests/                 # 1 script - Phase 4: Old architecture tests
├── one-time/              # 3 scripts - Phase 4: One-time operations
└── README.md              # This file
```

---

## Phase 4 Archive Details (2025-12-01)

### Legacy (3 scripts)

Scripts replaced by newer, better implementations:

| Script | Replaced By | Reason |
|--------|-------------|--------|
| `analyze_processes.py` | `process_analyzer_uv.py` | Old process analyzer, superseded by UV script with TOON format and helper process grouping |
| `coordinator.py` | `alfred.py` | Old coordinator (54KB), superseded by newer alfred.py (18KB) with TOON progress |
| `report_memory.py` | TOON format in `analyze_memory.py` | Old JSON reporting replaced by TOON format (60-75% token savings) |

### Utilities (4 scripts)

Helper scripts not used in core workflow:

| Script | Archive Reason |
|--------|----------------|
| `browser_utils.py` | Not used in proven workflow (82.6% → 40.1%) |
| `hibernation_utils.py` | Feature not implemented in current architecture |
| `ram_utils.py` | Functionality absorbed into analyze_memory.py |
| `verify_cleanup.py` | Not part of automated workflow |

### Tests (1 script)

| Script | Archive Reason |
|--------|----------------|
| `test_phase2_agents_1_2.sh` | Tests old 9-agent architecture |

### One-Time (3 scripts)

| Script | Archive Reason |
|--------|----------------|
| `convert_registry_to_toon.py` | One-time conversion completed |
| `analyze_script_usage.py` | One-time analysis for cleanup decision |
| `execute-cleanup.sh` | Superseded by automated optimize.py workflow |

---

## Active Scripts (12 Essential)

### Core Workflow Scripts (Proven 82.6% → 40.1% Success)

| Script | Size | Purpose | Agent |
|--------|------|---------|-------|
| `alfred.py` | 18KB | Parallel analysis coordinator | manager-resource-coordinator |
| `process_analyzer_uv.py` | 3.5KB | **CRITICAL** - Process pattern analysis | expert-memory-optimizer |
| `analyze_memory.py` | 4.6KB | Memory metrics (JSON output) | expert-memory-optimizer |
| `optimize.py` | 11KB | Advanced optimization with TOON | expert-memory-optimizer |

### Analysis Scripts (expert-system-optimizer)

| Script | Size | Purpose |
|--------|------|---------|
| `analyze_all.py` | 5.0KB | Unified multi-category analysis |
| `analyze_cpu.py` | 6.4KB | CPU metrics |
| `analyze_disk.py` | 3.8KB | Disk I/O metrics |
| `analyze_network.py` | 2.3KB | Network bandwidth metrics |
| `analyze_battery.py` | 2.9KB | Battery drain metrics |
| `analyze_thermal.py` | 3.0KB | CPU temperature metrics |

### Supporting Scripts

| Script | Size | Purpose |
|--------|------|---------|
| `status.py` | 5.9KB | Quick system status snapshot |
| `background_monitor.py` | 11KB | Continuous monitoring daemon |

**Total Active Size**: ~77KB

---

## Performance Metrics

### Script Reduction

| Phase | Before | After | Reduction |
|-------|--------|-------|-----------|
| Initial | 74 | 74 | 0% |
| Phase 1-3 | 74 | 23 | 69% |
| Phase 4 | 23 | 12 | 47% |
| **Total** | **74** | **12** | **83.8%** |

### Agent Reduction

| Before | After | Reduction |
|--------|-------|-----------|
| 9 agents | 3 agents | 66% |

**3-Agent Architecture**:
1. `manager-resource-coordinator` - Workflow orchestration
2. `expert-memory-optimizer` - Memory + app restart (RAM, Swap)
3. `expert-system-optimizer` - System resources (CPU, Disk, Network, Battery, Thermal)

### Proven Workflow Performance

**Success Result** (2025-12-01):
- Memory: 82.6% → 40.1% (42.5% reduction)
- Available: 11.12 GB → 38.37 GB (3.45x increase)
- Time: 52 seconds
- Actions: Restarted 3 apps (Dia, VS Code, Notion) + sudo purge

**Token Efficiency**:
- Traditional JSON: ~25-30K tokens
- TOON format: ~8-10K tokens
- Savings: 60-70%

---

## Restoration Instructions

```bash
# Example: Restore coordinator.py from legacy archive
cd /Users/rdmtv/Documents/claydev-local/projects-v2/moai-ir-deck/.claude/skills/macos-resource-optimizer/scripts
cp _archive/legacy/coordinator.py ./
```

**Before Restoring**: Consider if functionality is truly needed and won't conflict with current architecture.

---

## Deletion Policy

**Do NOT delete archived scripts** for:
1. Historical reference and learning
2. Pattern library for future enhancements
3. Rollback safety
4. Negligible disk space (<1.5MB total)

**Review Schedule**: Quarterly (every 3 months)
- Scripts untouched for 6+ months → Consider deletion
- Space constraints → Delete one-time category first

---

## Related Documentation

- Agent archive: `.claude/agents/macos-resource-optimizer/_archive/`
- Proven workflow: `.claude/commands/macos-resource-optimizer/quick-optimize.md`
- Enhanced memory agent: `.claude/agents/macos-resource-optimizer/expert-memory-optimizer.md`

---

**Archive Status**: ✅ Complete (4 phases)
**Next Review**: 2025-03-01
**Version**: 2.0.0
