# ADB Ecosystem Architecture: Builder Patterns to ADB Implementation

**Status**: ✅ Pattern Extraction Complete
**Date**: 2025-12-01
**Phase**: Learning from Builder Ecosystem
**Reference**: Extracted from builder-skill-uvscript and builder-workflow

---

## Executive Summary

This document maps builder ecosystem patterns to the ADB automation ecosystem. Key insight: The builder ecosystem provides proven patterns for code generation, workflow orchestration, and skill structure that can be directly adapted for ADB app automation.

---

## 1. Naming Convention Translation

### Builder Pattern → ADB Pattern

| Layer | Builder Pattern | ADB Pattern | Example |
|-------|-----------------|-------------|---------|
| **Prefix** | `builder-` | `adb-` | `adb-screen-detection` |
| **App Skill** | `moai-connector-*` | `adb-{app-name}` | `adb-karrot`, `adb-magisk` |
| **Foundation Skill** | `moai-library-*` | `adb-{capability}` | `adb-navigation-base` |
| **Meta Skill** | `builder-*` | `adb-*-generator` | `adb-skill-generator` |
| **Scripts** | `builder-skill_{action}.py` | `adb-{action}.py` | `adb-magisk-launch.py` |
| **Commands** | `/builder:action` | `/adb:action` | `/adb:magisk-setup` |

**Key Difference**: Builder uses `builder-skill_` prefix for scripts, but we'll use `adb-` prefix directly (following IndieDevDan pattern more closely)

---

## 2. SKILL.md Frontmatter Structure

### Builder Pattern (builder-skill-uvscript)

```yaml
---
name: builder-skill-uvscript
description: Unified UV CLI scripts collection with builder-skill_ prefix
version: 1.0.0
modularized: true
scripts_enabled: true
last_updated: 2025-11-30
compliance_score: 100
auto_trigger_keywords:
  - uvscript
  - builder-skill
color: red
---
```

### ADB Pattern Adaptation (adb-screen-detection)

```yaml
---
name: adb-screen-detection
description: Screen understanding with OCR and template matching for Android automation
version: 1.0.0
modularized: true
scripts_enabled: true
last_updated: 2025-12-01
compliance_score: 100
tier: 2
category: adb-automation
dependencies:
  - pytesseract>=0.3.10
  - opencv-python>=4.8.0
  - pillow>=10.0.0
  - numpy>=1.24.0
auto_trigger_keywords:
  - adb-screen
  - ocr
  - template-match
  - ui-detection
color: blue
---
```

**Changes Made**:
- Added `tier: 2` (foundation tier, below app-specific tier)
- Added `category: adb-automation` (for organization)
- Added `dependencies` list explicitly (critical for ADB scripts)
- Changed `color: red` to `color: blue` (ADB ecosystem color)
- Updated keywords to ADB-specific terms

---

## 3. UV Script Structure (PEP 723)

### Builder Pattern - 9-Section Template

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "rich>=13.0.0",
#     "pyyaml>=6.0",
# ]
# ///

"""SECTION 1: Docstring with usage examples"""

# SECTION 2: IMPORTS
import click
from pathlib import Path

# SECTION 3: CONSTANTS & CONFIGURATION
DEFAULT_OUTPUT_DIR = ".claude/skills"
VALID_SKILL_PREFIXES = ["moai-", "skill-"]

# SECTION 4: PROJECT ROOT AUTO-DETECTION
def find_project_root(start_path: Path) -> Path:
    """Auto-detect project root"""
    current = start_path.resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai", ".claude"]):
            return current

# SECTION 5: DATA MODELS (Dataclasses)
@dataclass
class SkillConfig:
    name: str
    description: str

# SECTION 6: CORE LOGIC
def generate_skill(config: SkillConfig) -> None:
    """Core implementation"""
    pass

# SECTION 7: FORMATTERS (Output formatting)
def format_output(data: dict) -> str:
    """Format for human + JSON"""
    return json.dumps(data)

