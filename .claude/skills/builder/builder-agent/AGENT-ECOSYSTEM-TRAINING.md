---
name: Agent Ecosystem Training Guide
description: Comprehensive training for builder agents on creating skills with TOON+MD workflow structure
version: 1.0.0
created: 2025-12-02
updated: 2025-12-02
audience: Builder agents (builder-skill, builder-workflow-designer, builder-agent)
status: active
---

# Agent Ecosystem Training Guide

**Purpose**: Train builder agents on the new ADB ecosystem skill creation workflow with TOON+MD pairing pattern.

**Duration**: 15-20 minutes to read fully, reference as needed during development.

---

## Quick Summary (2 minutes)

### What Changed?

Old structure (before Phase 3B):
```
skills/my-skill/
└── scripts/  # Python scripts only
```

New structure (Phase 3B onwards):
```
skills/my-skill/
├── scripts/  # Python scripts (existing pattern)
└── workflow/ # NEW - TOON+MD workflow pairs
    ├── action1.toon       # Orchestration definition
    ├── action1.md         # Documentation
    ├── action2.toon
    ├── action2.md
    └── README.md
```

### Key Points
- Skills now require TWO folders: `scripts/` + `workflow/`
- Each workflow needs PAIR: `name.toon` + `name.md`
- TOON file = orchestration logic; MD file = documentation
- Auto-nesting: 5+ items with same prefix → create subfolder
- Both folders required when creating new skills

---

## Part 1: New Skill Structure

### Traditional Skills (Phase 1-2)

Skills had **scripts only**:

```
.claude/skills/adb-screen-detection/
├── SKILL.md              # Skill metadata
├── scripts/              # Python scripts
│   ├── adb-screen-capture.py
│   ├── adb-ocr-extract.py
│   └── adb-find-element.py
└── workflow/             # NEW - empty initially
    └── README.md
```

### Enhanced Skills (Phase 3B)

Skills now have **scripts + workflows**:

```
.claude/skills/adb-screen-detection/
├── SKILL.md              # Skill metadata (UPDATED)
├── scripts/              # Python scripts (unchanged)
│   ├── adb-screen-capture.py
│   ├── adb-ocr-extract.py
│   └── adb-find-element.py
└── workflow/             # NEW - TOON+MD pairs
    ├── README.md         # Workflow documentation index
    ├── capture.toon      # Orchestration
    ├── capture.md        # Documentation
    ├── extract.toon      # Orchestration
    ├── extract.md        # Documentation
    ├── find.toon         # Orchestration
    └── find.md           # Documentation
```

### Directory Requirements

When creating a new skill, always include:

```markdown
✓ .claude/skills/[skill-name]/
  ✓ SKILL.md - Skill metadata and overview
  ✓ scripts/ - Python/Shell scripts (required)
  ✓ workflow/ - TOON+MD workflow pairs (required)
  ✓ README.md or workflow/README.md - Workflow index
```

**Never create**:
- Skills with only scripts/ (add workflow/)
- Skills with only workflow/ (scripts are still needed)
- Workflow files without both .toon and .md

---

## Part 2: TOON+MD Pairing Pattern

### What is TOON+MD?

**TOON** (Task-Oriented Orchestration Notation):
- File extension: `.toon`
- Purpose: Define workflow orchestration logic
- Format: YAML-based with specific sections
- Audience: Systems, agents, parsers
- Example: `login-automation.toon`

**MD** (Markdown Documentation):
- File extension: `.md`
- Purpose: Document workflow in human-readable format
- Format: Markdown with standard sections
- Audience: Developers, users, learners
- Example: `login-automation.md`

### The Pairing Rule

**Every TOON file must have a corresponding MD file with the same name.**

```
workflow/
├── login-automation.toon    ← Orchestration
├── login-automation.md      ← Documentation
├── ui-detection.toon
├── ui-detection.md
└── error-recovery.toon
└── error-recovery.md
```

**Why Pair Them?**
1. **Orchestration** (TOON): Tells systems HOW to execute
2. **Documentation** (MD): Tells humans WHAT and WHY
3. **Completeness**: Neither alone is sufficient
4. **Maintainability**: Changes update both together

---

### Part 2A: TOON File Structure (Orchestration)

A TOON file defines the workflow execution logic.

#### TOON v4.0 Basic Syntax

