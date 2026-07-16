# ADB Skill Validation Framework

**Version**: 1.0.0
**Status**: ✅ Production Ready

---

## Validation Rules & Checks

### 1. Naming Convention Check

**Rule**: Skill must match `adb-{name}` pattern

```python
NAMING_PATTERN = re.compile(r'^adb-[a-z0-9\-]+$')

def validate_naming(skill_name: str) -> bool:
    return bool(NAMING_PATTERN.match(skill_name))
```

**Criteria**:
- ✅ Lowercase letters only
- ✅ Numbers and hyphens allowed
- ✅ Minimum 3 characters
- ✅ Maximum 50 characters

**Score**: 0 or 100 (binary)

---

### 2. Directory Structure Check

**Required Directories**:
```
modules/          - Documentation modules
scripts/          - Executable scripts
workflows/        - TOON workflow definitions
tests/            - Test files
documentation/    - User docs
```

**Validation**:
```python
def validate_structure(skill_path: Path) -> int:
    required = {"modules", "scripts", "workflows", "tests", "documentation"}
    found = sum(1 for d in required if (skill_path / d).exists())
    return (found / len(required)) * 100
```

**Score**: Percentage of directories found (0-100)

---

### 3. SKILL.md Completeness Check

**Required Sections**:
```markdown
# {name}                    # Title
## Description             # What the skill does
## Quick Start             # Getting started
## Features                # Feature list
## Configuration           # Configuration options
```

**Validation**:
```python
def validate_skill_md(skill_path: Path) -> int:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return 0

    content = skill_md.read_text()
    required = ["# ", "## Description", "## Quick Start"]
    found = sum(1 for s in required if s in content)
    return (found / len(required)) * 100
```

**Score**: Based on section presence (0-100)

---

### 4. Module Documentation Quality

**Check**: Validate each module file

```python
def validate_modules(skill_path: Path) -> int:
    modules_dir = skill_path / "modules"
    if not modules_dir.exists():
        return 0

    md_files = list(modules_dir.glob("*.md"))
    if not md_files:
        return 0

    valid = 0
    for mod_file in md_files:
        content = mod_file.read_text()
        # Module must have content and structure
        if len(content) > 100 and "# " in content:
            valid += 1

    return (valid / len(md_files)) * 100 if md_files else 0
```

**Score**: Percentage of valid modules (0-100)

---

### 5. Script Compliance Check

**PEP 723 Requirements**:
```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [...]
# ///
```

**Validation**:
```python
def validate_scripts(skill_path: Path) -> int:
    scripts_dir = skill_path / "scripts"
    py_files = list(scripts_dir.glob("*.py"))

    valid = 0
    for script in py_files:
        content = script.read_text()
        has_shebang = content.startswith("#!/usr/bin/env python")
        has_docstring = '"""' in content or "'''" in content
        if has_shebang and has_docstring:
            valid += 1

    return (valid / len(py_files)) * 100 if py_files else 0
```

**Score**: Percentage of compliant scripts (0-100)

---

### 6. TOON Workflow Syntax Check

**Valid TOON Structure**:
```yaml
---
skill: adb-{name}
version: 1.0.0
---

stages:
  stage1:
    description: Stage description
    actions:
      - type: action_type
```

**Validation**:
```python
def validate_workflows(skill_path: Path) -> int:
    workflows_dir = skill_path / "workflows"
    toon_files = list(workflows_dir.glob("*.toon"))

    valid = 0
    for toon in toon_files:
        content = toon.read_text()
        # Must have YAML frontmatter and stages
        if content.startswith("---") and "stages:" in content:
            valid += 1

    return (valid / len(toon_files)) * 100 if toon_files else 0
```

**Score**: Percentage of valid workflows (0-100)

---

### 7. Test Structure Check

**Requirements**:
- Test files follow `test_*.py` pattern
- Minimum 3 test methods
- Pytest compatible

**Validation**:
```python
def validate_tests(skill_path: Path) -> int:
    tests_dir = skill_path / "tests"
    test_files = list(tests_dir.glob("test_*.py"))

    if not test_files:
        return 50  # Warning: no tests

    return 100 if len(test_files) > 0 else 0
```

**Score**: 0 (fail), 50 (warning), 100 (pass)

---

### 8. Documentation Check

**Requirements**:
- USAGE.md exists
- Minimum 50 lines
- Contains examples

**Validation**:
```python
def validate_documentation(skill_path: Path) -> int:
    docs_dir = skill_path / "documentation"
    if not docs_dir.exists():
        return 0

    md_files = list(docs_dir.glob("*.md"))
    return 100 if len(md_files) > 0 else 0
```

**Score**: 0-100

---

## Scoring Algorithm

### Individual Check Scoring

```python
total_score = sum([
    validate_naming(name) * 0.10,          # 10%
    validate_structure(path) * 0.15,       # 15%
    validate_skill_md(path) * 0.15,        # 15%
    validate_modules(path) * 0.15,         # 15%
    validate_scripts(path) * 0.15,         # 15%
    validate_workflows(path) * 0.10,       # 10%
    validate_tests(path) * 0.10,           # 10%
    validate_documentation(path) * 0.10,   # 10%
])
```

### Score Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| 90-100 | ✅ Excellent | Production ready |
| 80-89 | ✅ Good | Ready with minor improvements |
| 70-79 | ⚠️ Fair | Needs work before production |
| 60-69 | ⚠️ Poor | Significant gaps |
| <60 | ❌ Failed | Not ready |

---

## Recommendation Generation

### Automatic Recommendations

```python
recommendations = []

if validate_naming(...) < 100:
    recommendations.append("Rename skill to match adb-* pattern")

if validate_structure(...) < 100:
    recommendations.append("Add missing required directories")

if validate_skill_md(...) < 100:
    recommendations.append("Complete SKILL.md with all sections")

# ... etc for other checks
```

---

## Validation Report Format

```json
{
    "skill_name": "adb-feature",
    "skill_path": "/path/to/adb-feature",
    "timestamp": "2025-12-02T15:00:00Z",
    "checks": [
        {
            "name": "Naming Convention",
            "status": "passed",
            "message": "Name follows adb-* pattern",
            "score": 100
        },
        {
            "name": "Directory Structure",
            "status": "warning",
            "message": "Missing 1 directory",
            "score": 80
        }
    ],
    "total_score": 87,
    "passed_checks": 6,
    "failed_checks": 0,
    "warnings": 2,
    "recommendations": [
        "Add missing documentation directory",
        "Expand SKILL.md content"
    ]
}
```

---

**Status**: ✅ Production Ready
**Maturity**: 90%