# SECTION 8: CLI INTERFACE
@click.command()
@click.option('--name', required=True)
def cli(name: str):
    """Main CLI entry point"""
    pass

# SECTION 9: ENTRY POINT
if __name__ == "__main__":
    cli()
```

### ADB Pattern - Same Structure, ADB-Specific

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "pillow>=10.0.0",
#     "pytesseract>=0.3.10",
#     "numpy>=1.24.0",
# ]
# ///

"""SECTION 1: ADB-specific docstring"""

# SECTION 2: IMPORTS
import subprocess
from pathlib import Path
from dataclasses import dataclass

# SECTION 3: ADB-SPECIFIC CONSTANTS
ADB_COMMAND = "adb"
SCREENCAP_PATH = "/sdcard/screenshot.png"
OCR_TIMEOUT = 10

# SECTION 4: PROJECT ROOT AUTO-DETECTION (same)
def find_project_root(start_path: Path) -> Path:
    """Auto-detect project root"""
    # ... same pattern

# SECTION 5: ADB DATA MODELS
@dataclass
class ADBScreenshot:
    device_id: str
    image_path: Path
    ocr_text: str

# SECTION 6: CORE ADB LOGIC
def capture_screen(device_id: str) -> bytes:
    """Capture screenshot via ADB"""
    subprocess.run([ADB_COMMAND, "-s", device_id, "shell", "screencap", SCREENCAP_PATH])

# SECTION 7: FORMATTERS (same pattern)
def format_output(data: dict) -> str:
    """Dual output: human + JSON"""
    return json.dumps(data)

# SECTION 8: CLI INTERFACE (same pattern)
@click.command()
@click.option('--device', required=False, help="Device ID or leave empty for connected device")
def cli(device: str):
    """Main CLI entry point"""
    pass

# SECTION 9: ENTRY POINT (same)
if __name__ == "__main__":
    cli()
```

**Key Adaptations**:
- Add ADB-specific imports: `subprocess`, `adb` interaction
- Add ADB constants: `SCREENCAP_PATH`, `ADB_COMMAND`
- Add ADB data models: `ADBScreenshot`, device-specific structures
- Core logic focuses on ADB operations (capture, tap, swipe)
- Rest of structure remains identical

---

## 4. Script Organization Structure

### Builder Pattern (builder-skill-uvscript)

```
.claude/skills/builder-skill-uvscript/
├── SKILL.md                    # Skill metadata
├── README.md                   # Documentation
└── scripts/                    # 23 flat scripts
    ├── builder-skill_analyze_all.py
    ├── builder-skill_analyze_battery.py
    ├── builder-skill_analyze_cpu.py
    ├── builder-skill_generate_agent.py
    └── builder-skill_generate_skill.py
```

**Key Principle**: **Flat scripts directory** - no nested subdirectories

### ADB Pattern (3-Tier Organization)

**Tier 1: Foundation Skills** (like library/connector skills)
```
.claude/skills/adb-screen-detection/
├── SKILL.md
├── README.md
└── scripts/
    ├── adb-screen-capture.py
    ├── adb-ocr-extract.py
    ├── adb-find-element.py
    └── adb-tap-coordinate.py

.claude/skills/adb-navigation-base/
├── SKILL.md
└── scripts/
    ├── adb-tap.py
    ├── adb-swipe.py
    └── adb-wait-for.py

.claude/skills/adb-workflow-orchestrator/
├── SKILL.md
└── scripts/
    └── adb-run-workflow.py
```

**Tier 2: App-Specific Skills** (like connector skills)
```
.claude/skills/adb-magisk/
├── SKILL.md
├── scripts/
│   ├── adb-magisk-launch.py
│   ├── adb-magisk-navigate.py
│   └── adb-magisk-install-module.py
├── workflows/
│   ├── magisk-setup.toon
│   └── install-module.toon
├── templates/
│   ├── magisk-home.png
│   └── magisk-modules-tab.png
└── coordinates/
    └── magisk-ui-map.yaml

.claude/skills/adb-karrot/
├── SKILL.md
├── scripts/
│   ├── adb-karrot-launch.py
│   ├── adb-karrot-check-detection.py
│   └── adb-karrot-test-login.py
├── workflows/
│   └── karrot-bypass-playintegrity.toon
├── templates/
│   ├── karrot-home.png
│   └── karrot-error-dialog.png
└── analysis/
    ├── detection-report.md
    └── bypass-strategy.md
```

