# Rule: Workflow Complexity Tiers (0-3)

**Module**: `rule-workflow-complexity.md`
**Version**: 1.0.0
**Category**: Decision Rules

---

## Purpose

This module defines the 4-tier workflow complexity system for agent-owned workflows using TOON + MD pairing.

---

## Core Principle

> **Always use workflows for agent orchestration, regardless of complexity.**

Even simple tasks benefit from the consistency and traceability that workflows provide.

---

## Tier Overview

| Tier | Steps | Files | Use Case |
|------|-------|-------|----------|
| **0** | 1 | WORKFLOW.toon + 1 step MD | Hotfix, quick fix |
| **1** | 3-5 | + instructions.md | Simple feature |
| **2** | 5-10 | + checklist.md | Medium feature, parallel execution |
| **3** | 10+ | + architecture.md | Complex, multi-agent |

---

## Tier 0: Minimal Workflow

### Characteristics
- **Single step** workflow
- Hotfixes, bug fixes, quick changes
- Minimal overhead (~150 tokens total)
- No parallel execution

### Structure
```
workflows/{workflow-name}/
├── WORKFLOW.toon           # ~10-15 lines
└── steps/
    └── step-01-{action}.md # Single combined step
```

### WORKFLOW.toon Template
```toon
# Tier 0: Minimal Workflow

@metadata[1]{id,name,version,tier}:
WF-HOTFIX-001,Quick Hotfix,1.0.0,tier-0

@phases[1]{id,name,agent,mode,deps,step_file}:
1,Fix and Verify,manager-tdd,sequential,[],step-01-fix.md

@exec[1]{complexity,parallel_default,token_limit}:
tier-0,1,30000

@gates[1]{gate_id,validator,threshold}:
1,test-pass,100
```

### When to Use
```
Is it a single-file bug fix?
├─ YES → Tier 0
└─ NO  → Consider Tier 1+

Can it be done in one step?
├─ YES → Tier 0
└─ NO  → Tier 1+
```

---

## Tier 1: Simple Workflow

### Characteristics
- **3-5 steps** sequential workflow
- Simple features, straightforward tasks
- Includes instructions.md for guidance
- Typically single agent

### Structure
```
workflows/{workflow-name}/
├── WORKFLOW.toon           # ~25-35 lines
├── instructions.md         # Overall guidance
└── steps/
    ├── step-01-{action}.md
    ├── step-02-{action}.md
    └── step-03-{action}.md
```

### WORKFLOW.toon Template
```toon
# Tier 1: Simple Workflow

@metadata[1]{id,name,version,tier,instructions}:
WF-SIMPLE-001,Add Feature,1.0.0,tier-1,instructions.md

@phases[3]{id,name,agent,mode,deps,step_file}:
1,Plan Implementation,manager-strategy,sequential,[],step-01-plan.md
2,Implement Feature,expert-backend,sequential,[1],step-02-implement.md
3,Test and Validate,manager-tdd,sequential,[2],step-03-test.md

@files[3]{path,agent,operation}:
{project-root}/src/{module}.py,expert-backend,create
{project-root}/tests/test_{module}.py,manager-tdd,create
{project-root}/docs/{module}.md,manager-docs,create

@exec[1]{complexity,parallel_default,token_limit}:
tier-1,1,80000

@gates[2]{gate_id,validator,threshold}:
1,test-coverage,85
2,trust-5,100
```

### When to Use
```
Is it a well-defined feature with 3-5 steps?
├─ YES → Tier 1
└─ NO  → Consider Tier 2

Does it involve multiple domains (frontend + backend)?
├─ YES → Tier 2
└─ NO  → Tier 1 is fine
```

---

## Tier 2: Medium Workflow

### Characteristics
- **5-10 steps** with parallel phases
- Multi-domain features (frontend + backend + database)
- Includes checklist.md for validation
- Multiple agents working in parallel

