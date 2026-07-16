# SPEC-ADB-ECOSYSTEM-001: Unified ADB Workflow Ecosystem Restructuring

**ID**: SPEC-ADB-ECOSYSTEM-001
**Version**: 1.0.0
**Status**: Active Implementation
**Created**: 2025-12-02
**Category**: ADB Automation Architecture
**Complexity**: High (Ecosystem-wide Restructuring)
**Tier**: 2-3 (Foundation + App-Specific Skills)

---

## 1. ENVIRONMENT & CONTEXT

### Current State
The ADB Automation Ecosystem comprises 8 skills organized in a master folder (`.claude/skills/adb/`):
- **5 Foundation Skills** (Tier 2): adb-screen-detection, adb-navigation-base, adb-workflow-orchestrator, adb-uiautomator, adb-skill-generator
- **3 App-Specific Skills** (Tier 3): adb-magisk, adb-karrot, adb-bypass
- **Workflow Status**: Partially implemented (workflow/ folders created, TOON+MD pairs incomplete)
- **SKILL.md Status**: 7 of 8 files complete (adb-bypass missing)
- **Documentation**: ADB_ECOSYSTEM_README.md, ECOSYSTEM_PATTERNS.md, ECOSYSTEM_TEMPLATES.md exist

### Project Constraints
- Python 3.11+ environment with uv package manager
- TOON v4.0 specification compliance required
- Backwards compatibility with existing Python scripts essential
- MoAI-ADK framework integration mandatory
- Git-based version control with conventional commits
- Token budget: 150K active context, /clear strategy applied

### Stakeholders
- **Maintainers**: ADB ecosystem developers
- **Users**: Automation engineers, app testing teams
- **Builders**: Agent ecosystem for skill creation and workflow design
- **Integration**: MoAI-ADK SPEC-First TDD workflow

---

## 2. ASSUMPTIONS

1. **Architectural Assumptions**
   - All 8 ADB skills remain in `.claude/skills/adb/` master folder
   - Each skill has both `scripts/` (Python implementation) and `workflow/` (TOON orchestration) folders
   - TOON v4.0 is the preferred orchestration language for complex workflows
   - Markdown (MD) is the standard documentation format

2. **Technical Assumptions**
   - Python scripts use `adb` command-line interface (system-level)
   - All workflows are deterministic and retryable
   - TOON files define orchestration; Python files handle implementation
   - No hardcoded paths; all paths use environment variables or relative references
   - Backwards compatibility: Existing scripts continue working during transition

3. **Process Assumptions**
   - Builder agents (builder-skill, builder-workflow-designer) can be trained on new patterns
   - Auto-nesting logic applies when >4 items share same prefix
   - Workflows follow naming convention: `{domain}-{action}.toon` and `{domain}-{action}.md`
   - New workflows added quarterly; maintenance schedule monthly

4. **Resource Assumptions**
   - Development time: 3-4 hours for complete restructuring
   - Manual testing required for workflow validation
   - Existing scripts remain operational (no breaking changes)
   - Version control through Git with feature branches

---

## 3. REQUIREMENTS

### Functional Requirements

#### FR-1: Directory Structure Organization
- **Requirement**: All 8 ADB skills must reside in master folder `.claude/skills/adb/`
- **Rationale**: Single source of truth for ecosystem; simplified discovery and maintenance
- **Acceptance Criteria**:
  - ✅ All skills located under `.claude/skills/adb/`
  - ✅ Each skill is a distinct subdirectory
  - ✅ No duplicate skill locations
  - ✅ README.md exists in master folder documenting structure

#### FR-2: Skill Structure Standardization
- **Requirement**: Each skill must have consistent internal structure
- **Rationale**: Enables consistent tooling, builder agents, and documentation
- **Acceptance Criteria**:
  - ✅ Each skill has: `SKILL.md`, `scripts/`, `workflow/`, `analysis/`, `templates/` folders
  - ✅ `scripts/` folder contains Python implementation files
  - ✅ `workflow/` folder contains TOON+MD workflow pairs
  - ✅ `SKILL.md` includes metadata (name, version, dependencies, auto_trigger_keywords)
  - ✅ No duplicate or redundant folder structures

