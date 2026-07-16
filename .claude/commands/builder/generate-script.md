---
name: builder:generate-script
description: "Generate UV CLI script following IndieDevDan patterns for existing skill"
argument-hint: "[skill-name] [script-name] [purpose]"
allowed-tools:
  - Task
  - AskUserQuestion
  - Read
model: haiku
skills: moai-foundation-core, builder-workflow, builder-skill-uvscript
---

## Pre-execution Context

!git status --porcelain
!git branch --show-current

## Essential Files

@.moai/config/config.json

---

# Generate UV Script

> **Architecture**: Commands → Agents → Skills. This command orchestrates through `Task()` tool.
> **Delegation Model**: Script generation delegated to `builder-workflow` agent.

**Workflow Integration**: Creates single-file UV CLI scripts following IndieDevDan 13-rule patterns.

---

## Command Purpose

Generate production-ready UV CLI scripts with:
- PEP 723 inline dependencies
- Dual output modes (human + JSON)
- Project-root auto-detection
- Click CLI framework
- Comprehensive --help documentation

**Run on**: `$ARGUMENTS` (skill-name script-name [purpose])

**Variables**:
- `$1`: Target skill name
- `$2`: Script name to create
- `$3+`: Optional purpose description

---

## Execution Philosophy

`/builder:generate-script` creates scripts through agent delegation:

```
User Command: /builder:generate-script [skill] [script] [purpose]
    ↓
Phase 1: Verify skill exists
    ↓
Phase 2: Task(subagent_type="builder-workflow")
    → Apply IndieDevDan 13 rules
    → Generate 200-300 line script
    → Add PEP 723 dependencies
    → Create dual output modes
    ↓
Phase 3: Update SKILL.md
    ↓
Output: Production UV script
```

---

## Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| builder-workflow | UV script generation specialist |
| builder-skill-uvscript | Reference patterns (23 scripts) |
| mcp-context7 | Latest library documentation |
| moai-lang-unified | Python best practices |

---

## PHASE 1: Skill Verification

**Goal**: Verify target skill exists

### Step 1.1: Parse Arguments

```python
args = $ARGUMENTS.split()
skill_name = args[0] if len(args) > 0 else None
script_name = args[1] if len(args) > 1 else None
purpose = ' '.join(args[2:]) if len(args) > 2 else None
```

### Step 1.2: Validate Skill Exists

Read SKILL.md to verify:

```yaml
Tool: Read
Parameters:
  file_path: ".claude/skills/{skill_name}/SKILL.md"
```

### Step 1.3: Clarify if Missing

```python
AskUserQuestion({
    "questions": [{
        "question": "What type of script would you like to create?",
        "header": "Script Type",
        "multiSelect": false,
        "options": [
            {
                "label": "Analysis",
                "description": "Analyze data, code, or system resources"
            },
            {
                "label": "Validation",
                "description": "Validate configuration, schema, or compliance"
            },
            {
                "label": "Generation",
                "description": "Generate code, templates, or documentation"
            },
            {
                "label": "Automation",
                "description": "Automate repetitive tasks or workflows"
            }
        ]
    }]
})
```

---

## PHASE 2: Script Generation

**Goal**: Generate UV script following IndieDevDan patterns

### Step 2.1: Delegate to builder-workflow

```yaml
Tool: Task
Parameters:
- subagent_type: "builder-workflow"
- description: "Generate UV CLI script"
- prompt: """You are the builder-workflow agent generating a UV CLI script.

**Task**: Create production UV script following IndieDevDan 13 rules.

**Context**:
- Skill Name: {skill_name}
- Script Name: {script_name}
- Purpose: {purpose}
- Conversation Language: {{CONVERSATION_LANGUAGE}}

**IndieDevDan 13 Rules**:
1. Size: 200-300 lines target (500 max)
2. ASTRAL UV: PEP 723 `# /// script` dependencies
3. Directory: Flat scripts/ folder
4. Self-contained: Embedded HTTP clients, no shared imports
5. CLI: Click framework with --help, --json, --verbose
6. Structure: 9 sections (shebang, docstring, imports, constants, project-root, models, logic, formatters, CLI)
7. Dependencies: 0-3 packages, minimum version pins
8. Docstrings: Google-style with examples
9. Testing: Basic unit tests (5-10)
10. Single-file: No multi-file dependencies
11. Error handling: Dual-mode (human + JSON)
12. Config: Environment variables, no hardcoded secrets
13. Progressive disclosure: 0-token dormant

**Script Template**:
```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click>=8.1.0",
#     "rich>=13.0.0",
# ]
# ///
\"\"\"
{script_name}: {purpose}

Usage:
    uv run {script_path} [OPTIONS]

Examples:
    uv run {script_path} --help
    uv run {script_path} --json
\"\"\"

import json
import sys
from pathlib import Path

import click
from rich.console import Console

# Constants
VERSION = "1.0.0"
console = Console()

# Project root detection
def find_project_root() -> Path:
    \"\"\"Find project root by looking for .git or pyproject.toml.\"\"\"
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return current

PROJECT_ROOT = find_project_root()

# Data models
# ... (Pydantic models if needed)

# Core logic
def main_logic() -> dict:
    \"\"\"Main script logic.\"\"\"
    # Implementation here
    return {"status": "success"}

# Output formatters
def format_human(result: dict) -> None:
    \"\"\"Format output for human reading.\"\"\"
    console.print(result)

def format_json(result: dict) -> None:
    \"\"\"Format output as JSON.\"\"\"
    print(json.dumps(result, indent=2))

# CLI
@click.command()
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.version_option(VERSION)
def cli(json_output: bool, verbose: bool) -> None:
    \"\"\"{purpose}\"\"\"
    result = main_logic()

    if json_output:
        format_json(result)
    else:
        format_human(result)

if __name__ == "__main__":
    cli()
```

**Output**:
- Script at: .claude/skills/{skill_name}/scripts/{script_name}.py
- Updated SKILL.md with script entry
- Test command: uv run {script_path} --help
"""
```

---

## Summary: Execution Checklist

- [ ] **Skill Verified**: Target skill exists
- [ ] **Agent Delegated**: builder-workflow invoked
- [ ] **Script Generated**: 200-300 lines following IndieDevDan rules
- [ ] **SKILL.md Updated**: Script entry added
- [ ] **Tested**: --help flag works

---

## Quick Reference

| Scenario | Command | Expected Outcome |
|----------|---------|------------------|
| Analysis script | `/builder:generate-script my-skill analyze` | Analysis script for skill |
| With purpose | `/builder:generate-script my-skill validate "Check compliance"` | Validation script |
| Existing skill | `/builder:generate-script moai-foundation-core check-agents` | Script for foundation skill |

**Output Location**: `.claude/skills/{skill-name}/scripts/{script-name}.py`

---

## EXECUTION DIRECTIVE

**You must NOW execute the command following the "Execution Philosophy" described above.**

1. Parse `$ARGUMENTS` to extract skill-name and script-name.
2. Verify skill exists by reading SKILL.md.
3. Call the `Task` tool with `subagent_type="builder-workflow"`.
4. Verify script creation and --help works.
5. Offer next step options.

**Version**: 1.0.0
**Last Updated**: 2025-12-01
