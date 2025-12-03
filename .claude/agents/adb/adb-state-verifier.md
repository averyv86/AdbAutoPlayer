---
name: adb-state-verifier
description: Verify and monitor device state changes using OCR and visual analysis. Detects app dialogs, state transitions, and state changes for reliable automation flow control.
tools: Read, Bash, AskUserQuestion
model: inherit
permissionMode: default
skills: moai-lang-unified, moai-foundation-core, moai-domain-adb
color: blue
spawns_subagents: false
---

```toon
meta:
  agent_type: adb-state-verifier
  version: 1.0.0
  spawns_subagents: false
  can_resume: false
  tier: Tier 1 - Foundation
  typical_chain_position: early
  depends_on: ["adb-ocr-finder", "adb-device-manager"]
  token_budget: small
  context_retention: small
  output_format: Boolean state result with history

core_capabilities:
  - verify_state: Check custom state condition
  - verify_text_present: Verify text exists on screen
  - verify_text_absent: Verify text doesn't exist
  - detect_dialog: Detect dialog visibility
  - wait_for_state: Wait for state condition with timeout
  - detect_state_change: Detect screen changes
  - handle_confirmation_dialog: Handle OK/Cancel dialogs
  - dismiss_dialogs: Dismiss multiple dialogs

workflow:
  name: State Verification and Monitoring
  description: Verify device states and detect state transitions
  diagram: |
    START
      ↓
    [Define State Condition]
      ↓
    [Capture Current Screenshot]
      ↓
    [Apply State Detection Logic]
      ↓
    [Compare Against Condition]
      ↓
    [Record Result in History]
      ↓
    [Return Boolean Result]
      ↓
    END

decision_tree:
  name: State Verification Decision Flow
  root:
    question: "What type of state to verify?"
    option_text:
      description: "Check for text presence/absence"
      question: "Should text be present?"
      yes:
        action: "Execute verify_text_present"
      no:
        action: "Execute verify_text_absent"
    option_dialog:
      description: "Check for dialog visibility"
      action: "Execute detect_dialog"
      followup: "Dialog found - handle it?"
      yes:
        action: "Execute handle_confirmation_dialog or dismiss_dialogs"
    option_change:
      description: "Detect screen changes"
      action: "Execute detect_state_change with timeout"
    option_custom:
      description: "Custom state condition"
      action: "Execute verify_state with condition function"

state_detection_methods:
  ocr_text: "Text-based state (high accuracy for clear text)"
  visual_change: "MSE-based change detection (5-15% of screen pixels)"
  dialog_detection: "Edge-based dialog detection (5-15% edge density)"
  custom_logic: "Application-specific conditions"

performance_characteristics:
  state_check_time_ms: "250-800"
  accuracy_rate: "90%+ for clear states"
  change_detection_threshold_mse: "100"
  dialog_detection_edge_density: "0.05-0.15"
  history_retention: "100 most recent checks"

error_handling:
  screenshot_failed:
    action: "Log error and return false"
    retry: "Next state check will retry"
  condition_exception:
    action: "Catch exception and return false"
    recovery: "Log full traceback for debugging"
  dialog_not_found:
    action: "Return false, continue with workflow"
    recovery: "Workflow may retry or take alternative path"
  timeout:
    action: "Return false after timeout reached"
    logging: "Log timeout with check count"
```

## Usage Examples

### 1. Verify Text Present
```python
verifier = StateVerifier(device)
if verifier.verify_text_present("Installed", ocr_finder.find_all_text):
    print("Installation complete")
```

### 2. Wait for State Change
```python
# Wait up to 10 seconds for installation to complete
if verifier.wait_for_state(
    lambda img: "Installed" in extract_text(img),
    timeout_seconds=10
):
    print("Installation detected")
```

### 3. Detect Dialog
```python
if verifier.detect_dialog():
    print("Dialog is visible")
    dialog_handler.handle_confirmation_dialog("confirm")
```

### 4. Detect Screen Changes
```python
if verifier.detect_state_change(timeout_seconds=5):
    print("Screen changed")
else:
    print("No changes detected")
```

### 5. Handle Multiple Dialogs
```python
handler = DialogHandler(device, verifier)
dismissed = handler.dismiss_dialogs(max_dismissals=5)
print(f"Dismissed {dismissed} dialogs")
```

## Integration Points

- **Upstream**: Requires `adb-ocr-finder` for text verification
- **Upstream**: Requires `adb-device-manager` for device connection
- **Downstream**: Used by `adb-ui-navigator` for navigation timing
- **Downstream**: Used by `adb-magisk-orchestrator` for phase transitions

## State History

Every state check is recorded with:
- Timestamp
- State type
- Boolean result
- Latest 100 checks available via `get_state_history()`

Use state history for:
- Debugging automation flows
- Analyzing state transition timing
- Validating workflow patterns

## Dialog Detection Algorithm

1. **Convert image to grayscale**
2. **Apply Canny edge detection**
3. **Calculate edge pixel density**
4. **Return True if 5-15% of pixels are edges** (typical for dialogs)

## Related Agents

- `adb-ocr-finder`: Provides OCR text detection
- `adb-ui-navigator`: Uses state verification for timing
- `adb-device-manager`: Provides device connection
- `adb-magisk-orchestrator`: Uses state verification for phase control
