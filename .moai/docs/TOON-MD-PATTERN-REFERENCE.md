---
name: TOON+MD Pattern Reference
description: Technical reference for TOON orchestration files and MD documentation paired pattern
version: 1.0.0
created: 2025-12-02
updated: 2025-12-02
audience: Builder agents, developers, system architects
status: active
format: Technical Reference
---

# TOON+MD Pattern Reference

**Purpose**: Complete technical reference for TOON orchestration files paired with Markdown documentation.

**Scope**: Format specifications, syntax rules, validation criteria, and examples.

**Version**: Phase 3B (2025-12-02)

---

## Executive Summary

### What is TOON+MD?

**TOON** (Task-Oriented Orchestration Notation):
- File extension: `.toon`
- Format: YAML with standardized sections
- Purpose: Define workflow execution logic
- Audience: Automated systems, workflow engines, agents
- Philosophy: Machine-readable orchestration with human-readable structure

**MD** (Markdown):
- File extension: `.md`
- Format: Standard GitHub-flavored Markdown
- Purpose: Human-readable documentation and guidance
- Audience: Developers, end users, documentation systems
- Philosophy: Comprehensive documentation paired with orchestration

### The Pairing Pattern

Every workflow consists of **exactly two files** with the same base name:

```
workflow/
├── action_name.toon    ← Orchestration definition
└── action_name.md      ← Documentation
```

**Why Both?**
1. **TOON** tells systems HOW to execute the workflow
2. **MD** tells humans WHAT the workflow does, WHY it exists, and HOW to use it
3. **Pairing** ensures documentation and implementation stay synchronized
4. **Completeness** neither file is sufficient alone

---

## Part 1: TOON File Specification

### 1.1 File Format and Structure

TOON files are **valid YAML v1.2** with specific sections.

#### Document Marker

```yaml
---
# TOON v4.0 format
# All TOON files must start with document marker
```

#### Basic Structure

```yaml
---
# Metadata section
name: workflow_identifier
version: 1.0.0
type: automation | validation | transformation | integration
description: One-line description

# Configuration section (optional)
config:
  key: value

# Input parameters section (required)
inputs:
  param_name:
    type: string | number | boolean | array | object
    required: true | false
    default: value
    description: Parameter description
    validation: validation_rule

# Stages section (logical grouping)
stages:
  stage_name:
    description: What this stage does
    duration_seconds: estimated_time
    critical: true | false

# Steps section (detailed actions)
steps:
  stage_name:
    - name: step_identifier
      type: step_type
      # step-specific fields

# Output parameters section
outputs:
  output_name: type
  output_name: type

# Success criteria section (validation rules)
success_criteria:
  - rule_name: expected_value

# Error handling section
on_failure:
  - action: action_type
    # action-specific fields

# Optional sections
timing:
  total_timeout_seconds: number
  inter_step_delay_seconds: number

retry_policy:
  max_attempts: number
  exponential_backoff: true | false
  backoff_multiplier: float

logging:
  level: debug | info | warning | error
  output_file: path
  include_credentials: false
  include_timestamps: true
```

### 1.2 Metadata Section

**Purpose**: Identify and describe the workflow.

**Required Fields**:

```yaml
---
name: workflow_identifier
  # Identifies the workflow
  # Format: snake_case, lowercase letters and underscores only
  # Example: login_automation, capture_screen, verify_device

version: semantic_version
  # Semantic versioning: MAJOR.MINOR.PATCH
  # Initial: 1.0.0
  # Changes: increment PATCH for fixes, MINOR for features, MAJOR for breaking changes

type: automation | validation | transformation | integration
  # automation: Automated user actions (clicking, typing)
  # validation: Verify state or conditions (checks)
  # transformation: Data transformation (convert, process)
  # integration: External service integration (API calls)

description: string
  # One-line human-readable description
  # Max 200 characters
  # Example: "Automate login to Karrot app with credential validation"
```