```yaml
---
# TOON v4.0 - Task-Oriented Orchestration Notation
name: login_automation
version: 1.0.0
type: automation
description: Automate login to Karrot app with credential validation

# Metadata
author: builder-workflow-designer
created: 2025-12-02
tags: [automation, login, authentication, adb]

# Configuration options
config:
  detection_method: hybrid        # semantic → template → ocr fallback
  input_validation: true
  screenshot_on_error: true

# Input parameters (required by caller)
inputs:
  email:
    type: string
    required: true
    description: User email or account ID
    validation: "length >= 5"

  password:
    type: string
    required: true
    description: User password
    validation: "length >= 6"

  device:
    type: string
    required: false
    default: auto
    description: Target device (auto-detect if not specified)

# Workflow stages (logical grouping)
stages:
  verify_login_screen:
    description: Verify we're on login screen
    duration_seconds: 10
    critical: true

  enter_credentials:
    description: Enter email and password
    duration_seconds: 30
    critical: true

  submit_login:
    description: Submit login form
    duration_seconds: 20
    critical: true

  verify_success:
    description: Verify successful login
    duration_seconds: 30
    critical: true

# Individual steps (detailed actions)
steps:
  verify_login_screen:
    - name: check_login_button
      type: ui_find
      method: hybrid
      target_text: "로그인"
      timeout_seconds: 10
      on_failure: "screenshot_and_alert"

  enter_credentials:
    - name: find_email_input
      type: ui_find
      method: semantic
      target_text: "이메일"
      timeout_seconds: 10

    - name: tap_email_field
      type: ui_tap
      method: semantic
      target_class: android.widget.EditText
      index: 0

    - name: type_email
      type: ui_input
      text: "{email}"
      timeout_seconds: 5

# Output parameters (returned after execution)
outputs:
  login_successful: boolean
  home_screen_reached: boolean
  authentication_time_seconds: number
  error_message: string

# Success criteria (all must be true)
success_criteria:
  - login_button_exists: true
  - email_field_filled: true
  - password_field_filled: true
  - home_screen_accessible: true

# Error handling (what to do on failure)
on_failure:
  - action: take_screenshot
    output: /sdcard/login_error.png

  - action: check_error_message
    patterns:
      - "이메일 또는 비밀번호가 일치하지 않습니다"
      - "계정을 찾을 수 없습니다"

# Timing and retry
timing:
  total_timeout_seconds: 180
  inter_step_delay_seconds: 1

retry_policy:
  max_attempts: 3
  exponential_backoff: true
  backoff_multiplier: 1.5

# Logging
logging:
  level: info
  output_file: login_automation.log
  include_credentials: false
  include_timestamps: true
```

#### Key TOON Sections

| Section | Purpose | Required | Example |
|---------|---------|----------|---------|
| metadata | name, version, type | Yes | `name: login_automation` |
| config | Workflow configuration | No | `detection_method: hybrid` |
| inputs | Parameters from caller | Yes (usually) | `email: {type: string}` |
| stages | Logical workflow phases | Yes | `verify_login_screen:` |
| steps | Individual actions | Yes | `- name: check_login_button` |
| outputs | Return values | Yes | `login_successful: boolean` |
| success_criteria | Validation rules | Yes | `login_button_exists: true` |
| on_failure | Error handling | Yes | `- action: take_screenshot` |
| timing | Timeout configuration | No | `total_timeout_seconds: 180` |
| retry_policy | Retry strategy | No | `max_attempts: 3` |
| logging | Log configuration | No | `level: info` |

#### TOON Step Types

```yaml
steps:
  # Find UI element
  - type: ui_find
    method: semantic|template|ocr|hybrid
    target_text: string
    target_class: string
    timeout_seconds: number

  # Tap/click element
  - type: ui_tap
    method: semantic|template|ocr
    target_text: string
    coordinate: [x, y]
    timeout_seconds: number

  # Input text
  - type: ui_input
    text: string
    timeout_seconds: number

  # Wait for element
  - type: ui_wait
    target_text: string
    timeout_seconds: number

  # Screenshot
  - type: screenshot
    output: path
    optional: boolean

  # Delay
  - type: delay
    duration_seconds: number

  # Custom action
  - type: custom
    script: path_to_script.py
    params: {...}
```

---

### Part 2B: MD File Structure (Documentation)

A corresponding MD file documents the workflow in human-readable format.

#### MD Template

