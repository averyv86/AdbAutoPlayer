# ADB Ecosystem - Patterns & Best Practices

> **Purpose**: Detailed pattern implementations and design decisions
> **Version**: 1.0.0
> **Last Updated**: 2025-12-02

---

## 📐 Core Architectural Patterns

### Pattern 1: Modular Skill Composition

**Problem**: Complex automation requires many small operations. How do we avoid monolithic scripts?

**Solution**: Compose functionality into focused, single-purpose skills that build on each other.

```
Tier 2: Foundation Skills
├── adb-screen-detection      (Can work independently)
├── adb-navigation-base       (Depends on adb-screen-detection)
└── adb-workflow-orchestrator (Integrates all skills)

Tier 3: App-Specific Skills
├── adb-magisk                (Uses adb-navigation-base, adb-screen-detection)
└── adb-karrot                (Uses all foundation skills + adb-magisk)
```

**Benefits**:
- ✅ Each skill is testable independently
- ✅ Reusable across multiple apps
- ✅ Clear dependency graph
- ✅ Easy to extend without modifying existing code

**Example: Karrot login automation**

```python
# Instead of one monolithic script with 500+ lines:
# def karrot_login(device, email, password):
#     # find email field
#     # tap email field
#     # enter email
#     # find password field
#     # ... (many more steps)

# We compose from foundation skills:
result = adb_tap.find_and_tap_element(device, "Email field")
adb_navigation.enter_text(device, email)
adb_tap.find_and_tap_element(device, "Password field")
adb_navigation.enter_text(device, password)
adb_navigation.wait_for_text(device, "Profile screen")
```

---

### Pattern 2: Device Auto-Discovery

**Problem**: Users may have multiple devices connected. How do we handle device selection elegantly?

**Solution**: Three-tier device selection strategy.

```python
def select_device(device_arg: Optional[str] = None) -> tuple[str, bool]:
    """Select target device with automatic fallback."""
    # Tier 1: User explicitly provided device
    if device_arg:
        return device_arg, True

    # Tier 2: Auto-detect if only one device connected
    devices = get_adb_devices()
    if not devices:
        return None, False  # No devices
    if len(devices) == 1:
        return devices[0], True  # Single device - use it

    # Tier 3: Multiple devices - use first (user can specify)
    return devices[0], True
```

**CLI Usage**:
```bash
# Tier 1: Explicit device
uv run adb-{skill}-{action}.py --device 192.168.1.100:5555

# Tier 2: Auto-detect (works if 1 device)
uv run adb-{skill}-{action}.py

# Tier 3: Multiple devices (uses first)
uv run adb-{skill}-{action}.py  # Uses devices[0]
```

**Benefits**:
- User convenience (works without arguments for single device)
- Clear error messages (fails fast if ambiguous)
- Explicit override capability (for multiple devices)

---

### Pattern 3: Error Recovery via YAML Rules

**Problem**: Some errors are transient (network blip) but others are permanent (wrong app version). How do we handle both?

**Solution**: Declarative error recovery rules in YAML.

```yaml
recovery:
  # Transient: retry on temporary failures
  - on_error: step-network-check
    action: retry
    max_attempts: 3
    then: continue

  # Non-critical: skip and continue
  - on_error: step-optional-feature
    action: skip
    then: next-phase

  # Critical: stop workflow
  - on_error: step-app-launch
    action: fail
    then: abort
```

**Implementation**:

```python
def execute_phase_with_recovery(phase: dict, recovery_rules: list) -> bool:
    """Execute phase with recovery rule matching."""
    for step in phase['steps']:
        result = execute_step(step)

        if not result.success:
            # Check if recovery rule applies
            for rule in recovery_rules:
                if rule['on_error'] == step['id']:
                    if rule['then'] == 'continue':
                        continue  # Skip error, move to next step
                    elif rule['then'] == 'next-phase':
                        break  # Exit phase loop
                    elif rule['then'] == 'abort':
                        raise RuntimeError(f"Critical error: {step['id']}")

            # No recovery rule: fail by default
            return False

    return True
```