**Optional Fields**:

```yaml
author: name
  # Who created the workflow
  # Default: workflow-designer

created: ISO8601_date
  # Creation date in ISO 8601 format
  # Example: 2025-12-02T14:30:00Z

tags: [tag1, tag2, tag3]
  # Searchable tags for categorization
  # Examples: [automation, login, authentication, adb]

deprecated: false | true
  # Mark workflow as deprecated (will be removed)
  # If true, include deprecation_reason and deprecated_in

deprecated_in: version
  # Version in which workflow was deprecated

replacement: new_workflow_name
  # New workflow that replaces this one
```

### 1.3 Config Section (Optional)

**Purpose**: Workflow-specific configuration options.

**Common Config Options**:

```yaml
config:
  # Detection strategy (order of fallback methods)
  detection_method: hybrid | semantic | template | ocr
    # hybrid: Try semantic, fall back to template, then OCR
    # semantic: UI semantics/accessibility
    # template: Image template matching
    # ocr: Optical character recognition

  # Input validation
  input_validation: true | false
    # true: Validate inputs before execution
    # false: Skip validation (faster, less safe)

  # Screenshot on error
  screenshot_on_error: true | false
    # true: Take screenshot when error occurs
    # false: Don't capture screenshots

  # Custom options
  any_custom_option: value
    # Workflows can define custom config options
```

### 1.4 Inputs Section

**Purpose**: Define parameters required from the caller.

**Structure**:

```yaml
inputs:
  parameter_name:
    type: parameter_type
    required: boolean
    default: default_value
    description: string
    validation: validation_rule
    examples:
      - example1
      - example2
```

**Parameter Types**:

| Type | Examples | Usage |
|------|----------|-------|
| string | email, text, path | Text values, file paths |
| number | 10, 3.14, -5 | Numeric values |
| boolean | true, false | Flags, yes/no options |
| array | [1, 2, 3] | Lists of values |
| object | {key: value} | Complex structures |

**Examples**:

```yaml
inputs:
  # Required string
  email:
    type: string
    required: true
    description: "User email address"
    validation: "matches regex ^[^@]+@[^@]+\\.[^@]+$"
    examples:
      - user@example.com
      - test@domain.co.uk

  # Optional number with default
  timeout:
    type: number
    required: false
    default: 180
    description: "Operation timeout in seconds"
    validation: "greater_than 0, less_than 3600"

  # Optional boolean
  verbose:
    type: boolean
    required: false
    default: false
    description: "Enable verbose logging"

  # Optional array
  targets:
    type: array
    required: false
    default: []
    description: "List of target devices"
    examples:
      - ["192.168.1.100:5555"]
      - ["device1", "device2"]

  # Optional object
  config:
    type: object
    required: false
    description: "Custom configuration"
    examples:
      - {retries: 3, timeout: 180}
```

**Validation Rules**:

```yaml
# String validations
validation: "length >= 5"                    # Min length 5
validation: "length <= 100"                  # Max length 100
validation: "length >= 5, length <= 100"     # Between 5-100
validation: "matches regex ^[A-Z].*"         # Regex pattern
validation: "one_of [option1, option2]"      # Enum values

# Number validations
validation: "greater_than 0"                 # > 0
validation: "greater_equal 1"                # >= 1
validation: "less_than 100"                  # < 100
validation: "less_equal 100"                 # <= 100
validation: "between 1, 100"                 # 1 <= x <= 100

# Array validations
validation: "length >= 1"                    # At least 1 item
validation: "max_items 10"                   # At most 10 items

# Boolean validations
validation: "required true"                  # Must be true
```

### 1.5 Stages Section

**Purpose**: Organize workflow into logical phases.

**Structure**:

```yaml
stages:
  stage_identifier:
    description: string
    duration_seconds: number
    critical: boolean
    optional: boolean
    skip_on_condition: string
```

