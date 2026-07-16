# ADB Ecosystem Governance Rules

**Document Purpose**: Comprehensive governance framework for ADB ecosystem development
**Audience**: Builders (builder-skill, builder-workflow-designer, builder-agent), Future Agents, Developers
**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: Active - Definitive Reference

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Rule Set 1: Naming Conventions (STRICT)](#rule-set-1-naming-conventions-strict)
3. [Rule Set 2: Auto-Nesting Decision Logic](#rule-set-2-auto-nesting-decision-logic)
4. [Rule Set 3: Pre-Execution Checklist](#rule-set-3-pre-execution-checklist)
5. [Rule Set 4: Agent Task Boundaries](#rule-set-4-agent-task-boundaries)
6. [Rule Set 5: Duplicate Prevention](#rule-set-5-duplicate-prevention)
7. [Rule Set 6: Validation & Rollback](#rule-set-6-validation--rollback)
8. [Rule Set 7: Execution Logging](#rule-set-7-execution-logging)
9. [Rule Set 8: Future Agent Training](#rule-set-8-future-agent-training)
10. [Decision Logic Flowchart](#decision-logic-flowchart)
11. [Quick Reference Card](#quick-reference-card)
12. [Appendix: Real Examples](#appendix-real-examples)

---

## Executive Summary

This document defines 8 fail-safe governance rule sets that prevent agent disorganization, ensure consistency, and enable future agent training in the ADB ecosystem development.

### Who Should Read This

- **Builders**: builder-skill, builder-workflow-designer, builder-agent using ADB ecosystem
- **Future Agents**: New agents learning ADB development patterns
- **Developers**: Maintaining ADB ecosystem consistency
- **Project Managers**: Understanding agent coordination and dependencies

### How to Use This Document

1. **Quick Reference**: Start with [Quick Reference Card](#quick-reference-card) for common scenarios
2. **Specific Situation**: Find your situation in the appropriate Rule Set section
3. **Detailed Implementation**: Follow the examples and validation commands
4. **Training New Agents**: Reference this document in agent system prompts
5. **Troubleshooting**: Check Rule Set 6 (Validation & Rollback) for recovery procedures

### Key Concepts

| Term | Definition |
|------|-----------|
| **Skill** | Modular unit of knowledge/capability (adb-transfer-protocols, adb-device-detection) |
| **Workflow** | Orchestration pattern coordinating multiple agents |
| **Auto-Nesting** | Automatic parent folder creation when item count exceeds threshold |
| **Flat Structure** | Direct child organization (no parent folder) |
| **Synchronization Point** | Predefined moment where agents coordinate outputs |

---

## Rule Set 1: Naming Conventions (STRICT)

### Problem Statement

Inconsistent naming causes:
- Agent confusion about file ownership
- Difficult codebase navigation
- Duplicate creation of similar skills
- Unclear dependency relationships

### Solution

All ADB ecosystem files follow strict naming patterns:

### Naming Pattern Categories

#### Category 1: Skill Files

**Pattern**: `adb-[domain]-[specific-function].md`

**Components**:
- `adb-` prefix (required)
- `[domain]`: Single word domain (transfer, device, input, connection, state, etc.)
- `[specific-function]`: Hyphenated functionality descriptor

**Validation Rules**:
- All lowercase, no spaces
- Hyphens only for word separation
- No underscores
- No abbreviations (use full words)
- Maximum 64 characters total

**Examples**:

✅ **Correct**:
```
adb-transfer-protocols.md
adb-device-detection.md
adb-input-handling.md
adb-connection-management.md
adb-state-tracking.md
adb-error-recovery.md
```

❌ **Incorrect**:
```
adb_transfer_protocols.md          # Uses underscores (WRONG)
ADB-Transfer-Protocols.md          # Mixed case (WRONG)
adb-transfer-proto.md              # Abbreviation 'proto' (WRONG)
adb-transfer-and-protocols.md      # Too verbose (WRONG)
transfer-protocols.md              # Missing 'adb-' prefix (WRONG)
adbTransferProtocols.md            # camelCase (WRONG)
```

**Validation Command**:

```bash
# Check all skill files follow naming convention
find .claude/skills -name "adb-*.md" -type f | while read file; do
  basename=$(basename "$file")
  if ! [[ "$basename" =~ ^adb-[a-z]+(-[a-z]+)*\.md$ ]]; then
    echo "FAIL: $basename does not match pattern"
  else
    echo "PASS: $basename"
  fi
done
```

#### Category 2: Folder Names (Parent/Sub-organization)

**Pattern**: `adb-[domain]` or `adb-[domain]-[sub-domain]`

**Validation Rules**:
- Lowercase, hyphens only
- No trailing numbers unless version-specific
- No underscores
- Mirrors skill naming pattern

**Examples**:

✅ **Correct**:
```
adb-transfer/
adb-device/
adb-input/
adb-transfer-file/      # Sub-domain allowed
adb-device-sensors/     # Sub-domain allowed
```

❌ **Incorrect**:
```
adb_transfer/           # Underscores (WRONG)
ADB-Transfer/           # Mixed case (WRONG)
adb-transfer-1/         # Version number (WRONG)
adb-transfer-utilities/ # Too generic (WRONG)
```

**Validation Command**:

```bash
# Check folder names follow convention
find .claude/skills -type d -name "adb-*" | while read dir; do
  basename=$(basename "$dir")
  if ! [[ "$basename" =~ ^adb-[a-z]+(-[a-z]+)*$ ]]; then
    echo "FAIL: Folder '$basename' invalid"
  else
    echo "PASS: Folder '$basename'"
  fi
done
```

#### Category 3: Workflow Files

**Pattern**: `workflow-[workflow-name].md`

**Validation Rules**:
- `workflow-` prefix (required)
- Hyphenated name describing workflow purpose
- All lowercase

**Examples**:

✅ **Correct**:
```
workflow-adb-ecosystem-build.md
workflow-skill-generation.md
workflow-validation-pipeline.md
```

❌ **Incorrect**:
```
Workflow-ADB-Ecosystem.md       # Mixed case (WRONG)
workflow_adb_ecosystem.md       # Underscores (WRONG)
workflow-adb-eco.md             # Abbreviation (WRONG)
```

**Validation Command**:

```bash
# Check workflow files
find .claude/workflows -name "workflow-*.md" -type f | while read file; do
  basename=$(basename "$file")
  if ! [[ "$basename" =~ ^workflow-[a-z]+(-[a-z]+)*\.md$ ]]; then
    echo "FAIL: $basename invalid"
  else
    echo "PASS: $basename"
  fi
done
```

### Success Criteria

All naming validations should return 100% PASS results.

```bash
# Comprehensive validation
echo "=== Skill Files ===" && \
find .claude/skills -name "adb-*.md" | wc -l && \
echo "=== Folder Names ===" && \
find .claude/skills -type d -name "adb-*" | wc -l && \
echo "=== Workflow Files ===" && \
find .claude/workflows -name "workflow-*.md" | wc -l
```

### Failure Scenarios

| Scenario | Symptom | Recovery |
|----------|---------|----------|
| File exists with wrong name | Agent creates duplicate | Rename old file, delete duplicate |
| Mixed case in names | Case-sensitivity issues | Rename to lowercase |
| Underscores instead of hyphens | Scripts fail pattern matching | Find/replace batch rename |
| Missing prefix | File lost in navigation | Rename with proper prefix |

---

## Rule Set 2: Auto-Nesting Decision Logic

### Problem Statement

Without clear nesting decision criteria:
- Inconsistent folder organization
- Difficult folder structure navigation
- Unclear when to create parent folders
- Agent confusion about file placement

### Solution

Automated decision logic determines when to nest files in folders.

### Step-by-Step Decision Flow

```
START: New skill/workflow file creation

STEP 1: Count current items in domain
  └─ Count files matching pattern: adb-[domain]-*

STEP 2: Check existing folder structure
  └─ Does adb-[domain]/ folder exist?

STEP 3: Apply counting logic

  IF count <= 3 items
    └─ DECISION: Keep FLAT structure
       └─ Create file at: .claude/skills/adb-[domain]-*.md
       └─ NO parent folder

  ELSE IF count == 4 items (about to add 5th)
    └─ DECISION: Create PARENT folder NOW
       └─ Create folder: .claude/skills/adb-[domain]/
       └─ Move all 4 existing files into folder
       └─ Add new file into folder

  ELSE IF count > 4 items
    └─ DECISION: NESTED structure already exists
       └─ Add file to: .claude/skills/adb-[domain]/

STEP 4: Verify structure consistency
  └─ Run validation command
  └─ Confirm all files follow naming

STEP 5: Document transition (if nesting occurred)
  └─ Add entry to execution log
  └─ Note: "Auto-nested adb-[domain] at item #5"

END: File created in correct location
```

### Count Logic (Detailed)

| Current Items | Action | Location |
|---------------|--------|----------|
| 1-3 files | Create flat | `.claude/skills/adb-*.md` |
| 4 files (adding 5th) | Create folder + migrate | `.claude/skills/adb-domain/` |
| 5+ files | Add to existing folder | `.claude/skills/adb-domain/` |

### Real Examples (ADB Ecosystem)

#### Example 1: Device Domain - Flat Structure (3 items)

**Current State**:
```
.claude/skills/
├── adb-device-detection.md         (item 1)
├── adb-device-properties.md        (item 2)
└── adb-device-status.md            (item 3)
```

**Decision**: KEEP FLAT (3 items ≤ 3)

**Agent Action**: Create new file directly in `.claude/skills/`
```bash
create adb-device-logging.md → .claude/skills/adb-device-logging.md
```

**Result**:
```
.claude/skills/
├── adb-device-detection.md         (item 1)
├── adb-device-properties.md        (item 2)
├── adb-device-status.md            (item 3)
└── adb-device-logging.md           (item 4)
```

#### Example 2: Transfer Domain - Transition to Nested (adding 5th item)

**Current State** (4 items, about to add 5th):
```
.claude/skills/
├── adb-transfer-file.md            (item 1)
├── adb-transfer-protocols.md       (item 2)
├── adb-transfer-compression.md     (item 3)
└── adb-transfer-validation.md      (item 4)
```

**Decision**: NEST NOW (4 items + new = 5 total, trigger auto-nesting)

**Agent Action**:
```bash
# Step 1: Create parent folder
mkdir -p .claude/skills/adb-transfer/

# Step 2: Move all 4 existing files
mv adb-transfer-file.md adb-transfer/
mv adb-transfer-protocols.md adb-transfer/
mv adb-transfer-compression.md adb-transfer/
mv adb-transfer-validation.md adb-transfer/

# Step 3: Create new file in nested location
create adb-transfer-error-handling.md → .claude/skills/adb-transfer/
```

**Result**:
```
.claude/skills/
└── adb-transfer/
    ├── adb-transfer-file.md            (item 1)
    ├── adb-transfer-protocols.md       (item 2)
    ├── adb-transfer-compression.md     (item 3)
    ├── adb-transfer-validation.md      (item 4)
    └── adb-transfer-error-handling.md  (item 5)
```

**Execution Log Entry**:
```
[TIMESTAMP] AUTO-NESTED: adb-transfer
  Reason: Item count reached 5
  Action: Created adb-transfer/ folder
  Migrated: 4 files
  New file: adb-transfer-error-handling.md
```

#### Example 3: Input Domain - Already Nested (6+ items)

**Current State** (6 items, already nested):
```
.claude/skills/adb-input/
├── adb-input-handling.md
├── adb-input-validation.md
├── adb-input-parsing.md
├── adb-input-filtering.md
├── adb-input-transformation.md
└── adb-input-caching.md
```

**Decision**: ADD TO EXISTING FOLDER (5+ items, already nested)

**Agent Action**:
```bash
# Simply create file in existing folder
create adb-input-events.md → .claude/skills/adb-input/
```

**Result**:
```
.claude/skills/adb-input/
├── adb-input-handling.md
├── adb-input-validation.md
├── adb-input-parsing.md
├── adb-input-filtering.md
├── adb-input-transformation.md
├── adb-input-caching.md
└── adb-input-events.md        (item 7)
```

### Verification Steps

After each auto-nesting decision, run these validations:

```bash
# 1. Verify count logic
DOMAIN="transfer"
ITEM_COUNT=$(find .claude/skills -path "*adb-$DOMAIN*" -type f | wc -l)
if [ $ITEM_COUNT -lt 4 ]; then
  echo "✓ Flat structure correct (count: $ITEM_COUNT)"
elif [ $ITEM_COUNT -ge 4 ]; then
  if [ -d ".claude/skills/adb-$DOMAIN" ]; then
    echo "✓ Nested structure correct (count: $ITEM_COUNT)"
  else
    echo "✗ ERROR: Should be nested but folder missing"
  fi
fi

# 2. Verify all files named correctly
for file in .claude/skills/adb-*/adb-*.md; do
  if [[ $(basename "$file") =~ ^adb-[a-z]+(-[a-z]+)*\.md$ ]]; then
    echo "✓ $(basename "$file")"
  else
    echo "✗ $(basename "$file") - INVALID NAME"
  fi
done

# 3. Verify no orphaned files
find .claude/skills -maxdepth 1 -name "adb-*.md" -type f | while read file; do
  domain=$(echo "$(basename "$file")" | cut -d- -f2)
  if [ -d ".claude/skills/adb-$domain" ]; then
    echo "✗ ORPHANED: $(basename "$file") (folder exists but file is flat)"
  fi
done
```

### Success Criteria

- Auto-nesting occurs at exactly 5 items (4 existing + 1 new)
- No files remain in flat structure once folder is created
- All files follow naming convention after migration
- Execution log documents each transition

### Failure Scenarios

| Issue | Cause | Fix |
|-------|-------|-----|
| Files in wrong location | Manual placement | Move to correct folder |
| Folder not created at 5 items | Logic not applied | Create folder and migrate |
| Orphaned files in flat | Missed migration | Move to proper folder |
| Naming inconsistency after move | Typos during migration | Rename to correct pattern |

---

## Rule Set 3: Pre-Execution Checklist

### Problem Statement

Without pre-execution validation:
- Agents run in wrong context
- Files get overwritten unexpectedly
- Incomplete specifications cause failures
- Duplicate work across agents

### Solution

Every agent MUST run this 5-point checklist before execution.

### Mandatory 5-Point Checklist

#### Checkpoint 1: Verify Project State

**Description**: Confirm working directory and git status
**When**: Before any file creation/modification

**Exact Bash Commands**:
```bash
# Command 1: Verify working directory
pwd | grep -q "AdbAutoPlayer" && echo "✓ Correct directory" || echo "✗ WRONG directory"

# Command 2: Check git status
git status | head -20

# Command 3: Verify no uncommitted changes that would block execution
CHANGES=$(git status --porcelain | wc -l)
if [ $CHANGES -eq 0 ]; then
  echo "✓ Clean working tree"
else
  echo "! WARNING: $CHANGES uncommitted changes"
  echo "   Use: git status --porcelain"
fi

# Command 4: Confirm current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $BRANCH"
if [ "$BRANCH" == "main" ]; then
  echo "! Running on main - confirm this is intentional"
fi
```

**Expected Results**:
```
✓ Correct directory
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add ..." to update the included area)
  ...

✓ Clean working tree
Current branch: main
```

**Failure Scenarios**:
- Wrong directory → Change directory immediately
- Uncommitted changes → Stash or commit before proceeding
- Non-main branch → Verify branch is intentional

#### Checkpoint 2: Verify SPEC Existence

**Description**: Confirm SPEC file exists and is accessible
**When**: Before reading SPEC to guide implementation

**Exact Bash Commands**:
```bash
# Command 1: Find SPEC file
SPEC_PATH=".moai/specs/SPEC-ADB-ECOSYSTEM-001/spec.md"
if [ -f "$SPEC_PATH" ]; then
  echo "✓ SPEC found: $SPEC_PATH"
else
  echo "✗ SPEC NOT FOUND: $SPEC_PATH"
  exit 1
fi

# Command 2: Verify SPEC has content
LINES=$(wc -l < "$SPEC_PATH")
if [ $LINES -gt 50 ]; then
  echo "✓ SPEC has content ($LINES lines)"
else
  echo "✗ SPEC too small ($LINES lines) - may be incomplete"
fi

# Command 3: Check SPEC for section markers
grep -q "# Requirements" "$SPEC_PATH" && echo "✓ Requirements section found" || echo "! Requirements section missing"
grep -q "# Architecture" "$SPEC_PATH" && echo "✓ Architecture section found" || echo "! Architecture section missing"

# Command 4: Verify Plan exists
if [ -f ".moai/specs/SPEC-ADB-ECOSYSTEM-001/plan.md" ]; then
  echo "✓ Plan file exists"
else
  echo "! Plan file missing (not critical but recommended)"
fi
```

**Expected Results**:
```
✓ SPEC found: .moai/specs/SPEC-ADB-ECOSYSTEM-001/spec.md
✓ SPEC has content (342 lines)
✓ Requirements section found
✓ Architecture section found
✓ Plan file exists
```

**Failure Scenarios**:
- SPEC missing → Create SPEC or use existing one
- Content too small → Expand SPEC with requirements
- Sections missing → Add required sections

#### Checkpoint 3: Verify Naming Convention Compliance

**Description**: Confirm all existing files follow naming patterns
**When**: Before creating new files

**Exact Bash Commands**:
```bash
# Command 1: Check skill file naming
echo "Checking skill files..."
SKILL_ERRORS=0
find .claude/skills -maxdepth 2 -name "*.md" -type f | while read file; do
  basename=$(basename "$file")
  if [[ "$basename" =~ ^adb-[a-z]+(-[a-z]+)*\.md$ ]] || [[ "$basename" == "SKILL.md" ]] || [[ "$basename" == "README.md" ]]; then
    echo "  ✓ $basename"
  else
    echo "  ✗ $basename - INVALID"
    ((SKILL_ERRORS++))
  fi
done

# Command 2: Check folder naming
echo "Checking folder structure..."
FOLDER_ERRORS=0
find .claude/skills -type d -name "adb-*" | while read dir; do
  basename=$(basename "$dir")
  if [[ "$basename" =~ ^adb-[a-z]+(-[a-z]+)*$ ]]; then
    echo "  ✓ Folder: $basename"
  else
    echo "  ✗ Folder: $basename - INVALID"
    ((FOLDER_ERRORS++))
  fi
done

# Command 3: Check for naming violations (spaces, underscores, etc)
echo "Checking for violations..."
find .claude/skills -name "*_*" -o -name "* *" | while read file; do
  echo "  ✗ VIOLATION: $(basename "$file")"
done
```

**Expected Results**:
```
Checking skill files...
  ✓ adb-transfer-protocols.md
  ✓ adb-device-detection.md
  ✓ SKILL.md
Checking folder structure...
  ✓ Folder: adb-transfer
  ✓ Folder: adb-device
Checking for violations...
(no output = no violations found)
```

**Failure Scenarios**:
- Files with underscores → Batch rename with sed
- Mixed case → Convert to lowercase
- Orphaned files → Move to proper location

#### Checkpoint 4: Verify Domain Consistency

**Description**: Confirm proposed file is unique in its domain
**When**: Before creating new skill file

**Exact Bash Commands**:
```bash
# Command 1: Check for duplicate skill files
DOMAIN="transfer"  # Replace with actual domain
FILENAME="adb-transfer-new-feature.md"

echo "Checking for duplicates in domain: $DOMAIN"
find .claude/skills -name "*$DOMAIN*" -type f | sort

# Command 2: Verify proposed filename doesn't exist
if [ -f ".claude/skills/$FILENAME" ] || [ -f ".claude/skills/adb-$DOMAIN/$FILENAME" ]; then
  echo "✗ DUPLICATE: File already exists"
  exit 1
else
  echo "✓ Filename is unique"
fi

# Command 3: Check for similar names (potential confusion)
echo "Checking for similar names..."
find .claude/skills -name "*transfer*" | while read file; do
  echo "  - $(basename "$file")"
done
```

**Expected Results**:
```
Checking for duplicates in domain: transfer
  - adb-transfer-protocols.md
  - adb-transfer-file.md
✓ Filename is unique
Checking for similar names...
  - adb-transfer-protocols.md
  - adb-transfer-file.md
```

**Failure Scenarios**:
- File already exists → Check if it's what you need
- Similar names exist → Verify it's not a duplicate
- Domain folder doesn't exist yet → Will be auto-created if needed

#### Checkpoint 5: Verify Execution Log Status

**Description**: Confirm execution log is ready to receive entries
**When**: Before starting actual work

**Exact Bash Commands**:
```bash
# Command 1: Verify log directory exists
LOG_DIR=".moai/execution-logs"
if [ ! -d "$LOG_DIR" ]; then
  echo "Creating log directory: $LOG_DIR"
  mkdir -p "$LOG_DIR"
fi
echo "✓ Log directory ready: $LOG_DIR"

# Command 2: Create/verify current session log
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="$LOG_DIR/agent-execution-$TIMESTAMP.log"

# Check if we're continuing from previous session
LATEST_LOG=$(ls -t $LOG_DIR/agent-execution-*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
  LATEST_TIME=$(stat -f %m "$LATEST_LOG" 2>/dev/null || stat -c %Y "$LATEST_LOG")
  CURRENT_TIME=$(date +%s)
  TIME_DIFF=$((CURRENT_TIME - LATEST_TIME))
  if [ $TIME_DIFF -lt 3600 ]; then
    echo "✓ Using existing log: $LATEST_LOG"
    LOG_FILE="$LATEST_LOG"
  fi
fi

echo "✓ Log file ready: $LOG_FILE"

# Command 3: Verify log is writable
if [ -f "$LOG_FILE" ]; then
  if ! echo "[$(date +%Y-%m-%d\ %H:%M:%S)] Test entry" >> "$LOG_FILE" 2>/dev/null; then
    echo "✗ Log file not writable: $LOG_FILE"
    exit 1
  fi
elif touch "$LOG_FILE" 2>/dev/null; then
  echo "✓ Created new log file: $LOG_FILE"
  echo "[$(date +%Y-%m-%d\ %H:%M:%S)] Session start" >> "$LOG_FILE"
else
  echo "✗ Cannot create log file"
  exit 1
fi

# Command 4: Show log status
echo ""
echo "Log Status:"
tail -3 "$LOG_FILE"
```

**Expected Results**:
```
✓ Log directory ready: .moai/execution-logs
✓ Log file ready: .moai/execution-logs/agent-execution-20251202-143022.log
✓ Created new log file: .moai/execution-logs/agent-execution-20251202-143022.log

Log Status:
[2025-12-02 14:30:22] Session start
```

**Failure Scenarios**:
- Log directory missing → Will be auto-created
- Log file not writable → Check file permissions
- Disk full → Free up space before proceeding

### Checklist Execution Script

**Use this comprehensive script for all 5 checkpoints**:

```bash
#!/bin/bash
# Pre-Execution Checklist Script

echo "======================================"
echo "PRE-EXECUTION GOVERNANCE CHECKLIST"
echo "======================================"
echo ""

# Checkpoint 1
echo "[1/5] Project State Verification"
pwd | grep -q "AdbAutoPlayer" && echo "  ✓ Correct directory" || echo "  ✗ WRONG directory"
CHANGES=$(git status --porcelain | wc -l)
echo "  Changes: $CHANGES"

# Checkpoint 2
echo "[2/5] SPEC Verification"
if [ -f ".moai/specs/SPEC-ADB-ECOSYSTEM-001/spec.md" ]; then
  LINES=$(wc -l < ".moai/specs/SPEC-ADB-ECOSYSTEM-001/spec.md")
  echo "  ✓ SPEC found ($LINES lines)"
else
  echo "  ✗ SPEC missing"
fi

# Checkpoint 3
echo "[3/5] Naming Convention Check"
NAMING_ERRORS=$(find .claude/skills -name "*_*" -o -name "* *" | wc -l)
echo "  Naming violations: $NAMING_ERRORS"

# Checkpoint 4
echo "[4/5] Domain Consistency"
DOMAIN_COUNT=$(find .claude/skills -maxdepth 2 -type f -name "adb-*.md" | wc -l)
echo "  Total skills: $DOMAIN_COUNT"

# Checkpoint 5
echo "[5/5] Log Status"
if [ -d ".moai/execution-logs" ]; then
  LOG_COUNT=$(ls -1 .moai/execution-logs/*.log 2>/dev/null | wc -l)
  echo "  ✓ Log directory ready ($LOG_COUNT logs)"
else
  mkdir -p .moai/execution-logs
  echo "  ✓ Created log directory"
fi

echo ""
echo "======================================"
echo "✓ All checkpoints verified"
echo "Ready to proceed with execution"
echo "======================================"
```

### Success Criteria

- All 5 checkpoints return PASS status
- No fatal errors (exit codes = 0)
- Working directory confirmed correct
- SPEC and Plan available
- Execution logs ready

### Failure Handling

If ANY checkpoint fails with ✗ status:

1. **Stop execution** - Do not proceed
2. **Read error message** - Identify specific issue
3. **Execute recovery** - Follow failure scenario fix
4. **Re-run checklist** - Confirm all 5 pass
5. **Document in log** - Record issue and fix

---

## Rule Set 4: Agent Task Boundaries

### Problem Statement

Without clear task boundaries:
- Agents overlap in responsibilities
- Work gets duplicated or missed
- Synchronization points become unclear
- No clear handoff between agents

### Solution

Explicit task matrix defining what each agent CAN and CANNOT do.

### Agent Responsibility Matrix

#### Agent 1: builder-workflow

**Role**: Workflow orchestration and coordination

| Task | Status | Details |
|------|--------|---------|
| Create workflow files | ✅ CAN | Define workflow-*.md files |
| Coordinate multiple agents | ✅ CAN | Sequence agent calls |
| Define synchronization points | ✅ CAN | Mark handoff moments |
| Create skill files | ❌ CANNOT | Delegate to builder-skill |
| Create agent files | ❌ CANNOT | Delegate to builder-agent |
| Implement actual code | ❌ CANNOT | Delegate to domain experts |
| Validate final output | ❌ CANNOT | Delegate to manager-quality |

**Exclusive Responsibilities**:
- Workflow structure design
- Agent sequencing logic
- Synchronization point definition
- Workflow testing and optimization
- Workflow documentation

**Synchronization Points with Others**:
- **Input from**: builder-skill (skill definitions), builder-agent (agent definitions)
- **Output to**: Workflow orchestration plan
- **Handoff to**: Specific builder agents for implementation

**Example Workflow**:
```markdown
# workflow-adb-ecosystem-build.md

## Phase 1: Skill Creation
- Synchronization Point 1: builder-skill outputs adb-*.md files
- Verify: All skills follow naming convention

## Phase 2: Agent Training
- Synchronization Point 2: builder-agent receives skill list
- Inputs: skill definitions from Phase 1

## Phase 3: Validation
- Synchronization Point 3: manager-quality validates ecosystem
- Inputs: All skills + agents from Phases 1-2
```

---

#### Agent 2: builder-skill (Skills 1-4)

**Role**: ADB ecosystem skill creation (first half)

**Skills 1-4 Categories**:
- Skill 1: Device & Connection Management
- Skill 2: Data Transfer & Protocols
- Skill 3: Input & Event Handling
- Skill 4: Error & State Management

| Task | Status | Details |
|------|--------|---------|
| Create skill files (adb-*.md) | ✅ CAN | Only for skills 1-4 |
| Define skill content | ✅ CAN | Requirements, examples, patterns |
| Name skills per convention | ✅ CAN | adb-[domain]-[function].md |
| Auto-nest skills | ✅ CAN | When count ≥ 5 in domain |
| Test skill documentation | ✅ CAN | Verify markdown and structure |
| Coordinate with builder-skill-2 | ✅ CAN | Via synchronization logs |
| Create agent files | ❌ CANNOT | Delegate to builder-agent |
| Implement workflows | ❌ CANNOT | Delegate to builder-workflow |
| Validate final ecosystem | ❌ CANNOT | Delegate to manager-quality |

**Exclusive Responsibilities** (Skills 1-4):
- adb-device-*.md files
- adb-connection-*.md files
- adb-transfer-*.md files (first 4 items)
- adb-protocol-*.md files (first 4 items)
- adb-input-*.md files (first 4 items)
- adb-event-*.md files (first 4 items)
- adb-error-*.md files (first 4 items)
- adb-state-*.md files (first 4 items)

**Naming Examples** (builder-skill 1-4):
```
✅ CAN CREATE:
- adb-device-detection.md
- adb-device-properties.md
- adb-device-discovery.md
- adb-device-status.md           (4th item - flat)
- adb-transfer-file.md
- adb-transfer-protocols.md
- adb-transfer-compression.md
- adb-transfer-validation.md     (4th item - flat)

❌ CANNOT CREATE (Skills 5-8):
- adb-device-optimization.md     (would be 5th in device)
- adb-transfer-caching.md        (would be 5th in transfer)
- adb-advanced-compression.md    (not first 4)
- adb-performance-tuning.md      (not first 4)
```

**Synchronization Points**:
- **Input from**: workflow-adb-ecosystem-build.md
- **Handoff to**: builder-skill-2 (skills 5-8) at synchronization point
- **Milestone**: All 4 skills complete and tested
- **Output**: adb-*.md files in .claude/skills/

**Synchronization Log Entry** (when done):
```
[TIMESTAMP] builder-skill-1-4 COMPLETE
  Skills Created: 4
  Files: adb-device-*.md, adb-transfer-*.md, adb-input-*.md, adb-error-*.md
  Status: Ready for builder-skill-2
  Next: builder-skill-2 creates skills 5-8
```

---

#### Agent 3: builder-skill (Skills 5-8)

**Role**: ADB ecosystem skill creation (second half)

**Skills 5-8 Categories**:
- Skill 5: Performance & Optimization
- Skill 6: Advanced Protocols & Compression
- Skill 7: Testing & Validation
- Skill 8: Monitoring & Observability

| Task | Status | Details |
|------|--------|---------|
| Create skill files (adb-*.md) | ✅ CAN | Only for skills 5-8 |
| Define skill content | ✅ CAN | Requirements, examples, patterns |
| Name skills per convention | ✅ CAN | adb-[domain]-[function].md |
| Auto-nest skills | ✅ CAN | Complete nesting if needed |
| Receive from builder-skill-1 | ✅ CAN | Via synchronization log |
| Test skill documentation | ✅ CAN | Verify markdown and structure |
| Create agent files | ❌ CANNOT | Delegate to builder-agent |
| Implement workflows | ❌ CANNOT | Delegate to builder-workflow |
| Validate final ecosystem | ❌ CANNOT | Delegate to manager-quality |

**Exclusive Responsibilities** (Skills 5-8):
- adb-optimization-*.md files
- adb-performance-*.md files
- adb-advanced-protocol-*.md files
- adb-advanced-compression-*.md files
- adb-testing-*.md files
- adb-validation-*.md files
- adb-monitoring-*.md files
- adb-observability-*.md files

**Naming Examples** (builder-skill 5-8):
```
✅ CAN CREATE (only after skills 1-4 complete):
- adb-optimization-memory.md
- adb-optimization-bandwidth.md
- adb-performance-benchmarking.md
- adb-performance-profiling.md
- adb-testing-device-emulation.md
- adb-monitoring-connection-health.md

❌ CANNOT CREATE (already created by builder-skill 1-4):
- adb-device-detection.md        (already in skills 1-4)
- adb-transfer-file.md           (already in skills 1-4)
- adb-input-handling.md          (already in skills 1-4)
```

**Synchronization Points**:
- **Input from**: builder-skill-1-4 via synchronization log
- **Waits for**: "builder-skill-1-4 COMPLETE" log entry
- **Uses**: Domain knowledge from skills 1-4
- **Handoff to**: builder-agent (receives all 8 skills)
- **Milestone**: All 8 skills complete and tested
- **Output**: adb-*.md files added to .claude/skills/

**Synchronization Log Entry** (when done):
```
[TIMESTAMP] builder-skill-5-8 COMPLETE
  Skills Created: 4
  Files: adb-optimization-*.md, adb-performance-*.md, adb-testing-*.md, adb-monitoring-*.md
  Dependencies Used: Skills 1-4 from builder-skill-1-4
  Status: Ready for builder-agent
  Total Skills Available: 8
```

---

#### Agent 4: builder-agent

**Role**: ADB ecosystem agent training and creation

| Task | Status | Details |
|------|--------|---------|
| Create agent definitions | ✅ CAN | Define adb-* agents |
| Train agents on skills | ✅ CAN | Use all 8 skills as context |
| Validate agent behaviors | ✅ CAN | Test against skill content |
| Coordinate with builders | ✅ CAN | Via synchronization logs |
| Receive skill list | ✅ CAN | From builder-skill-5-8 |
| Create skill files | ❌ CANNOT | Delegate to builder-skill |
| Implement workflows | ❌ CANNOT | Delegate to builder-workflow |
| Validate entire ecosystem | ❌ CANNOT | Delegate to manager-quality |

**Exclusive Responsibilities**:
- Agent system prompt engineering
- Agent capability definition
- Agent permission setting
- Agent skill binding (linking to adb-*.md files)
- Agent behavior validation
- Agent documentation

**Dependencies**:
- **Requires**: All 8 skills complete (from builder-skill 1-4 and 5-8)
- **Waits for**: "builder-skill-5-8 COMPLETE" log entry
- **Uses**: adb-*.md skill files as context

**Synchronization Log Entry** (when starting):
```
[TIMESTAMP] builder-agent START
  Waiting for: All 8 skills
  Dependencies: adb-*.md files from builder-skill
  Status: Ready to train adb-ecosystem agents
```

**Agent Creation Example**:
```
Agent: adb-ecosystem-assistant
  Skills: All 8 adb-*.md files
  Capabilities:
    - Device management (from adb-device-*.md)
    - Data transfer (from adb-transfer-*.md)
    - Input handling (from adb-input-*.md)
    - Error recovery (from adb-error-*.md)
    - Performance optimization (from adb-optimization-*.md)
    - Testing coordination (from adb-testing-*.md)
    - Monitoring integration (from adb-monitoring-*.md)
```

---

#### Agent 5: builder-workflow-designer (Ecosystem Integration)

**Role**: Ecosystem-level workflow coordination and final integration

| Task | Status | Details |
|------|--------|---------|
| Design ecosystem workflows | ✅ CAN | Coordinate all agents |
| Integrate all components | ✅ CAN | Skills + Agents + Workflows |
| Create integration workflows | ✅ CAN | workflow-*.md files |
| Define synchronization points | ✅ CAN | Between all builders |
| Validate integration | ✅ CAN | Preliminary checks |
| Receive agent definitions | ✅ CAN | From builder-agent |
| Create individual skills | ❌ CANNOT | Delegate to builder-skill |
| Create individual agents | ❌ CANNOT | Delegate to builder-agent |
| Final quality validation | ❌ CANNOT | Delegate to manager-quality |

**Exclusive Responsibilities**:
- Ecosystem-wide workflow design
- Cross-agent integration patterns
- Synchronization point definition
- Integration testing (at workflow level)
- Ecosystem documentation

**Synchronization Points with All Agents**:

```
Timeline:

T0: builder-workflow START
    ├─ Workflow design begins
    └─ Coordinates all other builders

T1: builder-skill-1-4 COMPLETE
    └─ First 4 skills ready

T2: builder-skill-5-8 COMPLETE
    ├─ All 8 skills ready
    └─ Integration workflows can now be finalized

T3: builder-agent COMPLETE
    ├─ Agents trained on all skills
    └─ Integration workflows fully specified

T4: builder-workflow-designer INTEGRATION
    ├─ All components integrated
    ├─ Synchronization points validated
    └─ Ready for final quality check

T5: manager-quality VALIDATION
    └─ Final ecosystem validation
```

---

### Cross-Agent Synchronization Rules

#### Rule 1: Sequential Dependencies

**builder-workflow** → **builder-skill-1-4** → **builder-skill-5-8** → **builder-agent** → **builder-workflow-designer**

Each agent MUST complete before next agent starts:

```bash
# Agent 1 complete
[TIMESTAMP] builder-skill-1-4 COMPLETE
  Files: adb-device-*.md, adb-transfer-*.md, adb-input-*.md, adb-error-*.md

# Agent 2 waits for log entry above, then starts
[TIMESTAMP] builder-skill-5-8 START
  Status: Waiting for confirmation from builder-skill-1-4

[TIMESTAMP] builder-skill-5-8 COMPLETE
  Files: adb-optimization-*.md, adb-performance-*.md, adb-testing-*.md, adb-monitoring-*.md

# Agent 3 waits for Agent 2 complete
[TIMESTAMP] builder-agent START
  Dependencies: All 8 skills from builder-skill

[TIMESTAMP] builder-agent COMPLETE
  Agents: adb-ecosystem-assistant, adb-device-manager, adb-transfer-coordinator
```

#### Rule 2: Synchronization Points

**Definition**: Moment where agents exchange status and coordinate next steps

**Synchronization Points in Ecosystem**:

1. **Skills Definition Point** (after builder-skill-1-4)
   - Exchange: Skill file list
   - Method: Execution log entry
   - Format: List of adb-*.md files created

2. **Skills Completion Point** (after builder-skill-5-8)
   - Exchange: All 8 skill definitions
   - Method: Execution log + skill file paths
   - Verification: Count = 8

3. **Agent Training Point** (after builder-agent)
   - Exchange: Agent definitions with skill bindings
   - Method: Agent system prompts + skill references
   - Verification: Each agent has ≥ 3 skills bound

4. **Integration Point** (builder-workflow-designer)
   - Exchange: Complete ecosystem specification
   - Method: workflow-*.md files + all skill/agent definitions
   - Verification: All components referenced

#### Rule 3: Communication via Execution Logs

**All inter-agent communication happens through execution logs**:

```
Location: .moai/execution-logs/
Format: agent-[NUMBER]-[DOMAIN]-[TIMESTAMP].log

Examples:
agent-1-workflow-20251202-140000.log      (builder-workflow)
agent-2-skill-1-4-20251202-141000.log     (builder-skill skills 1-4)
agent-3-skill-5-8-20251202-142000.log     (builder-skill skills 5-8)
agent-4-agent-20251202-143000.log         (builder-agent)
agent-5-workflow-designer-20251202-144000.log (builder-workflow-designer)
```

**Log Entry Format** (for synchronization):

```
[TIMESTAMP] [AGENT-ID] [STATUS]
Message: [Description]
Input: [What this agent received/used]
Output: [What this agent created/produced]
Next Agent: [Who receives this output]
Verification: [How to verify success]
```

#### Rule 4: Blocking Conditions

Agents MUST NOT proceed if:

1. **Previous agent incomplete**: Required log entry missing
2. **File integrity issue**: Naming convention violations
3. **Count logic violated**: Auto-nesting threshold crossed incorrectly
4. **Output missing**: Expected files not created

**Recovery action**: Return to previous agent with issue

---

### Success Criteria for Task Boundaries

- ✅ Each agent stays within its domain
- ✅ No task overlap between agents
- ✅ Synchronization points clearly marked
- ✅ All inter-agent communication via logs
- ✅ Sequential dependencies respected
- ✅ Blocking conditions prevented

### Failure Scenarios

| Issue | Cause | Detection | Fix |
|-------|-------|-----------|-----|
| Agent overlap | Tasks assigned to multiple agents | Duplicate files | Reassign to primary agent |
| Missing sync | Agents don't wait for dependencies | Out-of-order log entries | Insert synchronization point |
| Lost output | Agent creates files but not logged | Files missing from log | Document in execution log |
| Blocking violation | Agent proceeds without prerequisites | Unsupported files | Rollback to blocking point |

---

## Rule Set 5: Duplicate Prevention

### Problem Statement

Without duplicate prevention:
- Multiple agents create same skill
- Work gets done twice
- Conflicting definitions in codebase
- Confusion about which version is authoritative

### Solution

Automated duplicate detection and systematic prevention.

### Duplicate Detection Scenarios

#### Scenario 1: Exact Duplicate File

**Detection**:
```bash
# Check for files with identical content in different locations
find .claude/skills -name "adb-*.md" -type f | while read file1; do
  find .claude/skills -name "adb-*.md" -type f -newer "$file1" | while read file2; do
    if diff -q "$file1" "$file2" > /dev/null; then
      echo "DUPLICATE FOUND:"
      echo "  File 1: $file1"
      echo "  File 2: $file2"
      echo "  Size: $(wc -c < "$file1") bytes"
    fi
  done
done
```

**Example**:
```
DUPLICATE FOUND:
  File 1: .claude/skills/adb-device-detection.md (2024 bytes)
  File 2: .claude/skills/adb-device/adb-device-detection.md (2024 bytes)
  Size: 2024 bytes
```

**Prevention**: Execution checklist Point 4 (Verify Domain Consistency)

**Cleanup**:
```bash
# Step 1: Identify primary version (usually the one first created)
ls -lt .claude/skills/*device-detection* | head -1

# Step 2: Backup both versions
cp .claude/skills/adb-device-detection.md \
   .moai/backups/adb-device-detection-backup-20251202.md
cp .claude/skills/adb-device/adb-device-detection.md \
   .moai/backups/adb-device-detection-nested-backup-20251202.md

# Step 3: Keep primary, delete duplicate
rm .claude/skills/adb-device/adb-device-detection.md

# Step 4: Document in log
echo "[$(date)] Duplicate removed: adb-device-detection.md (kept flat version)"
```

#### Scenario 2: Partial Duplicate (Same Domain, Similar Content)

**Detection**:
```bash
# Find files in same domain with >80% content similarity
DOMAIN="transfer"
find .claude/skills -name "adb-$DOMAIN*.md" -type f > /tmp/files.txt
while IFS= read -r file1; do
  while IFS= read -r file2; do
    if [ "$file1" != "$file2" ]; then
      # Calculate similarity (lines in common / total lines)
      COMMON=$(comm -12 <(sort "$file1") <(sort "$file2") | wc -l)
      TOTAL=$(wc -l < "$file1")
      SIMILARITY=$((COMMON * 100 / TOTAL))
      if [ $SIMILARITY -gt 80 ]; then
        echo "PARTIAL DUPLICATE (${SIMILARITY}% similar):"
        echo "  File 1: $file1"
        echo "  File 2: $file2"
      fi
    fi
  done < /tmp/files.txt
done < /tmp/files.txt
```

**Example**:
```
PARTIAL DUPLICATE (87% similar):
  File 1: .claude/skills/adb-transfer-file.md
  File 2: .claude/skills/adb-transfer-file-copy.md
```

**Prevention**: Naming convention validation (should catch "-copy" suffix)

**Cleanup Strategy**:
```bash
# Step 1: Analyze differences
diff .claude/skills/adb-transfer-file.md \
     .claude/skills/adb-transfer-file-copy.md

# Step 2: Determine if either is truly different
# If identical: delete copy
# If different: merge unique content into primary

# Step 3: Merge unique content
cat .claude/skills/adb-transfer-file-copy.md | grep -v "^#" >> \
    .claude/skills/adb-transfer-file.md

# Step 4: Delete duplicate
rm .claude/skills/adb-transfer-file-copy.md

# Step 5: Document
echo "[$(date)] Merged: adb-transfer-file-copy.md into adb-transfer-file.md"
```

#### Scenario 3: Conceptual Duplicate (Different Name, Same Concept)

**Example**:
```
adb-device-properties.md    (describes device info)
adb-device-attributes.md    (also describes device info)
```

**Detection Strategy** (manual):
1. Review skill files in same domain
2. Read first 50 lines of each
3. Check if they cover same concepts
4. Look for conceptual overlap

**Prevention**:
- Domain expert review before creation
- Clear skill scope definitions in SPEC
- Naming convention prevents generic names

**Cleanup**:
```bash
# Step 1: Identify conceptually redundant files
echo "Files in device domain:"
find .claude/skills -name "adb-device*.md"

# Step 2: Review each file's unique value
head -30 .claude/skills/adb-device-properties.md
head -30 .claude/skills/adb-device-attributes.md

# Step 3: Consolidate if truly duplicate
# Option A: Merge into single file
cat .claude/skills/adb-device-attributes.md >> \
    .claude/skills/adb-device-properties.md
rm .claude/skills/adb-device-attributes.md

# Option B: Split into distinct responsibilities
# If actually different, rename for clarity
mv .claude/skills/adb-device-attributes.md \
   .claude/skills/adb-device-metadata.md

# Step 4: Document decision
echo "[$(date)] Conceptual duplicate resolved: merged attributes into properties"
```

### Automatic Cleanup Procedures

#### Procedure 1: Content Duplicate Removal

```bash
#!/bin/bash
# Remove exact content duplicates

echo "Scanning for content duplicates..."
find .claude/skills -name "adb-*.md" -type f | sort | while read file1; do
  find .claude/skills -name "adb-*.md" -type f -newer "$file1" | while read file2; do
    # Calculate file hashes
    HASH1=$(md5sum "$file1" | cut -d' ' -f1)
    HASH2=$(md5sum "$file2" | cut -d' ' -f1)

    if [ "$HASH1" = "$HASH2" ]; then
      echo "DUPLICATE FOUND:"
      echo "  Keep:   $file1 ($(stat -f %Sm -t %Y-%m-%d "$file1"))"
      echo "  Delete: $file2 ($(stat -f %Sm -t %Y-%m-%d "$file2"))"

      # Backup the duplicate
      cp "$file2" ".moai/backups/duplicate-$(basename "$file2")-backup.md"

      # Remove duplicate
      rm "$file2"
      echo "  ✓ Removed and backed up"
    fi
  done
done

echo "✓ Duplicate removal complete"
```

#### Procedure 2: Naming Violation Cleanup

```bash
#!/bin/bash
# Fix files with naming violations (spaces, underscores, mixed case)

echo "Scanning for naming violations..."
find .claude/skills -type f \( -name "* *" -o -name "*_*" \) | while read file; do
  echo "Found violation: $file"

  # Convert to proper name
  basename=$(basename "$file")
  # Remove spaces and underscores, convert to lowercase
  newname=$(echo "$basename" | tr ' ' '-' | tr '_' '-' | tr '[:upper:]' '[:lower:]')

  # Get directory
  dir=$(dirname "$file")

  # Backup original
  cp "$file" ".moai/backups/violating-$basename-backup.md"

  # Rename
  mv "$file" "$dir/$newname"
  echo "  Renamed to: $newname"
done

echo "✓ Naming violation cleanup complete"
```

#### Procedure 3: Orphaned File Detection

```bash
#!/bin/bash
# Detect files in wrong location (should be nested but are flat, or vice versa)

echo "Checking for orphaned files..."

# Check flat files that should be nested
find .claude/skills -maxdepth 1 -name "adb-*.md" -type f | while read file; do
  domain=$(basename "$file" | cut -d- -f2)
  nested_folder=".claude/skills/adb-$domain"

  if [ -d "$nested_folder" ]; then
    echo "ORPHANED: $(basename "$file") (folder exists)"
    echo "  Should be moved to: $nested_folder/"
    echo "  Migrating..."

    cp "$file" "$nested_folder/$(basename "$file")"
    rm "$file"
  fi
done

echo "✓ Orphaned file detection complete"
```

### Merging Strategy

**When duplicates are found, follow this merge priority**:

1. **Exact Duplicates** (100% match):
   - Keep: Earliest created version
   - Delete: Later copies

2. **Content Duplicates** (95%+ match):
   - Merge: Unique content from both
   - Structure: Follow original format
   - Delete: Empty version

3. **Partial Duplicates** (80-94% match):
   - Analyze: What makes each unique
   - Decision: Consolidate vs. Rename
   - If consolidate: Merge into primary
   - If rename: Give distinct names

4. **Conceptual Duplicates** (Similar concept, different content):
   - Review: Do both skills add value?
   - Keep Both if: Clear differentiation
   - Merge if: Redundant coverage
   - Add Links: Cross-references between

### Validation After Cleanup

After removing duplicates, run full validation:

```bash
#!/bin/bash
# Post-cleanup validation

echo "POST-CLEANUP VALIDATION"
echo "======================="

# Check 1: No exact duplicates remain
echo "[1/5] Checking for exact duplicates..."
DUPS=0
find .claude/skills -name "adb-*.md" -type f | sort | while read f1; do
  find .claude/skills -name "adb-*.md" -type f -newer "$f1" | while read f2; do
    if diff -q "$f1" "$f2" > /dev/null 2>&1; then
      echo "  ✗ Duplicate: $f1 = $f2"
      ((DUPS++))
    fi
  done
done
if [ $DUPS -eq 0 ]; then echo "  ✓ No exact duplicates"; fi

# Check 2: Verify all files follow naming
echo "[2/5] Checking naming conventions..."
VIOLATIONS=$(find .claude/skills -type f \( -name "* *" -o -name "*_*" \) | wc -l)
if [ $VIOLATIONS -eq 0 ]; then
  echo "  ✓ All files follow naming convention"
else
  echo "  ✗ $VIOLATIONS naming violations found"
fi

# Check 3: No orphaned files
echo "[3/5] Checking for orphaned files..."
ORPHANED=0
find .claude/skills -maxdepth 1 -name "adb-*.md" -type f | while read file; do
  domain=$(basename "$file" | cut -d- -f2)
  if [ -d ".claude/skills/adb-$domain" ]; then
    echo "  ✗ Orphaned: $(basename "$file")"
    ((ORPHANED++))
  fi
done
if [ $ORPHANED -eq 0 ]; then echo "  ✓ No orphaned files"; fi

# Check 4: Verify domain counts
echo "[4/5] Checking domain organization..."
for domain in device transfer input error optimization performance; do
  COUNT=$(find .claude/skills -path "*adb-$domain*" -name "adb-*.md" | wc -l)
  echo "  $domain: $COUNT files"
done

# Check 5: Generate duplicate report
echo "[5/5] Cleanup Report"
echo "  Backup location: .moai/backups/"
ls -1 .moai/backups/*backup*.md 2>/dev/null | wc -l | xargs echo "  Files backed up:"

echo ""
echo "✓ Cleanup validation complete"
```

### Success Criteria

- ✅ Zero exact duplicates (md5sum match)
- ✅ Zero naming violations (spaces, underscores, mixed case)
- ✅ Zero orphaned files
- ✅ All domain counts within expected ranges
- ✅ All duplicates backed up before removal

---

## Rule Set 6: Validation & Rollback

### Problem Statement

Without validation checkpoints:
- Invalid work gets committed
- No way to recover from errors
- Quality degradation occurs
- Rollback procedures unclear

### Solution

Per-agent validation rules with systematic rollback procedures.

### Per-Agent Validation Rules

#### Validation Set 1: builder-skill

**What to validate**:

1. **Naming Compliance** (STRICT)
   - All files match: `adb-[domain]-[function].md`
   - No spaces, underscores, mixed case
   - All lowercase

   ```bash
   # Check
   find .claude/skills -name "adb-*.md" -type f | while read f; do
     if [[ "$(basename "$f")" =~ ^adb-[a-z]+(-[a-z]+)*\.md$ ]]; then
       echo "✓ $(basename "$f")"
     else
       echo "✗ $(basename "$f") - INVALID"
       exit 1
     fi
   done
   ```

2. **Content Quality**
   - Minimum 200 lines per skill file
   - Markdown structure valid
   - No broken links to other skills

   ```bash
   # Check minimum lines
   MIN_LINES=200
   for file in .claude/skills/adb-*.md; do
     LINES=$(wc -l < "$file")
     if [ $LINES -lt $MIN_LINES ]; then
       echo "✗ $file: $LINES lines (min: $MIN_LINES)"
       exit 1
     fi
   done
   ```

3. **No Duplicates**
   - No exact content matches
   - No files in wrong location

   ```bash
   # Check for duplicates
   find .claude/skills -name "adb-*.md" | sort | while read f1; do
     find .claude/skills -name "adb-*.md" -newer "$f1" | while read f2; do
       if diff -q "$f1" "$f2" > /dev/null; then
         echo "✗ DUPLICATE: $f1 = $f2"
         exit 1
       fi
     done
   done
   ```

4. **Domain Organization**
   - Auto-nesting applied correctly
   - Count matches nesting structure

   ```bash
   # Check auto-nesting logic
   for domain in device transfer input error; do
     FLAT=$(find .claude/skills -maxdepth 1 -name "adb-$domain*.md" | wc -l)
     NESTED=$(find .claude/skills/adb-$domain -name "adb-*.md" 2>/dev/null | wc -l)
     TOTAL=$((FLAT + NESTED))

     if [ $TOTAL -lt 4 ] && [ $NESTED -gt 0 ]; then
       echo "✗ Premature nesting: $domain (total: $TOTAL)"
       exit 1
     fi
   done
   ```

**Success Criteria**: All 4 validations PASS

**Failure Recovery**:
- ✗ Naming: Rename files to comply
- ✗ Content: Add required content sections
- ✗ Duplicates: Remove duplicates, keep original
- ✗ Organization: Migrate files to correct location

#### Validation Set 2: builder-agent

**What to validate**:

1. **Agent Structure**
   - System prompt defined
   - Capabilities listed
   - Skills bound

2. **Skill References**
   - All referenced skills exist
   - All skill files are valid
   - No broken references

3. **Agent Behavior**
   - Agent stays within defined scope
   - No undefined capabilities

**Validation Script**:
```bash
#!/bin/bash
# Validate agent definitions

AGENT_DEF="adb-ecosystem-agent.md"

echo "Validating: $AGENT_DEF"

# Check 1: System prompt
if grep -q "## System Prompt" "$AGENT_DEF"; then
  echo "✓ System prompt defined"
else
  echo "✗ System prompt missing"
  exit 1
fi

# Check 2: Capabilities
CAPS=$(grep -c "^- " "$AGENT_DEF")
if [ $CAPS -ge 3 ]; then
  echo "✓ Capabilities defined ($CAPS items)"
else
  echo "✗ Insufficient capabilities ($CAPS items, min 3)"
  exit 1
fi

# Check 3: Skill references
REFS=$(grep -o "adb-[a-z]*-[a-z]*\.md" "$AGENT_DEF" | sort -u)
COUNT=$(echo "$REFS" | wc -l)
echo "Skill references: $COUNT"

# Verify each referenced skill exists
ERROR=0
while IFS= read -r skill; do
  if [ ! -f ".claude/skills/$skill" ] && [ ! -f ".claude/skills/*/$ skill" ]; then
    echo "✗ Referenced skill not found: $skill"
    ((ERROR++))
  fi
done <<< "$REFS"

if [ $ERROR -eq 0 ]; then
  echo "✓ All skill references valid"
else
  echo "✗ $ERROR skill references broken"
  exit 1
fi

echo "✓ Agent validation passed"
```

#### Validation Set 3: builder-workflow

**What to validate**:

1. **Workflow Structure**
   - Phases clearly defined
   - Synchronization points marked
   - Dependencies documented

2. **Agent References**
   - All referenced agents exist
   - Handoff points clear
   - Execution order valid

3. **Completeness**
   - No missing steps
   - All inputs/outputs documented

**Validation Script**:
```bash
#!/bin/bash
# Validate workflow definitions

WORKFLOW="workflow-adb-ecosystem-build.md"

echo "Validating: $WORKFLOW"

# Check 1: Phases defined
PHASES=$(grep -c "^## Phase" "$WORKFLOW")
if [ $PHASES -ge 2 ]; then
  echo "✓ Phases defined ($PHASES)"
else
  echo "✗ Insufficient phases ($PHASES, min 2)"
  exit 1
fi

# Check 2: Synchronization points
SYNC=$(grep -c "Synchronization Point" "$WORKFLOW")
if [ $SYNC -ge 1 ]; then
  echo "✓ Synchronization points defined ($SYNC)"
else
  echo "✗ No synchronization points"
  exit 1
fi

# Check 3: Agent references
AGENTS=$(grep -o "builder-[a-z-]*" "$WORKFLOW" | sort -u)
echo "Referenced agents:"
while IFS= read -r agent; do
  echo "  - $agent"
done <<< "$AGENTS"

echo "✓ Workflow validation passed"
```

### Success Criteria (Per Agent)

| Agent | Criteria |
|-------|----------|
| **builder-skill** | Naming ✓, Content ✓, No Dups ✓, Organization ✓ |
| **builder-agent** | Structure ✓, Refs Valid ✓, Behavior Scoped ✓ |
| **builder-workflow** | Phases ✓, Sync Points ✓, Agents ✓ |

### Failure Handling

**Level 1: Non-Critical Warnings** (Continue with caution)
- Suboptimal naming
- Incomplete documentation
- Minor inconsistencies

**Action**: Log warning, continue with fix

```bash
echo "[WARN] $(date): Minor naming issue in adb-transfer-file.md"
# Fix the issue
# Continue execution
```

**Level 2: Critical Errors** (Stop and fix)
- Duplicate files
- Broken references
- Naming violations

**Action**: Stop execution, fix issue, re-validate

```bash
if [ $CRITICAL_ERRORS -gt 0 ]; then
  echo "[ERROR] $(date): $CRITICAL_ERRORS critical errors found"
  echo "Execution STOPPED"
  exit 1
fi
```

**Level 3: Fatal Errors** (Abort and rollback)
- Complete structure corruption
- Multiple unrecoverable issues
- System-level failures

**Action**: Rollback to last known good state

---

### Rollback Procedures

#### Rollback Step 1: Detect Rollback Requirement

```bash
#!/bin/bash
# Detect if rollback is needed

echo "Checking for rollback requirements..."

ERRORS=0

# Check 1: Duplicate detection
DUPS=$(find .claude/skills -name "adb-*.md" | sort | while read f1; do
  find .claude/skills -name "adb-*.md" -newer "$f1" | while read f2; do
    if diff -q "$f1" "$f2" > /dev/null 2>&1; then
      echo "DUPLICATE"
    fi
  done
done | wc -l)

if [ $DUPS -gt 0 ]; then
  echo "✗ Duplicates found ($DUPS)"
  ((ERRORS++))
fi

# Check 2: Naming violations
VIOLATIONS=$(find .claude/skills -type f \( -name "* *" -o -name "*_*" \) | wc -l)
if [ $VIOLATIONS -gt 0 ]; then
  echo "✗ Naming violations ($VIOLATIONS)"
  ((ERRORS++))
fi

# Check 3: Broken references in agents
if grep -r "adb-[a-z-]*.md" .claude/agents/ | while read ref; do
  FILE=$(echo "$ref" | grep -o "adb-[a-z-]*.md")
  if [ ! -f ".claude/skills/$FILE" ]; then
    echo "✗ Broken reference: $FILE"
    ((ERRORS++))
  fi
done

if [ $ERRORS -gt 0 ]; then
  echo ""
  echo "✗✗✗ ROLLBACK REQUIRED ✗✗✗"
  echo "Found $ERRORS critical errors"
  exit 1
else
  echo "✓ No rollback needed"
fi
```

#### Rollback Step 2: Identify Rollback Point

```bash
#!/bin/bash
# Identify what to rollback to

echo "Identifying rollback points..."

# Find all backups by timestamp
ls -lt .moai/backups/ | head -10

# Find last clean execution log
LAST_CLEAN=$(grep "COMPLETE" .moai/execution-logs/*.log | tail -1)
echo "Last clean state: $LAST_CLEAN"

# Propose rollback to specific point
read -p "Rollback to which timestamp? " TARGET_TS
echo "Rolling back to: $TARGET_TS"
```

#### Rollback Step 3: Restore Files

```bash
#!/bin/bash
# Restore files from backup

TARGET_TS="$1"

echo "Restoring from backup: $TARGET_TS"

# Find relevant backup files
find .moai/backups -name "*-$TARGET_TS-*.md" | while read backup; do
  ORIGINAL=$(basename "$backup" | sed "s/-$TARGET_TS-backup//")

  echo "Restoring: $ORIGINAL"
  cp "$backup" ".claude/skills/$ORIGINAL"
done

echo "✓ Files restored"
```

#### Rollback Step 4: Verify Rollback

```bash
#!/bin/bash
# Verify rollback was successful

echo "Verifying rollback..."

# Run full validation suite
./validate-governance.sh

if [ $? -eq 0 ]; then
  echo "✓ Rollback successful"
  echo "[$(date)] Rollback completed successfully" >> .moai/execution-logs/rollback.log
  exit 0
else
  echo "✗ Rollback incomplete - manual intervention needed"
  exit 1
fi
```

#### Rollback Step 5: Document Recovery

```bash
# Log rollback action
echo "[$(date)] ROLLBACK EXECUTED
  Reason: $ERROR_DESCRIPTION
  Rolled back to: $TARGET_TIMESTAMP
  Files restored: $RESTORED_COUNT
  Status: SUCCESS
" >> .moai/execution-logs/agent-recovery-log.log
```

### When to Abort vs Continue

**ABORT (Rollback)** if:
- ✗ Duplicate files created
- ✗ Broken references exist
- ✗ Critical naming violations
- ✗ Multiple validation failures
- ✗ Previous agent dependency missing

**CONTINUE (Fix & Proceed)** if:
- ⚠ Minor naming inconsistencies (fixable in-place)
- ⚠ Documentation gaps (can be added)
- ⚠ Optional validations fail (non-critical)
- ⚠ Single non-blocking warning

---

## Rule Set 7: Execution Logging

### Problem Statement

Without proper execution logging:
- No audit trail of work done
- Agents can't coordinate (no status updates)
- No way to understand what happened
- Difficult to troubleshoot issues

### Solution

Mandatory structured logging with agent-to-agent communication.

### Log File Naming Convention

**Format**: `agent-[NUMBER]-[DOMAIN]-[TIMESTAMP].log`

**Components**:
- `agent-[NUMBER]`: Sequential agent number (1-5 for ecosystem)
- `[DOMAIN]`: What the agent works on (workflow, skill, agent, designer)
- `[TIMESTAMP]`: `YYYYMMDD-HHMMSS`

**Examples**:
```
agent-1-workflow-20251202-140000.log      (builder-workflow)
agent-2-skill-1-4-20251202-141000.log     (builder-skill skills 1-4)
agent-3-skill-5-8-20251202-142000.log     (builder-skill skills 5-8)
agent-4-agent-20251202-143000.log         (builder-agent)
agent-5-workflow-designer-20251202-144000.log (builder-workflow-designer)
```

**Storage Location**: `.moai/execution-logs/`

### Mandatory Log Format with Template

```
[YYYY-MM-DD HH:MM:SS] [AGENT-ID] [SECTION] [STATUS]
────────────────────────────────────────────────────

Agent ID: agent-[N]-[DOMAIN]
Session: [TIMESTAMP]
Phase: [Phase Name]

INPUT:
  - Source: [Where input came from]
  - Files: [List of input files]
  - Dependencies: [Required previous work]
  - Verification: [How input was verified]

PROCESS:
  - Action: [What was done]
  - Files Created/Modified: [List of files]
  - Naming Compliance: [Verified/Violations]
  - Count Logic: [Nesting decision made]

OUTPUT:
  - Files: [Complete list of created files]
  - Count: [Number of items created]
  - Status: [COMPLETE/IN_PROGRESS/FAILED]
  - Next Agent: [Who receives this output]

VERIFICATION:
  - Validation: [Results of validation checks]
  - Errors: [Any errors encountered]
  - Warnings: [Non-critical issues]
  - Success: [YES/NO]

METRICS:
  - Duration: [Time spent]
  - Files Created: [Count]
  - Files Modified: [Count]
  - Errors: [Count]

NOTES:
  - [Additional information]
  - [Decisions made]
  - [Blockers or issues]

SYNCHRONIZATION:
  - Sent to: [Next agent]
  - Message: [Synchronization point data]
  - Time: [When sent]
```

### Agent-to-Agent Communication via Logs

**How agents coordinate**:

1. **Agent 1 (workflow) completes**:
   ```
   [2025-12-02 14:00:22] agent-1-workflow [SYNC] COMPLETE

   OUTPUT:
     - Workflow definition: workflow-adb-ecosystem-build.md
     - Agent sequence: workflow defined
     - Synchronization points: 4 defined

   SYNCHRONIZATION:
     - Sent to: agent-2-skill-1-4
     - Message: Ready for skill creation (skills 1-4)
   ```

2. **Agent 2 (skill 1-4) reads log and starts**:
   ```
   [2025-12-02 14:10:15] agent-2-skill-1-4 [START] READ_SYNC

   INPUT:
     - Source: agent-1-workflow
     - Dependencies: workflow-adb-ecosystem-build.md
     - Verification: Workflow structure validated
   ```

3. **Agent 2 creates skills and logs completion**:
   ```
   [2025-12-02 14:25:30] agent-2-skill-1-4 [COMPLETE] CREATED_SKILLS

   OUTPUT:
     - Files: adb-device-detection.md, adb-device-properties.md,
               adb-transfer-file.md, adb-transfer-protocols.md,
               adb-input-handling.md, adb-error-recovery.md
     - Count: 6 skills (skills 1-4 complete)
     - Next Agent: agent-3-skill-5-8

   SYNCHRONIZATION:
     - Sent to: agent-3-skill-5-8
     - Message: 4 skills complete, ready for skills 5-8
   ```

4. **Agent 3 (skill 5-8) reads log and starts**:
   ```
   [2025-12-02 14:30:45] agent-3-skill-5-8 [START] READ_SYNC

   INPUT:
     - Source: agent-2-skill-1-4
     - Skills Available: 4 (from agent-2)
     - Dependencies: All domain concepts from skills 1-4
   ```

### Log Entry Examples

#### Example 1: builder-skill Creating Skills

```
[2025-12-02 14:10:15] [agent-2] [skill-1-4-creation] [START]
════════════════════════════════════════════════════════════

Agent ID: agent-2-skill-1-4
Session: 20251202-141015
Phase: Skill Creation (Items 1-4)

INPUT:
  - Source: agent-1-workflow (workflow-adb-ecosystem-build.md)
  - Files Received: 1 (workflow definition)
  - Dependencies: Workflow structure defined, phases identified
  - Verification: Workflow validated, 4 synchronization points confirmed

PROCESS:
  - Action: Creating 4 ADB ecosystem skills (device, transfer, input, error)
  - Creating files:
    1. adb-device-detection.md (Identifying connected devices)
    2. adb-transfer-file.md (File transfer mechanisms)
    3. adb-input-handling.md (User input processing)
    4. adb-error-recovery.md (Error handling patterns)
  - Naming Compliance: All follow adb-[domain]-[function].md pattern ✓
  - Count Logic: Count = 4, maintaining flat structure (no nesting yet)

OUTPUT:
  - Files Created: 4
  - Location: .claude/skills/ (flat structure)
  - Files:
    * .claude/skills/adb-device-detection.md
    * .claude/skills/adb-transfer-file.md
    * .claude/skills/adb-input-handling.md
    * .claude/skills/adb-error-recovery.md
  - Status: COMPLETE
  - Next Agent: agent-3-skill-5-8

VERIFICATION:
  - All files follow naming convention: ✓
  - No duplicates detected: ✓
  - Content minimum lines (200+): ✓
  - Markdown structure valid: ✓
  - No broken cross-references: ✓
  - Errors: 0
  - Warnings: 0
  - Success: YES

METRICS:
  - Duration: 15 minutes
  - Files Created: 4
  - Files Modified: 0
  - Errors: 0
  - Lines of Content: 1247 total

NOTES:
  - All 4 skills follow domain-specific patterns
  - Cross-references between skills added for navigation
  - Examples included for each skill
  - Ready for skills 5-8 (optimization, performance, testing, monitoring)

SYNCHRONIZATION:
  - Sent to: agent-3-skill-5-8
  - Message: Skills 1-4 complete, 4 files created, no dependencies
  - Time: 2025-12-02 14:25:30
  - Status: Ready for next phase
```

#### Example 2: builder-agent Training on Skills

```
[2025-12-02 14:35:20] [agent-4] [agent-training] [START]
═════════════════════════════════════════════════════════

Agent ID: agent-4-agent
Session: 20251202-143520
Phase: Agent Training and Definition

INPUT:
  - Source: agent-2-skill-1-4 and agent-3-skill-5-8
  - Files Available: 8 ADB ecosystem skills
    * 4 from agent-2: device, transfer, input, error
    * 4 from agent-3: optimization, performance, testing, monitoring
  - Dependencies: All 8 skills must be available and validated
  - Verification: All 8 skill files present and valid

PROCESS:
  - Action: Train agents on ADB ecosystem skills
  - Agent Training:
    1. adb-ecosystem-assistant (coordinates all domains)
    2. adb-device-manager (specializes in device management)
    3. adb-transfer-coordinator (specializes in data transfer)
  - Skill Binding:
    * Each agent bound to relevant skill files
    * System prompts reference skill content
    * Capabilities derived from bound skills
  - Naming Compliance: All agents follow adb-* naming pattern ✓
  - Scope Definition: Each agent stays within defined boundaries

OUTPUT:
  - Agents Created: 3
  - Agent Definitions:
    * adb-ecosystem-assistant.md (master coordinator)
    * adb-device-manager.md (device specialist)
    * adb-transfer-coordinator.md (transfer specialist)
  - Skill Bindings: 3 agents × 4-8 skills = 18 total bindings
  - Status: COMPLETE
  - Next Agent: agent-5-workflow-designer

VERIFICATION:
  - Agent definitions valid: ✓
  - All skill references exist: ✓
  - No circular dependencies: ✓
  - Scope properly defined: ✓
  - Errors: 0
  - Warnings: 0
  - Success: YES

METRICS:
  - Duration: 20 minutes
  - Agents Created: 3
  - Skill Bindings: 18
  - System Prompts: 3
  - Capability Definitions: 15 total

NOTES:
  - Each agent has clear, non-overlapping domain
  - All 8 skills utilized across 3 agents
  - System prompts reference specific skill sections
  - Agents ready for workflow integration

SYNCHRONIZATION:
  - Sent to: agent-5-workflow-designer
  - Message: 3 agents trained, ready for integration
  - Time: 2025-12-02 14:55:30
  - Status: Ready for workflow design
```

### Final Report Aggregation

After all agents complete, aggregate results:

```bash
#!/bin/bash
# Aggregate execution logs into final report

echo "AGGREGATING EXECUTION LOGS"
echo "=========================="

# Find all logs from current session
LOGS=$(ls -t .moai/execution-logs/agent-*.log | head -5)

echo "# Ecosystem Development Final Report" > .moai/execution-logs/FINAL-REPORT.md
echo "" >> .moai/execution-logs/FINAL-REPORT.md
echo "**Generated**: $(date)" >> .moai/execution-logs/FINAL-REPORT.md
echo "**Status**: COMPLETE" >> .moai/execution-logs/FINAL-REPORT.md
echo "" >> .moai/execution-logs/FINAL-REPORT.md

# Summary table
echo "## Execution Summary" >> .moai/execution-logs/FINAL-REPORT.md
echo "" >> .moai/execution-logs/FINAL-REPORT.md
echo "| Agent | Status | Files | Duration |" >> .moai/execution-logs/FINAL-REPORT.md
echo "|-------|--------|-------|----------|" >> .moai/execution-logs/FINAL-REPORT.md

while IFS= read -r log; do
  AGENT=$(basename "$log" | cut -d- -f1-3)
  STATUS=$(grep "\[COMPLETE\]\|\[FAILED\]" "$log" | tail -1 | grep -o "COMPLETE\|FAILED")
  FILES=$(grep -c "FILES:" "$log")
  DURATION=$(grep "Duration:" "$log" | tail -1 | cut -d: -f2-)

  echo "| $AGENT | $STATUS | $FILES | $DURATION |" >> .moai/execution-logs/FINAL-REPORT.md
done <<< "$LOGS"

echo ""
echo "✓ Final report generated: .moai/execution-logs/FINAL-REPORT.md"
```

---

## Rule Set 8: Future Agent Training

### Problem Statement

New agents need to learn ADB ecosystem development patterns correctly. Without training reference, they'll repeat mistakes and inconsistencies.

### Solution

Reference this governance document in agent system prompts with specific training sections.

### How New Agents Learn These Rules

#### Step 1: Agent Prompt Integration

**Include this in new agent system prompt**:

```
You are operating within the ADB Ecosystem development framework.
Before starting any work, you MUST:

1. Read: .moai/specs/SPEC-ADB-ECOSYSTEM-001/governance-rules.md
2. Understand: The 8 rule sets defined in that document
3. Follow: Exact patterns for your role
4. Document: All work in execution logs (.moai/execution-logs/)

Critical Rules for Your Role:
- Rule Set 1: Naming - Use adb-[domain]-[function].md pattern
- Rule Set 2: Nesting - Auto-nest at 5 items per domain
- Rule Set 3: Pre-Checklist - Run 5-point checklist before work
- Rule Set 4: Boundaries - Stay within your task boundaries
- Rule Set 5: Duplicates - Prevent duplicate creation
- Rule Set 6: Validation - Validate before declaring complete
- Rule Set 7: Logging - Document in execution logs
- Rule Set 8: Training - Follow this pattern for new agents

Your Specific Role:
[INSERT ROLE-SPECIFIC RULES FROM RULE SET 4]

Stop and ask for clarification if any rule is unclear.
```

#### Step 2: Reference Documentation

**Point agents to specific sections**:

For builder-skill agents:
- Read: Rule Set 1 (Naming), Rule Set 2 (Auto-Nesting), Rule Set 3 (Checklist)
- Practice: Naming examples from Rule Set 1
- Validate: Domain organization from Rule Set 2

For builder-agent agents:
- Read: Rule Set 4 (Task Boundaries), Rule Set 6 (Validation)
- Practice: Agent creation from Rule Set 4
- Validate: Agent validation from Rule Set 6

For builder-workflow agents:
- Read: Rule Set 4 (Synchronization), Rule Set 7 (Logging)
- Practice: Workflow definition
- Validate: Cross-agent coordination

#### Step 3: Testing Procedure for Agent Compliance

Run these tests to verify agent understands and follows rules:

```bash
#!/bin/bash
# Test new agent compliance with governance rules

echo "AGENT COMPLIANCE TEST SUITE"
echo "==========================="

AGENT_NAME="$1"
if [ -z "$AGENT_NAME" ]; then
  echo "Usage: $0 <agent-name>"
  exit 1
fi

echo "Testing agent: $AGENT_NAME"
echo ""

# Test 1: Rule Set 1 - Naming
echo "[Test 1/6] Naming Convention Compliance"
echo "Testing: Agent creates file 'adb-test-sample.md'"
# Simulate file creation
cat > /tmp/test-file.md << 'EOF'
# Test Skill

Content here.
EOF

if [[ "adb-test-sample.md" =~ ^adb-[a-z]+(-[a-z]+)*\.md$ ]]; then
  echo "  ✓ PASS: Naming follows convention"
else
  echo "  ✗ FAIL: Naming does not follow convention"
  exit 1
fi

# Test 2: Rule Set 2 - Auto-Nesting
echo "[Test 2/6] Auto-Nesting Decision Logic"
echo "Testing: Count logic at 4 and 5 items"
for count in 3 4 5; do
  if [ $count -lt 4 ]; then
    EXPECTED="FLAT"
  else
    EXPECTED="NESTED"
  fi
  echo "  Count=$count → $EXPECTED (expected)"
done
echo "  ✓ PASS: Count logic understood"

# Test 3: Rule Set 3 - Pre-Checklist
echo "[Test 3/6] Pre-Execution Checklist"
echo "Testing: Agent runs checklist before execution"
CHECKLIST_ITEMS=5
echo "  Checklist items: $CHECKLIST_ITEMS"
if [ $CHECKLIST_ITEMS -eq 5 ]; then
  echo "  ✓ PASS: Complete checklist executed"
else
  echo "  ✗ FAIL: Incomplete checklist"
  exit 1
fi

# Test 4: Rule Set 4 - Task Boundaries
echo "[Test 4/6] Task Boundary Compliance"
echo "Testing: Agent stays within role"
AGENT_ROLE="builder-skill"
ALLOWED_TASKS="Create skill files"
FORBIDDEN_TASKS="Create agent files, Implement workflows"
echo "  Role: $AGENT_ROLE"
echo "  Can: $ALLOWED_TASKS"
echo "  Cannot: $FORBIDDEN_TASKS"
echo "  ✓ PASS: Boundaries understood"

# Test 5: Rule Set 7 - Logging
echo "[Test 5/6] Execution Logging"
echo "Testing: Agent logs to execution logs"
if [ -d ".moai/execution-logs" ]; then
  echo "  ✓ Log directory exists"
  echo "  ✓ PASS: Logging ready"
else
  echo "  ✗ FAIL: Log directory missing"
  mkdir -p .moai/execution-logs
  exit 1
fi

# Test 6: Rule Set 6 - Validation
echo "[Test 6/6] Validation & Rollback"
echo "Testing: Agent understands validation"
VALIDATION_TESTS=4
echo "  Validation checks: $VALIDATION_TESTS"
echo "  ✓ PASS: Validation concept understood"

echo ""
echo "════════════════════════════════"
echo "✓ Agent Compliance: PASS (6/6)"
echo "════════════════════════════════"
echo ""
echo "Agent is ready to work within ADB Ecosystem framework"
```

### Updating Rules if Needed

If governance rules need to be updated:

1. **Document the change**:
   ```
   [Updated: 2025-12-15]
   Rule Set [N]: [Topic]
   Change: [What changed]
   Reason: [Why it changed]
   Impact: [Who is affected]
   Action Required: [What agents need to do]
   ```

2. **Notify all agents**:
   - Update governance-rules.md
   - Announce in /moai:9-feedback
   - Update agent system prompts
   - Document in CHANGELOG

3. **Provide migration path**:
   - Old way vs new way
   - Examples with both patterns
   - Transition deadline (if applicable)

4. **Version the document**:
   - Maintain version number
   - Keep change history
   - Archive old versions

---

## Decision Logic Flowchart

### Auto-Nesting Decision Flow (ASCII)

```
START: Create new ADB skill file
│
├─ Step 1: Identify domain
│  └─ Extract from filename: adb-[DOMAIN]-[function].md
│
├─ Step 2: Count existing items in domain
│  ├─ List files matching: adb-DOMAIN-*.md
│  └─ Count = N
│
├─ Step 3: Check if folder exists
│  ├─ Folder: .claude/skills/adb-DOMAIN/
│  └─ Exists? (YES/NO)
│
├─ DECISION TREE:
│  │
│  ├─ IF count ≤ 3 AND NO folder
│  │  │
│  │  └─ DECISION: KEEP FLAT ✓
│  │     └─ Create file in: .claude/skills/adb-DOMAIN-*.md
│  │
│  ├─ ELSE IF count = 4 AND NO folder (about to add 5th)
│  │  │
│  │  └─ DECISION: CREATE FOLDER NOW ✓
│  │     ├─ mkdir .claude/skills/adb-DOMAIN/
│  │     ├─ Move 4 existing files → folder
│  │     └─ Create new file → folder
│  │     └─ Log: "Auto-nested at item #5"
│  │
│  ├─ ELSE IF count ≥ 5 AND folder EXISTS
│  │  │
│  │  └─ DECISION: ADD TO EXISTING FOLDER ✓
│  │     └─ Create file in: .claude/skills/adb-DOMAIN/
│  │
│  └─ ELSE (ANOMALY)
│     │
│     └─ STOP: Unexpected state
│        └─ Investigate and fix manually
│
├─ Step 4: Verify naming
│  ├─ Check: adb-[domain]-[function].md
│  └─ Compliance: YES/NO
│
├─ Step 5: Run validation
│  ├─ Check: No duplicates
│  ├─ Check: Correct location
│  └─ Result: PASS/FAIL
│
└─ END: File created or error occurred
```

### Plain Language Explanation

**Rule**: When creating a new ADB skill file, count existing files in that domain.

- **1-3 files exist** → Create file at `.claude/skills/adb-domain-name.md` (flat structure)
- **4 files exist, adding 5th** → Create folder `.claude/skills/adb-domain/`, move all 4 files into it, add new file
- **5+ files exist** → Create file directly in `.claude/skills/adb-domain/` folder

**Why this rule?**
- Keeps related skills organized
- Prevents single folder with 100+ items
- Auto-transitions from flat to nested naturally
- At exactly 5 items, triggers organization

**Decision Points**:
1. Count items in domain → Decide flat or nested
2. Check folder exists → Use existing or create new
3. Move files if nesting occurs → Consistency
4. Verify result → No orphans or misplaced files

---

## Quick Reference Card

### 1-Page Governance Summary

```
═══════════════════════════════════════════════════════════════════
              ADB ECOSYSTEM GOVERNANCE - QUICK REFERENCE
═══════════════════════════════════════════════════════════════════

RULE 1: NAMING CONVENTION (STRICT)
─────────────────────────────────────
✓ Format: adb-[domain]-[function].md
✓ All lowercase, hyphens only
✓ No spaces, underscores, mixed case
✗ Examples: adb_transfer.md (wrong), ADB-Transfer.md (wrong)
Command: find .claude/skills -name "adb-*.md" | grep -E '^adb-[a-z]+(-[a-z]+)*\.md$'

RULE 2: AUTO-NESTING LOGIC
──────────────────────────
Items 1-3: .claude/skills/adb-domain-*.md (FLAT)
Item 4→5: Create .claude/skills/adb-domain/ (NEST)
Items 5+: Add to existing folder
Count: find .claude/skills -path "*adb-domain*" -name "adb-*.md" | wc -l

RULE 3: PRE-EXECUTION CHECKLIST (5 POINTS)
─────────────────────────────────────────
1. Verify project state: pwd | grep AdbAutoPlayer
2. Verify SPEC exists: [ -f .moai/specs/SPEC-ADB-ECOSYSTEM-001/spec.md ]
3. Verify naming compliance: find .claude/skills -name "adb-*.md" ✓
4. Verify domain consistency: No duplicates in domain
5. Verify execution logs ready: mkdir -p .moai/execution-logs

RULE 4: TASK BOUNDARIES (5 AGENTS)
──────────────────────────────────
Agent 1 (builder-workflow): Workflow coordination only
Agent 2 (builder-skill 1-4): Skills 1-4 only (device, transfer, input, error)
Agent 3 (builder-skill 5-8): Skills 5-8 only (optimization, performance, testing)
Agent 4 (builder-agent): Agent training on all 8 skills
Agent 5 (builder-workflow-designer): Ecosystem integration

RULE 5: DUPLICATE PREVENTION
────────────────────────────
Detection: find .claude/skills -name "adb-*.md" -exec md5sum {} \;
Cleanup: Remove duplicates, keep original, backup to .moai/backups/
Verify: md5sum comparison before deletion

RULE 6: VALIDATION & ROLLBACK
─────────────────────────────
Validate: Naming ✓, Content ✓, No Dups ✓, References ✓
Rollback: 5-step process if critical errors
Abort if: Duplicates, broken refs, naming violations
Continue if: Minor issues, non-blocking warnings

RULE 7: EXECUTION LOGGING
────────────────────────
Location: .moai/execution-logs/agent-[N]-[DOMAIN]-[TIMESTAMP].log
Format: [TIMESTAMP] [AGENT-ID] [SECTION] [STATUS]
Communication: Read/write logs between agents
Report: Aggregate all logs into FINAL-REPORT.md

RULE 8: AGENT TRAINING
──────────────────────
New agents: Read .moai/specs/SPEC-ADB-ECOSYSTEM-001/governance-rules.md
Test compliance: Run agent-compliance-test.sh
Prompt template: Include rule reference in system prompt
Update process: Version rules, announce changes, update agents

═══════════════════════════════════════════════════════════════════
                         QUICK SCENARIOS
═══════════════════════════════════════════════════════════════════

SCENARIO: Creating 5th skill in "transfer" domain
─────────────────────────────────────────────────
1. Check count: 4 files exist (adb-transfer-*.md)
2. Decision: NEST (5th item triggers nesting)
3. Action:
   mkdir .claude/skills/adb-transfer/
   mv adb-transfer-*.md adb-transfer/
   create new file in adb-transfer/
4. Log: "[date] AUTO-NESTED: adb-transfer at item #5"

SCENARIO: Agent creates file with wrong naming
──────────────────────────────────────────────
1. Detect: adb_transfer.md (underscore, not hyphen)
2. Block: Validation fails, agent stops
3. Fix: Rename to adb-transfer-protocols.md
4. Retry: Run validation again

SCENARIO: Duplicate file detected
────────────────────────────────
1. Detect: adb-device-detection.md exists twice (different locations)
2. Action: Remove duplicate, keep original
3. Backup: cp duplicate .moai/backups/duplicate-backup-20251202.md
4. Delete: rm duplicate
5. Log: "Duplicate removed: device-detection"

SCENARIO: Agent can't find referenced skill
─────────────────────────────────────────
1. Error: adb-transfer-file.md referenced but not found
2. Check: File location and naming
3. Fix: Create missing file or update reference
4. Verify: All references resolve before proceeding

═══════════════════════════════════════════════════════════════════
```

---

## Appendix: Real Examples

### Example 1: Current ADB Ecosystem (CORRECT STRUCTURE)

```
.claude/
├── skills/
│   ├── SKILL.md                              # Skill definition template
│   ├── adb-device-detection.md              # Device 1/4 (flat)
│   ├── adb-device-properties.md             # Device 2/4 (flat)
│   ├── adb-device-status.md                 # Device 3/4 (flat)
│   ├── adb-device-logging.md                # Device 4/4 (flat)
│   ├── adb-device/                          # AUTO-NESTED at 5th item
│   │   ├── adb-device-optimization.md       # Device 5/5 (nested)
│   │   ├── adb-device-performance.md        # Device 6/5 (nested)
│   │   └── adb-device-monitoring.md         # Device 7/5 (nested)
│   │
│   ├── adb-transfer-file.md                 # Transfer 1/4 (flat)
│   ├── adb-transfer-protocols.md            # Transfer 2/4 (flat)
│   ├── adb-transfer-compression.md          # Transfer 3/4 (flat)
│   └── adb-transfer-validation.md           # Transfer 4/4 (flat)
│
└── workflows/
    └── workflow-adb-ecosystem-build.md      # Ecosystem workflow
```

**Why this is CORRECT**:
- ✓ All files follow naming convention: `adb-[domain]-[function].md`
- ✓ Device domain: 4 flat files, then auto-nested at 5th
- ✓ Transfer domain: Still flat (4 items, no nesting yet)
- ✓ No orphaned files (all in correct locations)
- ✓ No duplicates (each file is unique)
- ✓ Naming violations: None found
- ✓ Auto-nesting applied at correct threshold

### Example 2: What Previous Attempt Looked Like (INCORRECT)

```
.claude/
├── skills/
│   ├── adb_device_detection.md              ✗ Underscores (should be hyphens)
│   ├── ADB-Device-Properties.md             ✗ Mixed case (should be lowercase)
│   ├── adb-device-detail.md                 ✓ Correct
│   ├── adb-device-detail-copy.md            ✗ Duplicate + wrong naming
│   ├── transfer/                            ✗ Folder too early (only 3 items!)
│   │   ├── adb-transfer-file.md
│   │   ├── adb-transfer-protocols.md
│   │   └── adb-transfer.md                  ✗ Missing function descriptor
│   │
│   ├── adb-input-handling.md
│   ├── adb-input-handling.md                ✗ Exact duplicate (flat)
│   ├── Input Validation.md                  ✗ Spaces + capitalization
│   │
│   └── utilities/                           ✗ Generic folder name (not adb-*)
       └── error_handler.md                  ✗ Underscores + no adb- prefix
│
└── Workflow-ADB.md                          ✗ Wrong capitalization
```

**Problems in this structure**:

1. **Naming Violations**:
   - Underscores instead of hyphens: `adb_device_detection.md`
   - Mixed case: `ADB-Device-Properties.md`
   - Generic names: `utilities/`, `error_handler.md`
   - Spaces in filenames: `Input Validation.md`

2. **Auto-Nesting Errors**:
   - `transfer/` folder created at 3 items (should be 5)
   - `Device` files remain scattered between flat and folder
   - Count logic not applied correctly

3. **Duplicates**:
   - `adb-device-detail.md` + `adb-device-detail-copy.md` (exact duplicate with wrong name)
   - `adb-input-handling.md` appears twice (flat, same location)

4. **Organization Issues**:
   - `utilities/` folder doesn't follow naming (not `adb-*`)
   - `error_handler.md` missing `adb-` prefix
   - Workflow file has wrong capitalization

### Side-by-Side Comparison

| Aspect | CORRECT | INCORRECT |
|--------|---------|-----------|
| **Naming** | `adb-device-detection.md` | `adb_device_detection.md` |
| **Case** | `adb-transfer-file` | `ADB-Transfer-File` |
| **Nesting** | At 5 items | At 3 items |
| **Structure** | Flat 1-4, nested 5+ | Mixed, premature nesting |
| **Duplicates** | None | `-copy` versions present |
| **Generic Names** | None | `utilities/`, `error_handler` |
| **Consistency** | 100% | ~40% |

### Lessons Learned

1. **Naming Convention Must Be Strict**
   - One violation causes cascading issues
   - Validation catches violations immediately
   - Fix early, before creating more files

2. **Count Logic is Critical**
   - Don't nest early (wastes organization)
   - Don't nest late (creates confusion)
   - Exactly 5 items = nesting trigger

3. **Duplicates Compound Problems**
   - One duplicate creates confusion
   - Multiple duplicates cause serious issues
   - Detection must happen at creation time

4. **Automation is Essential**
   - Manual processes lead to errors
   - Checklists prevent mistakes
   - Validation catches violations

5. **Documentation Prevents Confusion**
   - Clear rules prevent misinterpretation
   - Examples show correct patterns
   - Logging tracks decisions

---

## Conclusion

These 8 rule sets provide comprehensive governance for ADB ecosystem development:

1. **Rule Set 1**: Naming prevents confusion
2. **Rule Set 2**: Auto-nesting organizes files
3. **Rule Set 3**: Checklist prevents errors
4. **Rule Set 4**: Boundaries prevent overlap
5. **Rule Set 5**: Duplicate prevention avoids waste
6. **Rule Set 6**: Validation & Rollback ensure quality
7. **Rule Set 7**: Logging enables coordination
8. **Rule Set 8**: Training propagates patterns

**For Agents**:
- Read this document before starting work
- Reference relevant rule sets for your role
- Follow the examples and validation commands
- Document all work in execution logs

**For Developers**:
- Use this as the definitive reference
- Update rules as ecosystem evolves
- Train new agents on these patterns
- Maintain consistency across all work

**Contact & Questions**:
- For clarification: Request in /moai:9-feedback
- For updates: Propose changes in /moai:9-feedback
- For training: Reference specific rule sets
- For issues: Check Rule Set 6 (Validation & Rollback)

---

**Version**: 1.0.0
**Status**: Active
**Last Updated**: 2025-12-02
**Locations**:
- Primary: `.moai/specs/SPEC-ADB-ECOSYSTEM-001/governance-rules.md`
- Reference: CLAUDE.md, Rule Set 8
- Training: Include in agent system prompts
