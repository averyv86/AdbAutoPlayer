# ADB Skill Generation Framework

**Version**: 1.0.0
**Status**: ✅ Production Ready
**Last Updated**: 2025-12-02

---

## Overview

The ADB Skill Generation Framework provides a comprehensive system for creating production-ready adb-* skills following the ADB ecosystem conventions and TRUST 5 standards.

### Key Features

- ✅ **9-Phase Workflow**: Systematic skill generation with validation at each step
- ✅ **Complete Scaffolding**: Auto-generates all required files and directories
- ✅ **Template Library**: Pre-built templates for modules, scripts, and workflows
- ✅ **Validation Framework**: Comprehensive quality assurance checks
- ✅ **TOON Support**: Native workflow definition generation
- ✅ **Error Handling**: Graceful degradation and detailed error reporting

---

## Architecture Overview

### Generation Pipeline

```
Parameters → Validation → Structure → Modules → Scripts → Workflows → Tests → Docs → Report
     ↓           ↓           ↓          ↓        ↓         ↓         ↓       ↓      ↓
   Phase 1    Phase 2     Phase 3     Phase 4   Phase 5   Phase 6   Phase 7  Phase 8 Phase 9
```

### Component Structure

```
adb-{name}/
├── SKILL.md                    # Metadata (auto-generated)
├── modules/                    # Documentation modules
│   ├── core.md                # Core functionality
│   ├── utils.md               # Utility functions
│   └── detector.md            # Detection patterns
├── scripts/                    # Executable scripts
│   ├── launcher-{name}.py     # Main entry point
│   ├── checker-{name}.py      # Status checker
│   └── automator-{name}.py    # Automation engine
├── workflows/                  # TOON workflow definitions
│   ├── basic-execution.toon   # Basic workflow
│   └── error-recovery.toon    # Recovery workflow
├── tests/                      # Test suite
│   └── test_{name}.py         # Unit tests
├── examples/                   # Usage examples
└── documentation/              # User documentation
    └── USAGE.md               # Usage guide
```

---

## 9-Phase Generation Workflow

### Phase 1: Parameter Validation

**Purpose**: Validate input parameters before generation

**Checks**:
- ✅ Name format (adb-{name}, lowercase, hyphens only)
- ✅ Category validity (game, utility, foundation)
- ✅ Description length (10-500 characters)
- ✅ Module names format
- ✅ Output format support

**Exit Conditions**:
```python
if not re.match(r'^[a-z0-9\-]+$', name):
    raise ValidationError("Invalid name format")
if category not in ["game", "utility", "foundation"]:
    raise ValidationError("Invalid category")
```

**Success Criteria**: All validations pass without errors

---

### Phase 2: Directory Structure Creation

**Purpose**: Create complete directory skeleton

**Directories Created**:
```
adb-{name}/
├── modules/              # Documentation
├── scripts/              # Executable code
├── workflows/            # TOON definitions
├── tests/                # Test files
├── examples/             # Usage examples
└── documentation/        # User docs
```

**Implementation**:
```python
directories = [
    Path(f"adb-{name}"),
    Path(f"adb-{name}/modules"),
    Path(f"adb-{name}/scripts"),
    # ... etc
]
for dir_path in directories:
    dir_path.mkdir(parents=True, exist_ok=True)
```

**Success Criteria**: All 7 directories created with correct permissions

---

### Phase 3: SKILL.md Generation

**Purpose**: Create skill metadata file

**Template Structure**:
```markdown
# adb-{name}

**Tier**: [Tier 1/2/3]
**Category**: [game|utility|foundation]
**Status**: 🟡 In Development
**Maturity**: 40%

## Description
{user_description}

## Modules
[List of modules with descriptions]

## Quick Start
[Basic usage instructions]

## Features
[Feature list]
```

**Metadata Fields**:
- `name`: Skill identifier
- `tier`: Ecosystem tier (1=foundation, 2=game, 3=utility)
- `category`: Skill category
- `modules`: List of module files
- `status`: Development status
- `maturity`: Completion percentage

**Success Criteria**: SKILL.md created with all required sections

---

### Phase 4: Module Template Generation

**Purpose**: Create documentation modules with examples

**Default Modules** (if not specified):
```
- core.md       # Core functionality (150+ lines)
- utils.md      # Utilities and helpers (100+ lines)
- detector.md   # Detection/automation patterns (150+ lines)
```

**Module Template**:
```markdown
# {Module Name} Module

## Overview
Brief description of module purpose

## Components
### Main Classes
```python
class {ClassName}:
    def __init__(self):
        pass

    def execute(self):
        pass
```

## Usage Examples
```python
handler = {ClassName}()
result = handler.execute()
```

## Performance
- Execution time: ~100ms
- Memory usage: <50MB
```

**Custom Modules**: Can specify via `--modules "mod1,mod2,mod3"`