**Fields**:

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| description | string | Yes | What this stage does |
| duration_seconds | number | No | Estimated time in seconds |
| critical | boolean | No | Is stage essential? (default: true) |
| optional | boolean | No | Can stage be skipped? (default: false) |
| skip_on_condition | string | No | Skip if condition met |

**Examples**:

```yaml
stages:
  # Essential stage that must complete
  verify_login_screen:
    description: "Verify we're on the login screen"
    duration_seconds: 10
    critical: true

  # Optional stage that might be skipped
  handle_2fa:
    description: "Handle two-factor authentication if required"
    duration_seconds: 60
    critical: false
    optional: true
    skip_on_condition: "inputs.two_factor_enabled == false"

  # Long-running stage
  wait_for_sync:
    description: "Wait for data synchronization"
    duration_seconds: 300
    critical: true
```

### 1.6 Steps Section

**Purpose**: Define individual actions within each stage.

**Structure**:

```yaml
steps:
  stage_identifier:
    - name: step_identifier
      type: step_type
      # Type-specific fields below
      timeout_seconds: number
      required: boolean
      condition: string
      on_failure: string
      on_success: string
      on_timeout: string
```

**Universal Step Fields**:

| Field | Type | Purpose |
|-------|------|---------|
| name | string | Unique identifier within stage |
| type | string | Step type (determines behavior) |
| timeout_seconds | number | Max time for this step |
| required | boolean | Is step essential? |
| condition | string | Execute only if condition true |
| on_failure | string | Action if step fails |
| on_success | string | Action if step succeeds |
| on_timeout | string | Action if step times out |

**Step Types and Fields**:

#### ui_find (Find UI element)

```yaml
- name: find_login_button
  type: ui_find
  method: hybrid | semantic | template | ocr
  target_text: string              # Text to find
  target_class: string             # UI element class
  target_id: string                # Element ID
  target_xpath: string             # XPath expression
  index: number                    # Match index (0-based)
  region: {x, y, width, height}   # Search region
  timeout_seconds: number
  required: boolean
```

#### ui_tap (Tap/click element)

```yaml
- name: tap_button
  type: ui_tap
  method: semantic | coordinate
  target_text: string              # Text to tap
  target_class: string             # Class to tap
  coordinate: [x, y]              # Absolute coordinates
  offset: [dx, dy]                # Offset from target
  timeout_seconds: number
```

#### ui_input (Input text)

```yaml
- name: type_email
  type: ui_input
  text: string                     # Text to input (supports {variable})
  clear_first: boolean             # Clear field before input
  method: keyboard | clipboard    # Input method
  timeout_seconds: number
```

#### ui_wait (Wait for element)

```yaml
- name: wait_for_home
  type: ui_wait
  target_text: string              # Text to wait for
  target_class: string             # Class to wait for
  timeout_seconds: number
  on_timeout: action               # What to do if timeout
```

#### screenshot (Capture screen)

```yaml
- name: capture_login_screen
  type: screenshot
  output: /path/to/file.png       # Output file path
  include_timestamp: boolean       # Append timestamp to filename
  optional: boolean                # Is screenshot optional?
```

#### delay (Wait/pause)

```yaml
- name: pause_before_next
  type: delay
  duration_seconds: number
```

#### custom (Custom action)

```yaml
- name: run_custom_script
  type: custom
  script: path/to/script.py       # Script to execute
  params:                          # Script parameters
    key: value
  timeout_seconds: number
```

#### workflow (Execute nested workflow)

```yaml
- name: run_login_workflow
  type: workflow
  workflow_ref: login_automation.toon
  params:                          # Pass parameters
    email: "{inputs.email}"
    password: "{inputs.password}"
  timeout_seconds: number
```

**Examples**:

```yaml
steps:
  verify_login_screen:
    - name: check_login_button
      type: ui_find
      method: hybrid
      target_text: "로그인"           # Login button in Korean
      timeout_seconds: 10
      on_failure: "screenshot_and_alert"

  enter_credentials:
    - name: find_email_input
      type: ui_find
      method: semantic
      target_class: android.widget.EditText
      timeout_seconds: 10

    - name: tap_email_field
      type: ui_tap
      method: semantic
      target_class: android.widget.EditText
      index: 0
      timeout_seconds: 5

    - name: type_email
      type: ui_input
      text: "{inputs.email}"        # Reference input parameter
      clear_first: true
      timeout_seconds: 5

  submit_login:
    - name: find_login_button
      type: ui_find
      method: hybrid
      target_text: "로그인"
      timeout_seconds: 10

    - name: tap_login_button
      type: ui_tap
      method: semantic
      target_text: "로그인"
      timeout_seconds: 5

    - name: wait_after_tap
      type: delay
      duration_seconds: 2
```

### 1.7 Outputs Section

**Purpose**: Define values returned after workflow execution.

**Structure**:

```yaml
outputs:
  output_name: type
  output_name: type
  # Optional: include description
  output_name:
    type: type
    description: string
    required: boolean
```

**Examples**:

```yaml
outputs:
  # Simple output
  login_successful: boolean
  home_screen_reached: boolean
  authentication_time_seconds: number
  error_message: string
  final_screenshot_path: string

  # Complex output with description
  user_profile:
    type: object
    description: "User profile information"
    required: false
```

### 1.8 Success Criteria Section

**Purpose**: Define rules that determine success.

**Structure**:

```yaml
success_criteria:
  - criterion_name: expected_value
  - criterion_name: expected_value

# Complex criteria with conditions
success_criteria:
  - all_of:
    - login_button_exists: true
    - email_field_filled: true
    - password_field_filled: true

  - one_of:
    - home_screen_visible: true
    - profile_page_visible: true
```

**Examples**:

```yaml
success_criteria:
  - login_button_exists: true
  - email_field_filled: true
  - password_field_filled: true
  - home_screen_accessible: true
  - user_profile_visible: true
  - total_time_seconds: "less_than 180"
  - no_error_messages: true
```

### 1.9 Error Handling Section (on_failure)

**Purpose**: Define actions when workflow fails.

**Structure**:

```yaml
on_failure:
  - action: action_type
    # Action-specific fields

  - action: action_type
    condition: "error_type == 'timeout'"
    # Conditional action
```

**Action Types**:

#### screenshot (Save error screenshot)

```yaml
- action: screenshot
  output: /sdcard/error.png
  include_context: true
```

#### check_error_message (Analyze error)

```yaml
- action: check_error_message
  patterns:
    - "Pattern 1"
    - "Pattern 2"
```

#### alert (Send notification)

```yaml
- action: alert
  message: "Workflow failed: {error_message}"
  severity: error | warning | info
```

#### retry (Retry workflow)

```yaml
- action: retry
  max_attempts: 3
  exponential_backoff: true
  backoff_multiplier: 1.5
```

#### cleanup (Clean up resources)

```yaml
- action: cleanup
  # Custom cleanup logic
```

**Examples**:

```yaml
on_failure:
  - action: take_screenshot
    output: /sdcard/karrot_login_error.png

  - action: check_error_message
    patterns:
      - "이메일 또는 비밀번호가 일치하지 않습니다"    # Email/password mismatch
      - "계정을 찾을 수 없습니다"                     # Account not found
      - "로그인 횟수를 초과했습니다"                 # Too many attempts

  - action: alert
    message: "Login failed. Check credentials and retry."
    severity: error

  - action: cleanup
    # Clean up any temporary files
```

### 1.10 Timing and Retry Sections (Optional)

**Purpose**: Configure execution timing and retry behavior.

#### Timing

```yaml
timing:
  total_timeout_seconds: number      # Overall workflow timeout
  inter_step_delay_seconds: number   # Delay between steps
  stage_timeouts:
    stage1: number
    stage2: number
```

#### Retry Policy