#### FR-3: TOON+MD Workflow Pairs
- **Requirement**: Create 15+ TOON+MD workflow pairs across 8 skills
- **Rationale**: TOON orchestrates complex workflows; MD documents process and parameters
- **Distribution**:
  - adb-karrot: 3 workflows (launch, bypass-check, full-bypass)
  - adb-magisk: 2 workflows (setup, module-install)
  - Remaining 6 skills: 9 workflows distributed (1-2 each)
- **Acceptance Criteria**:
  - ✅ All TOON files follow v4.0 syntax specification
  - ✅ Each TOON has corresponding .md with same base name
  - ✅ All workflows are semantically valid and testable
  - ✅ Naming convention consistent: `{domain}-{action}.toon` + `{domain}-{action}.md`

#### FR-4: SKILL.md Enhancement
- **Requirement**: All SKILL.md files must include "Workflows" section documenting available workflows
- **Rationale**: Enables discovery of available workflows per skill
- **Acceptance Criteria**:
  - ✅ 7 existing SKILL.md files updated with Workflows section
  - ✅ Workflows section lists all available workflows with descriptions
  - ✅ Each workflow entry includes: name, purpose, phase count, dependencies
  - ✅ Consistent formatting across all 8 SKILL.md files

#### FR-5: Missing adb-bypass SKILL.md Creation
- **Requirement**: Create SKILL.md for adb-bypass skill
- **Rationale**: All 8 skills must have complete metadata and documentation
- **Acceptance Criteria**:
  - ✅ SKILL.md created with complete metadata
  - ✅ Metadata matches ecosystem standards
  - ✅ Auto-trigger keywords defined
  - ✅ Dependencies listed
  - ✅ Workflows section included

#### FR-6: Auto-Nesting Infrastructure
- **Requirement**: Implement auto-nesting rule: >4 items with same prefix → create folder
- **Rationale**: Keeps directories clean and organized as ecosystem grows
- **Acceptance Criteria**:
  - ✅ Auto-nesting detection logic implemented
  - ✅ When >4 workflows detected with same prefix, auto-nesting triggered
  - ✅ Builder agents apply auto-nesting on workflow creation
  - ✅ Documentation explains auto-nesting rules

#### FR-7: Builder Agent Training
- **Requirement**: Train builder agents on new ecosystem structure
- **Rationale**: Enables automatic skill/workflow creation with correct structure
- **Agents to Train**:
  - builder-skill: Create skills with workflow/ folder
  - builder-workflow-designer: Create TOON+MD workflow pairs
  - builder-agent: Understand ecosystem structure for agent creation
- **Acceptance Criteria**:
  - ✅ builder-skill training updated with workflow/ folder creation
  - ✅ builder-workflow-designer trained on TOON v4.0 + MD documentation
  - ✅ builder-agent understands ADB ecosystem structure
  - ✅ Training documentation created (AGENT-ECOSYSTEM-TRAINING.md)

### Non-Functional Requirements

#### NFR-1: TOON v4.0 Specification Compliance
- **Requirement**: All TOON workflows must follow v4.0 syntax and semantics
- **Verification**: Syntax validation, semantic checks, execution testing

#### NFR-2: Backwards Compatibility
- **Requirement**: Existing Python scripts continue working without modification
- **Verification**: All existing scripts execute successfully; test coverage maintained

#### NFR-3: Scalability
- **Requirement**: System designed to support 20+ workflows per skill without performance degradation
- **Verification**: Auto-nesting rules functional; no performance impact observed

#### NFR-4: Documentation Quality
- **Requirement**: All documentation (TOON comments, MD files, SKILL.md) comprehensive and accurate
- **Verification**: Documentation review, cross-reference validation

#### NFR-5: Code Quality
- **Requirement**: All code (Python, TOON, MD) follows project standards
- **Verification**: Linting (ruff, pylint), syntax validation, peer review

#### NFR-6: Naming Consistency
- **Requirement**: All files, folders, and identifiers follow consistent naming patterns
- **Verification**: Automated naming convention checks, manual review

---

## 4. SPECIFICATIONS

### System Architecture

