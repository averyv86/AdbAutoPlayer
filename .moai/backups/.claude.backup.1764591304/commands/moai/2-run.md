---
name: moai:2-run
description: "Execute TDD implementation cycle"
argument-hint: 'SPEC-ID - All with SPEC ID to implement (e.g. SPEC-001) or all "SPEC Implementation"'
allowed-tools:
  - Task
  - AskUserQuestion
  - TodoWrite
model: sonnet
skills: moai-toolkit-essentials, moai-foundation-quality, moai-lang-unified
---

## 📋 Pre-execution Context

!git status --porcelain
!git branch --show-current
!git log --oneline -5
!git diff --name-only HEAD

## 📁 Essential Files

@.moai/config/config.json
@.moai/specs/
@.moai/workflows/

---

## 🔄 Workflow System Integration

Before executing traditional TDD cycle, check for custom workflow:

1. **Check**: `.moai/workflows/$ARGUMENTS/WORKFLOW.toon` exists?
2. **If EXISTS**: Execute via workflow engine (builder-workflow-designer agent)
3. **If NOT**: Use default TDD cycle (Phase 1-4 below)

**Workflow Detection Flow**:
```
/moai:2-run SPEC-001
    ↓
Check: .moai/workflows/SPEC-001/WORKFLOW.toon
    ↓
Exists? → Task(subagent_type="builder-workflow-designer", prompt="Execute SPEC-001 workflow")
    ↓
Not exists? → Traditional Phase 1-4 (manager-strategy → manager-tdd → manager-quality → manager-git)
```

**Benefits**:
- ✅ **Custom workflows**: Execute complex multi-domain features with parallel agents
- ✅ **Backward compatible**: No workflow → default TDD cycle
- ✅ **TOON efficiency**: 60-70% token reduction for workflow definitions
- ✅ **Dynamic parallelism**: 1-10 agents based on complexity

---

# ⚒️ MoAI-ADK Step 2: Execute Implementation (Run) - TDD Implementation

> **Architecture**: Commands → Agents → Skills. This command orchestrates ONLY through `Task()` tool.
>
> **Delegation Model**: Phase-based sequential agent delegation. Command orchestrates 4 phases directly.

**Workflow**: Phase 1 → Analysis & Planning → Phase 2 → TDD Implementation → Phase 3 → Git Operations → Phase 4 → Completion & Guidance.

---

## 🎯 Command Purpose

Execute TDD implementation of SPEC requirements through complete agent delegation.

The `/moai:2-run` command orchestrates the complete implementation workflow:

1. **Phase 1**: SPEC analysis and execution plan creation
2. **Phase 2**: TDD implementation (RED → GREEN → REFACTOR)
3. **Phase 3**: Git commit management
4. **Phase 4**: Completion and next steps guidance

**Run on**: `$ARGUMENTS` (SPEC ID, e.g., SPEC-001)

---

## 💡 Execution Philosophy: "Plan → Run → Sync"

`/moai:2-run` performs SPEC implementation through phase-based sequential agent delegation:

```
User Command: /moai:2-run SPEC-001
    ↓
Phase 1: Task(subagent_type="manager-strategy")
    → SPEC Analysis & Execution Plan Creation
    ↓
Phase 2: Task(subagent_type="manager-tdd")
    → RED → GREEN → REFACTOR TDD Cycle
    ↓
Phase 2.5: Task(subagent_type="manager-quality")
    → TRUST 5 Quality Validation
    ↓
Phase 3: Task(subagent_type="manager-git")
    → Commit Creation & Git Operations
    ↓
Phase 4: AskUserQuestion(...)
    → Completion Summary & Next Steps Guidance
    ↓
Output: Implemented feature with passing tests and commits
```

### Key Principle: Zero Direct Tool Usage

**This command uses ONLY these tools:**

- ✅ **Task()** for phase agent delegation (manager-strategy → manager-tdd → manager-quality → manager-git)
- ✅ **AskUserQuestion()** for user approval and next steps
- ✅ **TodoWrite()** for task tracking
- ❌ No Read/Write/Edit/Bash (all delegated to agents)

Command orchestrates phases sequentially; agents handle complexity.

---

## 🧠 Associated Agents & Skills