```yaml
retry_policy:
  max_attempts: number               # How many times to retry
  exponential_backoff: true | false  # Use exponential backoff?
  backoff_multiplier: float          # Backoff multiplier (e.g., 1.5)
  retry_on:
    - error_type1
    - error_type2
  dont_retry_on:
    - error_type3
```

### 1.11 Logging Section (Optional)

**Purpose**: Configure logging behavior.

```yaml
logging:
  level: debug | info | warning | error
  output_file: path/to/logfile.log
  include_credentials: false         # Never log passwords!
  include_timestamps: true
  max_log_lines: number
  rotate_on_size: number             # Rotate logs at this size
```

---

## Part 2: Markdown Documentation Specification

### 2.1 File Format and Structure

Markdown files use **GitHub-flavored Markdown (GFM)** with standard sections.

#### Document Header

```markdown
---
name: Workflow Name
workflow: workflow_identifier.toon
version: 1.0.0
created: 2025-12-02
last_updated: 2025-12-02
---

# Workflow Name

[Content begins here]
```

#### Section Structure

```markdown
# Workflow Name (H1)

## Purpose (H2)
## Scope (H2)
## Prerequisites (H2)
## Parameters (H2)
## Workflow Phases (H2)
## Success Criteria (H2)
## Error Handling (H2)
## Execution Example (H2)
## See Also (H2)
## Changelog (H2)
```

### 2.2 Required Sections

#### Purpose Section

```markdown
## Purpose

Clear description of what the workflow does.

**In Scope:**
- Specific functionality included

**Out of Scope:**
- What this workflow does NOT do

**Use Cases:**
- When to use this workflow
- Common scenarios
```

#### Prerequisites Section

```markdown
## Prerequisites

Before running this workflow:

1. Device connected via ADB
2. Application installed
3. User account created
4. Internet connection available
5. Permissions configured

**Validation:**
```bash
# Command to verify prerequisites
adb devices
```

#### Parameters Section

```markdown
## Parameters

### Required Inputs

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| param1 | string | value | What it does |
| param2 | number | 10 | What it does |

### Optional Inputs

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| param3 | boolean | false | What it does |

### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| output1 | boolean | Result status |
| output2 | string | Result details |
```

#### Workflow Phases Section

```markdown
## Workflow Phases

### Phase 1: [Phase Name] (XX seconds)

**Goal**: [What this phase achieves]

**Steps:**
1. Step description
2. Step description
3. Step description

**Success Indicators:**
- [ ] Indicator 1
- [ ] Indicator 2

### Phase 2: [Phase Name] (XX seconds)
...
```

#### Success Criteria Section

```markdown
## Success Criteria

All of the following must be true:

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
- [ ] Criterion 4
- [ ] No error messages
```

#### Error Handling Section

```markdown
## Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|-----------|
| "Error message" | What causes it | How to fix it |

### Troubleshooting

**Problem: Description**
- Possible cause 1: Resolution
- Possible cause 2: Resolution

**Problem: Description**
- Possible cause 1: Resolution
```

#### Execution Example Section

```markdown
## Execution Example

### Command Line

```bash
# Basic execution
uv run .claude/skills/[skill]/workflow/[name].py \
  --param1 value \
  --param2 value

# With optional parameters
uv run .claude/skills/[skill]/workflow/[name].py \
  --param1 value \
  --param2 value \
  --timeout 180
```

### In Python

```python
from workflow import WorkflowName

workflow = WorkflowName()
result = workflow.run(
    param1="value",
    param2="value"
)

if result.success:
    print("Workflow completed")
```

### In TOON/Orchestration

```yaml
workflows:
  - name: my_workflow
    workflow_file: workflow_name.toon
    inputs:
      param1: value
      param2: value
```
```

#### See Also Section

```markdown
## See Also