```markdown
---
name: Login Automation
workflow: login_automation.toon
version: 1.0.0
last_updated: 2025-12-02
---

# Login Automation Workflow

## Purpose

Automate login to the Karrot app with semantic UI detection and error recovery.
Handles both regular login and two-factor authentication (2FA) when enabled.

## Scope

**Includes**:
- Verify login screen availability
- Enter email credentials
- Enter password credentials
- Submit login form
- Verify successful authentication
- Optional 2FA handling

**Excludes**:
- Account creation
- Password reset
- OAuth/social login

## Prerequisites

Before running this workflow:
1. Device connected via ADB
2. Karrot app installed on device
3. Bypass workflow completed (if device has security restrictions)
4. Valid email/password credentials
5. Stable internet connection on device

## Parameters

### Required Inputs

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| email | string | user@example.com | User email or account ID |
| password | string | MySecurePass123 | User password |

### Optional Inputs

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | auto | Target device (auto-detect if not specified) |
| timeout | integer | 180 | Total timeout in seconds |
| two_factor_enabled | boolean | false | Whether 2FA is required |
| two_factor_code | string | - | 2FA code (if 2FA enabled) |

### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| login_successful | boolean | True if login completed |
| home_screen_reached | boolean | True if home screen accessible |
| authentication_time_seconds | number | Time taken for login |
| error_message | string | Error details if failed |
| final_screenshot_path | string | Path to final screenshot |

## Workflow Phases

### Phase 1: Verify Login Screen (10 seconds)

**Goal**: Confirm we're on the login screen.

Steps:
1. Check login button exists
2. Verify email field is visible
3. Verify password field is visible

**Success Criteria**:
- Login button found
- Email input field visible
- Password input field visible

### Phase 2: Enter Credentials (30 seconds)

**Goal**: Populate email and password fields.

Steps:
1. Find and tap email input field
2. Clear any existing text
3. Type email address
4. Find and tap password input field
5. Clear any existing text
6. Type password

**Success Criteria**:
- Email field populated
- Password field populated
- Text visible on screen

### Phase 3: Submit Login (20 seconds)

**Goal**: Submit the login form.

Steps:
1. Find login button
2. Tap login button
3. Wait for response

**Success Criteria**:
- Login button tapped
- Screen transitions to next state

### Phase 4: Verify Success (30 seconds)

**Goal**: Confirm successful login.

Steps:
1. Wait for home screen appearance
2. Verify user profile accessible
3. Capture success screenshot

**Success Criteria**:
- Home screen reached
- User profile visible
- No error messages

## Success Criteria

All criteria must be true for successful login:
- [ ] Login button exists on initial screen
- [ ] Email field populated correctly
- [ ] Password field populated correctly
- [ ] Login form submitted successfully
- [ ] Home screen accessible
- [ ] User profile visible

## Error Handling

### Common Errors

| Error Message | Cause | Resolution |
|---------------|-------|-----------|
| "이메일 또는 비밀번호가 일치하지 않습니다" | Invalid credentials | Verify email and password |
| "계정을 찾을 수 없습니다" | Account doesn't exist | Check email address |
| "로그인 횟수를 초과했습니다" | Too many failed attempts | Wait and retry later |
| "네트워크 오류" | Connection issue | Check device internet |

### Retry Strategy

- Maximum attempts: 3
- Exponential backoff: enabled
- Backoff multiplier: 1.5x
- Screenshots on error: enabled

## Execution Example

### Using the Workflow

#### Command Line

```bash
# Run workflow with required parameters
uv run .claude/skills/adb-karrot/workflow/login_automation.py \
  --email user@example.com \
  --password MyPassword123 \
  --device 192.168.1.100:5555

# With optional parameters
uv run .claude/skills/adb-karrot/workflow/login_automation.py \
  --email user@example.com \
  --password MyPassword123 \
  --device auto \
  --timeout 180 \
  --two-factor-enabled \
  --two-factor-code 123456
```

#### In Python Code

```python
from adb_karrot.workflows import LoginAutomation

workflow = LoginAutomation()
result = workflow.run(
    email="user@example.com",
    password="MyPassword123",
    device="auto",
    two_factor_enabled=False
)

if result.login_successful:
    print(f"Login successful in {result.authentication_time_seconds}s")
else:
    print(f"Login failed: {result.error_message}")
