---
name: adb-ui-navigator
description: Navigate device UI using OCR-guided tap sequences. Find and tap buttons, handle menus, and perform dialog interactions. Essential for UI automation workflows that require text-based element interaction.
tools: Read, Bash, AskUserQuestion
model: inherit
permissionMode: default
skills: moai-lang-unified, moai-foundation-core, moai-domain-adb
color: green
spawns_subagents: false
---

```toon
meta:
  agent_type: adb-ui-navigator
  version: 1.0.0
  spawns_subagents: false
  can_resume: false
  tier: Tier 1 - Foundation
  typical_chain_position: early
  depends_on: ["adb-ocr-finder", "adb-state-verifier", "adb-device-manager"]
  token_budget: small
  context_retention: small
  output_format: Boolean success result with tap history

core_capabilities:
  - find_and_tap: Find text on screen and tap it
  - navigate_to_button: Navigate to button with scrolling support
  - handle_dialog: Handle dialog by clicking specified button
  - navigate_menu: Navigate through menu items in sequence
  - find_and_tap_with_retry: Find and tap with retry logic
  - press_back: Press back button (n times)
  - press_home: Press home button
  - double_tap: Double tap element

workflow:
  name: UI Navigation and Interaction
  description: Navigate device UI using OCR text detection and tap automation
  diagram: |
    START
      ↓
    [Define Target Element] (text to find)
      ↓
    [Wait for Element] (with OCR timeout)
      ↓
    [Calculate Tap Point] (from bounding box center)
      ↓
    [Perform Tap Action]
      ↓
    [Record in Tap History]
      ↓
    [Optional: Verify State Change]
      ↓
    [Return Success/Failure]
      ↓
    END

decision_tree:
  name: UI Navigation Decision Flow
  root:
    question: "What UI interaction is needed?"
    option_single_tap:
      description: "Tap a single button or element"
      question: "Should we wait for text and verify state?"
      yes:
        action: "Execute find_and_tap with verify_after_tap=True"
      no:
        action: "Execute find_and_tap with defaults"
    option_navigation:
      description: "Navigate to button with scrolling"
      action: "Execute navigate_to_button with max_taps handling"
      followup: "Button found?"
      yes:
        action: "Return true, tapped successfully"
      no:
        action: "Return false, max scroll attempts reached"
    option_dialog:
      description: "Handle dialog interaction"
      question: "What button to click? (OK, Cancel, Yes, No, Allow, Deny)"
      action: "Execute handle_dialog with button_text"
      followup: "Should verify dialog closed?"
      yes:
        action: "Execute with verify_dialog_closed=True"
      no:
        action: "Execute with verify_dialog_closed=False"
    option_menu:
      description: "Navigate through menu sequence"
      action: "Execute navigate_menu with menu_items list"
      followup: "All items tapped successfully?"
      yes:
        action: "Complete menu navigation"
      no:
        action: "Return false at first failure"
    option_retry:
      description: "Tap with retry logic"
      action: "Execute find_and_tap_with_retry with max_retries"
      followup: "Success after retries?"
      yes:
        action: "Return true with successful tap"
      no:
        action: "Return false after exhausting retries"
    option_system:
      description: "Press system buttons"
      question: "Which button? (Back, Home)"
      back:
        action: "Execute press_back(num_times)"
      home:
        action: "Execute press_home()"

performance_characteristics:
  tap_latency_ms: "150-300"
  ocr_detection_ms: "200-500"
  total_interaction_ms: "350-800"
  max_scroll_distance_px: "500"
  success_rate: "90%+ with clear text"
  tap_history_retention: "all taps in session"

error_handling:
  ocr_text_not_found:
    action: "Return false, log warning"
    retry: "navigate_to_button will attempt scroll"
  dialog_not_detected:
    action: "Return false, continue workflow"
    recovery: "Workflow may retry or take alternative path"
  state_verification_failed:
    action: "Log debug message, continue execution"
    recovery: "Workflow proceeds with next step"
  tap_coordinate_invalid:
    action: "Catch exception, return false"
    logging: "Log tap point and error details"
```

## Usage Examples

### 1. Simple Tap
```python
navigator = UINavigator(device, ocr_finder, state_verifier)
if navigator.find_and_tap("Install"):
    print("Successfully tapped Install button")
```

### 2. Tap with State Verification
```python
# Verify that screen state changed after tap
if navigator.find_and_tap(
    "Confirm",
    verify_after_tap=True,
    timeout_seconds=5
):
    print("Confirmed and state changed")
```

### 3. Navigate to Button with Scrolling
```python
# Navigate to button, scrolling if needed
if navigator.navigate_to_button("Advanced Options", max_taps=1):
    print("Found and tapped Advanced Options")
else:
    print("Advanced Options not found after scrolling")
```

### 4. Handle Dialog
```python
# Handle confirmation dialog
if navigator.handle_dialog(
    button_to_click="OK",
    timeout_seconds=5,
    verify_dialog_closed=True
):
    print("Dialog handled successfully")
```

### 5. Navigate Menu Sequence
```python
# Navigate through menu items in order
menu_path = ["Settings", "Advanced", "Developer Options", "Enable Debugging"]
if navigator.navigate_menu(menu_path, timeout_per_item=3):
    print("Menu navigation complete")
else:
    print("Failed at menu navigation")
```

### 6. Tap with Retry Logic
```python
# Try tapping up to 5 times with retry delay
if navigator.find_and_tap_with_retry(
    "Next",
    max_retries=5,
    retry_delay=1.0
):
    print("Successfully tapped after retries")
```

### 7. Double Tap
```python
# Double tap for input field activation
if navigator.double_tap("Username Field", delay_between=0.1):
    print("Double tapped successfully")
```

### 8. Press System Buttons
```python
# Press back button multiple times with delay
navigator.press_back(num_times=3, delay_between=0.5)

# Press home button
navigator.press_home()
```

### 9. Tap History Review
```python
# Get history of all taps for debugging
tap_history = navigator.get_tap_history()
for tap in tap_history:
    print(f"Tapped '{tap.element_text}' at ({tap.x}, {tap.y}) "
          f"with confidence {tap.confidence}")
```

## Integration Points

- **Upstream**: Requires `adb-ocr-finder` for text location detection
- **Upstream**: Requires `adb-state-verifier` for optional state verification after taps
- **Upstream**: Requires `adb-device-manager` for device connection
- **Downstream**: Used by `adb-magisk-orchestrator` for installation automation
- **Downstream**: Used by game automation workflows (AFKJourney, GuitarGirl, etc.)

## Tap History

Every tap is recorded with:
- Target element text
- X, Y coordinates
- Detected confidence level
- Number of attempts
- Timestamp (via parent workflow)

Access tap history via `get_tap_history()` for:
- Debugging automation flows
- Validating tap sequences
- Performance analysis
- State transition verification

## Related Agents

- `adb-ocr-finder`: Provides text location detection
- `adb-state-verifier`: Provides state verification for flow control
- `adb-device-manager`: Provides device connection
- `adb-magisk-orchestrator`: Uses UI navigation for installation automation
- `adb-zygisk-enabler`: Uses UI navigation for Zygisk enablement
