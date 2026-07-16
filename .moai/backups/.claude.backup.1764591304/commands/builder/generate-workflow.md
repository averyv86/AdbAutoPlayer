---
name: builder:generate-workflow
description: "Generate complete workflow with skill, agents, and scripts from analysis"
argument-hint: "[workflow-name] [source-analysis | 'interactive']"
allowed-tools:
  - Task
  - AskUserQuestion
  - Read
model: haiku
skills: moai-foundation-core, builder-workflow
---

## Pre-execution Context

!git status --porcelain
!git branch --show-current

## Essential Files

@.moai/config/config.json

---

# Generate Complete Workflow

> **Architecture**: Commands → Agents → Skills. This command orchestrates through `Task()` tool.
> **Delegation Model**: Full workflow generation through multiple builder agents.

**Workflow Integration**: End-to-end workflow generation combining skills, agents, and UV scripts.

---

## Command Purpose

Generate complete workflow ecosystem:
- New skill with SKILL.md
- Agent definitions (if needed)
- UV CLI scripts
- Integration configuration
- Documentation

**Run on**: `$ARGUMENTS` (workflow-name [source-analysis])

**Variables**:
- `$1`: Workflow name
- `$2`: Optional path to analysis report or 'interactive'

---

## Execution Philosophy

`/builder:generate-workflow` orchestrates multiple agents:

```
User Command: /builder:generate-workflow [name] [source]
    ↓
Phase 1: Gather requirements
    ↓
Phase 2: Design workflow architecture
    ↓
Phase 3: Generate skill structure
    → Task(subagent_type="builder-skill")
    ↓
Phase 4: Generate agent definitions (if needed)
    → Task(subagent_type="builder-agent")
    ↓
Phase 5: Generate UV scripts
    → Task(subagent_type="builder-workflow")
    ↓
Phase 6: Integration & documentation
    ↓
Output: Complete workflow ecosystem
```

---

## Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| builder-reverse-engineer | Analysis input (optional) |
| builder-workflow-designer | Architecture design |
| builder-skill | Skill structure creation |
| builder-agent | Agent definition creation |
| builder-workflow | UV script generation |

---

## PHASE 1: Requirements Gathering

**Goal**: Understand workflow requirements

### Step 1.1: Parse Arguments

```python
args = $ARGUMENTS.split(maxsplit=1)
workflow_name = args[0] if len(args) > 0 else None
source = args[1] if len(args) > 1 else 'interactive'
```

### Step 1.2: Clarify Requirements

```python
AskUserQuestion({
    "questions": [
        {
            "question": "What is the primary purpose of this workflow?",
            "header": "Workflow Purpose",
            "multiSelect": false,
            "options": [
                {
                    "label": "Automation",
                    "description": "Automate repetitive tasks or processes"
                },
                {
                    "label": "Integration",
                    "description": "Connect external services or APIs"
                },
                {
                    "label": "Analysis",
                    "description": "Analyze data, code, or systems"
                },
                {
                    "label": "Generation",
                    "description": "Generate code, content, or artifacts"
                }
            ]
        },
        {
            "question": "What components should be included?",
            "header": "Components",
            "multiSelect": true,
            "options": [
                {
                    "label": "Skill",
                    "description": "Create new skill with SKILL.md"
                },
                {
                    "label": "Agent",
                    "description": "Create agent definition"
                },
                {
                    "label": "Scripts",
                    "description": "Create UV CLI scripts"
                },
                {
                    "label": "Commands",
                    "description": "Create slash commands"
                }
            ]
        }
    ]
})
```

---

## PHASE 2: Architecture Design

**Goal**: Design workflow component architecture

### Step 2.1: Component Planning

Based on requirements, determine:
- Skill structure and tier
- Agent type (expert, manager, builder)
- Script count and purposes
- Command interfaces

### Step 2.2: Delegate Architecture Design

