# TOON v4.0 Syntax Reference for bluestacks-demo.toon

**Document Type**: Technical Reference
**Format**: TOON v4.0 (YAML-based hierarchical)
**Workflow**: Bluestacks Demonstration
**Last Updated**: 2025-12-02

---

## TOON v4.0 Format Overview

TOON (Token-Optimized Object Notation) v4.0 is a YAML-based hierarchical format inspired by BMAD Method v6. It provides:

- **40-60% token reduction** compared to JSON
- **Clean hierarchical structure** with minimal delimiters
- **Runtime variable substitution** for dynamic values
- **Human-readable** and **LLM-parseable** format
- **Direct mapping** to agent YAML (`*.agent.yaml`) and workflow structures

### Key Benefits
- Compact file size (550 lines vs 1000+ JSON equivalent)
- Natural YAML readability
- Full MoAI-ADK feature support
- No external dependencies

---

## Document Structure

### Top-Level: `workflow:`
```yaml
workflow:
  metadata: { ... }      # Version, categorization
  parameters: [ ... ]    # Input parameters with defaults
  phase1_*: { ... }      # Phase definitions (5 in this workflow)
  validation: { ... }    # Validation rules
  recovery: { ... }      # Error recovery strategies
  outputs: { ... }       # Output definitions
  settings: { ... }      # Execution settings
```

---

## Section 1: Metadata

### Structure
```yaml
metadata:
  name: workflow-id              # Internal identifier (lowercase, hyphens)
  title: Display Title           # Human-readable title
  description: Long description  # Detailed purpose
  version: X.Y.Z                 # Semantic versioning
  category: category-name        # Workflow category
  platform: platform-name        # Target platform
  difficulty: beginner|intermediate|advanced
  estimated_duration_minutes: 3  # Estimated time
  tags:                          # Search/discovery tags
    - tag1
    - tag2
```

### Example (from bluestacks-demo)
```yaml
metadata:
  name: bluestacks-demo
  title: Bluestacks Device Demonstration Workflow
  description: "Complete workflow demonstrating ADB connection..."
  version: 1.0.0
  category: adb-demonstrations
  platform: bluestacks
  difficulty: intermediate
  estimated_duration_minutes: 3
  tags:
    - bluestacks
    - adb
    - device-control
```

---

## Section 2: Configuration References

### Runtime Variable Resolution Pattern

**Syntax**:
```yaml
config_source: "{project-root}/.moai/config/config.json"
variable_name: "{config_source}:nested.key.path"
timestamp: "{system:timestamp}"
project_root: "{project-root}"
```

**Variable Types**:

| Type | Syntax | Resolved To | Example |
|------|--------|-------------|---------|
| Project Root | `{project-root}` | Absolute project directory | `/Users/dev/project` |
| Config File | `{config_source}` | Path to config.json | `.moai/config/config.json` |
| Nested Config | `{config_source}:path.to.key` | Value from config | `90` (from config.constitution.test_coverage_target) |
| System Timestamp | `{system:timestamp}` | ISO 8601 timestamp | `2025-12-02T14:30:45Z` |
| Workflow Path | `{installed_path}` | Current workflow directory | `.moai/workflows/adb/demos` |

### Example (from bluestacks-demo)
```yaml
config_source: "{project-root}/.moai/config/config.json"
output_folder: "{project-root}/.moai/workflows/adb/demos/outputs"
project_root: "{project-root}"
timestamp: "{system:timestamp}"
```

---

## Section 3: Parameters

### Parameter Definition
```yaml
parameters:
  - name: parameter-name
    type: string|integer|boolean|float
    default: default-value
    description: "Parameter description"
    required: true|false
    validation:
      pattern: "regex-pattern"  # Optional
      min: 1                    # For integers
      max: 100                  # For integers
```

### Parameter Reference in Workflow
```yaml
device: "{{ parameters.device }}"
timeout: "{{ parameters.tap_wait_duration }}"
```

