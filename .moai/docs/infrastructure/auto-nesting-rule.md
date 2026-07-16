# Auto-Nesting Rule for Skill Infrastructure

## Overview

The auto-nesting rule is a structural pattern that automatically creates parent folders when 4 or more items share the same naming prefix within a skill's infrastructure.

## Rule Definition

**Trigger Condition**: When a skill contains 4 or more files, folders, or artifacts that share the same prefix pattern.

**Action**: Automatically nest those items under a parent folder with the shared prefix name.

**Purpose**: 
- Reduce cognitive load and navigation complexity
- Create logical groupings for related functionality
- Maintain consistency across ADB ecosystem skills
- Improve discoverability and organization

## Examples from ADB Ecosystem

### Example 1: Workflow Directory Nesting

**Before Auto-Nesting** (without trigger):
```
adb-karrot/
├── login-flow.toon
├── login-flow.md
├── daily-tasks.toon
├── daily-tasks.md
├── game-automation.toon
└── game-automation.md
```

**Trigger**: 6 items with prefix `{name}.toon` and `{name}.md` pattern (4+ items = trigger)

**After Auto-Nesting** (with parent folder):
```
adb-karrot/
└── workflow/
    ├── login-flow.toon
    ├── login-flow.md
    ├── daily-tasks.toon
    ├── daily-tasks.md
    ├── game-automation.toon
    └── game-automation.md
```

### Example 2: Script Directory Nesting

**Pattern**: When a skill has 4+ scripts (`.py`, `.sh`, etc.), create `scripts/` directory

**Before**:
```
adb-bypass/
├── preflight-validation.py
├── magisk-check.py
├── zygisk-verify.py
└── integrity-test.py
```

**After**:
```
adb-bypass/
└── scripts/
    ├── preflight-validation.py
    ├── magisk-check.py
    ├── zygisk-verify.py
    └── integrity-test.py
```

### Example 3: Template Directory Nesting

**Pattern**: When a skill has 4+ template files (`.png`, `.xml`, etc.), create `templates/` directory

**Trigger**: 4+ template files with same extension or format

**Result**: `templates/` folder created automatically

## Implementation Approach

### Phase 1: Detection (Automated)

```python
def detect_auto_nesting_candidates(skill_path):
    """
    Scan skill directory for auto-nesting opportunities.
    
    Returns: List of (prefix, items) tuples where len(items) >= 4
    """
    items_by_prefix = {}
    
    for item in os.listdir(skill_path):
        # Extract prefix (first word before separator)
        prefix = extract_prefix(item)
        
        if prefix not in items_by_prefix:
            items_by_prefix[prefix] = []
        items_by_prefix[prefix].append(item)
    
    # Filter: only return prefixes with 4+ items
    candidates = {
        prefix: items 
        for prefix, items in items_by_prefix.items() 
        if len(items) >= 4
    }
    
    return candidates

def extract_prefix(filename):
    """
    Extract prefix from filename.
    
    Examples:
    - login-flow.toon → 'login'
    - test_utils.py → 'test'
    - config.yaml → 'config'
    """
    # Get base name without extension
    base = os.path.splitext(filename)[0]
    
    # Split on first separator (hyphen, underscore, or dot)
    prefix = re.split(r'[-_.]', base)[0]
    
    return prefix
```

### Phase 2: Clustering

Group items by prefix and determine parent folder name:

```python
def determine_parent_folder(items):
    """
    Determine parent folder name based on items.
    
    - If items are `.toon` + `.md` pairs → parent = 'workflow'
    - If items are `.py` + `.sh` scripts → parent = 'scripts'
    - If items are images/templates → parent = 'templates'
    - Otherwise → parent = shared_prefix
    """
    extensions = set(os.path.splitext(item)[1] for item in items)
    
    if {'.toon', '.md'} <= extensions:
        return 'workflow'
    elif {'.py'} <= extensions or {'.sh'} <= extensions:
        return 'scripts'
    elif extensions & {'.png', '.jpg', '.xml', '.json'}:
        return 'templates'
    else:
        # Use shared prefix as folder name
        return extract_prefix(items[0])
    
    return parent_folder_name
```

### Phase 3: Migration

When triggered, automatically:

1. Create parent folder (e.g., `workflow/`)
2. Move matching items into parent folder
3. Update all references in documentation
4. Create folder README with index

```bash
# Example migration
mkdir -p skill/workflow/
mv skill/*-flow.toon skill/workflow/
mv skill/*-flow.md skill/workflow/
# Update references in SKILL.md, config files, etc.
```

### Phase 4: Documentation

Create README in parent folder:

```markdown
# Skill Workflows

Index of all workflows in this skill.

- [login-flow](login-flow.md) - Description
- [daily-tasks](daily-tasks.md) - Description
- [game-automation](game-automation.md) - Description
```

## Current ADB Ecosystem Status

### Already Nested (Phase 6A Complete)

All 8 ADB skills now have `workflow/` directories:

| Skill | Workflows Count | Parent Folder | Status |
|-------|-----------------|---------------|--------|
| adb-bypass | 3 | workflow/ | ✅ Auto-nested |
| adb-karrot | 3 | workflow/ | ✅ Auto-nested |
| adb-magisk | 3 | workflow/ | ✅ Auto-nested |
| adb-uiautomator | 3 | workflow/ | ✅ Auto-nested |
| adb-screen-detection | 3 | workflow/ | ✅ Auto-nested |
| adb-navigation-base | 3 | workflow/ | ✅ Auto-nested |
| adb-skill-generator | 3 | workflow/ | ✅ Auto-nested |
| adb-workflow-orchestrator | 3 | workflow/ | ✅ Auto-nested |

### Scripts Directory Status

All skills already use `scripts/` directory for executable scripts.

### Future Nesting Opportunities

Monitor these areas for future auto-nesting triggers:

- Template files (detect 4+ images/XML/JSON files)
- Configuration files (detect 4+ config variants)
- Test files (detect 4+ test cases)
- Documentation files (detect 4+ guides/tutorials)

## Decision Criteria

**DO Auto-Nest When**:
- 4 or more items share same prefix
- Items are cohesively related by function
- Parent folder improves navigation clarity
- Prefix logically maps to folder name

**DON'T Auto-Nest When**:
- Fewer than 4 items with same prefix
- Items belong in different parent directories
- Current structure is already optimal
- Top-level access needed for critical files

## References

- TOON v4.0 Specification: [pattern-toon-workflow.md](./../../../.claude/builder/modules/pattern-toon-workflow.md)
- Skill Architecture: [SKILL-architecture.md](./../architecture/SKILL-architecture.md)
- Phase 6A: Workflow Infrastructure Setup
- Phase 6B: TOON Workflow File Generation

## Version History

- v1.0.0 (2025-12-02) - Initial auto-nesting rule documentation for ADB ecosystem
- Phase 6A Integration - Workflow/ nesting implemented across all 8 ADB skills

---

**Status**: Documented (Phase 6A)
**Applicable To**: All ADB skills + future skills
**Last Updated**: 2025-12-02
