# ADB Automation Ecosystem - Complete Guide

> **Status**: Production Ready (v1.0.0)
> **Last Updated**: 2025-12-02
> **Tier**: 2-3 (Foundation + App-Specific Skills)
> **Category**: adb-app-automation, adb-system-control

---

## 📋 Overview

The **ADB Automation Ecosystem** is a comprehensive, modularized system for automating Android device interactions via ADB (Android Debug Bridge). It follows **MoAI-ADK patterns** with all components prefixed with `adb-` for consistency.

### 🎯 Core Philosophy

- **Modular**: Each skill performs one primary function
- **Composable**: Skills build on each other in defined tiers
- **Automated**: Complex workflows orchestrated via TOON format
- **Reproducible**: Deterministic automation with retry logic and error recovery
- **Observable**: JSON output and verbose logging for debugging

### 🏗️ Architecture

```
ADB Ecosystem (5 Foundation + 2 App-Specific Skills)

Tier 2: Foundation Skills (Platform-level capabilities)
├── adb-screen-detection      (Screen capture + OCR + element finding)
├── adb-navigation-base       (Tap + swipe + wait gestures)
└── adb-workflow-orchestrator (TOON parser + subprocess execution)

Tier 3: App-Specific Skills (Real-world automation)
├── adb-magisk                (Magisk Manager + Zygisk + module installation)
└── adb-karrot                (Karrot app + login + Play Integrity detection)

Orchestration Layer
└── adb-run-workflow.py       (Master executor for complex multi-phase workflows)
```

---

## 📁 Directory Structure

```
.claude/skills/
├── adb-screen-detection/
│   ├── SKILL.md                          # Metadata + documentation
│   ├── scripts/
│   │   ├── adb-screen-capture.py         # Take device screenshot
│   │   ├── adb-ocr-extract.py            # Extract text via Tesseract
│   │   ├── adb-find-element.py           # Locate UI element via OCR
│   │   └── adb-tap-coordinate.py         # Tap specific coordinate
│   ├── workflows/                        # (Optional) workflow examples
│   ├── templates/                        # (Optional) shared templates
│   └── analysis/                         # (Optional) analysis results
│
├── adb-navigation-base/
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── adb-tap.py                    # Tap + OCR-based element location
│   │   ├── adb-swipe.py                  # Swipe with coordinates
│   │   └── adb-wait-for.py               # Wait for text/UI element
│   └── ... (same structure as above)
│
├── adb-workflow-orchestrator/
│   ├── SKILL.md
│   ├── scripts/
│   │   └── adb-run-workflow.py           # TOON workflow executor
│   └── ... (same structure)
│
├── adb-magisk/
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── adb-magisk-launch.py          # Launch Magisk Manager
│   │   ├── adb-magisk-enable-zygisk.py   # Enable Zygisk subsystem
│   │   └── adb-magisk-install-module.py  # Install Magisk module
│   └── workflows/
│       └── magisk-setup-complete.toon    # Full Magisk setup workflow
│
└── adb-karrot/
    ├── SKILL.md
    ├── scripts/
    │   ├── adb-karrot-launch.py          # Launch Karrot app
    │   ├── adb-karrot-check-detection.py # Monitor PlayIntegrity detection
    │   └── adb-karrot-test-login.py      # Automated login testing
    └── workflows/
        ├── karrot-launch-app.toon        # Simple app launch
        ├── karrot-check-bypass.toon      # Bypass validation workflow
        └── karrot-bypass-playintegrity.toon # Complete 7-phase bypass

ADB_ECOSYSTEM_README.md    # This file
adb-skill-generator.py     # Meta-tool for rapid skill creation
ECOSYSTEM_PATTERNS.md      # Detailed pattern documentation
ECOSYSTEM_TEMPLATES.md     # Reusable templates for future skills
```

---

## 🔧 Skill Categories

### **Tier 2: Foundation Skills** (Platform Infrastructure)

These skills provide low-level automation primitives that all other skills depend on.

