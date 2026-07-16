---
name: builder:workflow-designer
description: "Create SPEC documents and workflow diagrams from analysis reports"
argument-hint: "[analysis-report-path | 'interactive']"
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

# Workflow Designer

> **Architecture**: Commands → Agents → Skills. This command orchestrates through `Task()` tool.
> **Delegation Model**: SPEC creation delegated to `builder-workflow-designer` agent.

**Workflow Integration**: Second step in builder ecosystem pipeline - creates SPECs and diagrams from analysis reports.

---

## Command Purpose

Transform repository analysis into actionable artifacts:
- EARS-style SPEC documents
- Workflow diagrams (Mermaid)
- Agent coordination patterns
- Implementation roadmaps

**Run on**: `$ARGUMENTS` (analysis-report-path or 'interactive')

**Variables**:
- `$1`: Path to analysis report or 'interactive' for guided mode

---

## Execution Philosophy

`/builder:workflow-designer` creates SPECs through agent delegation:

```
User Command: /builder:workflow-designer [analysis-report]
    ↓
Phase 1: Load analysis report
    ↓
Phase 2: Task(subagent_type="builder-workflow-designer")
    → Parse analysis findings
    → Design workflow patterns
    → Create SPEC document
    → Generate diagrams
    ↓
Output: SPEC + Workflow diagrams
```

---

## Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| builder-workflow-designer | SPEC creation and diagram generation |
| builder-reverse-engineer | Provides analysis input |
| manager-spec | SPEC document standards |
| moai-library-mermaid | Diagram generation |

---

## PHASE 1: Analysis Input

**Goal**: Load or gather analysis data

### Step 1.1: Parse Arguments

```python
args = $ARGUMENTS.strip()
if args == 'interactive' or not args:
    mode = 'interactive'
else:
    analysis_path = args
    mode = 'report'
```

### Step 1.2: Interactive Mode

If no report provided, use AskUserQuestion:

```python
AskUserQuestion({
    "questions": [{
        "question": "How would you like to provide the analysis input?",
        "header": "Input Source",
        "multiSelect": false,
        "options": [
            {
                "label": "Recent Analysis",
                "description": "Use most recent analysis report from .moai/reports/"
            },
            {
                "label": "Specify Path",
                "description": "Provide path to existing analysis report"
            },
            {
                "label": "Run Analysis First",
                "description": "Run /builder:reverse-engineer first"
            },
            {
                "label": "Manual Input",
                "description": "Describe workflow requirements directly"
            }
        ]
    }]
})
```

---

## PHASE 2: SPEC & Diagram Creation

**Goal**: Generate SPEC documents and workflow diagrams

### Step 2.1: Delegate to builder-workflow-designer

```yaml
Tool: Task
Parameters:
- subagent_type: "builder-workflow-designer"
- description: "Create SPEC and workflow diagrams"
- prompt: """You are the builder-workflow-designer agent creating implementation specifications.

**Task**: Create SPEC document and workflow diagrams from analysis.

**Context**:
- Analysis Input: {analysis_content}
- Conversation Language: {{CONVERSATION_LANGUAGE}}

**Instructions**:

1. **Parse Analysis Findings**
   - Extract automation opportunities
   - Identify skill/agent candidates
   - Prioritize by value/effort ratio

2. **Design Workflow Patterns**
   - Define agent coordination flow
   - Establish dependency chains
   - Plan parallel execution opportunities

3. **Create EARS-style SPEC**
   - Title and summary
   - Requirements (When/If/While patterns)
   - Acceptance criteria
   - Test scenarios
   - Implementation notes

4. **Generate Mermaid Diagrams**
   - Workflow sequence diagram
   - Component interaction diagram
   - State transition diagram (if applicable)

**Output Structure**:

```markdown
# SPEC-XXX: [Title]

## Summary
[Brief description of the workflow]

## Requirements

### Functional Requirements
- **REQ-001**: When [condition], the system shall [action]
- **REQ-002**: If [condition], then [action]

### Non-Functional Requirements
- Performance: [criteria]
- Security: [criteria]

## Workflow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Agent1
    participant Agent2
    ...
```

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Implementation Notes
[Technical details and considerations]
```
"""
```

---

## Summary: Execution Checklist

- [ ] **Analysis Loaded**: Input data available
- [ ] **Agent Delegated**: builder-workflow-designer invoked
- [ ] **SPEC Created**: EARS-style document generated
- [ ] **Diagrams Generated**: Mermaid workflow diagrams
- [ ] **File Saved**: SPEC saved to .moai/specs/

---

## Quick Reference

| Scenario | Command | Expected Outcome |
|----------|---------|------------------|
| From report | `/builder:workflow-designer ./analysis.md` | SPEC from existing analysis |
| Interactive | `/builder:workflow-designer` | Guided SPEC creation |
| Recent | `/builder:workflow-designer recent` | Use most recent analysis |

**Output Location**: `.moai/specs/SPEC-XXX/`

---

## Final Step: Next Action Selection

```python
AskUserQuestion({
    "questions": [{
        "question": "SPEC document created. What would you like to do next?",
        "header": "Next Steps",
        "multiSelect": false,
        "options": [
            {
                "label": "Implement with TDD",
                "description": "Run /moai:2-run to start implementation"
            },
            {
                "label": "Generate Skills",
                "description": "Create skill structures from SPEC"
            },
            {
                "label": "Generate Scripts",
                "description": "Create UV scripts from SPEC"
            },
            {
                "label": "Review SPEC",
                "description": "Display SPEC for review and refinement"
            }
        ]
    }]
})
```

---

## EXECUTION DIRECTIVE

**You must NOW execute the command following the "Execution Philosophy" described above.**

1. Parse `$ARGUMENTS` to determine input mode.
2. Load analysis report or gather requirements.
3. Call the `Task` tool with `subagent_type="builder-workflow-designer"`.
4. Save SPEC to .moai/specs/.
5. Offer next step options via AskUserQuestion.

**Version**: 1.0.0
**Last Updated**: 2025-12-01