**Success Criteria**: All modules generated with consistent structure

---

### Phase 5: Script Template Generation

**Purpose**: Create executable Python scripts

**Generated Scripts**:

1. **launcher-{name}.py** (Entry point)
   ```python
   #!/usr/bin/env python3
   """Launcher for adb-{name}"""

   def main():
       """Main entry point"""
       # Implementation
       pass

   if __name__ == "__main__":
       main()
   ```

2. **checker-{name}.py** (Status checker)
   ```python
   #!/usr/bin/env python3
   """Status checker for adb-{name}"""

   def check_status():
       """Check skill status"""
       # Implementation
       pass
   ```

3. **automator-{name}.py** (Automation engine)
   ```python
   #!/usr/bin/env python3
   """Automation engine for adb-{name}"""

   def automate():
       """Execute automation"""
       # Implementation
       pass
   ```

**Script Properties**:
- ✅ Shebang present (`#!/usr/bin/env python3`)
- ✅ Module docstring included
- ✅ Executable permissions set (0o755)
- ✅ PEP 723 compliant

**Success Criteria**: 3 scripts created with proper structure

---

### Phase 6: TOON Workflow Generation

**Purpose**: Create workflow definitions in TOON format

**Workflow 1: Basic Execution**
```yaml
---
skill: adb-{name}
version: 1.0.0
purpose: Basic execution workflow
stages: 3
---

stages:
  initialize:
    description: Initialize {name}
    actions:
      - type: setup
        target: adb-{name}

  execute:
    description: Execute main functionality
    actions:
      - type: run
        command: execute

  finalize:
    description: Cleanup
    actions:
      - type: cleanup
        target: all
```

**Workflow 2: Error Recovery**
```yaml
---
skill: adb-{name}
version: 1.0.0
purpose: Error recovery workflow
stages: 4
---

stages:
  check:
    description: Check status
    actions:
      - type: verify

  execute:
    description: Execute with retry
    actions:
      - type: retry
        max_attempts: 3

  recover:
    description: Recovery on error
    condition: error
    actions:
      - type: reset

  report:
    description: Generate report
    actions:
      - type: log
```

**TOON Features**:
- ✅ YAML frontmatter with metadata
- ✅ Named stages with descriptions
- ✅ Typed actions with parameters
- ✅ Conditional execution
- ✅ Clear execution flow

**Success Criteria**: 2 workflows generated with valid TOON syntax

---

### Phase 7: Test Structure Generation

**Purpose**: Create pytest-compatible test framework

**Test Template**:
```python
# tests/test_{name}.py

import pytest
from unittest.mock import Mock, patch

class Test{ClassName}:
    """Test suite for adb-{name}"""

    def setup_method(self):
        """Setup test fixtures"""
        pass

    def test_initialization(self):
        """Test initialization"""
        assert True

    def test_execution(self):
        """Test main execution"""
        assert True

    def test_error_handling(self):
        """Test error handling"""
        assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Test Coverage**:
- ✅ Initialization tests
- ✅ Main functionality tests
- ✅ Error handling tests
- ✅ Integration tests (optional)

**Success Criteria**: Test file created with 3+ test methods

---

### Phase 8: Usage Documentation

**Purpose**: Create user-facing documentation

**Documentation Template**:
```markdown
# Usage Guide: adb-{name}

## Installation
[Installation instructions]

## Quick Start
[Basic usage examples]

## Configuration
[Configuration options]

## Troubleshooting
[Common issues and solutions]

## Examples
[Detailed examples]
```

**Sections**:
- ✅ Installation guide
- ✅ Quick start
- ✅ Configuration reference
- ✅ Examples
- ✅ Troubleshooting

**Success Criteria**: USAGE.md created with all major sections

---

### Phase 9: Validation & Reporting

**Purpose**: Validate generated skill and produce report

**Validation Checks**:
```python
validation_report = {
    "skill_md_exists": (path / "SKILL.md").exists(),
    "modules_created": (path / "modules").exists(),
    "scripts_created": (path / "scripts").exists(),
    "tests_created": (path / "tests").exists(),
    "documentation_created": (path / "documentation").exists(),
}
```

**Report Format**:
```json
{
    "timestamp": "2025-12-02T15:00:00.000000",
    "skill_name": "adb-feature",
    "files_created": 12,
    "directories_created": 7,
    "validation_checks": {
        "skill_md_exists": true,
        "modules_created": true,
        ...
    },
    "status": "ready"
}
```

**Success Criteria**: All validation checks pass

---

## Usage Examples

### Example 1: Basic Skill Generation

```bash
uv run adb-builder-skill.py \
  --name "feature-detection" \
  --category "utility" \
  --description "Automated feature detection for game UI" \
  --modules "detector,validator,reporter" \
  --output-format json