#### 4.1 Directory Hierarchy
```
.claude/skills/adb/                          # Master folder for all ADB skills
├── adb-screen-detection/                    # Foundation skill
│   ├── SKILL.md                             # Metadata + Workflows section
│   ├── scripts/
│   │   ├── adb-screen-capture.py
│   │   ├── adb-ocr-extract.py
│   │   └── ...
│   ├── workflow/                            # TOON+MD workflow pairs
│   │   ├── detection-capture.toon
│   │   ├── detection-capture.md
│   │   └── README.md                        # Workflow index
│   ├── analysis/
│   ├── templates/
│   └── README.md                            # Skill documentation
│
├── adb-navigation-base/                     # Foundation skill
│   ├── SKILL.md
│   ├── scripts/
│   ├── workflow/
│   │   ├── navigation-tap.toon
│   │   ├── navigation-tap.md
│   │   └── README.md
│   └── ...
│
├── adb-workflow-orchestrator/               # Foundation skill
│   ├── SKILL.md
│   ├── scripts/
│   ├── workflow/
│   │   └── README.md
│   └── ...
│
├── adb-uiautomator/                         # Foundation skill
│   ├── SKILL.md
│   ├── scripts/
│   ├── workflow/
│   │   └── README.md
│   └── ...
│
├── adb-skill-generator/                     # Foundation skill (meta-tool)
│   ├── SKILL.md
│   ├── scripts/
│   ├── workflow/
│   │   └── README.md
│   └── ...
│
├── adb-magisk/                              # App-specific skill (Tier 3)
│   ├── SKILL.md                             # Metadata + 2 workflows
│   ├── scripts/
│   │   ├── adb-magisk-launch.py
│   │   ├── adb-magisk-enable-zygisk.py
│   │   └── adb-magisk-install-module.py
│   ├── workflow/
│   │   ├── magisk-launch.toon
│   │   ├── magisk-launch.md
│   │   ├── magisk-full-setup.toon
│   │   ├── magisk-full-setup.md
│   │   └── README.md
│   └── ...
│
├── adb-karrot/                              # App-specific skill (Tier 3)
│   ├── SKILL.md                             # Metadata + 3 workflows
│   ├── scripts/
│   │   ├── adb-karrot-launch.py
│   │   ├── adb-karrot-check-detection.py
│   │   └── adb-karrot-test-login.py
│   ├── workflow/
│   │   ├── karrot-launch-app.toon
│   │   ├── karrot-launch-app.md
│   │   ├── karrot-check-bypass.toon
│   │   ├── karrot-check-bypass.md
│   │   ├── karrot-full-bypass.toon
│   │   ├── karrot-full-bypass.md
│   │   └── README.md
│   └── ...
│
├── adb-bypass/                              # App-specific skill (Tier 3)
│   ├── SKILL.md                             # NEW - Metadata + workflows
│   ├── scripts/
│   │   └── ...
│   ├── workflow/
│   │   ├── bypass-setup.toon
│   │   ├── bypass-setup.md
│   │   ├── bypass-validate.toon
│   │   ├── bypass-validate.md
│   │   └── README.md
│   └── ...
│
├── ADB_ECOSYSTEM_README.md                  # Ecosystem overview + structure
├── ECOSYSTEM_PATTERNS.md                    # Pattern documentation
├── ECOSYSTEM_TEMPLATES.md                   # Reusable templates
└── AGENT-ECOSYSTEM-TRAINING.md              # NEW - Agent training guide
```

#### 4.2 SKILL.md Template with Workflows Section
```yaml
---
name: adb-{skill-name}
description: {Detailed description}
version: {version}
modularized: true
scripts_enabled: true
tier: {2 or 3}
category: adb-{category}
last_updated: {date}
compliance_score: {score}
dependencies:
  - {dependency-1}
  - {dependency-2}
auto_trigger_keywords:
  - {keyword-1}
  - {keyword-2}
scripts:
  - name: {script-name}
    purpose: {purpose}
    type: python
    command: {command}
    version: {version}
workflows:
  - name: {workflow-name}
    toon_file: workflow/{workflow-name}.toon
    md_file: workflow/{workflow-name}.md
    purpose: {purpose}
    phases: {number}
    dependencies:
      - {dependency-1}
color: {color}
---
```

