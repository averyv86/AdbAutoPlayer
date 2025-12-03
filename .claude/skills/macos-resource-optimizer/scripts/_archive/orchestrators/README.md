# Archived Orchestrator (2025-11-30)

## ram-master-orchestrator.py

**Archived**: 2025-11-30
**Reason**: Functionality consolidated into coordinator.py
**Classes extracted**: MemorySnapshot, ProgressTracker, ErrorRecoveryManager

### What was consolidated

Three valuable classes from ram-master-orchestrator.py were extracted and integrated into coordinator.py:

1. **MemorySnapshot** (lines 47-139)
   - Memory state tracking functionality
   - Captures system memory metrics (total, available, used, swap)
   - Provides memory pressure detection
   - Used for before/after snapshots during optimization

2. **ProgressTracker** (lines 378-421)
   - Detailed progress reporting
   - Phase tracking with start/complete lifecycle
   - Agent completion percentage tracking
   - Console output formatting

3. **ErrorRecoveryManager** (lines 427-458)
   - Rollback capability
   - Retry logic for failed agents
   - Phase error handling (critical vs non-critical)
   - Error recovery strategies

### Why archived

The ram-master-orchestrator.py implemented a complex 11-phase workflow system that overlapped significantly with the existing coordinator.py. Instead of maintaining two orchestrators:

- **Kept**: coordinator.py (6-phase unified orchestration, 50 agents)
- **Archived**: ram-master-orchestrator.py (11-phase workflow, 25 agents)

The valuable classes were extracted to enhance coordinator.py without duplicating orchestration logic.

### Integration location

The extracted classes are now located in:
```
scripts/coordinator.py
Lines 112-291 (after console = Console())
```

### Restoration

If needed, restore with:
```bash
cp _archive/orchestrators/ram-master-orchestrator.py ../
# Update coordinator.py to re-add orchestrator (remove extracted classes to avoid duplication)
```

### Future considerations

If the 11-phase workflow is needed again:
1. Use the archived ram-master-orchestrator.py as reference
2. Extend coordinator.py's phase system (currently supports phases 1-6)
3. Reuse the extracted classes (MemorySnapshot, ProgressTracker, ErrorRecoveryManager)

---

**Refactoring Phase**: Phase 1 (Orchestrator Consolidation)
**Status**: Complete
**Next Phase**: Phase 2 (Duplicate Agent Consolidation)