### Structure
```
workflows/{workflow-name}/
├── WORKFLOW.toon           # ~50-80 lines
├── instructions.md         # Overall guidance
├── checklist.md            # Validation checklist
└── steps/
    ├── step-01-{action}.md
    ├── step-02-{action}.md
    ├── step-03-{action}.md
    ├── step-04-{action}.md
    ├── step-05-{action}.md
    └── step-06-{action}.md
```

### WORKFLOW.toon Template
```toon
# Tier 2: Medium Workflow

@metadata[1]{id,name,version,tier,instructions,checklist}:
WF-MED-001,Dashboard Feature,1.0.0,tier-2,instructions.md,checklist.md

@config[1]{source,artifacts_dir}:
{project-root}/.moai/config/defaults.toon,./artifacts

@phases[6]{id,name,agent,mode,deps,max_parallel,step_file}:
1,Strategy,manager-strategy,sequential,[],1,step-01-strategy.md
2,Backend API,expert-backend,parallel,[1],3,step-02-backend.md
3,Frontend UI,expert-frontend,parallel,[1],3,step-03-frontend.md
4,Integration,expert-backend,sequential,[2,3],1,step-04-integrate.md
5,Testing,manager-tdd,sequential,[4],1,step-05-test.md
6,Documentation,manager-docs,sequential,[5],1,step-06-docs.md

@files[6]{path,agent,operation,priority}:
{project-root}/src/api/{feature}.py,expert-backend,create,critical
{project-root}/src/components/{Feature}.tsx,expert-frontend,create,critical
{project-root}/tests/test_{feature}.py,manager-tdd,create,high
{project-root}/docs/{feature}.md,manager-docs,create,medium

@exec[1]{complexity,parallel_default,dynamic_adjust,token_limit}:
tier-2,3,true,150000

@gates[4]{gate_id,validator,threshold}:
1,architecture-clarity,90
2,test-coverage,90
3,type-check,100
4,trust-5,100
```

### When to Use
```
Does it involve multiple domains (frontend + backend)?
├─ YES → Tier 2
└─ NO  → Consider Tier 1

Will steps benefit from parallel execution?
├─ YES → Tier 2 (use parallel mode)
└─ NO  → Tier 1 sequential is fine

Is there complex validation needed?
├─ YES → Tier 2 (add checklist.md)
└─ NO  → Tier 1 is sufficient
```

---

## Tier 3: Complex Workflow

### Characteristics
- **10+ steps** with multi-phase execution
- Architectural changes, system redesigns
- Includes architecture.md for design docs
- Multiple quality checkpoints
- Resource monitoring

### Structure
```
workflows/{workflow-name}/
├── WORKFLOW.toon           # ~100+ lines
├── instructions.md         # Overall guidance
├── checklist.md            # Validation checklist
├── architecture.md         # Design documentation
└── steps/
    ├── step-01-{action}.md
    ├── step-02-{action}.md
    ├── ...
    └── step-12-{action}.md
```