### Example (from bluestacks-demo)
```yaml
parameters:
  - name: device
    type: string
    default: "127.0.0.1:5555"
    description: "Bluestacks device IP and port"
    required: false

  - name: screenshot_dir
    type: string
    default: "/tmp"
    description: "Directory to save screenshots"
    required: false

  - name: tap_wait_duration
    type: integer
    default: 1
    description: "Wait duration between taps (seconds)"
    required: false
```

---

## Section 4: Phase Definition

### Phase Structure
```yaml
phase[N]_[name]:
  name: "Phase N - Display Name"
  description: "What this phase does"
  sequence: N                      # Execution order
  depends_on: ["phase1", "phase2"] # Dependencies (optional)
  steps:
    - name: step_name
      title: Step Title
      description: "Step description"
      action: { ... }              # Action definition
      parameters: { ... }          # Step parameters
      validation: { ... }          # Success criteria
      outputs: [ ... ]             # Output definitions
      on_failure: { ... }          # Failure handling
      on_success: { ... }          # Success handling
      condition: "boolean expression" # Optional
  loop:                            # Loop definition (optional)
    type: items
    count: N
    items:
      - id: item-id
        field1: value1
        field2: value2
  loop_steps: [ ... ]              # Steps that run in loop
  checkpoint: true|false
  rollback_on_failure: true|false
  metrics: { ... }                 # Metrics collection
```

### Example: Phase 1 (Sequential Steps)
```yaml
phase1_connection:
  name: "Phase 1 - Connection and Device Information"
  description: "Establish ADB connection and retrieve device information"
  sequence: 1
  steps:
    - name: "step_1_1_connect"
      title: "Connect to Bluestacks Device"
      action: !include ../steps/connection/connect.yaml
      parameters:
        device: "{{ parameters.device }}"
        timeout: 10
      validation:
        success_exit_codes: [0]
      on_failure:
        action: "retry"
        max_attempts: 3
```

---

## Section 5: Loop-Based Execution

### What is a Loop?

A loop in TOON allows **repetition of steps with different values** from an items list. This is used in:
- **Phase 3**: Tap demonstration (3 different tap locations)
- **Phase 5**: Swipe demonstration (2 different directions)

### Loop Structure

```yaml
loop:
  type: items                    # Type of loop (only "items" in v4.0)
  count: N                       # Number of items
  items:                         # Array of item definitions
    - id: item-1                 # Unique identifier
      field1: value1             # Custom fields (any number)
      field2: value2             # Values used in {{ item.field }} substitution
    - id: item-2
      field1: value1
      field2: value2
```

### Loop Steps

```yaml
loop_steps:                      # Steps executed for each item
  - name: loop_action_step
    title: "Action for {{ item.id }}"
    action: { ... }
    # In action, use {{ item.field }} to reference current item values
  - name: loop_wait_step
    title: "Wait Between Iterations"
    action:
      type: sleep
      duration: "{{ parameters.wait_duration }}"
    condition: "{{ loop.index < loop.total }}"  # Skip on last iteration
```

### Loop Context Variables

**Available during loop execution**:

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{ item.id }}` | string | Current item ID | `tap_1`, `swipe_2` |
| `{{ item.FIELD }}` | any | Current item field value | `{{ item.x }}`, `{{ item.direction }}` |
| `{{ loop.index }}` | integer | Current iteration (1-based) | 1, 2, 3 |
| `{{ loop.total }}` | integer | Total iterations | 3, 2 |

### Phase 3 Loop Example: Tap Demonstration

**Loop Definition**:
```yaml
phase3_control_demo:
  loop:
    type: items
    count: 3
    items:
      - id: tap_1
        description: "Center Screen Tap"
        x: 540
        y: 960
      - id: tap_2
        description: "Top-Left Corner Tap"
        x: 200
        y: 400
      - id: tap_3
        description: "Bottom-Right Corner Tap"
        x: 880
        y: 1520
```

**Execution Sequence**:

```
Iteration 1:
  {{ item.id }} = "tap_1"
  {{ item.description }} = "Center Screen Tap"
  {{ item.x }} = 540
  {{ item.y }} = 960
  {{ loop.index }} = 1
  {{ loop.total }} = 3

  Step 1: Execute tap at (540, 960) with description "Center Screen Tap"
  Step 2: Wait 1 second (condition: 1 < 3 = true)