| Agent/Skill | Purpose |
|------------|---------|
| manager-strategy | Analyzes SPEC and creates execution strategy |
| manager-tdd | Implements code through TDD cycle (RED-GREEN-REFACTOR) |
| manager-quality | Verifies TRUST 5 principles and validates quality |
| manager-git | Creates and manages Git commits |
| moai-alfred-workflow | Workflow orchestration patterns |
| moai-alfred-todowrite-pattern | Task tracking and progress management |
| moai-alfred-ask-user-questions | User interaction patterns |
| moai-alfred-reporting | Result reporting and summaries |

---

## 🚀 Phase Execution Details

### Phase 1: Analysis & Planning

Command calls `Task(subagent_type="manager-strategy")`:

1. Agent reads SPEC document
2. Analyzes requirements and creates execution strategy
3. Returns plan for user approval
4. Waits for user confirmation (proceed/modify/postpone)
5. Stores plan context for Phase 2

### Phase 2: TDD Implementation

Command calls `Task(subagent_type="manager-tdd")`:

1. Agent initializes task tracking (TodoWrite)
2. Checks domain readiness (if multi-domain SPEC)
3. Executes RED → GREEN → REFACTOR cycle
4. Returns implementation results and coverage metrics

### Phase 2.5: Quality Validation

Command calls `Task(subagent_type="manager-quality")`:

1. Agent verifies TRUST 5 principles (Test-first, Readable, Unified, Secured, Trackable)
2. Validates test coverage (>= 85%)
3. Checks security compliance
4. Returns quality assessment (PASS/WARNING/CRITICAL)

### Phase 3: Git Operations

Command calls `Task(subagent_type="manager-git")`:

1. Agent creates feature branch if needed
2. Creates commits with implementation changes
3. Verifies commits were successful
4. Returns commit summary

### Phase 4: Completion & Guidance

Command calls `AskUserQuestion()`:

1. Displays implementation summary
2. Shows next action options
3. Guides user to `/moai:3-sync` or additional features

---

## 📋 Execution Flow (High-Level)

```
/moai:2-run SPEC-XXX
    ↓
Parse SPEC ID from $ARGUMENTS
    ↓
✅ Phase 1: Task(subagent_type="manager-strategy")
    → Analyze SPEC → Create execution plan → Get approval
    ↓
✅ Phase 2: Task(subagent_type="manager-tdd")
    → RED-GREEN-REFACTOR → Tests passing → Coverage verified
    ↓
✅ Phase 2.5: Task(subagent_type="manager-quality")
    → Validate TRUST 5 principles → Return quality status
    ↓
✅ Phase 3: Task(subagent_type="manager-git")
    → Create feature branch → Commit changes → Verify commits
    ↓
✅ Phase 4: AskUserQuestion(...)
    → Display summary → Guide next steps → Offer options
    ↓
Output: "Implementation complete. Next step: /moai:3-sync"
```

---

## 🎯 Command Implementation

### Sequential Phase Execution with Resume Chain

**Command implementation flow (with Resume for context continuity):**