```

#### In TOON/Orchestration

```yaml
workflows:
  - name: karrot_login
    workflow_file: login_automation.toon
    inputs:
      email: user@example.com
      password: MyPassword123
      device: auto
    on_success: proceed_to_main_app
    on_failure: retry_with_new_credentials
```

## Timing and Duration

- Typical duration: 2-3 minutes
- Stage breakdown:
  - Verify login screen: 10 seconds
  - Enter credentials: 30 seconds
  - Submit login: 20 seconds
  - Verify success: 30 seconds
- Total timeout: 3 minutes (180 seconds)

## Dependencies

### Required Skills

- adb-screen-detection (for UI element finding)
- adb-navigation-base (for input handling)
- adb-tap-automation (for tapping elements)

### External Dependencies

- Python 3.10+
- pytesseract >= 0.3.10
- opencv-python >= 4.8.0
- pillow >= 10.0.0

## Troubleshooting

### "Login button not found"
- Device might not be on login screen
- Try running bypass workflow first
- Increase timeout: `--timeout 300`

### "Email field not populated"
- Keyboard might not be visible
- Try tapping field first
- Check device keyboard settings

### "Timeout waiting for home screen"
- Server might be slow
- Connection issue on device
- Too many failed login attempts

### "2FA code not accepted"
- Code might be expired (30 second limit)
- Verify code format is correct
- Check time sync on device

## See Also

- [adb-screen-detection](../adb-screen-detection/SKILL.md) - UI detection skill
- [adb-navigation-base](../adb-navigation-base/SKILL.md) - Navigation skill
- [Karrot App Integration](../SKILL.md) - Parent skill documentation

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-02 | Initial implementation |

## Status

- **Version**: 1.0.0
- **Status**: Active
- **Last Tested**: 2025-12-02
- **Maintenance**: Ongoing
```

---

## Part 3: Auto-Nesting Rule

### When to Nest Items

**Rule**: If 5 or more items with the same prefix exist in a directory, create a subfolder with that prefix and nest the items.

### Detection

Count workflow files by prefix:

```bash
# Count files with "adb-" prefix
ls workflow/ | grep "^adb-" | wc -l

# If count >= 5:
#   Create adb/ folder
#   Move adb-* files into adb/
#   Update all imports and references
```

### Example: Before Nesting

```
.claude/skills/adb-screen-detection/workflow/
├── README.md
├── capture.toon           # count = 1
├── capture.md
├── extract.toon           # count = 2
├── extract.md
├── find.toon              # count = 3
├── find.md
├── match.toon             # count = 4
└── match.md
```

Count: 4 workflows with "adb-" prefix → No nesting needed.

### Example: After Accumulation

```
.claude/skills/adb-screen-detection/workflow/
├── README.md              # Root index
├── capture.toon           # New workflow (count = 5)
├── capture.md
├── extract.toon
├── extract.md
├── find.toon
├── find.md
├── match.toon
├── match.md
└── ...
```

Count: 5+ workflows → **Time to nest!**

### After Nesting

```
.claude/skills/adb-screen-detection/workflow/
├── README.md              # Update with new structure
├── screens/               # NEW FOLDER (grouped by prefix)
│   ├── README.md          # Subfolder index
│   ├── capture.toon
│   ├── capture.md
│   ├── extract.toon
│   ├── extract.md
│   ├── find.toon
│   ├── find.md
│   ├── match.toon
│   └── match.md
```

### Nesting Process

1. **Create subfolder** with prefix name (without dash):
   - `adb-screen` → `screen/`
   - `login-` → `login/`
   - `error-recovery-` → `error-recovery/`

2. **Move related files** into subfolder:
   ```bash
   mkdir -p workflow/screens
   mv workflow/capture.* workflow/screens/
   mv workflow/extract.* workflow/screens/
   ```

3. **Update imports and references** in all files:
   ```markdown
   # Before:
   See [capture workflow](./capture.md)

   # After:
   See [capture workflow](./screens/capture.md)
   ```

4. **Create subfolder README.md** with index:
   ```markdown
   # Screen Detection Workflows

   - [capture.md](capture.md) - Capture screen
   - [extract.md](extract.md) - Extract text
   - [find.md](find.md) - Find element
   - [match.md](match.md) - Match template
   ```

5. **Update parent README.md**:
   ```markdown
   # Workflows

   ## Screen Detection

   See [screens/README.md](screens/README.md) for details.
   ```

