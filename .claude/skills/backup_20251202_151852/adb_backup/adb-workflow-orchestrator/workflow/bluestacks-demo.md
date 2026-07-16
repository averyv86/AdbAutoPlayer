# Workflow: BlueStacks Interactive Demonstration

**File**: `bluestacks-demo.toon`
**Skill**: `adb-workflow-orchestrator`
**Version**: 1.0.0
**Category**: demonstration
**Difficulty**: beginner

---

## Purpose

Interactive demonstration of ADB automation capabilities on BlueStacks emulator. Showcases screen capture, app launching, shell commands, and workflow execution features.

---

## Example Execution

```bash
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-workflow-orchestrator/workflow/bluestacks-demo.toon \
  --param device="127.0.0.1:5555" \
  --param demo_type="quick" \
  --verbose
```

---

**Last Updated**: 2025-12-02