**Tier 3: Meta Skills** (code generators)
```
.claude/skills/adb-skill-generator/
├── SKILL.md
└── scripts/
    └── adb-create-app-skill.py
```

**Adaptation**: Add `workflows/`, `templates/`, `coordinates/`, `analysis/` directories for app-specific skills

---

## 5. Script Metadata Pattern

### Builder Pattern (SKILL.md scripts section)

```yaml
scripts:
  - name: builder-skill_generate_skill.py
    purpose: Generate skill with SKILL.md and scripts
    type: python
    command: uv run .claude/skills/builder-skill-uvscript/scripts/builder-skill_generate_skill.py
    zero_context: true
    version: 1.0.0
    last_updated: 2025-11-30
```

### ADB Pattern

For foundation skills (simpler):
```yaml
scripts:
  - name: adb-screen-capture.py
    purpose: Capture Android device screen via ADB screencap
    type: python
    command: uv run .claude/skills/adb-screen-detection/scripts/adb-screen-capture.py
    zero_context: true
    dependencies:
      - adb (system)
      - pillow
    version: 1.0.0
    last_updated: 2025-12-01
```

For app-specific skills (more complex):
```yaml
scripts:
  - name: adb-magisk-launch.py
    purpose: Launch Magisk Manager app via ADB
    type: python
    command: uv run .claude/skills/adb-magisk/scripts/adb-magisk-launch.py
    zero_context: false  # Requires screen detection context
    dependencies:
      - adb (system)
      - adb-screen-detection (skill)
    workflows:
      - magisk-setup.toon
      - install-module.toon
    version: 1.0.0
    last_updated: 2025-12-01
```

**Changes**:
- Add `dependencies` including both system and skill dependencies
- Add `workflows` reference for app-specific skills
- Set `zero_context: false` when script depends on other skills

---

## 6. IndieDevDan 13 Rules Applied to ADB

The builder ecosystem strictly follows IndieDevDan's 13 rules. ADB scripts must follow the same:

| Rule | Builder Implementation | ADB Implementation |
|------|------------------------|-------------------|
| **1. Size** | 200-300 lines target | 200-300 lines per script (adb-screen-capture.py) |
| **2. ASTRAL UV** | PEP 723 `# /// script` blocks | Same pattern, add ADB deps |
| **3. Directory** | Flat `scripts/` directory | Flat `scripts/` per skill |
| **4. Self-Contained** | Embedded HTTP, no shared imports | Import from related skills via sys.path |
| **5. CLI Interface** | Click framework, --help, --json | Click for ADB commands |
| **6. Structure** | 9-section template | Same 9-section template |
| **7. Dependencies** | 0-3 packages, min version pin | 0-5 packages (includes ADB-specific) |
| **8. Documentation** | Google docstrings, --help | Same, with ADB examples |
| **9. Testing** | 5-10 unit tests per script | Same (adb mocking) |
| **10. Single-File** | No multi-file dependencies | No multi-file (import from skills) |
| **11. Error Handling** | Dual-mode (human + JSON) | Dual-mode (human + JSON) |
| **12. Configuration** | Env vars, no hardcoded secrets | Env vars for device ID, ADB path |
| **13. Progressive Disclosure** | 0-token dormant | 0-token dormant until invoked |

---

## 7. Workflow Orchestration: TOON Format

### Builder Pattern (builder-workflow)

Builder ecosystem uses TOON (Token-Optimized Object Notation) format for workflows. Example from plan:

```yaml
name: Magisk Module Installation
steps:
  - id: launch
    action: adb-magisk-launch
    verify: home_screen
  - id: navigate_modules
    action: tap
    target: modules_tab
    verify: modules_screen
```