---

## Part 4: Skill Creation Checklist

Use this checklist when builder-skill creates a new skill.

### Step 1: Create Directory Structure

```markdown
- [ ] Create `.claude/skills/[skill-name]/` directory
- [ ] Create `.claude/skills/[skill-name]/scripts/` subdirectory
- [ ] Create `.claude/skills/[skill-name]/workflow/` subdirectory
```

**Commands**:
```bash
mkdir -p .claude/skills/adb-myfeature/{scripts,workflow}
```

### Step 2: Create SKILL.md

```markdown
- [ ] Create `SKILL.md` in skill root directory
- [ ] Include frontmatter (name, description, version)
- [ ] Include "Scripts" section documenting each script
- [ ] Include "Workflows" section with links to workflow/README.md
- [ ] Include dependencies list
- [ ] Include auto_trigger_keywords
- [ ] Include "Works Well With" section
- [ ] Verify file ≤500 lines
```

**Template Section in SKILL.md**:
```yaml
---
name: adb-myfeature
description: Brief description (max 200 chars)
version: 1.0.0
modularized: true
scripts_enabled: true
workflows_enabled: true
tier: 2
category: adb-automation
last_updated: 2025-12-02
compliance_score: 100

dependencies:
  - package1>=1.0.0
  - package2>=2.0.0

auto_trigger_keywords:
  - keyword1
  - keyword2
---
```

### Step 3: Create workflow/README.md

```markdown
- [ ] Create `workflow/README.md` in workflow directory
- [ ] List all workflow files with descriptions
- [ ] Include quick reference table
- [ ] Link to full documentation for each workflow
- [ ] Include any nesting information (if applicable)
```

**Template**:
```markdown
# Workflows

This directory contains TOON+MD workflow pairs for [skill name].

## Available Workflows

| Workflow | TOON | MD | Purpose |
|----------|------|----|---------|
| capture | [capture.toon](./capture.toon) | [capture.md](./capture.md) | Brief description |
| extract | [extract.toon](./extract.toon) | [extract.md](./extract.md) | Brief description |

See individual .md files for detailed documentation.
```

### Step 4: Create Initial Scripts

```markdown
- [ ] Create 1-3 starter Python scripts in scripts/ directory
- [ ] Scripts named: `adb-[action].py` following pattern
- [ ] Include docstring describing script purpose
- [ ] Include argument parsing
- [ ] Include error handling
```

**Script Template**:
```python
#!/usr/bin/env python3
"""
Brief description of script.

Usage:
    uv run .claude/skills/[skill]/scripts/[name].py --arg1 value --arg2 value
"""

import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arg1", help="Description")
    parser.add_argument("--arg2", help="Description")
    args = parser.parse_args()

    # Implementation
    pass

if __name__ == "__main__":
    main()
```

### Step 5: Create Initial Workflows

```markdown
- [ ] Create first workflow pair: [name].toon + [name].md
- [ ] TOON file includes: name, version, config, inputs, stages, steps, outputs, success_criteria, on_failure
- [ ] MD file includes: Purpose, Prerequisites, Parameters, Phases, Success Criteria, Execution Example
- [ ] Test both files for syntax errors
- [ ] Verify TOON syntax is valid YAML
- [ ] Verify MD renders correctly
```

### Step 6: Documentation

```markdown
- [ ] All code comments in English
- [ ] SKILL.md properly formatted
- [ ] workflow/README.md properly formatted
- [ ] Individual .md files complete and accurate
- [ ] Links between files verified
- [ ] No broken references
```

### Step 7: Final Verification

```markdown
- [ ] SKILL.md exists and is valid
- [ ] scripts/ folder exists with 1+ script
- [ ] workflow/ folder exists with README.md
- [ ] First workflow pair created (at least one .toon + .md)
- [ ] All files follow naming conventions
- [ ] Directory structure matches pattern
- [ ] No merge conflicts
- [ ] Ready for git commit
```

**Verification Command**:
```bash
# Check directory structure
tree .claude/skills/[skill-name]/

# Expected output:
# .claude/skills/[skill-name]/
# ├── SKILL.md
# ├── scripts/
# │   └── adb-action.py
# └── workflow/
#     ├── README.md
#     ├── action1.toon
#     ├── action1.md
#     ├── action2.toon
#     └── action2.md
```

---

