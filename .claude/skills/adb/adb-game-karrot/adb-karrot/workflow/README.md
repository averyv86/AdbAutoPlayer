# adb-karrot Workflows

Workflow infrastructure for Karrot game automation testing and task execution

## Overview

This directory contains TOON-based workflow definitions for automating Karrot game automation testing and task execution workflows. Each workflow pairs a `.toon` file (orchestration logic) with a `.md` file (documentation).

## Workflow Index

### Implemented Workflows (3 TOON+MD pairs)

1. **[login-automation.md](./login-automation.md)** - Login flow with SMS 2FA support
   - File: `login-automation.toon`
   - Automated phone number entry
   - SMS verification code handling
   - Session establishment verification

2. **[detection-check.md](./detection-check.md)** - Test app integrity detection
   - File: `detection-check.toon`
   - Monitor for detection warnings
   - Analyze network traffic
   - Test feature accessibility

3. **[validation-flow.md](./validation-flow.md)** - Post-bypass validation
   - File: `validation-flow.toon`
   - Test all app features
   - Verify data integrity
   - Validate payment systems

## Purpose

TOON (Task-Oriented Orchestration Notation) workflows provide:
- Structured task orchestration and sequencing
- Parameter validation and passing
- Multi-phase execution workflows
- Integration with adb-workflow-orchestrator
- Comprehensive error handling and recovery

## Usage

Execute any workflow using the ADB workflow orchestrator:

```bash
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-karrot/workflow/{workflow-name}.toon \
  --param device="127.0.0.1:5555" \
  --verbose
```

## Workflow Structure

Each workflow consists of two files:

### TOON File (Orchestration)
The `.toon` file defines:
- Workflow parameters and validation
- Execution phases and sequential steps
- Error handling and recovery actions
- Output and reporting

### Markdown File (Documentation)
The `.md` file documents:
- Purpose and use case
- Prerequisites and requirements
- Available parameters and constraints
- Execution phases and expected outputs
- Success criteria and error handling
- Example commands and integration patterns

## Creating New Workflows

To create a new workflow:

1. Create `{name}.toon` file using TOON v4.0 syntax
2. Create `{name}.md` documentation file
3. Test execution with workflow orchestrator
4. Update this README.md index

Refer to [pattern-toon-workflow.md](./../../builder/modules/pattern-toon-workflow.md) for detailed TOON patterns and specifications.

## Integration

These workflows integrate with:
- `adb-workflow-orchestrator` - Execution engine
- Other ADB skills for automation chains

## References

- TOON v4.0 Specification: [pattern-toon-workflow.md](./../../builder/modules/pattern-toon-workflow.md)
- Workflow Orchestrator: [adb-workflow-orchestrator SKILL.md](../adb-workflow-orchestrator/SKILL.md)
- Parent Skill: [SKILL.md](../SKILL.md)

---

**Status**: Phase 6B - Complete (3 TOON+MD workflow pairs created)
**Last Updated**: 2025-12-02
