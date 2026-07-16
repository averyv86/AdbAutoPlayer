# Workflow: Dynamic ADB Skill Generation

**File**: `skill-creation.toon`
**Skill**: `adb-skill-generator`
**Version**: 1.0.0
**Category**: skill-development
**Difficulty**: advanced

---

## Purpose

This workflow generates new ADB skills dynamically from templates. It creates complete skill structure including SKILL.md documentation, workflow directories, helper scripts, and validation checks.

Use this workflow to rapidly prototype new automation skills or create custom skills for application-specific tasks.

---

## Prerequisites

- Device with ADB access (for validation during generation)
- Write access to output directory
- Knowledge of skill types and templates
- Understanding of skill structure

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address (for validation) |
| skill_name | string | "" | Name of skill to generate (required) |
| skill_type | string | "automation" | Type: automation, detection, utility |
| base_template | string | "generic" | Template: generic, app-specific, hardware |
| output_path | string | "/tmp/generated_skill" | Output directory path |

---

## Skill Types

- **automation**: Task automation and workflow execution
- **detection**: Screen state and element detection
- **utility**: Helper functions and utilities

---

## Example Execution

```bash
# Generate automation skill
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-skill-generator/workflow/skill-creation.toon \
  --param device="127.0.0.1:5555" \
  --param skill_name="adb-custom-app" \
  --param skill_type="automation" \
  --param base_template="generic" \
  --param output_path="/tmp/adb-custom-app" \
  --verbose

# Generate detection skill
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-skill-generator/workflow/skill-creation.toon \
  --param device="emulator-5554" \
  --param skill_name="adb-app-detector" \
  --param skill_type="detection" \
  --verbose
```

---

**Last Updated**: 2025-12-02