Iteration 2:
  {{ item.id }} = "tap_2"
  {{ item.description }} = "Top-Left Corner Tap"
  {{ item.x }} = 200
  {{ item.y }} = 400
  {{ loop.index }} = 2
  {{ loop.total }} = 3

  Step 1: Execute tap at (200, 400) with description "Top-Left Corner Tap"
  Step 2: Wait 1 second (condition: 2 < 3 = true)

Iteration 3:
  {{ item.id }} = "tap_3"
  {{ item.description }} = "Bottom-Right Corner Tap"
  {{ item.x }} = 880
  {{ item.y }} = 1520
  {{ loop.index }} = 3
  {{ loop.total }} = 3

  Step 1: Execute tap at (880, 1520) with description "Bottom-Right Corner Tap"
  Step 2: Skip wait (condition: 3 < 3 = false)
```

**Loop Steps**:
```yaml
loop_steps:
  - name: "loop_tap_step"
    title: "Execute Tap at {{ item.description }}"
    description: "Tap at coordinates ({{ item.x }}, {{ item.y }})"
    action:
      script: ".claude/skills/moai-domain-adb/scripts/control/tap.py"
      args:
        - "--device"
        - "{{ parameters.device }}"
        - "--x"
        - "{{ item.x }}"              # <-- Substituted from current item
        - "--y"
        - "{{ item.y }}"              # <-- Substituted from current item
        - "--duration"
        - "100"

  - name: "loop_wait_between_taps"
    title: "Wait Between Taps"
    description: "Wait {{ parameters.tap_wait_duration }} second(s)"
    action:
      type: sleep
      duration_seconds: "{{ parameters.tap_wait_duration }}"
    condition: "{{ loop.index < loop.total }}"  # <-- Only wait between iterations
```

### Phase 5 Loop Example: Swipe Demonstration

**Loop Definition**:
```yaml
phase5_swipe_demo:
  loop:
    type: items
    count: 2
    items:
      - id: swipe_1
        direction: "up"
        start_y: 1400
        end_y: 600
        x_coordinate: 540
        description: "Upward swipe (scroll down)"
      - id: swipe_2
        direction: "down"
        start_y: 600
        end_y: 1400
        x_coordinate: 540
        description: "Downward swipe (scroll up)"
```

**Loop Steps**:
```yaml
loop_steps:
  - name: "loop_swipe_step"
    title: "Execute {{ item.direction | upcase }} Swipe"
    action:
      script: ".claude/skills/moai-domain-adb/scripts/control/swipe.py"
      args:
        - "--device"
        - "{{ parameters.device }}"
        - "--direction"
        - "{{ item.direction }}"      # <-- "up" or "down"
        - "--x"
        - "{{ item.x_coordinate }}"   # <-- 540
        - "--start-y"
        - "{{ item.start_y }}"        # <-- 1400 or 600
        - "--end-y"
        - "{{ item.end_y }}"          # <-- 600 or 1400
        - "--duration"
        - "500"

  - name: "loop_wait_between_swipes"
    title: "Wait Between Swipes"
    action:
      type: sleep
      duration_seconds: "{{ parameters.swipe_wait_duration }}"
    condition: "{{ loop.index < loop.total }}"
```

---

## Section 6: Output Variables

### Phase Output Variable Pattern

**Format**: `{{ phase[N].outputs.[variable_name] }}`

**Available in**:
- Subsequent phases
- Final outputs section
- Validation rules
- Recovery actions

### Phase Output Examples

**Phase 1 Outputs**:
```yaml
outputs:
  - name: device_model
    type: string
    path: "$.device.model"           # JSON path from script output
```

**Reference Later**:
```yaml
# In Phase 2 (display step):
field:
  name: "Model"
  source: "{{ phase1.outputs.device_model }}"  # Reference Phase 1 output