## Part 5: Workflow Creation Checklist

Use this checklist when builder-workflow-designer creates individual workflows.

### Step 1: Create TOON File

```markdown
- [ ] Create [name].toon in workflow/ folder
- [ ] Include all required TOON sections:
  - [ ] Metadata (name, version, type, description)
  - [ ] Config (if needed)
  - [ ] Inputs (parameters from caller)
  - [ ] Stages (logical workflow phases)
  - [ ] Steps (individual actions)
  - [ ] Outputs (return values)
  - [ ] Success criteria (validation rules)
  - [ ] On failure (error handling)
- [ ] Validate YAML syntax
- [ ] Test orchestration logic
```

**TOON Syntax Validation**:
```bash
# Quick validation (no special tools needed)
# YAML must be valid - use online YAML validators
# All required keys present
# All step types are valid
```

### Step 2: Create MD File

```markdown
- [ ] Create [name].md in workflow/ folder (same name as TOON)
- [ ] Include all required sections:
  - [ ] Frontmatter (name, workflow file reference, version)
  - [ ] Purpose (what workflow does)
  - [ ] Scope (what's included/excluded)
  - [ ] Prerequisites (setup required)
  - [ ] Parameters section (inputs and outputs)
  - [ ] Workflow Phases (step-by-step explanation)
  - [ ] Success Criteria (validation checklist)
  - [ ] Error Handling (common issues and fixes)
  - [ ] Execution Example (command line and code examples)
- [ ] Verify all links are correct
- [ ] Ensure code examples are copy-paste ready
```

**MD Template Check**:
```markdown
- Purpose: Clear and specific ✓
- Prerequisites: Complete list ✓
- Parameters: Input/output table ✓
- Phases: Numbered sections ✓
- Examples: Working code ✓
- Troubleshooting: Common issues ✓
```

### Step 3: Link Workflow to Skill

```markdown
- [ ] Update skill's SKILL.md "Workflows" section
- [ ] Add entry in workflow/README.md table
- [ ] Update any parent/root README.md files
- [ ] Verify all links point to correct files
```

**Example SKILL.md Update**:
```yaml
workflows:
  - name: action1
    toon: workflow/action1.toon
    documentation: workflow/action1.md
    purpose: Brief description
    status: active
```

### Step 4: Verify Pairing

```markdown
- [ ] Both [name].toon and [name].md exist
- [ ] Files have identical base names
- [ ] TOON file references match MD file
- [ ] MD file references TOON file
- [ ] No orphaned files (unpaired .toon or .md)
```

### Step 5: Test Documentation

```markdown
- [ ] Render .md file in viewer (Markdown preview)
- [ ] Verify all links are clickable
- [ ] Verify code examples work
- [ ] Verify syntax highlighting (YAML, Python, bash)
- [ ] Check for typos and grammar
```

### Step 6: Final Checklist

```markdown
- [ ] TOON file is valid YAML
- [ ] MD file is valid Markdown
- [ ] Both files named identically (except extension)
- [ ] TOON has all required sections
- [ ] MD has all required sections
- [ ] Inputs in TOON match Parameters in MD
- [ ] Outputs in TOON match Parameters section in MD
- [ ] Phases in TOON match Phases in MD
- [ ] Success criteria documented in both
- [ ] Error handling documented in both
- [ ] All links verified
- [ ] No broken references
- [ ] Ready for workflow/README.md addition
```

---

## Part 6: Common Patterns and Examples

### Pattern 1: Simple Single-Action Workflow

**Scenario**: Need a simple workflow that does one thing (e.g., "take screenshot")

**TOON**:
```yaml
name: simple_screenshot
version: 1.0.0
type: automation
description: Capture Android device screen

inputs:
  device:
    type: string
    required: false
    default: auto

stages:
  capture_screen:
    description: Capture device screen
    duration_seconds: 5

steps:
  capture_screen:
    - name: take_screenshot
      type: screenshot
      output: /sdcard/screenshot.png

outputs:
  screenshot_path: string
  success: boolean

success_criteria:
  - screenshot_file_exists: true

on_failure:
  - action: alert
    message: "Failed to capture screenshot"
```

**MD**:
```markdown
# Simple Screenshot Workflow

## Purpose
Capture device screen quickly and save to file.

## Execution
uv run .claude/skills/[name]/workflow/simple_screenshot.py
```

