# ADB Ecosystem - Reusable Templates

> **Purpose**: Copy-paste templates for rapid adb-* skill development
> **Version**: 1.0.0
> **Last Updated**: 2025-12-02

---

## 🎯 Quick Start: Pick Your Template

Choose based on script type:
- **[Launcher Script](#launcher-script-template)** - Open/start app
- **[Checker Script](#checker-script-template)** - Verify state, detect status
- **[Automator Script](#automator-script-template)** - Multi-step interaction
- **[Tester Script](#tester-script-template)** - Validation and testing
- **[SKILL.md Template](#skillmd-template)** - Metadata and documentation
- **[TOON Workflow Template](#toon-workflow-template)** - Orchestration

---

## 📄 Launcher Script Template

**When to use**: Opening/launching apps, starting services

**Characteristics**:
- Single primary action (launch app)
- Optional verification (wait for UI element)
- Exit codes: 0 (success), 1 (launched but unverified), 2 (failed), 3 (critical)

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""
ADB {SKILL_NAME} Launcher - Open {APP_NAME} application

Launches {APP_NAME} and optionally waits for specific UI elements to appear.

Usage:
    uv run adb-{skillname}-launch.py
    uv run adb-{skillname}-launch.py --device 127.0.0.1:5555
    uv run adb-{skillname}-launch.py --wait-text "Login" --timeout 15

Examples:
    # Launch on default device
    uv run adb-{skillname}-launch.py

    # Specify device
    uv run adb-{skillname}-launch.py --device 192.168.1.100:5555

    # Wait for specific screen to appear
    uv run adb-{skillname}-launch.py \\
        --wait-text "Login" \\
        --timeout 20

Exit Codes:
    0 - Success (app launched)
    1 - Warning (app launched but verification incomplete)
    2 - Error (app not launched or timeout)
    3 - Critical (invalid device or ADB failure)
"""

# ========== SECTION 2: IMPORTS ==========
import subprocess
import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import click

# ========== SECTION 3: CONSTANTS ==========
APP_PACKAGE = "{APP_PACKAGE_NAME}"  # e.g., "kr.co.flo.karrot"
APP_ACTIVITY = f"{APP_PACKAGE}/.ui.MainActivity"
ADB_COMMAND = "adb"
LAUNCH_TIMEOUT = 10
VERIFICATION_TIMEOUT = 20

# ========== SECTION 4: PROJECT ROOT AUTO-DETECTION ==========
def find_project_root(start_path: Path = None) -> Path:
    """Auto-detect project root by searching for markers."""
    current = (start_path or Path.cwd()).resolve()
    while current != current.parent:
        if any((current / marker).exists() for marker in
               [".git", "pyproject.toml", ".moai", ".claude"]):
            return current
        current = current.parent
    return Path.cwd()

# ========== SECTION 5: DATA MODELS ==========
@dataclass
class LaunchResult:
    """Result of app launch operation."""
    device_id: str
    success: bool = False
    app_launched: bool = False
    verification_passed: bool = False
    timestamp: float = 0.0
    duration: float = 0.0
    wait_text: Optional[str] = None
    text_found: bool = False
    error: Optional[str] = None
    exit_code: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return asdict(self)

# ========== SECTION 6: HELPER FUNCTIONS ==========
def get_adb_devices() -> list:
    """Get list of connected ADB devices."""
    try:
        result = subprocess.run(
            [ADB_COMMAND, "devices"],
            capture_output=True,
            text=True,
            timeout=5
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
    return devices[0], True

def launch_app(device_id: str) -> bool:
    """Launch app via adb shell am start."""
    try:
        cmd = [
            ADB_COMMAND, "-s", device_id, "shell", "am", "start",
            "-n", APP_ACTIVITY
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        return "Error" not in result.stderr and result.returncode == 0
    except Exception:
        return False

def check_text_on_screen(device_id: str, search_text: str, timeout: float = 10) -> bool:
    """Check if text appears on screen using OCR."""
    try:
        project_root = find_project_root()
        script_path = project_root / ".claude/skills/adb-screen-detection/scripts/adb-ocr-extract.py"

        if not script_path.exists():
            return False

        result = subprocess.run(
            ["uv", "run", str(script_path), "--device", device_id, "--json"],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if "text_items" in data:
                    for item in data["text_items"]:
                        if search_text.lower() in item.get("text", "").lower():
                            return True
            except:
                pass

        return False
    except Exception:
        return False

# ========== SECTION 7: CORE LOGIC ==========
def launch_app_with_verification(device_id: str, wait_text: Optional[str] = None,
                                  timeout: float = VERIFICATION_TIMEOUT) -> LaunchResult:
    """Launch app and optionally verify UI element appears."""
    start_time = time.time()
    result = LaunchResult(
        device_id=device_id,
        success=False,
        timestamp=start_time
    )

    # Step 1: Launch app
    app_launched = launch_app(device_id)
    result.app_launched = app_launched

    if not app_launched:
        result.error = "Failed to launch app via adb shell am start"
        result.exit_code = 2
        result.duration = time.time() - start_time
        return result

    # Step 2: Wait for app to fully load
    time.sleep(3)

    # Step 3: Verify via text if requested
    if wait_text:
        result.wait_text = wait_text
        elapsed = 0
        poll_interval = 0.5
        max_wait = timeout

        while elapsed < max_wait:
            if check_text_on_screen(device_id, wait_text):
                result.text_found = True
                result.verification_passed = True
                break
            time.sleep(poll_interval)
            elapsed += poll_interval

        if not result.text_found:
            result.error = f"Timeout waiting for text '{wait_text}' (waited {timeout}s)"
            result.exit_code = 1  # Warning
    else:
        # No verification requested
        result.verification_passed = True
        result.exit_code = 0

    result.success = result.app_launched and result.verification_passed
    result.duration = time.time() - start_time

    if result.success:
        result.exit_code = 0
    elif result.app_launched and not result.verification_passed:
        result.exit_code = 1  # Warning
    else:
        result.exit_code = 2  # Error

    return result

# ========== SECTION 8: FORMATTERS ==========
def format_human_output(result: LaunchResult) -> str:
    """Format result for human-readable output."""
    lines = []

    if result.success:
        lines.append(f"✅ {APP_PACKAGE.split('.')[-1].upper()} app launched on {result.device_id}")
    else:
        lines.append(f"❌ Failed to launch {APP_PACKAGE.split('.')[-1].upper()} app on {result.device_id}")

    lines.append(f"  App Launched: {'✅ Yes' if result.app_launched else '❌ No'}")

    if result.wait_text:
        lines.append(f"  Waiting for: {result.wait_text}")
        lines.append(f"  Text Found: {'✅ Yes' if result.text_found else '❌ No'}")

    lines.append(f"  Duration: {result.duration:.1f}s")

    if result.error:
        lines.append(f"  Error: {result.error}")

    return "\n".join(lines)

def format_json_output(result: LaunchResult) -> str:
    """Format result as JSON."""
    return json.dumps(result.to_dict(), indent=2)

# ========== SECTION 9: CLI INTERFACE ==========
@click.command()
@click.option(
    '--device',
    type=str,
    help='Target device ID (e.g., 127.0.0.1:5555 or emulator-5554)'
)
@click.option(
    '--wait-text',
    type=str,
    help='Wait for this text to appear on screen'
)
@click.option(
    '--timeout',
    type=float,
    default=VERIFICATION_TIMEOUT,
    help='Max seconds to wait for text (default: 20)'
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output as JSON'
)
def cli(device: Optional[str], wait_text: Optional[str], timeout: float,
        output_json: bool) -> None:
    """
    Launch {APP_NAME} application.

    Examples:
        uv run adb-{skillname}-launch.py
        uv run adb-{skillname}-launch.py --device 127.0.0.1:5555
        uv run adb-{skillname}-launch.py --wait-text "Login" --timeout 20
    """
    # Select device
    selected_device, device_ok = select_device(device)

    if not selected_device:
        error_result = LaunchResult(
            device_id="unknown",
            success=False,
            error="No connected ADB devices found",
            exit_code=3
        )
        if output_json:
            click.echo(format_json_output(error_result), err=True)
        else:
            click.echo(f"❌ Error: No connected ADB devices", err=True)
        sys.exit(3)

    # Launch app
    result = launch_app_with_verification(selected_device, wait_text=wait_text, timeout=timeout)

    # Output result
    if output_json:
        click.echo(format_json_output(result))
    else:
        click.echo(format_human_output(result))

    sys.exit(result.exit_code)

# ========== SECTION 10: ENTRY POINT ==========
if __name__ == "__main__":
    cli()
```

---

## 🔍 Checker Script Template

**When to use**: Monitoring state, detecting errors, validation checks

**Characteristics**:
- Check for presence/absence of condition
- Parse output for keywords
- Exit codes indicate detection status

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""
ADB {SKILL_NAME} Checker - Monitor {CHECK_DESCRIPTION}

Checks if {CHECK_DESCRIPTION} by monitoring logs or device state.

Exit Codes:
    0 - Success (condition not met)
    1 - Warning (unclear result)
    2 - Error (condition detected / negative result)
    3 - Critical (device error)
"""

# ========== SECTIONS 2-9: Follow launcher template structure ==========
# (Import, constants, models, helpers, core logic, formatters, CLI, entry)

# ========== SECTION 7: CORE LOGIC (KEY DIFFERENCES) ==========
def check_condition(device_id: str) -> tuple[bool, List[str]]:
    """Check if condition is present in logs or device state."""
    is_condition_met = False
    messages = []

    # Capture relevant logs
    try:
        result = subprocess.run(
            [ADB_COMMAND, "-s", device_id, "logcat", "-d"],
            capture_output=True,
            text=True,
            timeout=10
        )
        logcat_lines = result.stdout.split('\n') if result.returncode == 0 else []
    except Exception:
        return False, ["Failed to capture logcat"]

    # Parse logs for detection keywords
    DETECTION_KEYWORDS = ["error", "failure", "critical", "detected"]

    for line in logcat_lines:
        for keyword in DETECTION_KEYWORDS:
            if keyword.lower() in line.lower():
                is_condition_met = True
                messages.append(line.strip())
                break

    return is_condition_met, messages[:5]  # Return first 5 matches
```

---

## ⚙️ Automator Script Template

**When to use**: Multi-step interactions, complex workflows

**Characteristics**:
- Multiple sequential steps
- OCR-based element finding and tapping
- Progress tracking through steps

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
# ]
# ///

"""
ADB {SKILL_NAME} Automator - {TASK_DESCRIPTION}

Automates multi-step interaction:
  1. Step 1: {STEP_1}
  2. Step 2: {STEP_2}
  3. Step 3: {STEP_3}
  ...
"""

# ========== SECTION 7: CORE LOGIC (STEP-BASED) ==========
def find_and_tap_element(device_id: str, search_text: str,
                         fallback_x: int = 720, fallback_y: int = 1000) -> bool:
    """Find text via OCR and tap the location."""
    try:
        project_root = find_project_root()
        script_path = project_root / ".claude/skills/adb-screen-detection/scripts/adb-find-element.py"

        if not script_path.exists():
            return False

        result = subprocess.run(
            ["uv", "run", str(script_path), "--device", device_id,
             "--text", search_text, "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get("found"):
                    x, y = data.get("x", fallback_x), data.get("y", fallback_y)
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

    # Fallback to default coordinates
    subprocess.run(
        [ADB_COMMAND, "-s", device_id, "shell",
         "input", "tap", str(fallback_x), str(fallback_y)],
        timeout=5
    )
    return False

def enter_text(device_id: str, text: str) -> bool:
    """Enter text via adb input."""
    try:
        # Escape special characters for shell
        escaped_text = text.replace(" ", "%s").replace("'", "\\'")
        subprocess.run(
            [ADB_COMMAND, "-s", device_id, "shell",
             "input", "text", escaped_text],
            timeout=5
        )
        return True
    except:
        return False

def execute_automation_steps(device_id: str, **params) -> AutomationResult:
    """Execute multi-step automation with tracking."""
    result = AutomationResult(device_id=device_id)
    start_time = time.time()

    # Step 1: Perform initial action
    if not find_and_tap_element(device_id, "Element1"):
        result.error = "Failed to find Element1"
        result.exit_code = 2
        return result

    time.sleep(1)

    # Step 2: Enter data
    if not enter_text(device_id, "some text"):
        result.error = "Failed to enter text"
        result.exit_code = 2
        return result

    time.sleep(1)

    # Step 3: Verify result
    if check_text_on_screen(device_id, "Expected text"):
        result.success = True
        result.exit_code = 0
    else:
        result.error = "Expected text not found"
        result.exit_code = 2

    result.duration = time.time() - start_time
    return result
```

---

## 🧪 Tester Script Template

**When to use**: Validation, testing, verification of functionality

**Characteristics**:
- Tests success condition
- Verifies expected output
- Reports pass/fail with details

```python
# Similar to Automator but focused on verification
# Include: test setup, execute test, verify results, report status
```

---

## 📋 SKILL.md Template

**Use for**: Every new skill - metadata + documentation

```yaml
---
name: adb-{skillname}
description: {Brief description of what skill does}
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
  - name: adb-{skillname}-launch.py
    purpose: Launch {app name} application
    type: python
    command: uv run .claude/skills/adb-{skillname}/scripts/adb-{skillname}-launch.py
    zero_context: true
    version: 1.0.0
    last_updated: 2025-12-02

  - name: adb-{skillname}-check.py
    purpose: Check {app name} state or detect issues
    type: python
    command: uv run .claude/skills/adb-{skillname}/scripts/adb-{skillname}-check.py
    zero_context: false
    version: 1.0.0
    last_updated: 2025-12-02

  - name: adb-{skillname}-test.py
    purpose: Test {app name} functionality
    type: python
    command: uv run .claude/skills/adb-{skillname}/scripts/adb-{skillname}-test.py
    zero_context: false
    version: 1.0.0
    last_updated: 2025-12-02

color: cyan
---

---

## Quick Reference (30 seconds)

**{Brief description}**

**What It Does**: {Detailed paragraph explaining skill}

**Core Capabilities**:
- 🚀 **Capability 1**: Description
- 🔍 **Capability 2**: Description
- ✅ **Capability 3**: Description

**When to Use**:
- Use case 1
- Use case 2
- Use case 3

---

## Scripts

### adb-{skillname}-launch.py

Launch {app name}.

```bash
uv run .claude/skills/adb-{skillname}/scripts/adb-{skillname}-launch.py
uv run .claude/skills/adb-{skillname}/scripts/adb-{skillname}-launch.py --device 127.0.0.1:5555
uv run .claude/skills/adb-{skillname}/scripts/adb-{skillname}-launch.py --json
```

[Additional documentation and examples]

### adb-{skillname}-check.py

Check {app name} status.

[Similar documentation structure]

### adb-{skillname}-test.py

Test {app name} functionality.

[Similar documentation structure]
```

---

## 📊 TOON Workflow Template

**Use for**: Orchestrating multi-phase automation

```yaml
# Simple 2-phase workflow
name: {skillname}-basic-workflow
description: Basic automation workflow for {skillname}

parameters:
  device: "127.0.0.1:5555"
  timeout: 30

phases:
  - id: phase-1
    name: "Launch app"
    steps:
      - id: launch
        action: {skillname}-launch
        params:
          device: "{{ device }}"
          timeout: "{{ timeout }}"

  - id: phase-2
    name: "Check status"
    steps:
      - id: check
        action: {skillname}-check
        params:
          device: "{{ device }}"

recovery:
  - on_error: launch
    action: retry
    then: continue

---

# Complex 5-phase workflow with recovery
name: {skillname}-advanced-workflow
description: Advanced automation with error handling

parameters:
  device: "127.0.0.1:5555"
  timeout: 30
  retry_attempts: 3

phases:
  - id: setup
    name: "Setup phase"
    steps:
      - id: step-1
        action: action-1
        params:
          device: "{{ device }}"

  - id: main
    name: "Main automation"
    steps:
      - id: step-2
        action: action-2
        params:
          device: "{{ device }}"

      - id: step-3
        action: action-3
        params:
          device: "{{ device }}"

  - id: verify
    name: "Verification"
    steps:
      - id: step-4
        action: action-4
        params:
          device: "{{ device }}"

recovery:
  # Retry on transient failures
  - on_error: step-2
    action: retry
    max_attempts: "{{ retry_attempts }}"
    then: continue

  # Skip non-critical steps
  - on_error: step-3
    action: skip
    then: next-phase

  # Fail on critical errors
  - on_error: step-4
    action: fail
    then: abort
```

---

## 🔌 Integration Patterns

### **Pattern: Call Another Skill's Script**

```python
def call_skill_script(device_id: str, skill_name: str, script_name: str,
                     **params) -> dict:
    """Call another skill's script and parse JSON result."""
    try:
        project_root = find_project_root()
        script_path = project_root / f".claude/skills/{skill_name}/scripts/{script_name}"

        if not script_path.exists():
            return {"error": f"Script not found: {script_name}"}

        # Build command
        cmd = ["uv", "run", str(script_path)]
        for key, value in params.items():
            cmd.append(f"--{key}")
            cmd.append(str(value))
        cmd.append("--json")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr[:200]}
    except Exception as e:
        return {"error": str(e)}
```

### **Pattern: Retry with Exponential Backoff**

```python
def execute_with_backoff(action_func, max_retries=3):
    """Execute action with exponential backoff retry."""
    for attempt in range(1, max_retries + 1):
        try:
            result = action_func()
            if result.success:
                return result
        except Exception as e:
            if attempt < max_retries:
                wait_time = 2 ** (attempt - 1)  # 1s, 2s, 4s
                time.sleep(wait_time)
    return result
```

### **Pattern: Timeout with Polling**

```python
def wait_for_condition(check_func, timeout=30, poll_interval=0.5):
    """Wait for condition with polling."""
    elapsed = 0
    while elapsed < timeout:
        if check_func():
            return True
        time.sleep(poll_interval)
        elapsed += poll_interval
    return False
```

---

## ✅ Checklist for New Skills

- [ ] Use `adb-skill-generator` to scaffold
- [ ] Choose appropriate script template (launcher, checker, automator, tester)
- [ ] Follow 9-section template structure
- [ ] Use `click` for CLI framework
- [ ] Implement `format_human_output()` and `format_json_output()`
- [ ] Use exit codes 0-3 consistently
- [ ] Add device auto-detection
- [ ] Create SKILL.md with proper frontmatter
- [ ] Include example TOON workflows
- [ ] Test with `adb-run-workflow.py --dry-run`
- [ ] Document with examples in SKILL.md

---

**Version**: 1.0.0 (Production Ready)
**Last Updated**: 2025-12-02