# In final outputs:
device_info:
  model: "{{ phase1.outputs.device_model }}"
  version: "{{ phase1.outputs.android_version }}"
```

### Loop Metrics

**Format**: `{{ phase[N].metrics.[metric_name] }}`

**Available Metrics** (for loop phases):
- `total_taps` / `total_swipes`: Total iterations (= `{{ loop.total }}`)
- `successful_taps` / `successful_swipes`: Successful iterations
- `failed_taps` / `failed_swipes`: Failed iterations
- `success_rate`: Percentage (calculated from metrics)

### Reference Loop Metrics

```yaml
# In Phase 3 metrics:
metrics:
  total_taps: "{{ loop.total }}"
  successful_taps: "{{ loop.successful_count }}"
  failed_taps: "{{ loop.failed_count }}"

# Reference in final outputs:
phase3_summary:
  total_taps: "{{ phase3.metrics.total_taps }}"
  successful_taps: "{{ phase3.metrics.successful_taps }}"
  success_rate: "{{ phase3.metrics.successful_taps / phase3.metrics.total_taps * 100 }}%"
```

---

## Section 7: Validation Rules

### Validation Structure

```yaml
validation:
  conditions:
    - name: condition-name
      rule: "Human-readable rule"
      type: check-type
      # Type-specific fields below
```

### Validation Types

**1. Pattern Matching** (Regex):
```yaml
- name: "device_parameter_valid"
  rule: "device must match IP:port or serial format"
  pattern: "^(\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}:\\d{4,5}|[a-zA-Z0-9-]+)$"
  applies_to: "{{ parameters.device }}"
```

**2. Directory Check**:
```yaml
- name: "output_folder_exists"
  rule: "output folder must be accessible"
  type: directory_check
  path: "{{ parameters.screenshot_dir }}"
  checks: [exists, writable]
```

**3. Phase Success Check**:
```yaml
- name: "all_phases_completed"
  rule: "all phases must complete successfully"
  depends_on: [phase1, phase2, phase3, phase4, phase5]
  check: "all_phases.status == 'success'"
```

**4. Success Rate Check**:
```yaml
- name: "minimum_phase_success_rate"
  rule: "at least 80% of loop iterations must succeed"
  applies_to: [phase3_control_demo, phase5_swipe_demo]
  check: "success_rate >= 0.8"
```

---

## Section 8: Recovery Strategies

### Retry Configuration

```yaml
recovery:
  retry_strategy:
    max_attempts: 3              # Maximum retry attempts
    backoff_multiplier: 1.5      # Exponential backoff factor
    initial_delay_seconds: 2     # First delay
    applies_to:
      - phase1_connection        # Phases to retry
      - phase2_display_info
```

**Backoff Calculation**:
```
Attempt 1: Immediate
Attempt 2: 2 seconds
Attempt 3: 2 * 1.5 = 3 seconds
Attempt 4: 3 * 1.5 = 4.5 seconds
```

### Per-Phase Failure Handling

```yaml
on_phase_failure:
  phase1: "Reconnect to device and retry"
  phase2: "Skip phase, continue to phase 3"
  phase3: "Continue to next iteration or skip phase"
  phase4: "Retry screenshot capture once, then continue"
  phase5: "Continue to next iteration or skip phase"
```

### Cleanup Actions

```yaml
cleanup_actions:
  - name: "close_connection"
    description: "Close ADB connection gracefully"
    action:
      script: ".claude/skills/moai-domain-adb/scripts/connection/disconnect.py"
      args: ["--device", "{{ parameters.device }}"]
    on_error: "log_warning"     # Don't fail on cleanup error

  - name: "cleanup_temp_files"
    description: "Clean up temporary files"
    action:
      type: file_cleanup
      patterns: ["/tmp/bluestacks-demo-*.tmp"]
      keep_recent: 3
```

---

## Section 9: Variable Substitution Examples

### Basic Substitution

```yaml
# Parameter reference
device: "{{ parameters.device }}"
# Resolves to: "127.0.0.1:5555"