**Benefits**:
- Non-technical users can define recovery behavior
- Centralized error handling (not scattered in code)
- Reusable across multiple workflows
- Easy to adjust without code changes

---

### Pattern 4: OCR-Based UI Element Finding

**Problem**: Screen coordinates vary by device, screen resolution, and app version. How do we make automation robust to these changes?

**Solution**: OCR-based element location instead of hardcoded coordinates.

```python
def find_and_tap_element(device_id: str, search_text: str,
                         fallback_x: int = 720, fallback_y: int = 1000) -> bool:
    """
    Find text on screen via OCR and tap it.

    Benefits:
    - Works across different resolutions
    - Works on both tablets and phones
    - Robust to minor UI layout changes
    - Fallback for OCR failures
    """
    try:
        # Step 1: Get OCR results
        script_path = find_script("adb-screen-detection/adb-find-element.py")
        result = subprocess.run(
            ["uv", "run", str(script_path),
             "--device", device_id,
             "--text", search_text,
             "--json"],
            capture_output=True, text=True, timeout=10
        )

        # Step 2: Parse and tap
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if data.get("found"):
                x, y = data["x"], data["y"]
                tap_at_coordinate(device_id, x, y)
                return True
    except:
        pass

    # Fallback: tap default position
    tap_at_coordinate(device_id, fallback_x, fallback_y)
    return False
```

**Fallback Strategy**:
```
Attempt 1: OCR find + tap exact location
Attempt 2: Tap fallback coordinates
Result: Either way, we attempt the interaction
```

