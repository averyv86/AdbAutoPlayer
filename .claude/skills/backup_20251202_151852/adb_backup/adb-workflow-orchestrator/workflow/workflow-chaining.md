# Workflow: Multi-Workflow Orchestration and Chaining

**File**: `workflow-chaining.toon`
**Skill**: `adb-workflow-orchestrator`
**Version**: 1.0.0
**Category**: workflow-orchestration
**Difficulty**: advanced

---

## Purpose

This workflow chains multiple workflows together in sequence, managing dependencies, passing state between workflows, and aggregating results into a unified output.

Use this workflow to orchestrate complex multi-step automation sequences that require output from one workflow to feed into the next.

---

## Prerequisites

- Multiple TOON workflows to chain
- Device connectivity verified
- Output compatibility between workflows
- State format compatibility

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| workflows | string | "" | Comma-separated workflow list |
| pass_state | boolean | true | Pass output state between workflows |

---

## Example Execution

```bash
# Chain bypass validation, login, and detection check
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-workflow-orchestrator/workflow/workflow-chaining.toon \
  --param device="127.0.0.1:5555" \
  --param workflows=".claude/skills/adb-bypass/workflow/bypass-validation.toon,.claude/skills/adb-karrot/workflow/login-automation.toon,.claude/skills/adb-karrot/workflow/detection-check.toon" \
  --param pass_state=true \
  --verbose
```

---

**Last Updated**: 2025-12-02