#### 4.3 TOON+MD Workflow Pair Pattern
**TOON File** (`workflow/{name}.toon`):
```toon
// Workflow: {Descriptive Name}
// Purpose: {One-line purpose}
// Phases: {Number of phases}
// Dependencies: {List}
// Last Updated: {Date}

workflow {
  name: "{workflow-name}"
  description: "{Multi-line description}"
  phases: [
    {
      name: "phase-1"
      type: "action"
      action: "script"
      script: "scripts/{script-name}.py"
      args: ["arg1", "arg2"]
      retry: { max_attempts: 3, delay: 2 }
    },
    {
      name: "phase-2"
      type: "condition"
      condition: "${phase-1.result} == success"
      on_true: "next_phase"
      on_false: "error_handler"
    }
  ]
  error_handler: "rollback"
}
```

**MD File** (`workflow/{name}.md`):
```markdown
# Workflow: {Descriptive Name}

## Purpose
{Detailed purpose}

## Phases
1. **Phase 1: {Name}** - {Description}
2. **Phase 2: {Name}** - {Description}

## Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|

## Execution
```bash
uv run .claude/skills/adb/adb-workflow-orchestrator/scripts/adb-run-workflow.py workflow/{name}.toon
```

## Output
{Description of expected output}

## Error Handling
{Error cases and recovery strategies}

## Notes
{Implementation notes}
```

#### 4.4 Workflow Distribution (15+ TOON+MD Pairs)

| Skill | Workflows | Purpose |
|-------|-----------|---------|
| adb-screen-detection | 2 | Screen capture, OCR extraction |
| adb-navigation-base | 2 | Tap coordination, swipe gestures |
| adb-workflow-orchestrator | 1 | Workflow execution |
| adb-uiautomator | 2 | UIAutomator integration |
| adb-skill-generator | 1 | Skill scaffolding |
| adb-magisk | 2 | Magisk setup, module installation |
| adb-karrot | 3 | App launch, bypass check, full bypass |
| adb-bypass | 2 | Bypass setup, validation |
| **TOTAL** | **15** | |

#### 4.5 Auto-Nesting Rules
- **Trigger**: When `N > 4` items in directory share same prefix
- **Action**: Create subdirectory with prefix name, move items to subdirectory
- **Example**:
  ```
  Before (5 items):
  workflow/karrot-launch.toon
  workflow/karrot-bypass-check.toon
  workflow/karrot-bypass-full.toon
  workflow/karrot-login.toon
  workflow/karrot-validate.toon

  After (auto-nesting):
  workflow/
  ├── karrot/
  │   ├── launch.toon
  │   ├── bypass-check.toon
  │   ├── bypass-full.toon
  │   ├── login.toon
  │   └── validate.toon
  └── README.md
  ```

#### 4.6 Builder Agent Training Specifications
**builder-skill Updates**:
- Add `workflow/` folder creation to skill scaffolding
- Update SKILL.md template to include Workflows section
- Document workflow folder structure

**builder-workflow-designer Updates**:
- TOON v4.0 syntax generation
- Markdown documentation auto-generation
- Workflow validation against specification

**builder-agent Updates**:
- Understand ADB ecosystem hierarchy (Foundation → App-Specific)
- Know skill dependencies and inter-skill communication
- Apply auto-nesting rules on creation

---

## 5. CONSTRAINTS & BOUNDARIES

### Technical Constraints
- Python 3.11+ required (async support, type hints)
- TOON v4.0 syntax (no earlier versions)
- Markdown formatting (GitHub-flavored)
- Git-based version control
- No hardcoded absolute paths
- UTF-8 file encoding

### Operational Constraints
- Backwards compatibility: Existing scripts must continue working
- Breaking changes: None permitted during transition
- Testing: All workflows must be manually tested before merging
- Documentation: 100% coverage required
- Code review: Minimum 1 approval

### Scope Boundaries
- **In Scope**: Directory structure, SKILL.md updates, TOON+MD creation, builder training
- **Out of Scope**: Script implementation changes, ADB functionality enhancements, performance optimization
- **Future Work**: Workflow versioning, dependency resolution, parameter validation

