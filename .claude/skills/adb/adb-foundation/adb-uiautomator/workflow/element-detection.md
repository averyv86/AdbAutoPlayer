# Workflow: UI Element Detection and Identification

**File**: `element-detection.toon`
**Skill**: `adb-uiautomator`
**Version**: 1.0.0
**Category**: ui-automation
**Difficulty**: intermediate

---

## Purpose

This workflow detects and identifies UI elements on the current screen using Android's accessibility tree dump. It can search by text pattern, resource ID, or analyze view hierarchy to locate buttons, input fields, scrollable content, and other interactive elements.

Use this workflow to programmatically locate specific UI elements for interaction or validation.

---

## Prerequisites

- Device with ADB debugging enabled
- UIAutomator framework installed (built-in)
- Target app running or on specific screen
- ADB shell access
- Temporary file write access (/tmp or device storage)

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| text_pattern | string | "" | Text pattern to find (regex or literal) |
| resource_id | string | "" | Resource ID to find (com.app:id/resource) |
| timeout | integer | 10 | Element detection timeout in seconds |

---

## Phases

### Phase 1: Capture Current Screen State

**Objective**: Get accessibility tree and visual capture of current screen

Steps:
1. Capture screenshot of current screen
2. Dump accessibility tree to XML file
3. Get window focus information
4. Verify UI state data available

**Success Indicators**:
- Screenshot captured
- Accessibility tree dumped
- Window focus info available
- Files accessible

---

### Phase 2: Detect Elements by Text

**Objective**: Find elements matching text pattern

Steps:
1. Search accessibility tree for text pattern
2. Extract element bounds/coordinates
3. Count matching elements
4. Get element properties

**Success Indicators**:
- Text matches found
- Coordinates extracted
- Element count returned
- Properties available

---

### Phase 3: Detect Elements by Resource ID

**Objective**: Locate elements by their resource identifier

Steps:
1. Search by resource ID in tree
2. Extract element information
3. Get element bounds and properties
4. Verify element accessibility

**Success Indicators**:
- Element found by ID
- Complete element info available
- Bounds correctly identified
- Element accessible

---

### Phase 4: Analyze Element Properties

**Objective**: Extract detailed element properties and state

Steps:
1. Check if elements are clickable
2. Find scrollable elements
3. Identify input fields (EditText)
4. Determine element state

**Success Indicators**:
- Properties clearly identified
- Interactive states known
- Input capability determined
- State information available

---

### Phase 5: Detect Button Elements

**Objective**: Find and catalog all button elements

Steps:
1. Locate all button elements
2. Extract button labels/text
3. Get button coordinates
4. Check button clickability

**Success Indicators**:
- Buttons identified
- Labels extracted
- Coordinates available
- Clickability verified

---

## Success Criteria

- [ ] Accessibility tree successfully dumped
- [ ] Screen capture obtained
- [ ] Elements found by text (if text_pattern provided)
- [ ] Elements found by resource ID (if resource_id provided)
- [ ] Element coordinates extracted
- [ ] Element properties identified
- [ ] View hierarchy analyzed
- [ ] Report generated successfully

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| UIAutomator dump fails | Permissions issue or service down | Enable developer options, check ADB access |
| Text pattern not found | Wrong pattern or element not visible | Verify text and screenshot, check app state |
| Resource ID not found | Wrong ID format or element doesn't exist | Use DevTools to verify correct ID format |
| Empty accessibility tree | Service not responding | Restart adb and app, check accessibility settings |
| File not accessible | Permission denied | Check /tmp write permissions |
| Timeout | Device slow to respond | Increase timeout parameter |

---

## Element Properties

The accessibility tree provides:
- **Text**: Display text of element
- **Resource ID**: Unique identifier (com.app:id/name)
- **Class**: UI element type (Button, EditText, etc.)
- **Content Description**: Accessibility text
- **Bounds**: Screen coordinates [x1,y1][x2,y2]
- **Clickable**: Whether element accepts clicks
- **Scrollable**: Whether element scrolls
- **Enabled**: Whether element is active
- **Focused**: Whether element has focus

---

## Example Execution

```bash
# Detect element by text pattern
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-uiautomator/workflow/element-detection.toon \
  --param device="127.0.0.1:5555" \
  --param text_pattern="로그인|Login" \
  --verbose

# Find element by resource ID
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-uiautomator/workflow/element-detection.toon \
  --param device="emulator-5554" \
  --param resource_id="com.daangn.android.app:id/login_button" \
  --verbose

# Analyze all UI elements on screen
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-uiautomator/workflow/element-detection.toon \
  --param device="192.168.1.100:5555" \
  --param timeout=15 \
  --verbose
```

---

## Element Detection Patterns

### By Text (Korean/English)
```
text_pattern="로그인"          # Find Korean text
text_pattern="Login"           # Find English text
text_pattern="로그인|Login"    # Find either pattern
text_pattern="^버튼.*"         # Regex pattern (starts with "버튼")
```

### By Resource ID
```
resource_id="com.app:id/button"              # Full ID
resource_id="com.daangn.android.app:id/*"   # Wildcard search
```

### By Element Type
- Button: `resource-id=".*button"`
- EditText: `class=".*EditText"`
- ImageView: `class=".*ImageView"`
- TextView: `class=".*TextView"`

---

## Coordinate System

Bounds are in format `[x1,y1][x2,y2]` where:
- x1, y1 = top-left corner
- x2, y2 = bottom-right corner
- Center point = ((x1+x2)/2, (y1+y2)/2)

Example: `[100,200][300,400]`
- Top-left: 100, 200
- Bottom-right: 300, 400
- Center: 200, 300

---

## View Hierarchy Analysis

The workflow analyzes:
- Total elements on screen
- Element type distribution
- Clickable vs non-clickable
- Input fields count
- Scrollable containers
- Common UI patterns

---

## Related Workflows

- [ui-interaction.md](./ui-interaction.md) - Interact with detected elements
- [../adb-screen-detection/workflow/template-matching.md](../adb-screen-detection/workflow/template-matching.md) - Visual element detection
- [../adb-karrot/workflow/login-automation.md](../adb-karrot/workflow/login-automation.md) - Uses element detection
- [../adb-navigation-base/workflow/app-navigation.md](../adb-navigation-base/workflow/app-navigation.md) - Navigate using detected elements

---

**Last Updated**: 2025-12-02
**Status**: Active
**Complexity**: Intermediate
**Framework**: Android UIAutomator (built-in)