### ADB Pattern - Same TOON, ADB-Specific Actions

**Foundation Workflow** (adb-navigation-base):
```yaml
name: Wait for Element
description: Wait for UI element by text or template

steps:
  - id: capture
    action: adb-screen-capture
    params:
      device: "{{ device_id }}"
  - id: detect
    action: adb-find-element
    params:
      method: "{{ detection_method }}"  # ocr | template
      target: "{{ target }}"
    timeout: 10s
    retry:
      max_attempts: 3
      delay: 1s
```

**App Workflow** (adb-magisk - install module):
```yaml
name: Install Magisk Module
version: 1.0.0

parameters:
  device_id: "127.0.0.1:5555"
  module_path: "/sdcard/PlayIntegrityFork.zip"

phases:
  - id: phase1_setup
    name: "Launch Magisk Manager"
    steps:
      - id: launch
        action: adb-magisk-launch
        params:
          device: "{{ device_id }}"
      - id: verify_launch
        action: adb-wait-for
        params:
          element: "modules_button"
          timeout: 5s

  - id: phase2_navigate
    name: "Navigate to Modules"
    steps:
      - id: tap_modules
        action: adb-tap
        params:
          coordinates: [100, 200]
          device: "{{ device_id }}"
      - id: verify_modules
        action: adb-wait-for
        params:
          text: "Install from storage"

  - id: phase3_install
    name: "Install Module"
    steps:
      - id: tap_fab
        action: adb-tap
        params:
          coordinates: [400, 800]
      - id: select_file
        action: adb-file-select
        params:
          path: "{{ module_path }}"
      - id: wait_install
        action: adb-wait-for
        params:
          text: "Installation complete"
          timeout: 10s

recovery:
  - on_error: phase2_navigate
    action: retry
    max_attempts: 2
  - on_error: phase3_install
    action: adb-karrot-clear-cache
    then: retry
```

**Key Patterns**:
- `parameters` section for template variables
- `phases` for multi-stage workflows
- `steps` with `id`, `action`, `params`, `timeout`
- `recovery` section with retry logic
- Action names map to ADB scripts (`adb-tap`, `adb-wait-for`)

---

## 8. Agent Ecosystem Pattern

### Builder Agent Chain

```
builder-reverse-engineer → builder-workflow-designer → builder-workflow
     (Analyze repo)           (Create SPEC)            (Generate scripts)
```

### ADB Agent Chain (Future)

```
adb-reverse-engineer → adb-workflow-designer → adb-skill-generator
   (Analyze app)         (Create SPEC)        (Generate app skill)
```

**Agents to Create** (future phases):
- `adb-skill-analyzer` - Analyze existing app skills
- `adb-workflow-designer` - Design TOON workflows
- `adb-code-generator` - Generate ADB scripts

---

## 9. Quality Standards Translation

### Builder Standards

| Standard | Builder Implementation | ADB Implementation |
|----------|------------------------|-------------------|
| **TRUST 5** | Testable, Readable, Understandable, Secure, Traceable | Same, with ADB mocking |
| **Code Coverage** | 85%+ target | 85%+ target for scripts |
| **MCP Compliance** | JSON output, no interactive prompts | Same |
| **Version Control** | Git history for all generated code | Git history for all generated code |

### ADB-Specific Quality

```
✅ Device Compatibility: Script works on Android 9+
✅ ADB Communication: Proper error handling for ADB errors
✅ Screen Detection: OCR and template matching validation
✅ Workflow Verification: Each step verifies success before proceeding
```

---

## 10. Complete Pattern Mapping Summary

### Builder → ADB Translation Table

