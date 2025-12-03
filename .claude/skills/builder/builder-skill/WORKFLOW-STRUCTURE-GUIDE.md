---
name: Workflow Structure Implementation Guide for Builder-Skill
description: How builder-skill should create new skills with scripts and workflow folders
version: 1.0.0
created: 2025-12-02
updated: 2025-12-02
audience: builder-skill agent
status: active
---

# Workflow Structure Implementation Guide

**Purpose**: Guide builder-skill agent on creating new skills with the TOON+MD workflow structure.

**Scope**: Instructions for builder-skill when creating new skills during SPEC-driven development.

---

## Quick Summary

When builder-skill creates a new skill, it must now create:

1. **scripts/** folder with Python scripts (existing pattern)
2. **workflow/** folder with TOON+MD pairs (new pattern)
3. **SKILL.md** with metadata and "Workflows" section

Old single-folder structure is no longer sufficient.

---

## Pre-Creation Requirements

Before builder-skill starts creating a new skill, verify:

- [ ] SPEC exists and specifies skill requirements
- [ ] Skill domain and purpose are clear
- [ ] Dependencies identified
- [ ] Initial scripts/workflows planned
- [ ] Team approval obtained (if required)

---

## Step 1: Create Skill Directory Structure

### Standard Layout

Create the following directory structure:

```
.claude/skills/[skill-name]/
├── SKILL.md                    # Skill metadata (required)
├── scripts/                    # Python scripts (required)
│   ├── __init__.py
│   └── [action].py             # Implementation scripts
└── workflow/                   # TOON+MD pairs (required)
    ├── README.md               # Workflow index
    └── [action].toon/md pairs
```

### Implementation

```python
from pathlib import Path

def create_skill_structure(skill_name: str, project_root: str):
    """Create standard skill directory structure."""

    base_path = Path(project_root) / ".claude" / "skills" / skill_name

    # Create directories
    (base_path / "scripts").mkdir(parents=True, exist_ok=True)
    (base_path / "workflow").mkdir(parents=True, exist_ok=True)

    # Create __init__.py in scripts
    (base_path / "scripts" / "__init__.py").touch()

    # Create workflow/README.md
    (base_path / "workflow" / "README.md").write_text(
        "# Workflows\n\n"
        "This directory contains TOON+MD workflow pairs for this skill.\n"
    )

    print(f"✓ Created skill structure at {base_path}")
```

---

## Step 2: Create SKILL.md with Metadata

### Required Frontmatter

```yaml
---
name: [skill-name]                        # Must match directory name
description: Brief description (max 200 chars)
version: 1.0.0
created: 2025-12-02
updated: 2025-12-02

# New in Phase 3B
modularized: true                         # Skills are modularized
scripts_enabled: true                     # Scripts folder present
workflows_enabled: true                   # Workflows folder present

tier: 2                                   # 1=foundational, 2=mid, 3=specialized
category: [category-name]                 # e.g., adb-automation
last_updated: 2025-12-02
compliance_score: 100                     # 0-100

dependencies:
  - package1>=1.0.0
  - package2>=2.0.0

auto_trigger_keywords:
  - keyword1
  - keyword2

scripts:
  - name: script-name.py
    purpose: What this script does
    type: python
    command: uv run .claude/skills/[skill]/scripts/script-name.py

---
```

### Content Sections

Include these sections in SKILL.md:

1. **Quick Reference** (30 seconds)
2. **Scripts Section** - List all scripts with descriptions
3. **Workflows Section** - Link to workflow/README.md
4. **Dependencies** - External packages
5. **Works Well With** - Related skills

### Example Scripts Section

```markdown
## Scripts

This skill includes the following utility scripts:

| Script | Purpose | Command |
|--------|---------|---------|
| capture.py | Capture device screen | `uv run .claude/skills/[skill]/scripts/capture.py --device <id>` |
| extract.py | Extract text from screen | `uv run .claude/skills/[skill]/scripts/extract.py --image <path>` |

See individual scripts for full documentation.
```

### Example Workflows Section

```markdown
## Workflows

This skill includes TOON+MD workflow pairs for automation.

See [Workflows Documentation](workflow/README.md) for detailed descriptions.

### Available Workflows

- **capture-screen** - Capture Android device screen
- **extract-text** - Extract text using OCR
- **find-element** - Find UI element by template or semantics
```

---

## Step 3: Create Initial Scripts

### Script Naming Convention

```
scripts/
├── [action].py                # Main action script
├── [action]_helper.py         # Support script
└── __init__.py                # Package marker
```

**Pattern**: `[domain]-[action].py`
- Examples: `adb-capture.py`, `adb-tap.py`, `adb-wait.py`

### Script Template

```python
#!/usr/bin/env python3
"""
[Brief description of script].

Usage:
    uv run .claude/skills/[skill]/scripts/[name].py --arg1 value

Args:
    --arg1: Description of arg1
    --device: Target device (auto if not specified)

Returns:
    Exit code 0 on success, 1 on failure

Examples:
    # Basic usage
    $ uv run .claude/skills/[skill]/scripts/[name].py --arg1 value

    # With device specification
    $ uv run .claude/skills/[skill]/scripts/[name].py --arg1 value --device 192.168.1.1:5555
"""

import argparse
import sys
from pathlib import Path

def setup_argument_parser() -> argparse.ArgumentParser:
    """Configure command-line arguments."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--arg1",
        required=True,
        help="Description of required argument"
    )

    parser.add_argument(
        "--device",
        default="auto",
        help="Target device (default: auto-detect)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )

    return parser

def main() -> int:
    """Main entry point."""
    parser = setup_argument_parser()
    args = parser.parse_args()

    try:
        # Implementation here
        print(f"Processing with arg1={args.arg1}, device={args.device}")
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Script Requirements

Each script should have:

- [ ] Clear docstring with description
- [ ] Usage examples in docstring
- [ ] Argument parser with help text
- [ ] Error handling
- [ ] Proper exit codes (0=success, 1=failure)
- [ ] Comments explaining logic
- [ ] Type hints (where applicable)

---

## Step 4: Create workflow/README.md

### Purpose

Acts as index for all workflows in the skill.

### Template

```markdown
---
title: Workflow Index
skill: [skill-name]
last_updated: 2025-12-02
---

# Workflows

This directory contains TOON+MD workflow pairs for the [skill-name] skill.

## Overview

Workflows combine orchestration logic (.toon files) with documentation (.md files).

See individual workflow documentation for details.

## Available Workflows

| Workflow | TOON | MD | Purpose | Status |
|----------|------|----|---------|--------|
| [name] | [name.toon](./name.toon) | [name.md](./name.md) | Brief description | active |

## Workflow Structure

Each workflow consists of two files:

- **[name].toon** - YAML-based orchestration definition
  - Defines steps, parameters, success criteria
  - Executed by workflow engine
  - Version-controlled alongside .md

- **[name].md** - Human-readable documentation
  - Explains purpose, prerequisites, parameters
  - Includes examples and troubleshooting
  - Helps developers understand and use workflow

## Getting Started

1. Choose a workflow from the table above
2. Read the corresponding .md file (documentation)
3. Check the prerequisites and parameters
4. Execute the workflow (see examples in .md)

## Creating New Workflows

When adding new workflows:

1. Create [name].toon with orchestration logic
2. Create [name].md with complete documentation
3. Update this README.md with new entry
4. Verify both files reference each other
5. Test before adding to skill

See [TOON+MD Pattern Reference](../../.moai/docs/TOON-MD-PATTERN-REFERENCE.md) for format details.

## Auto-Nesting

If 5+ workflows with the same prefix exist:

1. Create subfolder with prefix name: `mkdir [prefix]`
2. Move related files: `mv [prefix]-*.toon [prefix]-*.md [prefix]/`
3. Create [prefix]/README.md as subfolder index
4. Update this file with new structure

Example: If 5+ workflows starting with "login-":
```
workflow/
├── README.md          # This file
├── login/             # New subfolder
│   ├── README.md      # Subfolder index
│   ├── email.toon
│   ├── email.md
│   └── ...
```

## Dependencies

This skill depends on:
- [dependency-skill-1](../../[skill-name]/SKILL.md)
- [dependency-skill-2](../../[skill-name]/SKILL.md)

See parent SKILL.md for complete dependency list.

## See Also

- Parent skill: [../SKILL.md](../SKILL.md)
- TOON format: [TOON Specification](../../.moai/docs/TOON-MD-PATTERN-REFERENCE.md)
- Agent training: [Agent Ecosystem Training](../../builder-agent/AGENT-ECOSYSTEM-TRAINING.md)
```

---

## Step 5: Create Initial Workflows

### First Workflow: Simple Action

Create at least one workflow pair to establish pattern:

**File 1: action1.toon**
```yaml
---
name: simple_action
version: 1.0.0
type: automation
description: Brief description of workflow

inputs:
  device:
    type: string
    required: false
    default: auto

stages:
  main:
    description: Main workflow stage
    duration_seconds: 10

steps:
  main:
    - name: step1
      type: ui_find
      target_text: "text"
      timeout_seconds: 5

outputs:
  success: boolean

success_criteria:
  - element_found: true

on_failure:
  - action: alert
    message: "Workflow failed"
```

**File 2: action1.md**
```markdown
---
name: Simple Action Workflow
workflow: action1.toon
version: 1.0.0
---

# Simple Action Workflow

## Purpose
[What the workflow does]

## Execution
uv run .claude/skills/[skill]/workflow/action1.py

## Parameters

### Inputs
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|

### Outputs
| Name | Type | Description |
|------|------|-------------|

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Error Handling
[Common errors and solutions]
```

### New Workflow Checklist

When adding new workflows, verify:

- [ ] [name].toon created with valid YAML syntax
- [ ] [name].md created with full documentation
- [ ] Both files have identical base names
- [ ] TOON has: inputs, stages, steps, outputs, success_criteria, on_failure
- [ ] MD has: Purpose, Prerequisites, Parameters, Phases, Success Criteria, Examples
- [ ] workflow/README.md updated with new entry
- [ ] All links verified
- [ ] No broken references

---

## Step 6: Update SKILL.md Workflows Section

### Add Workflows Entry

```yaml
workflows:
  - name: action1
    toon: workflow/action1.toon
    documentation: workflow/action1.md
    purpose: Brief description
    status: active

  - name: action2
    toon: workflow/action2.toon
    documentation: workflow/action2.md
    purpose: Brief description
    status: active

workflows_description: |
  See [Workflows](workflow/README.md) for complete documentation
  and TOON+MD pair specifications.
```

---

## Step 7: Complete SKILL.md Content

### Minimal SKILL.md Structure

```markdown
---
name: [skill-name]
description: [One-line description]
version: 1.0.0
modularized: true
scripts_enabled: true
workflows_enabled: true
tier: 2
category: [category]
last_updated: 2025-12-02
compliance_score: 100

dependencies:
  - package1>=1.0.0

auto_trigger_keywords:
  - keyword1
  - keyword2

---

# [Skill Name]

## Quick Reference

[30-second overview]

## Scripts

[Script table with descriptions]

## Workflows

[Links to workflow/README.md]

See [Workflows](workflow/README.md) for detailed documentation.

## Dependencies

[List of required packages and skills]

## Works Well With

- [Related skill 1](../[skill]/SKILL.md)
- [Related skill 2](../[skill]/SKILL.md)
```

### Keep Under 500 Lines

If SKILL.md exceeds 500 lines:

1. Move advanced content to `modules/[topic].md`
2. Link from SKILL.md: `See [Advanced Topic](modules/topic.md)`
3. Follow progressive disclosure pattern

---

## Step 8: Auto-Nesting Awareness

### Detecting Need for Nesting

After creating multiple workflows:

```bash
# Count workflows by prefix
ls -1 workflow/*.toon | sed 's/.*\///' | cut -d'_' -f1 | sort | uniq -c | sort -rn

# If any prefix has count >= 5:
#   Create subfolder with prefix name
#   Move related files into subfolder
#   Update workflow/README.md
```

### Nesting Implementation

```python
def check_and_apply_nesting(workflow_dir: Path) -> bool:
    """Check if nesting is needed and apply if so."""

    # Count files by prefix
    files = list(workflow_dir.glob("*.toon"))
    prefixes = {}

    for f in files:
        prefix = f.stem.split('_')[0]
        prefixes[prefix] = prefixes.get(prefix, 0) + 1

    # Find prefixes with >= 5 items
    need_nesting = {p: c for p, c in prefixes.items() if c >= 5}

    if not need_nesting:
        return False

    # Create subfolders and move files
    for prefix, count in need_nesting.items():
        subfolder = workflow_dir / prefix
        subfolder.mkdir(exist_ok=True)

        # Move all files with this prefix
        for f in workflow_dir.glob(f"{prefix}_*.toon"):
            f.rename(subfolder / f.name)

        for f in workflow_dir.glob(f"{prefix}_*.md"):
            f.rename(subfolder / f.name)

        # Create subfolder README.md
        # Update parent README.md with new structure

    return True
```

---

## Step 9: Documentation Verification

### Pre-Release Checklist

- [ ] SKILL.md valid Markdown
- [ ] workflow/README.md valid Markdown
- [ ] All .toon files valid YAML
- [ ] All .md files valid Markdown
- [ ] All script files valid Python
- [ ] All inter-file links verified
- [ ] No broken references
- [ ] All examples working
- [ ] Scripts have proper shebang
- [ ] Scripts have proper permissions
- [ ] Code comments in English
- [ ] No credentials in documentation
- [ ] No hardcoded paths (use relative/env vars)
- [ ] All scripts tested

### Syntax Validation

```bash
# Validate YAML in TOON files
for f in workflow/*.toon; do
  python3 -c "import yaml; yaml.safe_load(open('$f'))" || echo "ERROR: $f"
done

# Validate Markdown
# Use your favorite Markdown linter or online tool

# Validate Python scripts
python3 -m py_compile scripts/*.py
```

---

## Step 10: Final Structure Verification

After completing skill creation, verify:

### Directory Structure

```bash
tree .claude/skills/[skill-name]

# Expected:
# .claude/skills/[skill-name]/
# ├── SKILL.md
# ├── scripts/
# │   ├── __init__.py
# │   ├── action1.py
# │   └── action2.py
# └── workflow/
#     ├── README.md
#     ├── action1.toon
#     ├── action1.md
#     ├── action2.toon
#     └── action2.md
```

### File Validation

```python
def validate_skill_structure(skill_path: Path) -> bool:
    """Validate complete skill structure."""

    checks = [
        (skill_path / "SKILL.md").exists(),           # Skill metadata
        (skill_path / "scripts").is_dir(),            # Scripts folder
        (skill_path / "scripts" / "__init__.py").exists(),
        (skill_path / "workflow").is_dir(),           # Workflow folder
        (skill_path / "workflow" / "README.md").exists(),
    ]

    # Check at least one workflow pair
    toon_files = list((skill_path / "workflow").glob("*.toon"))
    md_files = list((skill_path / "workflow").glob("*.md"))

    checks.append(len(toon_files) >= 1)
    checks.append(len(md_files) >= 1)

    # Check pairing
    for toon in toon_files:
        md = (skill_path / "workflow" / toon.stem).with_suffix(".md")
        if not md.exists():
            print(f"ERROR: TOON {toon.name} missing paired MD file")
            checks.append(False)

    if all(checks):
        print(f"✓ Skill structure validated: {skill_path}")
        return True
    else:
        print(f"✗ Skill structure invalid: {skill_path}")
        return False
```

---

## Common Scenarios

### Scenario 1: Simple Utility Skill

**Example**: Screen capture utility

**Structure**:
```
skill-name/
├── SKILL.md (simple, <200 lines)
├── scripts/
│   └── capture.py (main implementation)
└── workflow/
    ├── README.md
    ├── capture.toon (orchestration)
    └── capture.md (documentation)
```

**SKILL.md**:
- Quick reference
- Script: capture.py
- Workflow: capture workflow
- Dependencies: pytesseract, opencv-python
- Works well with: other detection skills

### Scenario 2: Complex Multi-Action Skill

**Example**: Full app automation skill

**Structure**:
```
skill-name/
├── SKILL.md (comprehensive, ~400 lines)
├── scripts/
│   ├── setup.py
│   ├── login.py
│   ├── interact.py
│   └── cleanup.py
└── workflow/
    ├── README.md
    ├── setup.toon + setup.md
    ├── login/          # Nested (5+ workflows)
    │   ├── README.md
    │   ├── email.toon + email.md
    │   ├── 2fa.toon + 2fa.md
    │   └── ...
    ├── interact/       # Nested
    │   ├── README.md
    │   └── ...
```

**SKILL.md**:
- Progressive disclosure
- Scripts section (multiple scripts)
- Workflows section (links to nested organization)
- Dependencies (many packages)
- Works well with (many skills)
- Advanced patterns (modules/)

---

## Integration with Builder-Skill Workflow

When builder-skill receives SPEC to create a skill:

### Phase 1: Planning
1. Parse SPEC for skill requirements
2. Determine scripts needed
3. Plan initial workflows
4. Estimate complexity

### Phase 2: Structure Creation
1. Create directory structure (see Step 1)
2. Create SKILL.md with frontmatter (see Step 2)
3. Create initial scripts (see Step 3)
4. Create workflow/README.md (see Step 4)

### Phase 3: Implementation
1. Implement scripts in scripts/ folder
2. Create workflow pairs in workflow/ folder
3. Verify all files created
4. Validate syntax and structure

### Phase 4: Documentation
1. Complete SKILL.md content
2. Complete workflow/README.md
3. Document all scripts
4. Document all workflows

### Phase 5: Verification
1. Run validation checks (see Step 9)
2. Verify directory structure (see Step 10)
3. Test all components
4. Prepare for merge

---

## Quality Standards

### Code Quality

- [ ] Scripts follow PEP 8
- [ ] Proper type hints
- [ ] Comprehensive error handling
- [ ] Clear variable names
- [ ] Comments where needed

### Documentation Quality

- [ ] Clear and concise
- [ ] Examples are working
- [ ] Links are accurate
- [ ] Markdown valid
- [ ] YAML valid
- [ ] No typos

### Testing

- [ ] Scripts execute without errors
- [ ] Workflows have valid syntax
- [ ] Examples work as documented
- [ ] Error handling tested
- [ ] Edge cases considered

---

## Troubleshooting

### "workflows_enabled not recognized in SKILL.md"

**Cause**: Field might be in YAML frontmatter
**Solution**: Check YAML syntax, verify field name matches exactly

### "workflow/README.md is empty"

**Cause**: Initial template might be minimal
**Solution**: Add full content including workflow table and instructions

### "TOON syntax errors"

**Cause**: YAML indentation or structure issues
**Solution**: Validate YAML syntax, use online YAML validators

### "Links broken between SKILL.md and workflow/"

**Cause**: Incorrect relative paths
**Solution**: Use `workflow/README.md` not `workflow.md`, verify actual file names

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-02 | Initial version - Phase 3B implementation guide |

---

## See Also

- [Agent Ecosystem Training](../builder-agent/AGENT-ECOSYSTEM-TRAINING.md) - Comprehensive training for all builder agents
- [TOON+MD Pattern Reference](../../.moai/docs/TOON-MD-PATTERN-REFERENCE.md) - Technical TOON/MD specification
- [Skill Examples](../adb/*/SKILL.md) - Real skill examples in ADB ecosystem

---

**Status**: Active
**Audience**: builder-skill agent
**Last Updated**: 2025-12-02