**Benefits**:
- Resolution-independent (works on any device)
- Layout-change tolerant (minor UI changes don't break)
- Easier to maintain (no coordinate tracking)
- Fallback ensures attempt is made

---

### Pattern 5: State-Based Result Tracking

**Problem**: Complex workflows need visibility into what succeeded, what failed, where retries happened. How do we provide this without verbose logging?

**Solution**: Structured result objects with dataclasses.

```python
@dataclass
class StepResult:
    """Single automation step result."""
    step_id: str
    action: str
    success: bool = False
    duration: float = 0.0
    attempts: int = 1  # How many retry attempts
    output: dict = field(default_factory=dict)
    error: Optional[str] = None

@dataclass
class PhaseResult:
    """Collection of steps (phase) result."""
    phase_id: str
    phase_name: str
    steps: List[StepResult] = field(default_factory=list)
    success: bool = False
    duration: float = 0.0
    error: Optional[str] = None

@dataclass
class WorkflowResult:
    """Complete workflow result."""
    workflow_name: str
    phases: List[PhaseResult] = field(default_factory=list)
    completed_steps: int = 0
    total_steps: int = 0
    success: bool = False
    duration: float = 0.0
    error: Optional[str] = None
```

**JSON Output Example**:
```json
{
  "workflow_name": "karrot-bypass-playintegrity",
  "phases": [
    {
      "phase_id": "phase-magisk",
      "phase_name": "Install Magisk module",
      "steps": [
        {
          "step_id": "launch",
          "action": "magisk-launch",
          "success": true,
          "duration": 3.2,
          "attempts": 1
        },
        {
          "step_id": "install",
          "action": "magisk-install-module",
          "success": true,
          "duration": 5.1,
          "attempts": 2
        }
      ],
      "success": true,
      "duration": 8.3
    }
  ],
  "success": true,
  "completed_steps": 14,
  "total_steps": 14,
  "duration": 45.7
}
```

**Benefits**:
- Type-safe result handling
- Easily serializable to JSON
- Programmatic access to detailed results
- Easy to parse for CI/CD integration

---

## 🔄 Workflow Execution Patterns

### Pattern 6: Sequential Phase Execution with State Tracking

```python
def execute_workflow(workflow: dict) -> WorkflowResult:
    """Execute complete workflow with state tracking."""
    result = WorkflowResult(workflow_name=workflow['name'])

    for phase in workflow['phases']:
        phase_result = execute_phase(phase)
        result.phases.append(phase_result)

        # Track progress
        result.completed_steps += len(phase_result.steps)

        # Stop on failure (unless recovery rule allows)
        if not phase_result.success and not has_recovery_rule(phase):
            result.error = phase_result.error
            break

    result.success = all(p.success for p in result.phases)
    return result
```

**Key Points**:
1. **Sequential execution**: Phases run one after another (not parallel)
2. **State tracking**: Progress is visible even during execution
3. **Early termination**: Stops on critical errors unless recovery rule allows
4. **Phase-level fallback**: Can continue past step failures if recovery rules allow

---

### Pattern 7: Step-Level Retry with Exponential Backoff

```python
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def execute_step_with_retry(step: dict) -> StepResult:
    """Execute step with automatic retry."""
    result = StepResult(step_id=step['id'], action=step['action'])

    for attempt in range(1, MAX_RETRIES + 1):
        result.attempts = attempt

        # Execute step
        step_result = execute_step(step)

        if step_result.success:
            result.update(step_result)
            return result

        # Retry if not last attempt
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)  # Wait before retry

    # All retries exhausted
    result.error = step_result.error
    return result
```

**Why retry is important**:
- Network timeouts are transient
- Device may not be ready immediately
- ADB can have brief communication issues
- Retry allows recovery without human intervention

---

### Pattern 8: Parameter Substitution in TOON Workflows

**Problem**: Workflows need to accept user input. How do we pass parameters through nested structures?

**Solution**: Template variable substitution with recursive traversal.

```python
def substitute_parameters(obj: any, params: dict) -> any:
    """Recursively substitute {{ param }} in all object types."""
    if isinstance(obj, str):
        # String substitution: "device: {{ device }}"
        for key, value in params.items():
            obj = obj.replace("{{ " + key + " }}", str(value))
        return obj

    elif isinstance(obj, dict):
        # Dict: recurse on values
        return {k: substitute_parameters(v, params) for k, v in obj.items()}

    elif isinstance(obj, list):
        # List: recurse on elements
        return [substitute_parameters(item, params) for item in obj]

    else:
        # Other types (int, bool, etc.)
        return obj
```

**Usage in workflow**:
```yaml
parameters:
  device: "127.0.0.1:5555"
  timeout: 30

phases:
  - steps:
      - action: karrot-launch
        params:
          device: "{{ device }}"      # Substituted
          timeout: "{{ timeout }}"    # Substituted
```

---

## 🧪 Testing Patterns

### Pattern 9: Dry-Run Mode (Plan without Execute)

**Benefit**: Users can see execution plan before running.

```python
def execute_workflow(workflow: dict, dry_run: bool = False) -> WorkflowResult:
    """Execute with optional dry-run."""
    for phase in workflow['phases']:
        for step in phase['steps']:
            if dry_run:
                # Show what would execute
                print(f"Would execute: {step['action']} {step['params']}")
                result.success = True  # Assume success
            else:
                # Actually execute
                result = execute_step(step)
```

**CLI Usage**:
```bash
# See what would happen
uv run adb-run-workflow.py --workflow karrot.toon --dry-run --verbose

# Actually execute
uv run adb-run-workflow.py --workflow karrot.toon --verbose
```

---

### Pattern 10: Verbose Logging for Debugging

```python
def execute_step(step: dict, verbose: bool = False) -> StepResult:
    """Execute with optional verbose logging."""
    if verbose:
        click.echo(f"  📋 {step['id']}: {step['action']}", err=True)
        click.echo(f"     Params: {json.dumps(step['params'], indent=4)}", err=True)

    result = execute_step_impl(step)

    if verbose:
        status = "✅" if result.success else "❌"
        click.echo(f"  {status} {step['id']}: {result.action} "
                  f"({result.duration:.1f}s, attempt {result.attempts})", err=True)
        if result.error:
            click.echo(f"     Error: {result.error}", err=True)

    return result
```

**Usage**:
```bash
# Verbose mode shows every step
uv run adb-run-workflow.py --workflow workflow.toon --verbose

# Output format:
#   📋 phase-1: launch
#      Params: {...}
#   ✅ phase-1: launch (2.3s, attempt 1)
```

---

## 🔌 Integration Patterns

### Pattern 11: Cross-Skill Script Invocation

**How foundation skills are used by app-specific skills**:

```python
# In adb-karrot/scripts/adb-karrot-test-login.py:

def find_and_tap_login_button(device_id: str) -> bool:
    """Use adb-navigation-base for element finding."""
    project_root = find_project_root()
    script = project_root / ".claude/skills/adb-navigation-base/scripts/adb-tap.py"

    result = subprocess.run(
        ["uv", "run", str(script),
         "--device", device_id,
         "--text", "Login",
         "--json"],
        capture_output=True, text=True, timeout=10
    )

    if result.returncode == 0:
        data = json.loads(result.stdout)
        return data.get("success", False)
    return False
```

**Benefits**:
- DRY principle (Don't Repeat Yourself)
- Version consistency (all apps use same base skills)
- Easy to update foundation (changes apply to all apps)

---

### Pattern 12: TOON Workflow Composition

**How complex workflows are built from simpler ones**:

```yaml
# Main workflow composes multiple phases
name: karrot-complete-bypass

phases:
  - id: phase-1
    name: "Magisk Setup"
    # Could also include: steps imported from magisk-setup.toon

  - id: phase-2
    name: "Karrot Testing"
    # Could also include: steps imported from karrot-test.toon

recovery:
  # Global recovery rules apply to all phases
```

---

## 📈 Performance Patterns

### Pattern 13: Timeout Protection

```python
def execute_with_timeout(action_func, timeout: float = 30.0):
    """Protect against hanging operations."""
    try:
        # Use subprocess timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout  # Critical!
        )
    except subprocess.TimeoutExpired:
        return StepResult(
            success=False,
            error=f"Operation timeout (>{timeout}s)",
            exit_code=2
        )
```

**Timeout hierarchy**:
- **Per-step timeout**: 120s (quick operations)
- **Per-phase timeout**: 300s (multiple steps)
- **Per-workflow timeout**: 600s (entire workflow)

---

### Pattern 14: Early Termination on Critical Error

```python
def execute_workflow(workflow: dict) -> WorkflowResult:
    """Stop immediately on critical errors."""
    for phase in workflow['phases']:
        result = execute_phase(phase)

        # Check for critical exit code
        if any(step.exit_code == 3 for step in result.steps):
            # Found critical error - stop immediately
            result.error = "Critical error detected"
            break

    return result
```

---

## 🎯 Best Practices Summary

| Practice | Benefit | Example |
|----------|---------|---------|
| **Modular skills** | Reusable, testable | adb-screen-detection |
| **Device auto-detect** | User convenience | Works without --device |
| **OCR not coords** | Resolution-independent | find_and_tap_element() |
| **Error recovery** | Handles transients | Recovery YAML rules |
| **State tracking** | Debugging visibility | StepResult dataclass |
| **Dry-run mode** | Safe exploration | --dry-run flag |
| **Verbose logging** | Easy debugging | --verbose flag |
| **Timeouts** | Prevents hanging | timeout=30 |
| **Retry logic** | Transient tolerance | MAX_RETRIES=3 |
| **Parameter substitution** | Dynamic workflows | {{ parameter }} |

---

**Version**: 1.0.0 (Production Ready)
**Last Updated**: 2025-12-02