### Pattern 2: Multi-Step Decision Workflow

**Scenario**: Workflow with branching logic based on conditions

**TOON**:
```yaml
name: login_with_2fa
steps:
  verify_login_screen:
    - name: check_login_button
      type: ui_find

  enter_credentials:
    - name: enter_email
      type: ui_input

  check_2fa_needed:
    - name: look_for_2fa_prompt
      type: ui_find
      required: false
      condition_variable: needs_2fa

  handle_2fa:
    - name: enter_2fa_code
      type: ui_input
      condition: "needs_2fa == true"
```

### Pattern 3: Workflow Composition

**Scenario**: Workflow calls other workflows

**TOON**:
```yaml
name: full_app_automation
description: Run complete app automation flow

steps:
  setup_phase:
    - name: run_bypass_workflow
      type: workflow
      workflow_ref: bypass_automation.toon
      params:
        device: "{device}"

  login_phase:
    - name: run_login_workflow
      type: workflow
      workflow_ref: login_automation.toon
      params:
        email: "{email}"
        password: "{password}"
```

---

## Part 7: Troubleshooting Guide

### TOON Syntax Errors

**Error**: "Invalid YAML"
- Check indentation (2 spaces, not tabs)
- Verify all colons have values or proper nesting
- Use online YAML validator

**Error**: "Unknown step type"
- Verify step type is valid (ui_find, ui_tap, ui_input, etc.)
- Check spelling

**Error**: "Parameter not found"
- Check parameter name matches exactly in inputs section
- Verify parameter is in curly braces: `{parameter_name}`

### MD Documentation Issues

**Problem**: Links not working
- Verify file paths are relative to current location
- Use ./ for same directory: `./capture.md`
- Use ../ for parent directory: `../SKILL.md`

**Problem**: Code examples not rendering
- Wrap in triple backticks: ` ``` `
- Specify language: ` ```yaml `

**Problem**: Tables not rendering
- Verify pipe alignment
- Include header separator row with dashes

### Pairing Issues

**Error**: "TOON file without MD"
- Create matching .md file immediately
- Both files must exist for workflow to be complete

**Error**: "MD file without TOON"
- Either create matching .toon file, or
- Delete orphaned .md file and start over

---

## Part 8: References and Resources

### Files and Locations

- TOON specification: `/.moai/docs/TOON-MD-PATTERN-REFERENCE.md`
- Skill templates: `.claude/skills/[skill-name]/SKILL.md`
- Workflow examples: `.claude/skills/adb/*/workflow/`
- Builder skill guide: `.claude/skills/builder-skill/WORKFLOW-STRUCTURE-GUIDE.md`

### Related Skills

- `builder-skill`: Creates new skills with proper structure
- `builder-workflow-designer`: Creates TOON+MD workflow pairs
- `builder-agent`: Creates agents (different purpose, similar structure)

### Commands

```bash
# Validate YAML in TOON file
python3 -c "import yaml; yaml.safe_load(open('workflow/name.toon'))"

# List all workflow files
find .claude/skills -name "*.toon" -o -name "*.md" | grep workflow/

# Count workflows by prefix
ls -1 workflow/*.toon | sed 's/.*-//' | cut -d'_' -f1 | sort | uniq -c
```

---

## Summary

### When Creating a New Skill:

1. Create both `scripts/` and `workflow/` folders
2. Create SKILL.md with metadata
3. Create workflow/README.md as index
4. Create first workflow pair: `action.toon` + `action.md`
5. Add workflow to SKILL.md "Workflows" section

### When Creating a New Workflow:

1. Create [name].toon with full orchestration
2. Create [name].md with complete documentation
3. Both files must have identical names
4. Add to workflow/README.md table
5. Verify all references and links

### Auto-Nesting:

- 5+ items with same prefix → create subfolder
- Move items into subfolder
- Update all imports and references
- Create subfolder README.md

### Quality Checklist:

- [ ] Both files exist for each workflow
- [ ] TOON syntax is valid YAML
- [ ] MD syntax is valid Markdown
- [ ] All parameters documented
- [ ] All examples working
- [ ] All links verified
- [ ] Code in English
- [ ] Ready for use

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-02 | Initial version - Phase 3B release |

**Status**: Active and Complete
**Last Updated**: 2025-12-02
**Audience**: Builder agents (builder-skill, builder-workflow-designer, builder-agent)