```
# Phase 1: SPEC Analysis & Planning
plan_result = Task(
  subagent_type="manager-strategy",
  description="Analyze SPEC-$ARGUMENTS and create execution plan",
  prompt="""
SPEC ID: $ARGUMENTS

Analyze this SPEC and create detailed execution plan:
1. Extract requirements and success criteria
2. Identify implementation phases and tasks
3. Determine tech stack and dependencies
4. Estimate complexity and effort
5. Create step-by-step execution strategy
6. Present plan for user approval
"""
)

# Store agent ID for resume chain
$PLANNER_AGENT_ID = plan_result.metadata.agent_id

# Log Phase 1 checkpoint
Log to .moai/logs/phase-checkpoints.json:
  phase: 1
  agent_id: $PLANNER_AGENT_ID
  status: "PLANNING_COMPLETE"
  timestamp: NOW()

# User approval checkpoint
approval = AskUserQuestion({
    "question": "Does this execution plan look good?",
    "header": "Plan Review",
    "multiSelect": false,
    "options": [
        {"label": "Proceed with plan", "description": "Start implementation"},
        {"label": "Modify plan", "description": "Request changes"},
        {"label": "Postpone", "description": "Stop here, continue later"}
    ]
})

# Phase 2: TDD Implementation (Resume from Phase 1)
if approval == "Proceed with plan":
    implementation_result = Task(
        subagent_type="manager-tdd",
        resume="$PLANNER_AGENT_ID",  # ⭐ Resume: Inherit planning context
        description="Implement SPEC-$ARGUMENTS using TDD cycle",
        prompt="""
SPEC ID: $ARGUMENTS

You are the manager-tdd agent. You are continuing from the implementation plan created in Phase 1.

The full planning context (analysis, decisions, architecture) is inherited from previous phase via resume.
Use this context to proceed directly to implementation without re-analyzing requirements.

Execute complete TDD implementation:
1. Write failing tests (RED phase)
2. Implement minimal code (GREEN phase)
3. Refactor for quality (REFACTOR phase)
4. Ensure test coverage >= 85%
5. Verify all tests passing
6. Return implementation summary
"""
    )

    # Store agent ID for next phase
    $IMPL_AGENT_ID = implementation_result.metadata.agent_id

    # Log Phase 2 checkpoint
    Log to .moai/logs/phase-checkpoints.json:
      phase: 2
      agent_id: $IMPL_AGENT_ID
      resumed_from: $PLANNER_AGENT_ID
      status: "IMPLEMENTATION_COMPLETE"
      timestamp: NOW()

    # Phase 2.5: Quality Validation (Resume from Phase 1)
    quality_result = Task(
        subagent_type="manager-quality",
        resume="$PLANNER_AGENT_ID",  # ⭐ Resume: Keep full context chain
        description="Validate TRUST 5 compliance for SPEC-$ARGUMENTS",
        prompt="""
SPEC ID: $ARGUMENTS

You are the manager-quality agent. You are continuing from the implementation context.

The full context (planning, implementation results) is inherited from previous phases via resume.
This ensures quality validation has complete architectural and implementation context.

Validate implementation against TRUST 5 principles:
- T: Test-first (tests exist and pass)
- R: Readable (code is clear and documented)
- U: Unified (follows project patterns)
- S: Secured (no security vulnerabilities)
- T: Trackable (changes are logged and traceable)

Return quality assessment with specific findings.
"""
    )

    # Store agent ID for next phase
    $QA_AGENT_ID = quality_result.metadata.agent_id

    # Log Phase 2.5 checkpoint
    Log to .moai/logs/phase-checkpoints.json:
      phase: "2.5"
      agent_id: $QA_AGENT_ID
      resumed_from: $PLANNER_AGENT_ID
      status: quality_result.status
      timestamp: NOW()

    # Phase 3: Git Operations (Resume from Phase 1)
    if quality_result.status == "PASS" or quality_result.status == "WARNING":
        git_result = Task(
            subagent_type="manager-git",
            resume="$PLANNER_AGENT_ID",  # ⭐ Resume: Maintain full feature context
            description="Create commits for SPEC-$ARGUMENTS implementation",
            prompt="""
SPEC ID: $ARGUMENTS

You are the manager-git agent. You are continuing from the full implementation context.

The complete context (planning, implementation, quality review) is inherited via resume.
This context enables creation of meaningful commit messages with full understanding of feature scope and design decisions.

Create git commits for implementation:
1. Create feature branch: feature/SPEC-$ARGUMENTS
2. Stage all relevant files
3. Create meaningful commits (follow conventional commits, use context for descriptions)
4. Verify commits created successfully
5. Return commit summary with SHA references
"""
        )

        # Store agent ID for reference
        $GIT_AGENT_ID = git_result.metadata.agent_id

        # Log Phase 3 checkpoint
        Log to .moai/logs/phase-checkpoints.json:
          phase: 3
          agent_id: $GIT_AGENT_ID
          resumed_from: $PLANNER_AGENT_ID
          status: "GIT_OPERATIONS_COMPLETE"
          commit_shas: git_result.commits
          timestamp: NOW()

        # Phase 4: Completion & Guidance
        next_steps = AskUserQuestion({
            "question": "Implementation complete. What would you like to do next?",
            "header": "Next Steps",
            "multiSelect": false,
            "options": [
                {"label": "Sync Documentation", "description": "/moai:3-sync"},
                {"label": "Implement Another Feature", "description": "/moai:1-plan"},
                {"label": "Review Results", "description": "Examine the implementation"},
                {"label": "Finish", "description": "Session complete"}
            ]
        })

        # Log Phase 4 checkpoint
        Log to .moai/logs/phase-checkpoints.json:
          phase: 4
          status: "COMPLETE"
          user_selection: next_steps
          timestamp: NOW()
```

### Resume Chain Summary

**Context Flow (with Resume):**