| Aspect | Builder | ADB |
|--------|---------|-----|
| **Prefix** | `builder-` | `adb-` |
| **Script Prefix** | `builder-skill_` | `adb-` |
| **SKILL.md** | Metadata + scripts list | Metadata + scripts + workflows |
| **Script Size** | 200-300 lines | 200-300 lines |
| **Dependencies** | PEP 723 | PEP 723 + ADB-specific |
| **Sections** | 9 standard sections | 9 standard sections |
| **Flat Structure** | Yes (scripts/) | Yes (scripts/, but + workflows/) |
| **Workflow Format** | TOON YAML | TOON YAML |
| **Workflow Scope** | Code generation | Device automation |
| **Recovery Logic** | Not applicable | Retry + fallback actions |
| **Templates** | Code templates | UI screenshot templates |
| **Quality** | TRUST 5 + IndieDevDan | TRUST 5 + IndieDevDan + Device compat |

---

## 11. Implementation Priorities

Based on pattern analysis, implement in this order:

**Phase 1: Foundation Skills** (low risk, reusable)
1. `adb-screen-detection` - Prerequisite for all UI automation
2. `adb-navigation-base` - Gestures and waiting
3. `adb-workflow-orchestrator` - TOON executor

**Phase 2: App Skills** (medium risk, goal-focused)
4. `adb-magisk` - Magisk Manager automation
5. `adb-karrot` - Karrot app automation

**Phase 3: Meta Skills** (generator skills)
6. `adb-skill-generator` - Create new app skills easily

**Phase 4: Agents** (higher-order orchestration)
7. `adb-workflow-designer` - SPEC + TOON generation
8. `adb-skill-analyzer` - Analyze app patterns

---

## 12. File Templates to Create

Based on builder patterns, create these templates:

### Template 1: SKILL.md for Foundation Skills
```
File: .moai/templates/skill-foundation-template.md
Purpose: Template for adb-screen-detection, adb-navigation-base type skills
Lines: 150-200
Structure: Metadata + Quick Reference + Usage + API docs
```

### Template 2: SKILL.md for App Skills
```
File: .moai/templates/skill-app-template.md
Purpose: Template for adb-karrot, adb-magisk type skills
Lines: 200-300
Structure: Metadata + Quick Reference + Workflows + Configuration
```

### Template 3: Python Script Template (PEP 723)
```
File: .moai/templates/script-adb-template.py
Purpose: 9-section template for adb-* scripts
Lines: 250-300 with docstring examples
Structure: 9-section IndieDevDan pattern with ADB-specific sections
```

### Template 4: TOON Workflow Template
```
File: .moai/templates/workflow-adb-template.toon
Purpose: TOON structure for ADB workflows
Lines: 40-60
Structure: parameters, phases with steps, recovery logic
```

---

## 13. Key Learnings to Apply

### From builder-skill-uvscript
- ✅ Unified script naming with prefix
- ✅ Flat scripts directory (no nesting)
- ✅ PEP 723 for dependency declaration
- ✅ 9-section template consistency
- ✅ Dual output modes (human + JSON)
- ✅ Auto-detect project root pattern
- ✅ Metadata-driven SKILL.md

### From builder-workflow
- ✅ TOON format for workflow definition
- ✅ Multi-stage workflow orchestration
- ✅ Recovery and retry logic
- ✅ Parameter templating with `{{ }}` syntax
- ✅ Phase-based execution tracking
- ✅ Verification steps between phases
- ✅ Error handling with fallback actions

### ADB-Specific Adaptations
- ❌ No sharing of import code → ✅ Explicit skill dependencies in SKILL.md
- ❌ Single app in builder → ✅ Multiple apps in ADB ecosystem
- ❌ Static code generation → ✅ Dynamic device interaction
- ❌ One-time execution → ✅ Recovery and retry patterns
- ❌ Linear workflows → ✅ Device state verification loops

---

## Next Steps (Phase 2)

With patterns extracted, proceed to:

1. Create skill directory structures
2. Implement foundation skills with extracted patterns
3. Write SKILL.md files using builder template
4. Create UV scripts following 9-section pattern
5. Implement TOON workflow parser
6. Build app-specific skills for Magisk and Karrot

---

**Document Status**: ✅ Complete
**Pattern Extraction**: ✅ Successful
**Ready for Implementation**: ✅ Yes
**Next Phase**: Build Foundation Skills