| Skill | Purpose | Scripts | Dependencies |
|-------|---------|---------|--------------|
| **adb-screen-detection** | Screen understanding: capture, OCR, element finding | 4 | ADB, Tesseract OCR, OpenCV |
| **adb-navigation-base** | Gesture automation: tap, swipe, wait | 3 | adb-screen-detection |
| **adb-workflow-orchestrator** | TOON parsing and subprocess execution | 1 | All skills |

### **Tier 3: App-Specific Skills** (Real-World Automation)

These skills automate specific apps, building on foundation skills.

| Skill | Purpose | Scripts | Dependencies |
|-------|---------|---------|--------------|
| **adb-magisk** | Magisk Manager automation + Zygisk + module installation | 3 | adb-navigation-base, adb-screen-detection |
| **adb-karrot** | Karrot app automation + login + Play Integrity bypass | 3 | adb-magisk, adb-screen-detection, adb-navigation-base |

---

## 📜 Skill File Structure (Template)

Every skill follows this standardized structure:

### **SKILL.md** (Metadata + Documentation)

```yaml
---
name: adb-{skillname}
description: Brief description of what skill does
version: 1.0.0
modularized: true
scripts_enabled: true
tier: 3
category: adb-app-automation
last_updated: 2025-12-02
compliance_score: 100

dependencies:
  - adb-screen-detection
  - adb-navigation-base
  - adb-workflow-orchestrator

auto_trigger_keywords:
  - skillname
  - primary-use-case
  - secondary-use-case

scripts:
  - name: adb-{skillname}-{action}.py
    purpose: Brief description of what script does
    type: python
    command: uv run .claude/skills/adb-{skillname}/scripts/adb-{skillname}-{action}.py
    zero_context: true  # Can be understood without context
    version: 1.0.0
    last_updated: 2025-12-02

color: cyan
---

## Quick Reference (30 seconds)

**What It Does**: [Single paragraph explaining skill]

**Core Capabilities**:
- 🚀 **Primary capability**: Description
- 🔍 **Secondary capability**: Description

**When to Use**: [List 3-4 specific use cases]

---

## Scripts

### adb-{skillname}-{action}.py

[Description]

```bash
# Basic usage
uv run .claude/skills/adb-{skillname}/scripts/adb-{skillname}-{action}.py

# With parameters
uv run .claude/skills/adb-{skillname}/scripts/adb-{skillname}-{action}.py \
    --device 127.0.0.1:5555 \
    --param value

# JSON output
uv run .claude/skills/adb-{skillname}/scripts/adb-{skillname}-{action}.py --json
```

[Detailed usage examples and parameter descriptions]
```

### **Script Files** (9-Section IndieDevDan Template)