```
Phase 1: SPEC Analysis
  → Agent ID: abc123

Phase 2: Task(resume="abc123")
  → Inherits: Full planning context
  → Implements: Without re-reading SPEC or re-analyzing

Phase 2.5: Task(resume="abc123")
  → Inherits: Planning + Implementation context
  → Validates: With complete feature knowledge

Phase 3: Task(resume="abc123")
  → Inherits: Complete feature context
  → Creates: Commits with full context understanding
```

**Benefits:**

- ✅ **99K Token Savings**: No re-transmission of context between phases
- ✅ **Context Continuity**: Full knowledge chain across all phases
- ✅ **Unified Coding**: Phase 1 architectural decisions naturally propagate
- ✅ **Better Commits**: manager-git understands full context for meaningful messages

---

## 📊 Design Improvements (vs Previous Version)

| Metric                 | Before           | After          | Improvement            |
| ---------------------- | ---------------- | -------------- | ---------------------- |
| **Command LOC**        | ~420             | ~120           | **71% reduction**      |
| **allowed-tools**      | 14 types         | 1 type         | **93% reduction**      |
| **Direct tool usage**  | Yes (Read/Bash)  | No             | **100% eliminated**    |
| **Agent count**        | 4 separate calls | 1 orchestrator | **100% simplified**    |
| **User approval flow** | In command       | In agent       | **Cleaner separation** |
| **Error handling**     | Dispersed        | Centralized    | **Better structure**   |

---

## 🔍 Verification Checklist

After implementation, verify:

- [ ] ✅ Command has ONLY `Task`, `AskUserQuestion`, `TodoWrite` in allowed-tools
- [ ] ✅ Command contains NO `Read`, `Write`, `Edit`, `Bash` usage
- [ ] ✅ Command delegates execution to phase agents sequentially
- [ ] ✅ Phase 1: manager-strategy executes successfully
- [ ] ✅ Phase 2: manager-tdd executes successfully
- [ ] ✅ Phase 2.5: manager-quality validates TRUST 5
- [ ] ✅ Phase 3: manager-git creates commits
- [ ] ✅ Phase 4: User guided to next steps
- [ ] ✅ User approval checkpoints working

---

## 📚 Quick Reference

| Scenario | Entry Point | Key Phases | Expected Outcome |
|----------|-------------|------------|------------------|
| Implement SPEC feature | `/moai:2-run SPEC-XXX` | Phase 1 → Planning → Phase 2 → TDD → Phase 2.5 → Quality → Phase 3 → Git | Implemented feature with ≥85% test coverage |
| Resume failed implementation | `/moai:2-run SPEC-XXX` (retry) | Resume from last successful phase | Completed implementation |
| Implement with modifications | `/moai:2-run SPEC-XXX` (with plan changes) | Modify plan → Execute phases | Modified implementation |

**Associated Agents**:

- `manager-strategy` - SPEC analysis and execution strategy
- `manager-tdd` - TDD implementation (RED-GREEN-REFACTOR)
- `manager-quality` - TRUST 5 validation
- `manager-git` - Git operations and commit management

**Implementation Results**:

- **Code**: Implemented feature files
- **Tests**: Test files with ≥85% coverage
- **Commits**: Git commits with proper messages
- **Quality**: PASS/WARNING/CRITICAL status

**Version**: 3.1.0 (Command-Level Phase Orchestration with Resume Chain)
**Updated**: 2025-11-25
**Pattern**: Sequential Phase-Based Agent Delegation
**Compliance**: Claude Code Best Practices + Zero Direct Tool Usage
**Architecture**: Commands → Agents → Skills (Complete delegation)

---

## Final Step: Next Action Selection

After TDD implementation completes, use AskUserQuestion tool to guide user to next action:

```python
AskUserQuestion({
    "questions": [{
        "question": "Implementation is complete. What would you like to do next?",
        "header": "Next Steps",
        "multiSelect": false,
        "options": [
            {
                "label": "Sync Documentation",
                "description": "Execute /moai:3-sync to organize documentation and create PR"
            },
            {
                "label": "Additional Implementation",
                "description": "Implement more features"
            },
            {
                "label": "Quality Verification",
                "description": "Review tests and code quality"
            }
        ]
    }]
})
```

**Important**:

- Use conversation language from config
- No emojis in any AskUserQuestion fields
- Always provide clear next step options

## ⚡️ EXECUTION DIRECTIVE

**You must NOW execute the command following the "Execution Philosophy" described above.**

1. Start Phase 1: Analysis & Planning immediately.
2. Call the `Task` tool with `subagent_type="manager-strategy"`.
3. Do NOT just describe what you will do. DO IT.