# Parameter with default
timeout: "{{ parameters.timeout }}"
# Resolves to: 10 (default value if not provided)
```

### Phase Output Substitution

```yaml
# Reference previous phase output
model: "{{ phase1.outputs.device_model }}"
# Resolves to: "SM-G991B (Galaxy S21)"

# Reference with fallback
model_or_unknown: "{{ phase1.outputs.device_model || 'Unknown' }}"
```

### Loop Variable Substitution

```yaml
# Tap at coordinates from current item
args:
  - "{{ item.x }}"     # 540, 200, or 880
  - "{{ item.y }}"     # 960, 400, or 1520

# In loop condition
condition: "{{ loop.index < loop.total }}"
# Evaluates to: true for iteration 1-2, false for iteration 3
```

### Complex Substitution

```yaml
# File path with timestamp
path: "{{ parameters.screenshot_dir }}/screenshot-{{ workflow.timestamp }}.png"
# Resolves to: "/tmp/screenshot-2025-12-02T14:30:45Z.png"

# Math in substitution
success_rate: "{{ phase3.metrics.successful_taps / phase3.metrics.total_taps * 100 }}%"
# Resolves to: "100%" (if all successful)

# Conditional in title
title: "Execute {{ item.direction | upcase }} Swipe"
# With direction="up": "Execute UP Swipe"
```

---

## Section 10: Complete Example - Phase 3

### Full Phase 3 Definition

```yaml
phase3_control_demo:
  name: "Phase 3 - Interactive Control Demonstration"
  description: "Demonstrate tap commands at various screen locations"
  sequence: 3
  depends_on: ["phase2_display_info"]

  # Loop definition - 3 tap locations
  loop:
    type: items
    count: 3
    items:
      - id: tap_1
        description: "Center Screen Tap"
        x: 540
        y: 960
        coordinates_explanation: "Center of standard 1080x1920 display"
      - id: tap_2
        description: "Top-Left Corner Tap"
        x: 200
        y: 400
        coordinates_explanation: "Upper left quadrant"
      - id: tap_3
        description: "Bottom-Right Corner Tap"
        x: 880
        y: 1520
        coordinates_explanation: "Lower right quadrant"

  # Steps executed for each loop item
  loop_steps:
    - name: "loop_tap_step"
      title: "Execute Tap at {{ item.description }}"
      description: "Tap at coordinates ({{ item.x }}, {{ item.y }})"
      action:
        script: ".claude/skills/moai-domain-adb/scripts/control/tap.py"
        args:
          - "--device"
          - "{{ parameters.device }}"
          - "--x"
          - "{{ item.x }}"              # Substituted: 540, 200, 880
          - "--y"
          - "{{ item.y }}"              # Substituted: 960, 400, 1520
          - "--duration"
          - "100"
        timeout_seconds: 5
      validation:
        exit_code: 0
      on_success:
        log: "Tap {{ loop.index }}/{{ loop.total }} - {{ item.description }} successful at ({{ item.x }}, {{ item.y }})"
      on_failure:
        log: "Tap {{ loop.index }}/{{ loop.total }} failed, continuing..."
        action: continue

    - name: "loop_wait_between_taps"
      title: "Wait Between Taps"
      description: "Wait {{ parameters.tap_wait_duration }} second(s) before next tap"
      action:
        type: sleep
        duration_seconds: "{{ parameters.tap_wait_duration }}"
      condition: "{{ loop.index < loop.total }}"

  checkpoint: true
  metrics:
    total_taps: "{{ loop.total }}"
    successful_taps: "{{ loop.successful_count }}"
    failed_taps: "{{ loop.failed_count }}"
```

### Execution Trace

```
Phase 3: Interactive Control Demonstration
Depends on: Phase 2 (must succeed)

Loop defined: 3 items

=== ITERATION 1 ===
Loop Variables:
  item.id = "tap_1"
  item.description = "Center Screen Tap"
  item.x = 540
  item.y = 960
  loop.index = 1
  loop.total = 3