### WORKFLOW.toon Template
```toon
# Tier 3: Complex Workflow

@metadata[1]{id,name,version,tier,instructions,checklist}:
WF-ARCH-001,Payment System,1.0.0,tier-3,instructions.md,checklist.md

@config[1]{source,artifacts_dir,architecture}:
{project-root}/.moai/config/payment.toon,./artifacts,architecture.md

@phases[12]{id,name,agent,mode,deps,max_parallel,step_file}:
1,Architecture Planning,manager-strategy,sequential,[],1,step-01-architecture.md
2,Backend Core,expert-backend,parallel,[1],5,step-02-backend-core.md
3,Backend API,expert-backend,parallel,[1],5,step-03-backend-api.md
4,Frontend Core,expert-frontend,parallel,[1],5,step-04-frontend-core.md
5,Frontend Pages,expert-frontend,parallel,[1],5,step-05-frontend-pages.md
6,Database Design,expert-database,parallel,[1],5,step-06-database.md
7,Security Audit,expert-security,sequential,[2,3,4,5,6],1,step-07-security.md
8,Integration,expert-backend,sequential,[7],1,step-08-integration.md
9,Unit Tests,manager-tdd,sequential,[8],1,step-09-unit-tests.md
10,E2E Tests,mcp-playwright,sequential,[9],1,step-10-e2e-tests.md
11,Documentation,manager-docs,sequential,[10],1,step-11-docs.md
12,Deployment Prep,expert-devops,sequential,[11],1,step-12-deploy.md

@checkpoint[3]{checkpoint_id,after_phase,validation,rollback_enabled}:
1,6,architecture-validation,true
2,9,test-coverage-validation,true
3,11,integration-validation,true

@exec[1]{complexity,parallel_default,dynamic_adjust,token_limit,max_agents}:
tier-3,5,true,200000,10

@resource_limits[1]{cpu_threshold,memory_threshold,token_threshold}:
80,75,180000

@gates[6]{gate_id,validator,threshold}:
1,architecture-clarity,98
2,test-coverage,95
3,security-audit,100
4,performance-benchmarks,90
5,type-check,100
6,trust-5,100
```

### When to Use
```
Is it an architectural change or system redesign?
├─ YES → Tier 3
└─ NO  → Consider Tier 2

Does it require 10+ distinct steps?
├─ YES → Tier 3
└─ NO  → Tier 2 is sufficient

Does it need quality checkpoints with rollback?
├─ YES → Tier 3 (add @checkpoint)
└─ NO  → Tier 2 may work
```

---

## Tier Selection Flowchart

```
┌────────────────────────────────────────────┐
│         WORKFLOW COMPLEXITY                 │
└─────────────────┬──────────────────────────┘
                  │
                  ▼
┌────────────────────────────────────────────┐
│        Is it a single-step fix?            │
├──────────────────┬─────────────────────────┤
│       YES        │          NO             │
│        ↓         │           ↓             │
│    TIER 0        │                         │
└──────────────────┴────────────┬────────────┘
                                │
                                ▼
┌────────────────────────────────────────────┐
│       Does it have 3-5 sequential steps?   │
├──────────────────┬─────────────────────────┤
│       YES        │          NO             │
│        ↓         │           ↓             │
│    TIER 1        │                         │
└──────────────────┴────────────┬────────────┘
                                │
                                ▼
┌────────────────────────────────────────────┐
│     Does it need parallel execution?       │
│     OR involve multiple domains?           │
├──────────────────┬─────────────────────────┤
│       YES        │          NO             │
│        ↓         │           ↓             │
│    TIER 2        │       TIER 1            │
└──────────────────┴────────────┬────────────┘
                                │
                                ▼
┌────────────────────────────────────────────┐
│     Is it 10+ steps OR architectural?      │
├──────────────────┬─────────────────────────┤
│       YES        │          NO             │
│        ↓         │           ↓             │
│    TIER 3        │       TIER 2            │
└──────────────────────────────────────────────┘
```

---

## Comparison Table

| Aspect | Tier 0 | Tier 1 | Tier 2 | Tier 3 |
|--------|--------|--------|--------|--------|
| Steps | 1 | 3-5 | 5-10 | 10+ |
| Execution | Sequential | Sequential | Mixed | Complex |
| Agents | 1 | 1-2 | 2-4 | 5+ |
| Parallel | No | No | Yes | Yes |
| instructions.md | No | Yes | Yes | Yes |
| checklist.md | No | No | Yes | Yes |
| architecture.md | No | No | No | Yes |
| Checkpoints | No | No | Optional | Required |
| Token Budget | 30K | 80K | 150K | 200K |

---

## Quick Reference

```
TIER 0: 1 step     → WORKFLOW.toon + step-01.md
TIER 1: 3-5 steps  → + instructions.md
TIER 2: 5-10 steps → + checklist.md + parallel
TIER 3: 10+ steps  → + architecture.md + checkpoints
```

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
