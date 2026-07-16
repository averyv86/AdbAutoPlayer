# Master Workflow Index - ADB Ecosystem

**Status**: Active
**Version**: 1.0.0
**Date**: 2025-12-02
**Total Workflows**: 14 core workflows + dynamic patterns
**Format**: TOON v4.0 (BMAD-style YAML) with Markdown documentation

---

## Quick Navigation

**By Skill**: [ADB-Bypass](#adb-bypass) | [ADB-Karrot](#adb-karrot) | [ADB-Magisk](#adb-magisk) | [ADB-Navigation](#adb-navigation-base) | [ADB-Screen-Detection](#adb-screen-detection) | [ADB-Skill-Generator](#adb-skill-generator) | [ADB-UIAutomator](#adb-uiautomator) | [ADB-Workflow-Orchestrator](#adb-workflow-orchestrator)

**By Category**: [Authentication](#authentication-workflows) | [Detection](#detection-workflows) | [Validation](#validation-workflows) | [Navigation](#navigation-workflows) | [Generation](#generation-workflows) | [Orchestration](#orchestration-workflows)

**By Difficulty**: [Beginner](#beginner-level) | [Intermediate](#intermediate-level) | [Advanced](#advanced-level)

---

## Index Structure

Each workflow entry includes:
- **Skill**: Parent skill that contains the workflow
- **File Path**: TOON definition and Markdown documentation locations
- **Purpose**: Brief description of workflow function
- **Category**: Functional category (authentication, detection, etc.)
- **Difficulty**: Beginner/Intermediate/Advanced
- **Time**: Estimated execution time
- **Dependencies**: Required modules or other workflows
- **Inputs**: Required parameters
- **Outputs**: Expected results

---

## All Workflows by Skill

### ADB-Bypass

**Skill Directory**: `.claude/skills/adb-bypass/workflow/`

#### 1. Bypass Validation

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-bypass/bypass-validation` |
| **File Paths** | `bypass-validation.toon` / `bypass-validation.md` |
| **Purpose** | Validates SafetyNet bypass functionality on connected devices |
| **Category** | Validation |
| **Difficulty** | Intermediate |
| **Est. Time** | 3-5 minutes |
| **Dependencies** | adb-bypass skill, device connection |
| **Inputs** | `device_id`, `check_type` (full/basic/quick), `timeout` |
| **Outputs** | `validation_result` (json), `bypass_status` (bool), `safetynet_passed` (bool) |
| **Error Handling** | Auto-retry on connection loss (3 attempts) |

**Quick Start**:
```bash
alfred-task execute "adb-bypass/bypass-validation" --device-id "device1"
```

**Use Cases**:
- Verify bypass functionality after Magisk installation
- Diagnostic check for SafetyNet issues
- Pre-automation validation
- Quality assurance testing

---

### ADB-Karrot

**Skill Directory**: `.claude/skills/adb-karrot/workflow/`

#### 1. Detection Check

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-karrot/detection-check` |
| **File Paths** | `detection-check.toon` / `detection-check.md` |
| **Purpose** | Checks if Karrot game is installed and running state on device |
| **Category** | Detection |
| **Difficulty** | Beginner |
| **Est. Time** | 1-2 minutes |
| **Dependencies** | adb-karrot skill |
| **Inputs** | `device_id`, `check_running` (bool) |
| **Outputs** | `is_installed` (bool), `is_running` (bool), `app_version` (string) |
| **Error Handling** | Graceful handling for app not installed |

**Quick Start**:
```bash
alfred-task execute "adb-karrot/detection-check" --device-id "device1"
```

**Use Cases**:
- Check if Karrot is installed before automation
- Verify app running state
- Detect app version compatibility

#### 2. Login Automation

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-karrot/login-automation` |
| **File Paths** | `login-automation.toon` / `login-automation.md` |
| **Purpose** | Automates Karrot app login process |
| **Category** | Authentication |
| **Difficulty** | Intermediate |
| **Est. Time** | 2-4 minutes |
| **Dependencies** | adb-karrot skill, adb-navigation-base, adb-screen-detection |
| **Inputs** | `device_id`, `username`, `password`, `server_address` |
| **Outputs** | `login_success` (bool), `session_token` (string), `user_id` (string) |
| **Error Handling** | Retry on network errors (3 attempts), credential validation |

**Quick Start**:
```bash
alfred-task execute "adb-karrot/login-automation" \
  --device-id "device1" \
  --username "user@example.com" \
  --password "secret"
```

**Use Cases**:
- Automate user login to Karrot
- Integrate with larger automation workflows
- Support multi-account testing

#### 3. Validation Flow

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-karrot/validation-flow` |
| **File Paths** | `validation-flow.toon` / `validation-flow.md` |
| **Purpose** | Complete validation flow for Karrot app state |
| **Category** | Validation |
| **Difficulty** | Advanced |
| **Est. Time** | 5-8 minutes |
| **Dependencies** | detection-check, login-automation, all other karrot workflows |
| **Inputs** | `device_id`, `deep_check` (bool) |
| **Outputs** | `full_validation_result` (json), `issues` (array), `recommendations` (array) |
| **Error Handling** | Comprehensive error logging and suggestions |

**Quick Start**:
```bash
alfred-task execute "adb-karrot/validation-flow" --device-id "device1" --deep-check
```

**Use Cases**:
- Complete health check of Karrot setup
- Diagnostic for automation failures
- Pre-automation validation

---

### ADB-Magisk

**Skill Directory**: `.claude/skills/adb-magisk/workflow/`

#### 1. Magisk Verification

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-magisk/magisk-verification` |
| **File Paths** | `magisk-verification.toon` / `magisk-verification.md` |
| **Purpose** | Verifies Magisk installation and functionality |
| **Category** | Validation |
| **Difficulty** | Beginner |
| **Est. Time** | 2-3 minutes |
| **Dependencies** | adb-magisk skill |
| **Inputs** | `device_id`, `check_modules` (bool) |
| **Outputs** | `magisk_installed` (bool), `magisk_version` (string), `active_modules` (array) |
| **Error Handling** | Graceful handling for missing Magisk |

**Quick Start**:
```bash
alfred-task execute "adb-magisk/magisk-verification" --device-id "device1"
```

**Use Cases**:
- Verify Magisk is correctly installed
- Check active modules status
- Diagnostic for root access issues

#### 2. Module Management

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-magisk/module-management` |
| **File Paths** | `module-management.toon` / `module-management.md` |
| **Purpose** | Manages Magisk modules (install/uninstall/enable/disable) |
| **Category** | System Management |
| **Difficulty** | Advanced |
| **Est. Time** | 3-6 minutes per operation |
| **Dependencies** | adb-magisk skill, magisk-verification |
| **Inputs** | `device_id`, `operation` (install/uninstall/enable/disable), `module_name`, `module_path` |
| **Outputs** | `operation_success` (bool), `new_modules` (array), `conflicts` (array) |
| **Error Handling** | Conflict detection, rollback on failure |

**Quick Start**:
```bash
alfred-task execute "adb-magisk/module-management" \
  --device-id "device1" \
  --operation "install" \
  --module-name "my-module" \
  --module-path "/path/to/module"
```

**Use Cases**:
- Install/uninstall Magisk modules
- Enable/disable modules without uninstalling
- Manage module dependencies

---

### ADB-Navigation-Base

**Skill Directory**: `.claude/skills/adb-navigation-base/workflow/`

#### 1. App Navigation

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-navigation-base/app-navigation` |
| **File Paths** | `app-navigation.toon` / `app-navigation.md` |
| **Purpose** | Navigates through app UI elements using various strategies |
| **Category** | Navigation |
| **Difficulty** | Intermediate |
| **Est. Time** | 1-5 minutes (variable) |
| **Dependencies** | adb-navigation-base skill, adb-uiautomator, adb-screen-detection |
| **Inputs** | `device_id`, `target_screen`, `navigation_path`, `strategy` (uiautomator/ocr/template) |
| **Outputs** | `navigation_success` (bool), `current_screen` (string), `navigation_log` (array) |
| **Error Handling** | Fallback strategies, state recovery |

**Quick Start**:
```bash
alfred-task execute "adb-navigation-base/app-navigation" \
  --device-id "device1" \
  --target-screen "login_screen" \
  --strategy "uiautomator"
```

**Use Cases**:
- Navigate to specific app screens
- Support complex multi-step workflows
- Handle dynamic UI changes

---

### ADB-Screen-Detection

**Skill Directory**: `.claude/skills/adb-screen-detection/workflow/`

#### 1. OCR Detection

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-screen-detection/ocr-detection` |
| **File Paths** | `ocr-detection.toon` / `ocr-detection.md` |
| **Purpose** | Detects text on screen using OCR (Tesseract) |
| **Category** | Detection |
| **Difficulty** | Intermediate |
| **Est. Time** | 2-4 minutes |
| **Dependencies** | adb-screen-detection skill |
| **Inputs** | `device_id`, `region` (optional), `languages` (array) |
| **Outputs** | `detected_text` (string), `text_regions` (array), `confidence` (float) |
| **Error Handling** | Fallback to different languages, quality validation |

**Quick Start**:
```bash
alfred-task execute "adb-screen-detection/ocr-detection" \
  --device-id "device1" \
  --languages "ko,en"
```

**Use Cases**:
- Extract text from game screens
- Detect status messages
- Dynamic content detection

#### 2. Template Matching

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-screen-detection/template-matching` |
| **File Paths** | `template-matching.toon` / `template-matching.md` |
| **Purpose** | Matches visual templates against screen captures |
| **Category** | Detection |
| **Difficulty** | Intermediate |
| **Est. Time** | 1-3 minutes |
| **Dependencies** | adb-screen-detection skill |
| **Inputs** | `device_id`, `template_path`, `threshold` (float 0-1), `region` (optional) |
| **Outputs** | `match_found` (bool), `match_location` (x,y), `confidence` (float) |
| **Error Handling** | Threshold adjustment, region optimization |

**Quick Start**:
```bash
alfred-task execute "adb-screen-detection/template-matching" \
  --device-id "device1" \
  --template-path "templates/login-button.png" \
  --threshold 0.85
```

**Use Cases**:
- Find UI buttons and elements
- Detect specific game states
- Validate expected screen layouts

---

### ADB-Skill-Generator

**Skill Directory**: `.claude/skills/adb-skill-generator/workflow/`

#### 1. Skill Creation

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-skill-generator/skill-creation` |
| **File Paths** | `skill-creation.toon` / `skill-creation.md` |
| **Purpose** | Generates new ADB skills from templates |
| **Category** | Generation |
| **Difficulty** | Advanced |
| **Est. Time** | 5-10 minutes |
| **Dependencies** | builder-skill agent, builder-skill-uvscript |
| **Inputs** | `skill_name`, `base_modules` (array), `workflows` (array), `description` |
| **Outputs** | `skill_path` (string), `generated_files` (array), `next_steps` (array) |
| **Error Handling** | Validation of skill name, conflict detection |

**Quick Start**:
```bash
alfred-task execute "adb-skill-generator/skill-creation" \
  --skill-name "adb-new-feature" \
  --base-modules "device,bypass" \
  --description "New feature skill"
```

**Use Cases**:
- Generate new skills for new game support
- Create specialized automation skills
- Extend ADB ecosystem functionality

---

### ADB-UIAutomator

**Skill Directory**: `.claude/skills/adb-uiautomator/workflow/`

#### 1. Element Detection

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-uiautomator/element-detection` |
| **File Paths** | `element-detection.toon` / `element-detection.md` |
| **Purpose** | Detects UI elements using UIAutomator framework |
| **Category** | Detection |
| **Difficulty** | Beginner |
| **Est. Time** | 1-2 minutes |
| **Dependencies** | adb-uiautomator skill |
| **Inputs** | `device_id`, `selector` (id/text/xpath), `timeout` |
| **Outputs** | `element_found` (bool), `element_properties` (json), `clickable_areas` (array) |
| **Error Handling** | Fallback to alternative selectors |

**Quick Start**:
```bash
alfred-task execute "adb-uiautomator/element-detection" \
  --device-id "device1" \
  --selector-type "id" \
  --selector-value "login_button"
```

**Use Cases**:
- Find interactive elements
- Get element properties
- Support click/input operations

#### 2. UI Interaction

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-uiautomator/ui-interaction` |
| **File Paths** | `ui-interaction.toon` / `ui-interaction.md` |
| **Purpose** | Performs UI interactions (click, input, swipe) |
| **Category** | Interaction |
| **Difficulty** | Beginner |
| **Est. Time** | 0.5-2 minutes |
| **Dependencies** | adb-uiautomator skill, element-detection |
| **Inputs** | `device_id`, `action` (click/input/swipe), `target`, `parameters` |
| **Outputs** | `interaction_success` (bool), `new_state` (string) |
| **Error Handling** | Element not found, interaction timeout |

**Quick Start**:
```bash
alfred-task execute "adb-uiautomator/ui-interaction" \
  --device-id "device1" \
  --action "click" \
  --target "login_button"
```

**Use Cases**:
- Click buttons and interactive elements
- Enter text into fields
- Swipe gestures

---

### ADB-Workflow-Orchestrator

**Skill Directory**: `.claude/skills/adb-workflow-orchestrator/workflow/`

#### 1. BlueStacks Demo

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-workflow-orchestrator/bluestacks-demo` |
| **File Paths** | `bluestacks-demo.toon` / `bluestacks-demo.md` |
| **Purpose** | Demonstrates workflow execution on BlueStacks emulator |
| **Category** | Orchestration |
| **Difficulty** | Intermediate |
| **Est. Time** | 5-10 minutes |
| **Dependencies** | adb-workflow-orchestrator, all other ADB skills |
| **Inputs** | `bluestacks_instance`, `demo_scenario` |
| **Outputs** | `demo_complete` (bool), `results` (json), `performance_metrics` (json) |
| **Error Handling** | Comprehensive error recovery, state management |

**Quick Start**:
```bash
alfred-task execute "adb-workflow-orchestrator/bluestacks-demo" \
  --bluestacks-instance "BlueStacks5" \
  --demo-scenario "login-and-navigate"
```

**Use Cases**:
- Demonstrate ADB ecosystem capabilities
- Test complex multi-workflow scenarios
- Performance baseline measurement

#### 2. Workflow Execution

| Property | Value |
|----------|-------|
| **Workflow ID** | `adb-ecosystem/adb-workflow-orchestrator/workflow-execution` |
| **File Paths** | `workflow-execution.toon` / `workflow-execution.md` |
| **Purpose** | Orchestrates execution of multiple workflows in sequence or parallel |
| **Category** | Orchestration |
| **Difficulty** | Advanced |
| **Est. Time** | Variable (depends on chained workflows) |
| **Dependencies** | adb-workflow-orchestrator |
| **Inputs** | `workflows` (array), `execution_mode` (sequential/parallel), `error_handling` |
| **Outputs** | `all_success` (bool), `workflow_results` (array), `total_time` (float) |
| **Error Handling** | Per-workflow error handling, rollback capability |

**Quick Start**:
```bash
alfred-task execute "adb-workflow-orchestrator/workflow-execution" \
  --workflows "adb-karrot/detection-check,adb-karrot/login-automation" \
  --execution-mode "sequential"
```

**Use Cases**:
- Chain multiple workflows
- Complex multi-step automations
- Parallel execution of independent tasks

---

## Categorized Index

### Authentication Workflows

| Workflow | Skill | Difficulty | Time |
|----------|-------|-----------|------|
| Login Automation | adb-karrot | Intermediate | 2-4 min |

### Detection Workflows

| Workflow | Skill | Difficulty | Time |
|----------|-------|-----------|------|
| Detection Check | adb-karrot | Beginner | 1-2 min |
| OCR Detection | adb-screen-detection | Intermediate | 2-4 min |
| Template Matching | adb-screen-detection | Intermediate | 1-3 min |
| Element Detection | adb-uiautomator | Beginner | 1-2 min |
| Magisk Verification | adb-magisk | Beginner | 2-3 min |

### Validation Workflows

| Workflow | Skill | Difficulty | Time |
|----------|-------|-----------|------|
| Bypass Validation | adb-bypass | Intermediate | 3-5 min |
| Validation Flow | adb-karrot | Advanced | 5-8 min |

### Navigation Workflows

| Workflow | Skill | Difficulty | Time |
|----------|-------|-----------|------|
| App Navigation | adb-navigation-base | Intermediate | 1-5 min |

### Generation Workflows

| Workflow | Skill | Difficulty | Time |
|----------|-------|-----------|------|
| Skill Creation | adb-skill-generator | Advanced | 5-10 min |

### Orchestration Workflows

| Workflow | Skill | Difficulty | Time |
|----------|-------|-----------|------|
| BlueStacks Demo | adb-workflow-orchestrator | Intermediate | 5-10 min |
| Workflow Execution | adb-workflow-orchestrator | Advanced | Variable |

### System Management Workflows

| Workflow | Skill | Difficulty | Time |
|----------|-------|-----------|------|
| Module Management | adb-magisk | Advanced | 3-6 min |

### Interaction Workflows

| Workflow | Skill | Difficulty | Time |
|----------|-------|-----------|------|
| UI Interaction | adb-uiautomator | Beginner | 0.5-2 min |

---

## Difficulty Level Summary

### Beginner Level
- Detection Check (adb-karrot)
- Element Detection (adb-uiautomator)
- UI Interaction (adb-uiautomator)
- Magisk Verification (adb-magisk)

*Estimated Learning Time: 5-10 minutes each*

### Intermediate Level
- Bypass Validation (adb-bypass)
- Login Automation (adb-karrot)
- OCR Detection (adb-screen-detection)
- Template Matching (adb-screen-detection)
- App Navigation (adb-navigation-base)
- BlueStacks Demo (adb-workflow-orchestrator)

*Estimated Learning Time: 15-30 minutes each*

### Advanced Level
- Validation Flow (adb-karrot)
- Module Management (adb-magisk)
- Skill Creation (adb-skill-generator)
- Workflow Execution (adb-workflow-orchestrator)

*Estimated Learning Time: 1-2 hours each*

---

## Common Workflow Chains

### Basic Automation Chain
```
Detection Check → Login Automation → App Navigation → UI Interaction
Time: ~8-15 minutes
Difficulty: Intermediate
```

### Complete Validation Chain
```
Bypass Validation → Magisk Verification → Validation Flow
Time: ~10-16 minutes
Difficulty: Advanced
```

### Complex Multi-Feature Automation
```
Detection Check
  → Login Automation
    → App Navigation
      → Template Matching
        → UI Interaction
Time: ~12-18 minutes
Difficulty: Advanced
```

---

## Workflow Execution Cheat Sheet

### Quick Command Reference

```bash
# Execute single workflow
alfred-task execute "{skill}/{workflow-name}" --device-id "device1"

# Chain workflows
alfred-task execute-chain --workflows "skill1/workflow1,skill2/workflow2"

# Execute with custom timeout
alfred-task execute "{skill}/{workflow-name}" --device-id "device1" --timeout 600

# Dry-run before execution
alfred-task execute "{skill}/{workflow-name}" --device-id "device1" --dry-run

# Execute with detailed logging
alfred-task execute "{skill}/{workflow-name}" --device-id "device1" --verbose
```

---

## Finding the Right Workflow

### By Use Case

**"I need to log in to the app"**
→ `adb-karrot/login-automation`

**"I need to verify the app is installed"**
→ `adb-karrot/detection-check`

**"I need to find a button on screen"**
→ `adb-uiautomator/element-detection`

**"I need to click on a button"**
→ `adb-uiautomator/ui-interaction`

**"I need to check Magisk is working"**
→ `adb-magisk/magisk-verification`

**"I need to run a complete health check"**
→ `adb-karrot/validation-flow`

**"I need to create a new automation skill"**
→ `adb-skill-generator/skill-creation`

---

## Version Information

| Version | Release Date | Changes |
|---------|--------------|---------|
| 1.0.0 | 2025-12-02 | Initial release with 14 core workflows |

---

## Support & Documentation

For detailed information on any workflow:
1. Read the quick reference above
2. Review the Markdown documentation file (e.g., `login-automation.md`)
3. Check the TOON definition (e.g., `login-automation.toon`)
4. Review SKILL.md in parent skill directory
5. Contact ADB ecosystem maintainers

---

*Master Index Version: 1.0.0*
*Last Updated: 2025-12-02*
*Total Workflows Indexed: 14*
*Status: Complete and Active*
