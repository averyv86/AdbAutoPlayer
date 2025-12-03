# Step Schema: step-{NN}-{action}.md Template

**Schema**: `step-schema.md`
**Version**: 1.0.0
**Usage**: Template for workflow step files

---

## File Naming

```
step-{NN}-{action}.md

Where:
  NN     = Two-digit step number (01, 02, 03, ...)
  action = Lowercase hyphenated action name

Examples:
  step-01-analyze.md
  step-02-implement-backend.md
  step-03-test-coverage.md
  step-10-deploy-staging.md
```

---

## Template

Copy and customize the template below:

```markdown
# Step {NN}: {Action Title}

## Overview

| Field | Value |
|-------|-------|
| **Phase** | {phase-id} |
| **Agent** | {assigned-agent} |
| **Mode** | {sequential\|parallel} |
| **Dependencies** | {comma-separated phase IDs or "None"} |

---

## Objectives

1. {objective-1}
2. {objective-2}
3. {objective-3}

---

## Prerequisites

- [ ] {prerequisite-1}
- [ ] {prerequisite-2}
- [ ] From previous phase: {input-artifacts}

---

## Instructions

### 1. {Sub-step Name}

{Detailed instructions for this sub-step}

**Commands** (if applicable):
\`\`\`bash
{example-command}
\`\`\`

**Expected Output**:
{description-of-expected-output}

### 2. {Sub-step Name}

{...additional sub-steps...}

---

## Output Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| {artifact-1} | {path} | {description} |
| {artifact-2} | {path} | {description} |

---

## Quality Criteria

- [ ] {criterion-1}
- [ ] {criterion-2}
- [ ] {criterion-3}

---

## Error Handling

| Error Condition | Recovery Action |
|-----------------|-----------------|
| {error-condition-1} | {recovery-action-1} |
| {error-condition-2} | {recovery-action-2} |

**Escalate to**: {escalation-agent}

---

## Handoff

**Next Phase**: step-{NN+1}-{next-action}.md

**Context to Pass**:
- {context-item-1}
- {context-item-2}

---

**Step Version**: 1.0.0
```

---

## Section Descriptions

### Overview Table
Required metadata for every step file.

| Field | Description |
|-------|-------------|
| Phase | Phase ID from WORKFLOW.toon |
| Agent | Agent assigned to this step |
| Mode | sequential or parallel |
| Dependencies | Phase IDs that must complete first |

### Objectives
Clear, numbered objectives for what this step accomplishes. Keep to 2-5 items.

### Prerequisites
What must be true before starting this step. Include:
- State from previous phases
- Required tools/access
- Input artifacts needed

### Instructions
Detailed step-by-step guide. Break into numbered sub-steps with:
- Clear actions
- Commands (in code blocks)
- Expected outputs

### Output Artifacts
Table of files/artifacts this step produces. Include:
- Artifact name
- File path
- Brief description

### Quality Criteria
Checklist of criteria that must be met before step is complete.

### Error Handling
Table of common errors and recovery actions. Always include escalation path.

### Handoff
Information for transitioning to next step:
- Next step file
- Context/artifacts to pass forward

---

## Examples by Tier

### Tier 0 Step (Minimal)

```markdown
# Step 01: Fix and Verify

## Overview

| Field | Value |
|-------|-------|
| **Phase** | 1 |
| **Agent** | manager-tdd |
| **Mode** | sequential |
| **Dependencies** | None |

---

## Objectives

1. Identify bug from SPEC/issue
2. Write failing test
3. Fix code
4. Verify no regression

---

## Instructions

### 1. Write Failing Test

Create test that reproduces the bug.

### 2. Implement Fix

Minimal code change to pass test.

### 3. Run Full Suite

Ensure no regression.

---

## Quality Criteria

- [ ] Bug reproduced in test
- [ ] Test passes after fix
- [ ] No regression

---

**Step Version**: 1.0.0
```

### Tier 1 Step

```markdown
# Step 02: Implement Feature

## Overview

| Field | Value |
|-------|-------|
| **Phase** | 2 |
| **Agent** | expert-backend |
| **Mode** | sequential |
| **Dependencies** | 1 |

---

## Objectives

1. Create data models
2. Implement API endpoints
3. Add validation

---

## Prerequisites

- [ ] Phase 1 (Plan) completed
- [ ] From previous phase: requirements.md

---

## Instructions

### 1. Create Models

\`\`\`python
# src/models/feature.py
from dataclasses import dataclass

@dataclass
class Feature:
    id: str
    name: str
\`\`\`

### 2. Implement Endpoints

Create REST endpoints for CRUD operations.

### 3. Add Validation

Add input validation using Pydantic.

---

## Output Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Models | src/models/feature.py | Data models |
| API | src/api/feature.py | REST endpoints |

---

## Quality Criteria

- [ ] Models follow conventions
- [ ] Endpoints handle errors
- [ ] Validation complete

---

## Handoff

**Next Phase**: step-03-test.md

**Context to Pass**:
- List of created endpoints
- Model schema

---

**Step Version**: 1.0.0
```

### Tier 2 Step (Parallel)

```markdown
# Step 02: Backend Implementation

## Overview

| Field | Value |
|-------|-------|
| **Phase** | 2 |
| **Agent** | expert-backend |
| **Mode** | parallel |
| **Dependencies** | 1 |

---

## Objectives

1. Implement API layer
2. Create service layer
3. Add data layer

---

## Prerequisites

- [ ] Phase 1 (Strategy) completed
- [ ] From previous phase: architecture diagram
- [ ] Can run parallel with Phase 3 (Frontend)

---

## Instructions

### 1. API Layer

Create FastAPI routes matching spec.

### 2. Service Layer

Business logic implementation.

### 3. Data Layer

Database models and queries.

---

## Output Artifacts

| Artifact | Path | Description |
|----------|------|-------------|
| Routes | src/api/ | API endpoints |
| Services | src/services/ | Business logic |
| Models | src/models/ | DB models |

---

## Quality Criteria

- [ ] All endpoints implemented
- [ ] Error handling complete
- [ ] Type hints added

---

## Error Handling

| Error Condition | Recovery Action |
|-----------------|-----------------|
| Spec unclear | Ask manager-strategy |
| DB connection fail | Retry with backoff |

**Escalate to**: manager-strategy

---

## Handoff

**Next Phase**: step-04-integrate.md (after Phase 3 completes)

**Context to Pass**:
- API endpoint list
- Database schema

---

**Step Version**: 1.0.0
```

---

## Best Practices

1. **Keep steps focused** - One clear purpose per step
2. **Be explicit** - Don't assume knowledge from other files
3. **Include examples** - Code blocks for commands/outputs
4. **Document errors** - Common failures and recoveries
5. **Clear handoff** - What next step needs to know

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