---

## 6. SUCCESS CRITERIA

### Functional Success
- ✅ All 8 skills reside in `.claude/skills/adb/`
- ✅ All skills have consistent structure (scripts/, workflow/, etc.)
- ✅ 15+ TOON+MD workflow pairs created and validated
- ✅ All 8 SKILL.md files have Workflows section
- ✅ adb-bypass SKILL.md created with full metadata
- ✅ Auto-nesting rules documented and functional
- ✅ Builder agents trained and tested

### Quality Success
- ✅ All TOON files follow v4.0 specification
- ✅ All MD files are comprehensive and accurate
- ✅ Naming consistency across all files (100%)
- ✅ No broken cross-references
- ✅ Code review passed (1+ approvals)
- ✅ All existing scripts continue working

### Integration Success
- ✅ Ecosystem integrates with MoAI-ADK framework
- ✅ SPEC-First TDD workflow completed
- ✅ Documentation synchronized with codebase
- ✅ Git history clean (conventional commits)
- ✅ No merge conflicts or issues

### Performance Success
- ✅ Auto-nesting performs O(n) time complexity
- ✅ Workflow execution time unchanged
- ✅ Builder agents create skills correctly
- ✅ No performance regression observed

---

## 7. TRACEABILITY & MAPPING

### Requirements to Deliverables
| Requirement | Deliverable | Status |
|-------------|-------------|--------|
| FR-1: Directory Structure | `.moai/specs/SPEC-ADB-ECOSYSTEM-001/` | In Progress |
| FR-2: Skill Standardization | SKILL.md updates (all 8) | In Progress |
| FR-3: TOON+MD Pairs | 15+ workflow files | In Progress |
| FR-4: SKILL.md Enhancement | Workflows section | In Progress |
| FR-5: adb-bypass SKILL.md | New file creation | In Progress |
| FR-6: Auto-Nesting | Implementation rules | Documented |
| FR-7: Builder Training | Agent training docs | Pending |

### Dependencies
- FR-2 depends on: FR-1
- FR-3 depends on: FR-2, FR-1
- FR-4 depends on: FR-2
- FR-5 depends on: FR-2
- FR-6 depends on: FR-3
- FR-7 depends on: FR-1, FR-2, FR-3, FR-4, FR-5, FR-6

---

## 8. GLOSSARY & DEFINITIONS

| Term | Definition |
|------|-----------|
| **ADB** | Android Debug Bridge - command-line interface for device control |
| **Skill** | Reusable component in MoAI-ADK ecosystem |
| **Workflow** | Orchestrated sequence of phases/steps |
| **TOON** | Task Orchestration Object Notation v4.0 |
| **Phase** | Logical unit within workflow (action, condition, etc.) |
| **Tier 2** | Foundation skills (platform-level capabilities) |
| **Tier 3** | App-specific skills (real-world automation) |
| **Auto-nesting** | Automatic folder creation for >4 items with same prefix |

---

## 9. REFERENCES & LINKS

### Internal References
- `.claude/skills/ADB_ECOSYSTEM_README.md` - Ecosystem overview
- `.claude/skills/ECOSYSTEM_PATTERNS.md` - Pattern documentation
- `.claude/skills/ECOSYSTEM_TEMPLATES.md` - Reusable templates
- `.moai/specs/SPEC-ADB-ECOSYSTEM-001/plan.md` - Implementation plan
- `.moai/specs/SPEC-ADB-ECOSYSTEM-001/acceptance.md` - Acceptance criteria

### External References
- TOON v4.0 Specification: `.claude/specs/TOON-v4.0-SPEC.md`
- MoAI-ADK Framework: `CLAUDE.md`
- Git Workflow: `github.com/claydev-local/opensource-v2`

### Agent Training Materials
- `AGENT-ECOSYSTEM-TRAINING.md` - Builder agent training guide
- `WORKFLOW-STRUCTURE-GUIDE.md` - Workflow creation guide
- `TOON-MD-PATTERN-REFERENCE.md` - Pattern reference

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: Ready for Implementation
**Next Phase**: [Review plan.md for implementation strategy]
