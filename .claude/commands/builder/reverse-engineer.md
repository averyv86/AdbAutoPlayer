---
name: builder:reverse-engineer
description: "Analyze repository to extract patterns, conventions, and automation opportunities"
argument-hint: "[repo-path | github-url]"
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

# Repository Reverse Engineering

> **Architecture**: Commands → Agents → Skills. This command orchestrates through `Task()` tool.
> **Delegation Model**: Analysis delegated to `builder-reverse-engineer` agent.

**Workflow Integration**: First step in builder ecosystem pipeline - analyzes repositories to identify automation opportunities.

---

## Command Purpose

Analyze a repository (local path or GitHub URL) to extract:
- Project structure and file organization
- Technology stack and dependencies
- Design patterns and conventions
- Automation opportunities (UV script candidates)
- Skill candidates for extraction
- Agent candidates for orchestration

**Run on**: `$ARGUMENTS` (repo-path or github-url)

**Variables**:
- `$1`: Repository path or GitHub URL

---

## Execution Philosophy

`/builder:reverse-engineer` performs repository analysis through agent delegation:

```
User Command: /builder:reverse-engineer [repo-path]
    ↓
Phase 1: Validate repository access
    ↓
Phase 2: Task(subagent_type="builder-reverse-engineer")
    → Scan structure (6-phase analysis)
    → Identify technology stack
    → Extract patterns
    → Find automation opportunities
    → Create generation plan
    ↓
Output: TOON-formatted analysis report
```

---

## Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| builder-reverse-engineer | Repository analysis and pattern extraction |
| builder-workflow-designer | SPEC/diagram creation from analysis |
| moai-foundation-core | TRUST 5 framework and standards |
| moai-library-toon | TOON format for token-efficient output |

---

## PHASE 1: Repository Validation

**Goal**: Validate repository exists and is accessible

### Step 1.1: Parse Arguments

Extract repository path:

```python
args = $ARGUMENTS.strip()
repo_path = args if args else None
```

### Step 1.2: Validate Repository

If local path:
- Check directory exists
- Verify it contains code files

If GitHub URL:
- Validate URL format
- Check repository accessibility

### Step 1.3: Clarify if Missing

If no path provided, use AskUserQuestion:

```python
AskUserQuestion({
    "questions": [{
        "question": "Which repository would you like to analyze?",
        "header": "Repository",
        "multiSelect": false,
        "options": [
            {
                "label": "Current Directory",
                "description": "Analyze the current project"
            },
            {
                "label": "Specify Path",
                "description": "Provide a local path to analyze"
            },
            {
                "label": "GitHub URL",
                "description": "Analyze a GitHub repository"
            }
        ]
    }]
})
```

---

## PHASE 2: Repository Analysis

**Goal**: Delegate full analysis to builder-reverse-engineer agent

### Step 2.1: Delegate to builder-reverse-engineer

Use Task tool with analysis instructions:

```yaml
Tool: Task
Parameters:
- subagent_type: "builder-reverse-engineer"
- description: "Analyze repository for patterns and automation opportunities"
- prompt: """You are the builder-reverse-engineer agent performing repository analysis.

**Task**: Perform 6-phase repository analysis.

**Context**:
- Repository Path: {repo_path}
- Conversation Language: {{CONVERSATION_LANGUAGE}}

**Instructions**:

1. **Phase 1: Structure Scan**
   - Scan directory structure
   - Identify key files (README, package.json, pyproject.toml, etc.)
   - Count files by type

2. **Phase 2: Technology Stack Identification**
   - Detect primary language
   - Identify frameworks
   - List dependencies with versions

3. **Phase 3: Pattern Extraction**
   - Detect architecture patterns (MVC, Clean Architecture, etc.)
   - Identify design patterns (Repository, Factory, Service)
   - Extract naming conventions

4. **Phase 4: Automation Opportunity Discovery**
   - Find CLI automation candidates
   - Identify repetitive tasks
   - Suggest UV script opportunities

5. **Phase 5: Generation Candidate Assessment**
   - Assess skill candidates
   - Assess agent candidates
   - Assess script candidates

6. **Phase 6: Generation Plan Creation**
   - Prioritize generation targets
   - Create execution order
   - Estimate effort

**Output Format**: TOON format for 40-60% token savings

**Report Structure**:
```toon
# Repository Analysis Report

## Structure Summary
files[N]{path,type,lines,importance}:
...

## Technology Stack
stack{language,version,frameworks,deps}:
...

## Patterns Detected
patterns[M]{category,name,confidence,files}:
...

## Automation Opportunities
automation[K]{type,name,value,effort}:
...

## Generation Plan
skills[S]{name,tier,priority}:
...
agents[A]{name,type,priority}:
...
scripts[C]{name,skill,priority}:
...
```
"""
```

---

## Summary: Execution Checklist

Before completing this command, verify:

- [ ] **Repository Validated**: Path exists and is accessible
- [ ] **Agent Delegated**: builder-reverse-engineer invoked with clear instructions
- [ ] **6-Phase Analysis**: All phases completed
- [ ] **TOON Output**: Report in token-efficient format
- [ ] **Generation Plan**: Clear prioritized list of candidates

---

## Quick Reference

| Scenario | Command | Expected Outcome |
|----------|---------|------------------|
| Local repo | `/builder:reverse-engineer ./my-project` | Full analysis of local project |
| GitHub repo | `/builder:reverse-engineer https://github.com/owner/repo` | Analysis of GitHub repository |
| Current dir | `/builder:reverse-engineer .` | Analyze current working directory |

**Output Location**: `.moai/reports/analysis-{repo-name}-{timestamp}.md`

**Next Steps After Analysis**:
1. `/builder:workflow-designer` - Create SPECs from analysis
2. `/builder:generate-skill` - Generate identified skill candidates
3. `/builder:generate-script` - Create UV scripts

---

## Final Step: Next Action Selection

After analysis completes, use AskUserQuestion:

```python
AskUserQuestion({
    "questions": [{
        "question": "Repository analysis complete. What would you like to do next?",
        "header": "Next Steps",
        "multiSelect": false,
        "options": [
            {
                "label": "Create SPEC",
                "description": "Use builder-workflow-designer to create SPEC from analysis"
            },
            {
                "label": "Generate Skills",
                "description": "Generate identified skill candidates"
            },
            {
                "label": "Generate Scripts",
                "description": "Create UV scripts from automation opportunities"
            },
            {
                "label": "View Full Report",
                "description": "Display detailed analysis report"
            }
        ]
    }]
})
```

---

## EXECUTION DIRECTIVE

**You must NOW execute the command following the "Execution Philosophy" described above.**

1. Parse `$ARGUMENTS` to extract repository path.
2. Validate repository exists and is accessible.
3. Call the `Task` tool with `subagent_type="builder-reverse-engineer"`.
4. Report analysis results to user.
5. Offer next step options via AskUserQuestion.

**Version**: 1.0.0
**Last Updated**: 2025-12-01