All scripts follow the same 9-section structure:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""
SECTION 1: DOCSTRING
Comprehensive script description with examples and exit codes
"""

# SECTION 2: IMPORTS
import subprocess, json, sys, time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import click

# SECTION 3: CONSTANTS
ADB_COMMAND = "adb"
TIMEOUT = 30
PACKAGE_NAME = "com.example.app"

# SECTION 4: PROJECT ROOT AUTO-DETECTION
def find_project_root(start_path: Path = None) -> Path:
    """Auto-detect project root by searching for markers."""
    current = (start_path or Path.cwd()).resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai", ".claude"]):
            return current
        current = current.parent
    return Path.cwd()

# SECTION 5: DATA MODELS
@dataclass
class MyResult:
    """Result of operation."""
    success: bool = False
    duration: float = 0.0
    error: Optional[str] = None
    exit_code: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        from dataclasses import asdict
        return asdict(self)

# SECTION 6: HELPER FUNCTIONS
def get_adb_devices() -> list:
    """Get list of connected ADB devices."""
    # Implementation
    pass

# SECTION 7: CORE LOGIC
def execute_action(device_id: str) -> MyResult:
    """Execute primary operation."""
    result = MyResult()
    # Implementation
    return result

# SECTION 8: FORMATTERS
def format_human_output(result: MyResult) -> str:
    """Format for human-readable output."""
    # Implementation
    pass

def format_json_output(result: MyResult) -> str:
    """Format as JSON."""
    import json
    return json.dumps(result.to_dict(), indent=2)

# SECTION 9: CLI INTERFACE
@click.command()
@click.option('--device', type=str, help='Target device ID')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def cli(device: Optional[str], output_json: bool) -> None:
    """Script description and examples."""
    result = execute_action(device)
    if output_json:
        click.echo(format_json_output(result))
    else:
        click.echo(format_human_output(result))
    sys.exit(result.exit_code)

# SECTION 10: ENTRY POINT
if __name__ == "__main__":
    cli()
```

### **Workflow Files** (TOON Format)

```yaml
# Workflow definition in TOON format
name: adb-{skillname}-{workflow}
description: Description of multi-step workflow

parameters:
  device: "127.0.0.1:5555"
  timeout: 30

phases:
  - id: phase-1
    name: "Phase name"
    steps:
      - id: step-1
        action: {skillname}-action-1
        params:
          device: "{{ device }}"
          param: "value"

      - id: step-2
        action: {skillname}-action-2
        params:
          device: "{{ device }}"

recovery:
  - on_error: step-1
    action: retry
    then: continue

  - on_error: step-2
    action: skip
    then: next-phase
```

---

## 🎯 Common Patterns

### **Pattern 1: Device Auto-Detection**

```python
def get_adb_devices() -> list:
    """Get list of connected ADB devices."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "devices"],
            capture_output=True, text=True, timeout=5
        )
        devices = []
        for line in result.stdout.split('\n')[1:]:
            line = line.strip()
            if line and '\t' in line:
                device_id, state = line.split('\t')
                if state == 'device':
                    devices.append(device_id)
        return devices
    except Exception:
        return []

def select_device(device_arg: Optional[str] = None) -> tuple[str, bool]:
    """Select target device or use default."""
    if device_arg:
        return device_arg, True

    devices = get_adb_devices()
    if not devices:
        return None, False
    if len(devices) == 1:
        return devices[0], True
    return devices[0], True  # Use first device if multiple
```

### **Pattern 2: Timeout Protection with Retry**

```python
def execute_with_retry(action_func, max_retries=3, retry_delay=2):
    """Execute action with automatic retry on failure."""
    for attempt in range(1, max_retries + 1):
        try:
            result = action_func()
            if result.success:
                return result
        except Exception as e:
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                raise
    return result
```

### **Pattern 3: Dual Output Modes**

```python
def format_human_output(result: MyResult) -> str:
    """Format for human-readable output."""
    lines = []
    lines.append(f"✅ Success" if result.success else f"❌ Failed")
    # ... additional formatting
    return "\n".join(lines)

