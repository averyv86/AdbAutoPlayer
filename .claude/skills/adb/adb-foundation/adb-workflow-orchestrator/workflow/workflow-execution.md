# Workflow: TOON Workflow Execution Engine

**File**: `workflow-execution.toon`
**Skill**: `adb-workflow-orchestrator`
**Version**: 1.0.0
**Category**: workflow-orchestration
**Difficulty**: intermediate

---

## Purpose

This workflow executes TOON workflow files with full phase orchestration, parameter management, and comprehensive error recovery. It validates workflow structure, parses configuration, executes phases sequentially, and generates detailed execution reports.

Use this workflow as the central execution engine for all ADB automation workflows.

---

## Prerequisites

- Device with ADB debugging enabled
- TOON workflow file to execute
- Valid TOON syntax (.toon file)
- All referenced scripts accessible
- Device connectivity verified

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| workflow_file | string | "" | Path to TOON workflow file (required) |
| verbose | boolean | true | Enable verbose logging |

---

## Example Execution

```bash
# Execute a workflow
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-workflow-orchestrator/workflow/workflow-execution.toon \
  --param device="127.0.0.1:5555" \
  --param workflow_file=".claude/skills/adb-bypass/workflow/bypass-validation.toon" \
  --verbose

# Execute Karrot login workflow
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-workflow-orchestrator/workflow/workflow-execution.toon \
  --param device="emulator-5554" \
  --param workflow_file=".claude/skills/adb-karrot/workflow/login-automation.toon" \
  --param verbose=true
```

---

**Last Updated**: 2025-12-02