Step 1: "loop_tap_step"
  Title: Execute Tap at Center Screen Tap
  Action: tap.py --device 127.0.0.1:5555 --x 540 --y 960 --duration 100
  Result: SUCCESS
  Log: Tap 1/3 - Center Screen Tap successful at (540, 960)

Step 2: "loop_wait_between_taps"
  Condition: 1 < 3 = TRUE
  Action: sleep 1 second
  Result: SUCCESS

=== ITERATION 2 ===
Loop Variables:
  item.id = "tap_2"
  item.description = "Top-Left Corner Tap"
  item.x = 200
  item.y = 400
  loop.index = 2
  loop.total = 3

Step 1: "loop_tap_step"
  Title: Execute Tap at Top-Left Corner Tap
  Action: tap.py --device 127.0.0.1:5555 --x 200 --y 400 --duration 100
  Result: SUCCESS
  Log: Tap 2/3 - Top-Left Corner Tap successful at (200, 400)

Step 2: "loop_wait_between_taps"
  Condition: 2 < 3 = TRUE
  Action: sleep 1 second
  Result: SUCCESS

=== ITERATION 3 ===
Loop Variables:
  item.id = "tap_3"
  item.description = "Bottom-Right Corner Tap"
  item.x = 880
  item.y = 1520
  loop.index = 3
  loop.total = 3

Step 1: "loop_tap_step"
  Title: Execute Tap at Bottom-Right Corner Tap
  Action: tap.py --device 127.0.0.1:5555 --x 880 --y 1520 --duration 100
  Result: SUCCESS
  Log: Tap 3/3 - Bottom-Right Corner Tap successful at (880, 1520)

Step 2: "loop_wait_between_taps"
  Condition: 3 < 3 = FALSE
  Action: SKIPPED (don't wait after last iteration)

=== PHASE COMPLETE ===
Checkpoint: SUCCESS (can resume from here)
Metrics:
  total_taps: 3
  successful_taps: 3
  failed_taps: 0
  success_rate: 100%
```

---

## Section 11: TOON Syntax Cheat Sheet

### Common Patterns

**Parameter with Default**:
```yaml
default: "127.0.0.1:5555"
reference: "{{ parameters.device }}"
```

**Timestamp**:
```yaml
timestamp: "{{ workflow.timestamp }}"
file: "demo-{{ workflow.timestamp }}.png"
```

**Loop Iteration**:
```yaml
title: "Iteration {{ loop.index }}/{{ loop.total }}"
condition: "{{ loop.index < loop.total }}"
```

**Phase Output**:
```yaml
value: "{{ phase1.outputs.device_model }}"
reference: "{{ phase3.metrics.successful_taps }}"
```

**Phase Success**:
```yaml
depends_on: ["phase1_connection"]
check: "phase1.status == 'success'"
```

**File Path**:
```yaml
path: "/tmp/output-{{ timestamp }}.png"
reference: "{{ parameters.screenshot_dir }}"
```

**Conditional**:
```yaml
condition: "{{ loop.index < loop.total }}"
check: "success_rate >= 0.8"
```

---

## Token Efficiency Analysis

### TOON vs JSON Comparison

**TOON YAML** (550 lines):
```yaml
loop:
  type: items
  count: 3
  items:
    - id: tap_1
      x: 540
```
**Tokens**: ~45

**Equivalent JSON**:
```json
{
  "loop": {
    "type": "items",
    "count": 3,
    "items": [
      {
        "id": "tap_1",
        "x": 540
      }
    ]
  }
}
```
**Tokens**: ~78

**Savings**: 42% reduction

---

## Best Practices

1. **Use Template Variables**: Always use `{{ }}` for dynamic values
2. **Reference Phase Outputs**: Use `{{ phaseN.outputs.* }}` in subsequent phases
3. **Validate Conditions**: Use `condition:` to skip steps conditionally
4. **Log Actions**: Add `on_success` and `on_failure` handlers
5. **Handle Errors**: Use `on_error` with appropriate actions (retry, continue, abort)
6. **Checkpoint Phases**: Mark critical phases with `checkpoint: true`
7. **Document Custom Fields**: Add comments for non-standard item fields

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: Complete Reference