def format_json_output(result: MyResult) -> str:
    """Format as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# In CLI:
if output_json:
    click.echo(format_json_output(result))
else:
    click.echo(format_human_output(result))
```

### **Pattern 4: OCR-Based Element Location**

```python
def find_and_tap_element(device_id: str, search_text: str,
                         fallback_x: int = 720, fallback_y: int = 1000) -> bool:
    """Find text on screen via OCR, tap if found."""
    try:
        project_root = find_project_root()
        script_path = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"

        result = subprocess.run(
            ["uv", "run", str(script_path), "--device", device_id,
             "--text", search_text, "--json"],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get("found"):
                    x, y = data.get("x", fallback_x), data.get("y", fallback_y)
                    # Tap the found element
                    subprocess.run(
                        [ADB_COMMAND, "-s", device_id, "shell",
                         "input", "tap", str(x), str(y)],
                        timeout=5
                    )
                    return True
            except:
                pass
    except:
        pass

    # Fallback: tap default coordinates
    subprocess.run(
        [ADB_COMMAND, "-s", device_id, "shell",
         "input", "tap", str(fallback_x), str(fallback_y)],
        timeout=5
    )
    return False
```

### **Pattern 5: Error Recovery Rules**

```yaml
recovery:
  # Retry on transient network failures
  - on_error: step-1
    action: retry
    then: continue

  # Skip non-critical step on error
  - on_error: step-2
    action: skip
    then: next-phase

  # Fail fast on critical errors
  - on_error: step-3
    action: fail
    then: abort
```

---

## 🚀 Execution Models

### **Model 1: Single Script Execution**

```bash
# Launch script directly
uv run .claude/skills/adb-karrot/scripts/adb-karrot-launch.py \
    --device 127.0.0.1:5555 \
    --json
```

### **Model 2: Simple Workflow (2-3 steps)**

Create a simple TOON workflow:

```yaml
name: karrot-launch-workflow
parameters:
  device: "127.0.0.1:5555"

phases:
  - id: launch
    name: "Launch app"
    steps:
      - id: launch-karrot
        action: karrot-launch
        params:
          device: "{{ device }}"
```

Execute:

```bash
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow karrot-launch-workflow.toon \
    --param device=127.0.0.1:5555 \
    --verbose
```

### **Model 3: Complex Orchestration (7+ phases)**

Master Karrot Play Integrity bypass workflow demonstrating all patterns:

```yaml
name: karrot-bypass-playintegrity
description: Complete Play Integrity bypass orchestration for Karrot

parameters:
  device: "127.0.0.1:5555"
  magisk_module: "/sdcard/PlayIntegrityFork.zip"
  test_email: "test@example.com"
  test_password: "testpass123"
  timeout: 30

phases:
  # Phase 1: Install Magisk module
  - id: phase-magisk-install
    name: "Install PlayIntegrityFork module"
    steps:
      - id: magisk-launch
        action: magisk-launch
        params:
          device: "{{ device }}"

      - id: magisk-install-module
        action: magisk-install-module
        params:
          device: "{{ device }}"
          module_path: "{{ magisk_module }}"

  # Phase 2: Enable Zygisk
  - id: phase-zygisk-enable
    name: "Enable Zygisk subsystem"
    steps:
      - id: zygisk-enable
        action: magisk-enable-zygisk
        params:
          device: "{{ device }}"

  # Phase 3: Verify Magisk setup
  - id: phase-magisk-verify
    name: "Verify Magisk module installed"
    steps:
      - id: verify-module
        action: magisk-verify
        params:
          device: "{{ device }}"

  # Phase 4: Test Karrot detection
  - id: phase-karrot-detection
    name: "Check Karrot detection status"
    steps:
      - id: check-detection
        action: karrot-check-detection
        params:
          device: "{{ device }}"
          launch: true

  # Phase 5: Test login
  - id: phase-karrot-login
    name: "Test Karrot login"
    steps:
      - id: test-login
        action: karrot-test-login
        params:
          device: "{{ device }}"
          email: "{{ test_email }}"
          password: "{{ test_password }}"
          check_bypass: true

  # Phase 6: Validate bypass
  - id: phase-bypass-validate
    name: "Validate bypass effectiveness"
    steps:
      - id: final-detection-check
        action: karrot-check-detection
        params:
          device: "{{ device }}"
          detailed: true

recovery:
  # Allow workflow to continue if app detection varies
  - on_error: check-detection
    action: continue
    then: continue

  # Skip login test if detection already confirmed
  - on_error: test-login
    action: skip
    then: next-phase

  # Critical: don't skip final validation
```

---

## 📊 Exit Codes Convention

All scripts follow this standardized exit code system:

| Code | Meaning | Action | Example |
|------|---------|--------|---------|
| **0** | ✅ Success | Continue to next step | App launched successfully |
| **1** | ⚠️ Warning | Continue (incomplete) | App launched but unverified |
| **2** | ❌ Error | Retry or skip | Device not responding |
| **3** | 🔴 Critical | Abort workflow | Invalid device ID |

---

## 🔍 Debugging Workflows

### **Dry-Run Mode** (See execution plan without running)

```bash
uv run adb-run-workflow.py \
    --workflow karrot-bypass-playintegrity.toon \
    --dry-run \
    --verbose
```

### **Verbose Mode** (Detailed step-by-step logging)

```bash
uv run adb-run-workflow.py \
    --workflow karrot-bypass-playintegrity.toon \
    --param device=127.0.0.1:5555 \
    --verbose
```

### **JSON Output** (Parse results programmatically)

```bash
uv run adb-run-workflow.py \
    --workflow karrot-bypass-playintegrity.toon \
    --json | jq '.phases[] | select(.success==false)'
```

---

## 📦 Creating New Skills

Use the **adb-skill-generator** to rapidly create new skills:

```bash
# Minimal skill (1 launcher script)
uv run .claude/skills/adb-skill-generator/adb-skill-generator.py \
    --skill-name banking \
    --description "Banking app automation via Play Integrity bypass"

# Full skill (3 scripts + workflow)
uv run .claude/skills/adb-skill-generator/adb-skill-generator.py \
    --skill-name fitness \
    --description "Fitness app testing" \
    --script-count 3 \
    --with-workflow

# List templates
uv run .claude/skills/adb-skill-generator/adb-skill-generator.py \
    --list-templates
```

The generator creates:
- ✅ Skill directory structure
- ✅ SKILL.md with proper frontmatter
- ✅ Script templates (launcher, checker, tester)
- ✅ Example TOON workflow (if requested)
- ✅ Proper file permissions

---

## 🎓 Learning Path

### **Beginner**: Single Script
1. Use existing skill to solve problem
2. Run script with `--json` to understand output
3. Read SKILL.md for parameter options

### **Intermediate**: Simple Workflow
1. Create 2-3 step TOON workflow
2. Use `--dry-run` to preview
3. Execute with `--verbose` to see steps

### **Advanced**: Complex Orchestration
1. Design 5+ phase workflow with recovery rules
2. Test individual phases separately
3. Combine into master orchestration
4. Use error recovery for robustness

### **Expert**: Create New Skill
1. Run adb-skill-generator
2. Implement core script functions
3. Add SKILL.md documentation
4. Create TOON workflow examples
5. Test with adb-run-workflow

---

## 📚 Related Documentation

- **ECOSYSTEM_PATTERNS.md**: Detailed pattern implementations and best practices
- **ECOSYSTEM_TEMPLATES.md**: Reusable code templates for rapid script development
- **SKILL.md files**: Individual skill documentation with usage examples

---

## 🔗 Dependencies

### **System Requirements**
- Python 3.12+
- ADB (Android Debug Bridge) installed and in PATH
- Android device with USB debugging enabled
- Tesseract OCR (for adb-screen-detection)

### **Python Libraries** (via PEP 723)
- `click>=8.1.7` - CLI framework (all scripts)
- `pyyaml>=6.0` - YAML parsing (adb-run-workflow)

---

## ✨ Key Features

✅ **Modular Design**: Skills are independent and composable
✅ **Auto-Discovery**: Scripts found dynamically via glob patterns
✅ **Error Recovery**: Retry logic and recovery rules in workflows
✅ **Observable**: JSON output + verbose logging for debugging
✅ **Type-Safe**: Dataclasses for result tracking
✅ **Cross-Platform**: Works on Windows, macOS, Linux
✅ **Zero Dependencies**: Uses Python stdlib + minimal packages

---

## 🤝 Contributing New Skills

To create a new skill following ecosystem patterns:

1. **Use the generator**:
   ```bash
   uv run adb-skill-generator.py --skill-name myapp --description "..."
   ```

2. **Implement scripts** following the 9-section template

3. **Create SKILL.md** with proper frontmatter and documentation

4. **Add example workflows** in TOON format

5. **Test** with adb-run-workflow in dry-run mode

6. **Document** usage patterns and edge cases

---

**Version**: 1.0.0 (Production Ready)
**Last Updated**: 2025-12-02
**Maintainer**: MoAI-ADK Ecosystem
