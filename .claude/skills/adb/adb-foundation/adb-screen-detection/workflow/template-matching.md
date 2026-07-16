# Workflow: Screen Template Matching Detection

**File**: `template-matching.toon`
**Skill**: `adb-screen-detection`
**Version**: 1.0.0
**Category**: screen-detection
**Difficulty**: intermediate

---

## Purpose

This workflow detects screen states and UI elements by matching template images against the current device screen. It uses image similarity algorithms to locate specific UI patterns, buttons, or screen layouts with configurable confidence thresholds.

Use this workflow for robust screen state detection when text-based detection is unreliable or for locating complex UI elements.

---

## Prerequisites

- Device with ADB screen capture capability
- Template image file (PNG or JPG)
- Target UI/element visible on screen
- Template size reasonable (not larger than screen)
- Image comparison tools available on device

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| template_path | string | "" | Path to template image file (required) |
| threshold | float | 0.8 | Match confidence threshold (0.0-1.0) |
| timeout | integer | 30 | Detection timeout in seconds |

---

## Phases

### Phase 1: Capture Current Screen

**Objective**: Get screenshot of current device screen state

Steps:
1. Take screenshot of current display
2. Save to temporary location
3. Verify file validity
4. Check screenshot quality

**Success Indicators**:
- Screenshot captured
- File valid and readable
- Image dimensions correct
- Ready for comparison

---

### Phase 2: Load Template Image

**Objective**: Load and verify template file

Steps:
1. Verify template file exists
2. Check file format (PNG/JPG)
3. Get template dimensions
4. Validate template quality

**Success Indicators**:
- Template found
- Format valid
- Dimensions readable
- File accessible

---

### Phase 3: Perform Template Matching

**Objective**: Execute image matching algorithm

Steps:
1. Execute matching algorithm
2. Compute similarity scores
3. Locate best match position
4. Calculate match confidence

**Success Indicators**:
- Matching executed
- Similarity computed
- Position located (if match)
- Confidence score obtained

---

### Phase 4: Analyze Matching Results

**Objective**: Process match results and validate

Steps:
1. Check if match found above threshold
2. Extract match coordinates
3. Validate against threshold
4. Determine detection confidence

**Success Indicators**:
- Match validated
- Coordinates extracted
- Confidence verified
- Result determined

---

### Phase 5: Compare Multiple Screens

**Objective**: Check template against multiple screen states

Steps:
1. Compare against baseline
2. Track match variations
3. Build comparison metrics
4. Identify state changes

**Success Indicators**:
- Comparisons executed
- Metrics collected
- State differences identified
- Trends analyzed

---

## Success Criteria

- [ ] Screenshot captured successfully
- [ ] Template file found and valid
- [ ] Matching algorithm executed
- [ ] Confidence score computed
- [ ] Match coordinates located
- [ ] Result above threshold (if expected)
- [ ] Report generated
- [ ] No errors during process

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Screenshot fails | Device unresponsive | Check ADB connection and restart |
| Template not found | Wrong path | Verify template_path is correct |
| Matching timeout | Slow device or large image | Increase timeout or reduce template size |
| No match found | Template not on screen | Verify template exists and is visible |
| Low confidence | Template too small/different | Lower threshold or update template |
| Invalid image | Corrupted file | Re-capture or verify template |

---

## Threshold Guidance

- **0.95-1.0**: Exact or near-exact match (for identical UI)
- **0.85-0.95**: High confidence match (typical use)
- **0.75-0.85**: Moderate confidence (allows minor variations)
- **0.65-0.75**: Low confidence (may have false positives)
- **Below 0.65**: Not recommended (too loose)

---

## Example Execution

```bash
# Detect screen using template with default threshold
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-screen-detection/workflow/template-matching.toon \
  --param device="127.0.0.1:5555" \
  --param template_path="/tmp/login_screen.png" \
  --verbose

# Detect with stricter threshold
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-screen-detection/workflow/template-matching.toon \
  --param device="emulator-5554" \
  --param template_path="/tmp/button_template.png" \
  --param threshold="0.9" \
  --verbose

# Detect with longer timeout for slow device
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-screen-detection/workflow/template-matching.toon \
  --param device="192.168.1.100:5555" \
  --param template_path="/tmp/ui_element.png" \
  --param threshold="0.85" \
  --param timeout="60" \
  --verbose
```

---

## Template Image Guidelines

**Best Practices**:
- Use exact screenshot of desired UI element
- Include sufficient context but minimal extra
- Ensure template is visible on target screen
- Template should be smaller than full screen
- Use common image formats (PNG preferred)

**Template Size**:
- Minimum: 32x32 pixels
- Typical: 100-400 pixels
- Maximum: Screen width/height
- Recommended: 50-200 pixels for best performance

**Template Content**:
- Should be recognizable and unique
- Include context around element
- Avoid highly dynamic content
- Minimize sensitive information
- Keep consistent with expected state

---

## Output Coordinates

Matching returns coordinates in format:
- X, Y = top-left corner of match
- Full rectangle = (x, y) to (x+width, y+height)
- Center point = (x + width/2, y + height/2)

Use coordinates for subsequent interactions via ui-interaction.toon.

---

## Performance Optimization

- **Reduce template size**: Smaller templates match faster
- **Increase threshold**: Higher threshold skips low-confidence matches
- **Pre-process images**: Remove dynamic elements
- **Use specific templates**: Unique patterns match better
- **Cache results**: Store known screen states

---

## Related Workflows

- [ocr-detection.md](./ocr-detection.md) - Text-based detection alternative
- [../adb-uiautomator/workflow/element-detection.md](../adb-uiautomator/workflow/element-detection.md) - Accessibility-based detection
- [../adb-uiautomator/workflow/ui-interaction.md](../adb-uiautomator/workflow/ui-interaction.md) - Interact with detected elements
- [../adb-navigation-base/workflow/app-navigation.md](../adb-navigation-base/workflow/app-navigation.md) - Navigate using detection

---

**Last Updated**: 2025-12-02
**Status**: Active
**Complexity**: Intermediate
**Algorithm**: Image template matching with similarity scoring