- [Related Skill 1](../skill-name/SKILL.md)
- [Related Skill 2](../skill-name/SKILL.md)
- [Documentation](path/to/docs)
- [External Resource](https://example.com)
```

#### Changelog Section

```markdown
## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-02 | Initial version |
| 1.1.0 | 2025-12-05 | Added 2FA support |
```

---

## Part 3: Pairing Rules and Validation

### 3.1 Naming Convention

**Rule**: File names must match exactly (except extension).

```
workflow/
├── login_automation.toon      ✓ Paired
├── login_automation.md        ✓ Paired
├── capture_screen.toon        ✓ Paired
├── capture_screen.md          ✓ Paired
├── process_image.toon         ✗ Missing .md (ERROR)
└── extract_text.md            ✗ Missing .toon (ERROR)
```

### 3.2 Cross-Reference Requirements

**In TOON file**:
```yaml
# Reference the paired MD file
# (implicit, for documentation purposes)
```

**In MD file frontmatter**:
```markdown
---
name: Workflow Name
workflow: workflow_name.toon  ← Reference TOON file
version: 1.0.0
---
```

### 3.3 Content Alignment

**Rule**: Parameters, outputs, and phases must align.

#### Inputs Alignment

**In TOON**:
```yaml
inputs:
  email:
    type: string
    required: true
  password:
    type: string
    required: true
```

**In MD (Parameters section)**:
```markdown
| email | string | required | User email |
| password | string | required | User password |
```

#### Outputs Alignment

**In TOON**:
```yaml
outputs:
  login_successful: boolean
  error_message: string
```

**In MD (Output Parameters section)**:
```markdown
| login_successful | boolean | Whether login succeeded |
| error_message | string | Error details if failed |
```

#### Phases Alignment

**In TOON**:
```yaml
stages:
  verify_screen:
    description: Verify login screen
  enter_credentials:
    description: Enter email and password
```

**In MD**:
```markdown
### Phase 1: Verify Login Screen
### Phase 2: Enter Credentials
```

### 3.4 Validation Checklist

When creating TOON+MD pair:

```markdown
## File Pairing
- [ ] .toon file exists
- [ ] .md file exists
- [ ] File names identical (except extension)

## TOON Validation
- [ ] Valid YAML syntax
- [ ] Contains: name, version, type, inputs, stages, steps, outputs, success_criteria, on_failure
- [ ] All step types are valid
- [ ] Parameter references use {param_name} format
- [ ] No hardcoded values (use inputs)

## MD Validation
- [ ] Valid Markdown syntax
- [ ] Frontmatter includes workflow reference
- [ ] Contains: Purpose, Prerequisites, Parameters, Phases, Success Criteria, Error Handling, Execution, Changelog
- [ ] All links work
- [ ] Code examples are correct

## Alignment
- [ ] Input parameters in TOON match MD Parameters section
- [ ] Output parameters in TOON match MD Output section
- [ ] Stages in TOON match Phases in MD
- [ ] Success criteria in TOON documented in MD
- [ ] Error patterns in TOON documented in Error Handling MD section

## Cross-References
- [ ] MD references TOON file name correctly
- [ ] Links to related workflows work
- [ ] Links to parent skill work
- [ ] No broken relative paths
```

---

## Part 4: TOON v4.0 Examples

### Example 1: Simple Screenshot Workflow

**File: screenshot.toon**

```yaml
---
name: simple_screenshot
version: 1.0.0
type: automation
description: Capture Android device screen and save to file

config:
  screenshot_on_error: true

inputs:
  device:
    type: string
    required: false
    default: auto
    description: Target device ID or auto-detect

stages:
  capture:
    description: Capture device screen
    duration_seconds: 5
    critical: true

steps:
  capture:
    - name: take_screenshot
      type: screenshot
      output: /sdcard/screenshot_{timestamp}.png
      timeout_seconds: 5

outputs:
  screenshot_path: string
  success: boolean
  timestamp: string

success_criteria:
  - screenshot_taken: true
  - file_exists: true

on_failure:
  - action: alert
    message: "Failed to capture screenshot"
```

**File: screenshot.md**

```markdown
---
name: Simple Screenshot
workflow: screenshot.toon
version: 1.0.0
---

# Simple Screenshot Workflow

## Purpose
Quickly capture a screenshot of the Android device screen.

## Prerequisites
- Device connected via ADB
- Sufficient storage on device

## Parameters

### Optional Inputs
| Name | Type | Default | Description |
|------|------|---------|-------------|
| device | string | auto | Target device ID |

### Outputs
| Name | Type | Description |
|------|------|-------------|
| screenshot_path | string | Path to screenshot file |
| success | boolean | Success status |

## Execution
```bash
uv run .claude/skills/[skill]/workflow/screenshot.py
```

## Success Criteria
- [ ] Screenshot captured
- [ ] File saved to device

## Changelog
| 1.0.0 | 2025-12-02 | Initial version |
```

### Example 2: Complex Login with 2FA

**File: login_with_2fa.toon**

```yaml
---
name: login_with_2fa
version: 1.0.0
type: automation
description: Login with email, password, and optional 2FA

config:
  detection_method: hybrid
  input_validation: true
  screenshot_on_error: true

inputs:
  email:
    type: string
    required: true
    description: User email
    validation: "matches regex ^[^@]+@[^@]+\\.[^@]+$"

  password:
    type: string
    required: true
    description: User password
    validation: "length >= 6"

  two_factor_enabled:
    type: boolean
    required: false
    default: false
    description: Is 2FA enabled?

  two_factor_code:
    type: string
    required: false
    description: 2FA code (if 2FA enabled)

stages:
  verify_login_screen:
    description: Verify we're on login screen
    duration_seconds: 10
    critical: true

  enter_credentials:
    description: Enter email and password
    duration_seconds: 30
    critical: true

  handle_2fa:
    description: Handle 2FA if required
    duration_seconds: 60
    critical: false
    optional: true
    skip_on_condition: "inputs.two_factor_enabled == false"

  verify_success:
    description: Verify successful login
    duration_seconds: 30
    critical: true

steps:
  verify_login_screen:
    - name: check_login_button
      type: ui_find
      method: hybrid
      target_text: "로그인"
      timeout_seconds: 10

  enter_credentials:
    - name: find_email_input
      type: ui_find
      method: semantic
      target_class: android.widget.EditText
      timeout_seconds: 10

    - name: tap_email_field
      type: ui_tap
      method: semantic
      target_class: android.widget.EditText
      index: 0
      timeout_seconds: 5

    - name: type_email
      type: ui_input
      text: "{inputs.email}"
      clear_first: true
      timeout_seconds: 5

    - name: find_password_input
      type: ui_find
      method: semantic
      target_class: android.widget.EditText
      index: 1
      timeout_seconds: 10

    - name: tap_password_field
      type: ui_tap
      method: semantic
      target_class: android.widget.EditText
      index: 1
      timeout_seconds: 5

    - name: type_password
      type: ui_input
      text: "{inputs.password}"
      clear_first: true
      timeout_seconds: 5

  handle_2fa:
    - name: look_for_2fa_prompt
      type: ui_find
      method: semantic
      target_text: "인증코드"
      timeout_seconds: 5
      condition: "inputs.two_factor_enabled == true"
      required: false

    - name: tap_2fa_input
      type: ui_tap
      method: semantic
      target_class: android.widget.EditText
      index: 0
      timeout_seconds: 5
      condition: "inputs.two_factor_enabled == true"

    - name: type_2fa_code
      type: ui_input
      text: "{inputs.two_factor_code}"
      timeout_seconds: 5
      condition: "inputs.two_factor_enabled == true"

  verify_success:
    - name: wait_home_screen
      type: ui_wait
      target_text: "홈"
      timeout_seconds: 30

    - name: capture_success
      type: screenshot
      output: /sdcard/login_success_{timestamp}.png

outputs:
  login_successful: boolean
  home_screen_reached: boolean
  authentication_time_seconds: number
  error_message: string

success_criteria:
  - login_button_exists: true
  - email_field_populated: true
  - password_field_populated: true
  - home_screen_visible: true

on_failure:
  - action: screenshot
    output: /sdcard/login_error_{timestamp}.png

  - action: check_error_message
    patterns:
      - "이메일 또는 비밀번호가 일치하지 않습니다"
      - "계정을 찾을 수 없습니다"
      - "2FA 코드가 일치하지 않습니다"

  - action: alert
    message: "Login failed: {error_message}"
    severity: error

timing:
  total_timeout_seconds: 180
  inter_step_delay_seconds: 1

retry_policy:
  max_attempts: 3
  exponential_backoff: true
  backoff_multiplier: 1.5

logging:
  level: info
  output_file: login_2fa.log
  include_credentials: false
  include_timestamps: true
```

---

## Part 5: Auto-Nesting Rules

### 5.1 Detection Rules

**Rule**: If 5 or more workflow files with the same prefix exist, nest them.

### 5.2 Nesting Process

1. **Count workflows by prefix**
   ```bash
   ls -1 *.toon | sed 's/_.*//' | sort | uniq -c | sort -rn
   ```

2. **Create subfolder** if count >= 5
   ```bash
   mkdir [prefix]
   ```

3. **Move related files**
   ```bash
   mv [prefix]_*.toon [prefix]/
   mv [prefix]_*.md [prefix]/
   ```

4. **Create subfolder README.md**
   ```markdown
   # [Prefix] Workflows

   - [File 1](file1.md)
   - [File 2](file2.md)
   ```

5. **Update parent README.md**
   ```markdown
   ## [Prefix] Workflows

   See [prefix/README.md](prefix/README.md)
   ```

---

## Part 6: Validation and Quality

### 6.1 TOON Syntax Validation

```bash
# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('file.toon'))"

# Validate JSON schema (if schema exists)
jsonschema validate -d file.toon schema.json
```

### 6.2 Markdown Validation

```bash
# Check Markdown syntax
markdownlint file.md

# Check links
markdown-link-check file.md

# Render check
pandoc file.md -f markdown -t html > output.html
```

### 6.3 Pairing Validation

```bash
# Find unpaired files
ls *.toon | sed 's/.toon//' | while read f; do
  [ ! -f "$f.md" ] && echo "Missing: $f.md"
done

ls *.md | sed 's/.md//' | while read f; do
  [ ! -f "$f.toon" ] && echo "Missing: $f.toon"
done
```

---

## Part 7: Best Practices

### Parameter Handling

✓ Use input parameters: `text: "{inputs.email}"`
✗ Don't hardcode values: `text: "hardcoded_value"`

### Error Messages

✓ Specific error patterns: `"Email format invalid"`
✗ Generic patterns: `"Error occurred"`

### Timeouts

✓ Reasonable timeouts: `timeout_seconds: 10`
✗ Very long timeouts: `timeout_seconds: 3600`

### Logging

✓ Never log credentials: `include_credentials: false`
✗ Don't log passwords: `include_credentials: true`

### Documentation

✓ Comprehensive examples in MD
✗ Minimal or no examples
✗ Code examples that don't work

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-02 | Initial TOON+MD reference for Phase 3B |

---

## References

- TOON Specification: Task-Oriented Orchestration Notation v4.0
- Markdown: GitHub-flavored Markdown (GFM)
- YAML: YAML v1.2 specification
- Agent Training: [Agent Ecosystem Training](../skills/builder-agent/AGENT-ECOSYSTEM-TRAINING.md)
- Implementation Guide: [Workflow Structure Guide](../skills/builder-skill/WORKFLOW-STRUCTURE-GUIDE.md)

---

**Status**: Active Reference Document
**Audience**: Builder agents, developers, system architects
**Last Updated**: 2025-12-02
