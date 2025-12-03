# Workflow: UI Element Interaction Workflow

**File**: `ui-interaction.toon`
**Skill**: `adb-uiautomator`
**Version**: 1.0.0
**Category**: ui-automation
**Difficulty**: intermediate

---

## Purpose

This workflow performs various interactions with UI elements including tapping, long-pressing, swiping, and text input. It handles coordinate-based interactions, verifies results through screen captures, and logs interaction outcomes.

Use this workflow to programmatically interact with app interfaces for testing or automation.

---

## Prerequisites

- Device with ADB debugging enabled
- Target app running and UI visible
- Correct screen coordinates identified (use element-detection.toon)
- ADB shell access with input capabilities
- Temporary file storage accessible

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| interaction | string | "tap" | Type: tap, long_press, swipe, text_input |
| x | integer | 540 | X coordinate for interaction |
| y | integer | 960 | Y coordinate for interaction |
| text | string | "" | Text to input (for text_input) |
| duration | integer | 500 | Long-press duration in milliseconds |
| swipe_direction | string | "up" | Swipe direction: up, down, left, right |

---

## Phases

### Phase 1: Prepare for Interaction

**Objective**: Verify device state and interaction parameters

Steps:
1. Capture current screen state
2. Validate coordinates are in valid range
3. Verify device is responsive
4. Check input system available

**Success Indicators**:
- Screen capture successful
- Coordinates valid format
- Device responsive
- Ready for interaction

---

### Phase 2: Perform Tap Interaction

**Objective**: Tap on specified coordinates

Steps:
1. Execute tap at (x, y)
2. Wait for screen response
3. Monitor UI changes
4. Log tap result

**Success Indicators**:
- Tap command executed
- Screen changes detected
- UI responds appropriately
- No errors during tap

---

### Phase 3: Perform Long Press

**Objective**: Long-press on element for extended duration

Steps:
1. Calculate long-press touch path
2. Execute swipe (press) for duration
3. Wait for context menu or action
4. Monitor response

**Success Indicators**:
- Long-press executed
- Duration correct
- Context menu appears (if expected)
- Response detected

---

### Phase 4: Perform Swipe Interaction

**Objective**: Swipe in specified direction to scroll or navigate

Steps:
1. Calculate swipe start/end coordinates
2. Determine direction and magnitude
3. Execute swipe gesture
4. Wait for content to settle

**Success Indicators**:
- Swipe executed smoothly
- Content scrolls in correct direction
- UI stable after swipe
- No errors during swipe

---

### Phase 5: Perform Text Input

**Objective**: Input text into focused text field

Steps:
1. Clear any existing text
2. Enter new text via input command
3. Verify text appears in field
4. Confirm text was entered correctly

**Success Indicators**:
- Field cleared
- Text entered completely
- Visible in UI
- No input errors

---

### Phase 6: Verify Interaction Result

**Objective**: Confirm interaction had desired effect

Steps:
1. Capture post-interaction screen
2. Dump updated UI tree
3. Compare state change
4. Generate result report

**Success Indicators**:
- Screen capture obtained
- UI tree updated
- State change detected
- Report generated

---

## Success Criteria

- [ ] Coordinates validated before interaction
- [ ] Interaction command executed successfully
- [ ] Device responds to input
- [ ] UI state changes as expected
- [ ] Screen captures obtained
- [ ] No errors during operation
- [ ] Result verified
- [ ] Report generated

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid coordinates | Out of bounds | Verify screen dimensions and coordinates |
| Tap ignored | Element not interactive | Check element is clickable and visible |
| Swipe not working | Gesture not recognized | Try increasing swipe duration or magnitude |
| Text not input | Input service issue | Ensure input method enabled, try again |
| Long-press fails | Timing issue | Adjust duration or try standard tap |
| Screen frozen | Device hang | Restart adb connection and device |

---

## Interaction Types

### Tap
- Single touch contact
- Best for buttons and interactive elements
- Immediate response expected

```bash
interaction="tap" x=540 y=960
```

### Long Press
- Extended touch duration (configurable)
- Opens context menus or long-press actions
- Duration in milliseconds

```bash
interaction="long_press" x=540 y=960 duration=1000
```

### Swipe
- Gesture movement in direction
- Scrolls lists or navigates screens
- Supports: up, down, left, right

```bash
interaction="swipe" swipe_direction="up"
```

### Text Input
- Enters text into focused field
- Clears existing text first
- Handles special characters

```bash
interaction="text_input" text="Hello World"
```

---

## Example Execution

```bash
# Tap on button at coordinates
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-uiautomator/workflow/ui-interaction.toon \
  --param device="127.0.0.1:5555" \
  --param interaction="tap" \
  --param x="540" \
  --param y="600" \
  --verbose

# Long-press for context menu
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-uiautomator/workflow/ui-interaction.toon \
  --param device="emulator-5554" \
  --param interaction="long_press" \
  --param x="300" \
  --param y="400" \
  --param duration="1500" \
  --verbose

# Swipe up to scroll
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-uiautomator/workflow/ui-interaction.toon \
  --param device="192.168.1.100:5555" \
  --param interaction="swipe" \
  --param swipe_direction="up" \
  --param x="540" \
  --param y="960" \
  --verbose

# Input text into field
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-uiautomator/workflow/ui-interaction.toon \
  --param device="127.0.0.1:5555" \
  --param interaction="text_input" \
  --param x="540" \
  --param y="400" \
  --param text="01012345678" \
  --verbose
```

---

## Coordinate Finding Tips

**Find element coordinates using element-detection.toon**:
```bash
# Get element bounds
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-uiautomator/workflow/element-detection.toon \
  --param text_pattern="로그인" \
  --verbose
```

**Calculate center from bounds**:
- Bounds format: [x1,y1][x2,y2]
- Center X = (x1 + x2) / 2
- Center Y = (y1 + y2) / 2

---

## Swipe Calculations

The workflow automatically calculates swipe coordinates:
- **Up**: Start at (x, y+200), end at (x, y-200)
- **Down**: Start at (x, y-200), end at (x, y+200)
- **Left**: Start at (x+200, y), end at (x-200, y)
- **Right**: Start at (x-200, y), end at (x+200, y)

Magnitude can be adjusted by modifying coordinate offsets.

---

## Text Input Behavior

The workflow:
1. Selects all existing text (Ctrl+A)
2. Deletes selected text (DEL)
3. Inputs new text character by character
4. Verifies result via screenshot

Special characters are handled by the input command.

---

## Related Workflows

- [element-detection.md](./element-detection.md) - Find elements first
- [../adb-screen-detection/workflow/template-matching.md](../adb-screen-detection/workflow/template-matching.md) - Visual element detection
- [../adb-karrot/workflow/login-automation.md](../adb-karrot/workflow/login-automation.md) - Uses interactions for login
- [../adb-navigation-base/workflow/app-navigation.md](../adb-navigation-base/workflow/app-navigation.md) - Navigate using interactions

---

**Last Updated**: 2025-12-02
**Status**: Active
**Complexity**: Intermediate
**Framework**: Android Input System