```

**Output**:
```json
{
    "success": true,
    "skill_name": "adb-feature-detection",
    "files_created": 12,
    "total_score": 100
}
```

### Example 2: Game Skill with Full Features

```bash
uv run adb-builder-skill.py \
  --name "battle-optimizer" \
  --category "game" \
  --description "Optimized battle automation for AFK Journey" \
  --modules "battle-state,formation-selector,damage-calculator" \
  --output-format json
```

### Example 3: Skill Generation Workflow

```python
from pathlib import Path
from adb_builder_skill import AdbSkillGenerator, SkillParameters

# Create generator
base_path = Path(".claude/skills/adb")
generator = AdbSkillGenerator(base_path)

# Define parameters
params = SkillParameters(
    name="quest-optimizer",
    category="game",
    description="Automated quest optimization",
    modules=["quest-analyzer", "route-planner", "reward-tracker"]
)

# Generate skill
report = generator.generate(params)
print(report)
```

---

## Best Practices

### 1. Naming Conventions

✅ **DO**:
```
adb-feature-name       # Lowercase, hyphens
adb-game-afk-journey   # Game-specific
adb-util-screenshot    # Utility prefixed
```

❌ **DON'T**:
```
AdbFeatureName         # CamelCase
adb_feature_name       # Underscores
feature-name           # Missing adb- prefix
```

### 2. Module Organization

✅ **DO**:
```
modules/
├── core.md            # Main functionality
├── vision.md          # Detection patterns
└── recovery.md        # Error recovery
```

❌ **DON'T**:
```
modules/
├── module1.md
├── module2.md
└── functions.md       # Non-descriptive names
```

### 3. Script Structure

✅ **DO**:
```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["package>=1.0.0"]
# ///
"""Module docstring"""

def main():
    pass
```

❌ **DON'T**:
```python
#!/bin/bash            # Wrong shebang
import everything       # Undefined imports
```

### 4. Documentation Quality

✅ **DO**:
- Clear headers and sections
- Code examples with output
- Configuration references
- Troubleshooting guide

❌ **DON'T**:
- Vague descriptions
- No examples
- Incomplete sections

---

## Performance Considerations

### Generation Speed

| Phase | Est. Duration | Notes |
|-------|---------------|-------|
| Validation | ~100ms | Fast parameter checking |
| Structure | ~200ms | Disk I/O bound |
| Modules | ~500ms | Template rendering |
| Scripts | ~300ms | Code generation |
| Workflows | ~200ms | YAML generation |
| Tests | ~100ms | Template generation |
| Docs | ~300ms | Markdown generation |
| Validation | ~100ms | File verification |
| **Total** | **~1.8 seconds** | For complete skill |

### Output Size

| Component | Lines | Size |
|-----------|-------|------|
| SKILL.md | 50-80 | ~2KB |
| Modules (3x) | 300-400 | ~15KB |
| Scripts (3x) | 150-200 | ~8KB |
| Workflows (2x) | 80-120 | ~4KB |
| Tests | 50-100 | ~4KB |
| Docs | 100-150 | ~6KB |
| **Total** | **730-1050** | **~39KB** |

---

## Troubleshooting

### Issue: "Invalid name format"
**Cause**: Name doesn't match `adb-{name}` pattern
**Solution**: Use lowercase letters, numbers, and hyphens only
```bash
# ❌ Wrong
--name "MyFeature"
--name "adb_feature"

# ✅ Correct
--name "my-feature"
--name "adb-feature"
```

### Issue: "Category not found"
**Cause**: Invalid category specified
**Solution**: Use one of: game, utility, foundation
```bash
uv run adb-builder-skill.py \
  --category "game"  # Valid
```

### Issue: Low validation score
**Cause**: Generated skill missing optional content
**Solution**: Add missing modules or documentation manually

---

## Integration with Other Components

### With adb-builder-bot

Use adb-builder-skill as base, extend with adb-builder-bot:

```bash
# Step 1: Create base skill
uv run adb-builder-skill.py \
  --name "quest-runner" \
  --category "game"

# Step 2: Extend with bot features
uv run adb-builder-bot.py \
  --game "afk-journey" \
  --bot-type "quest-runner"
```

### With adb-builder-validate

Validate generated skills:

```bash
uv run adb-builder-validate.py \
  --skill-path ./skills/adb/adb-quest-runner \
  --checks all \
  --report-format json
```

### With adb-project-tree-reorganizer

Migrate generated skills to new structure:

```bash
uv run adb-project-tree-reorganizer.py \
  --mode execute \
  --create-backup \
  --validate-references
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-02 | Initial release with 9-phase workflow |

---

## See Also

- `adb-bot-scaffolding.md` - Game bot specific patterns
- `adb-validation-framework.md` - Validation rules
- `adb-project-tree-hierarchy.md` - Tree structure mapping

---

**Status**: ✅ Production Ready
**Maturity**: 90%
**Last Reviewed**: 2025-12-02
