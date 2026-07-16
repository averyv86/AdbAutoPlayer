---
name: moai:create-skill-script
description: "Generate a new utility script for an existing skill"
argument-hint: "skill-name script-name [purpose]"
allowed-tools:
  - Task
  - AskUserQuestion
  - Read
model: haiku
skills: moai-foundation-core, moai-foundation-claude
---

## 📋 Pre-execution Context

!git status --porcelain
!git branch --show-current

## 📁 Essential Files

@.moai/config/config.json

---

# 🛠️ Create Skill Script

> **Architecture**: Commands → Agents → Skills. This command orchestrates through `Task()` tool.
> **Delegation Model**: Script creation delegated to `builder-skill` agent.

**Workflow Integration**: This command creates utility scripts for existing skills, following MoAI-ADK skill extension patterns.

---

## 🎯 Command Purpose

Generate a new utility script for an existing skill with proper structure, help documentation, and integration.

**Run on**: `$ARGUMENTS` (skill-name script-name [purpose])

**Variables**:
- `$1`: Target skill name (e.g., moai-foundation-core)
- `$2`: Script name to create (e.g., analyze-skill)
- `$3+`: Optional purpose description

---

## 💡 Execution Philosophy

`/moai:create-skill-script` performs script generation through agent delegation:

```
User Command: /moai:create-skill-script skill-name script-name [purpose]
    ↓
Phase 1: Verify skill exists (Read SKILL.md)
    ↓
Phase 2: Task(subagent_type="builder-skill")
    → Analyze skill structure
    → Design script interface
    → Generate script with --help
    → Update SKILL.md scripts section
    ↓
Output: Script created and documented
```

### Key Principle: DO NOT Read Existing Scripts

**IMPORTANT**: When delegating to builder-skill, instruct it to:
- ✅ Use `--help` flag to understand existing scripts
- ✅ Analyze SKILL.md for context
- ❌ NEVER read full script source code directly
- ❌ NEVER analyze implementation details

This follows the "prime agents with instruction" pattern from the MoAI architecture.

---

## 🧠 Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| builder-skill | Script generation and skill integration |
| moai-foundation-core | TRUST 5 framework and standards |
| moai-foundation-claude | Claude Code skill patterns |

---

## 🚀 PHASE 1: Skill Verification

**Goal**: Verify target skill exists and is valid

### Step 1.1: Parse Arguments

Extract command parameters:

```python
args = $ARGUMENTS.split()
skill_name = args[0] if len(args) > 0 else None
script_name = args[1] if len(args) > 1 else None
purpose = ' '.join(args[2:]) if len(args) > 2 else None
```

### Step 1.2: Validate Skill Exists

Use Read tool to verify skill:

```yaml
Tool: Read
Parameters:
  file_path: ".claude/skills/{skill_name}/SKILL.md"
```

If skill doesn't exist, report error and suggest available skills.

### Step 1.3: Clarify Requirements (if needed)

If script name or purpose is missing, use AskUserQuestion:

```python
AskUserQuestion({
    "questions": [{
        "question": "What should the script do?",
        "header": "Script Purpose",
        "multiSelect": false,
        "options": [
            {
                "label": "Analysis/Validation",
                "description": "Analyze skill structure or validate content"
            },
            {
                "label": "Conversion/Migration",
                "description": "Convert or migrate skill data"
            },
            {
                "label": "Maintenance/Cleanup",
                "description": "Maintain or clean up skill files"
            },
            {
                "label": "Testing/Development",
                "description": "Test skill behavior or assist development"
            }
        ]
    }]
})
```

---

## 🚀 PHASE 2: Script Generation

**Goal**: Delegate script creation to builder-skill agent

### Step 2.1: Delegate to builder-skill

Use Task tool with clear instructions:

```yaml
Tool: Task
Parameters:
- subagent_type: "builder-skill"
- description: "Generate utility script for existing skill"
- prompt: """You are the builder-skill agent acting as a script generator.

**Task**: Create a new utility script for an existing skill.

**Context**:
- Skill Name: {skill_name}
- Script Name: {script_name}
- Purpose: {purpose}
- Conversation Language: {{CONVERSATION_LANGUAGE}}

**CRITICAL INSTRUCTION - DO NOT Read Existing Scripts**:
- Use ONLY --help flags to understand existing scripts
- Example: `uv run .claude/skills/{skill_name}/scripts/existing.py --help`
- NEVER read full source code of existing scripts
- Analyze SKILL.md for context instead

**Instructions**:

1. **Analyze Skill Structure**:
   - Read SKILL.md to understand skill purpose
   - Check scripts/ directory (if it exists)
   - Use --help to understand existing script patterns (DO NOT read source)

2. **Design Script Interface**:
   - Script name: {script_name}.py
   - Location: .claude/skills/{skill_name}/scripts/{script_name}.py
   - Include argparse with --help documentation
   - Follow Python CLI best practices

3. **Generate Script**:
   - Implement purpose: {purpose}
   - Add comprehensive --help text
   - Include error handling
   - Add usage examples in help
   - Follow TRUST 5 principles (readable, testable)

4. **Update SKILL.md**:
   - Add script entry to Scripts section
   - Document usage and purpose
   - Include example command

5. **Report Result**:
   - Script path created
   - Test command with --help
   - Verification steps

**Important**:
- Use conversation_language for user messages
- NO EMOJIS in AskUserQuestion options
- Ensure script is executable (chmod +x)
"""
```

---

## 🎯 Summary: Execution Checklist

Before completing this command, verify:

- [ ] **Skill Verified**: Target skill exists and SKILL.md is valid
- [ ] **Arguments Parsed**: Skill name, script name, and purpose extracted
- [ ] **Agent Delegated**: builder-skill agent was invoked with clear instructions
- [ ] **Script Created**: New script exists in .claude/skills/{skill_name}/scripts/
- [ ] **Help Works**: `--help` flag displays proper documentation
- [ ] **SKILL.md Updated**: Script is documented in skill reference

---

## 📚 Quick Reference

| Scenario | Command | Expected Outcome |
|----------|---------|------------------|
| Analysis script | `/moai:create-skill-script moai-foundation-core analyze-structure` | Script analyzes skill file structure |
| Validation script | `/moai:create-skill-script my-skill validate` | Script validates skill compliance |
| Cleanup script | `/moai:create-skill-script my-skill cleanup` | Script removes temporary files |
| With purpose | `/moai:create-skill-script my-skill helper "Extract code examples"` | Script with specific purpose |

**Script Standards**:
- **Location**: `.claude/skills/{skill-name}/scripts/{script-name}.py`
- **Format**: Python with argparse
- **Help**: Comprehensive `--help` documentation
- **Executable**: `chmod +x` applied automatically
- **Documentation**: Entry added to SKILL.md

**Testing**:
```bash
# Verify script works
uv run .claude/skills/{skill-name}/scripts/{script-name}.py --help

# Run script
uv run .claude/skills/{skill-name}/scripts/{script-name}.py [args]
```

**Version**: 1.0.0
**Last Updated**: 2025-11-30
**Architecture**: Commands → Agents → Skills (Complete delegation)

---

## Final Step: Next Action Selection

After script creation completes, use AskUserQuestion tool to guide user to next action:

```python
AskUserQuestion({
    "questions": [{
        "question": "Script created successfully. What would you like to do next?",
        "header": "Next Steps",
        "multiSelect": false,
        "options": [
            {
                "label": "Test Script",
                "description": "Run the script with --help to verify functionality"
            },
            {
                "label": "Create Another Script",
                "description": "Add another utility script to the skill"
            },
            {
                "label": "Update Documentation",
                "description": "Add detailed usage examples to SKILL.md"
            },
            {
                "label": "Continue Development",
                "description": "Return to main workflow"
            }
        ]
    }]
})
```

**Important**:
- Use conversation language from config
- No emojis in any AskUserQuestion fields
- Always provide clear next step options

---

## ⚡️ EXECUTION DIRECTIVE

**You must NOW execute the command following the "Execution Philosophy" described above.**

1. Parse `$ARGUMENTS` to extract skill-name and script-name.
2. Read the target skill's SKILL.md to verify it exists.
3. Call the `Task` tool with `subagent_type="builder-skill"`.
4. **CRITICAL**: Instruct builder-skill to use `--help` only, NEVER read existing script source.
5. Do NOT just describe what you will do. DO IT.