```yaml
Tool: Task
Parameters:
- subagent_type: "builder-workflow-designer"
- description: "Design workflow architecture"
- prompt: """Design component architecture for workflow: {workflow_name}

**Requirements**: {gathered_requirements}

**Output**:
1. Skill structure (name, tier, capabilities)
2. Agent definition (if needed: name, type, tools)
3. Script list (names, purposes, dependencies)
4. Command interfaces (if needed)
5. Integration points
"""
```

---

## PHASE 3-5: Component Generation

**Goal**: Generate all workflow components

### Step 3.1: Generate Skill

```yaml
Tool: Task
Parameters:
- subagent_type: "builder-skill"
- prompt: "Create skill: {skill_definition}"
```

### Step 4.1: Generate Agent (if needed)

```yaml
Tool: Task
Parameters:
- subagent_type: "builder-agent"
- prompt: "Create agent: {agent_definition}"
```

### Step 5.1: Generate Scripts

```yaml
Tool: Task
Parameters:
- subagent_type: "builder-workflow"
- prompt: "Create scripts: {script_definitions}"
```

---

## PHASE 6: Integration

**Goal**: Ensure all components work together

### Step 6.1: Verify Integration

- Test skill loading
- Verify agent invocation
- Run script --help
- Check command registration

### Step 6.2: Generate Documentation

Create workflow documentation:
- README in workflow directory
- Usage examples
- Integration guide

---

## Summary: Execution Checklist

- [ ] **Requirements Gathered**: Clear workflow purpose and components
- [ ] **Architecture Designed**: Component structure planned
- [ ] **Skill Generated**: SKILL.md created
- [ ] **Agent Generated**: Agent definition created (if needed)
- [ ] **Scripts Generated**: UV scripts created
- [ ] **Integration Verified**: All components work together
- [ ] **Documentation Created**: Usage guide available

---

## Quick Reference

| Scenario | Command | Expected Outcome |
|----------|---------|------------------|
| Interactive | `/builder:generate-workflow api-testing` | Guided workflow creation |
| From analysis | `/builder:generate-workflow api-testing ./analysis.md` | Workflow from analysis |
| Simple | `/builder:generate-workflow simple-automation` | Minimal workflow |

**Output Locations**:
- Skill: `.claude/skills/{workflow-name}/`
- Agent: `.claude/agents/moai/moai-{type}/{agent-name}.md`
- Scripts: `.claude/skills/{workflow-name}/scripts/`
- Commands: `.claude/commands/{namespace}/`

---

## Workflow Generation Pipeline

```
┌─────────────────────────────┐
│   Requirements Gathering    │
│   (AskUserQuestion)         │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│   Architecture Design       │
│   (builder-workflow-designer)│
└──────────────┬──────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Skill  │ │ Agent  │ │Scripts │
│builder │ │builder │ │builder │
│-skill  │ │-agent  │ │-workflow│
└────┬───┘ └────┬───┘ └────┬───┘
     │          │          │
     └──────────┼──────────┘
                │
                ▼
┌─────────────────────────────┐
│   Integration & Testing     │
│   (Verification)            │
└─────────────────────────────┘
```

---

## Final Step: Workflow Summary

After generation completes:

```python
AskUserQuestion({
    "questions": [{
        "question": "Workflow generated successfully. What would you like to do next?",
        "header": "Next Steps",
        "multiSelect": false,
        "options": [
            {
                "label": "Test Workflow",
                "description": "Run scripts and verify functionality"
            },
            {
                "label": "Add More Scripts",
                "description": "Generate additional UV scripts"
            },
            {
                "label": "Create Documentation",
                "description": "Generate detailed usage documentation"
            },
            {
                "label": "Continue Development",
                "description": "Return to main workflow"
            }
        ]
    }]
})
```

---

## EXECUTION DIRECTIVE

**You must NOW execute the command following the "Execution Philosophy" described above.**

1. Parse `$ARGUMENTS` to extract workflow-name and source.
2. Gather requirements via AskUserQuestion.
3. Design architecture via builder-workflow-designer.
4. Generate components via builder-skill, builder-agent, builder-workflow.
5. Verify integration and test components.
6. Report results and offer next steps.

**Version**: 1.0.0
**Last Updated**: 2025-12-01
