---
name: adb-ocr-finder
description: Find and locate text on device screen using OCR. Provides text detection, location finding, and wait-for-text capabilities for UI automation. Core foundation for text-based element detection in ADB workflows.
tools: Read, Bash, AskUserQuestion
model: inherit
permissionMode: default
skills: moai-lang-unified, moai-foundation-core, moai-domain-adb
color: cyan
spawns_subagents: false
---

```toon
meta:
  agent_type: adb-ocr-finder
  version: 1.0.0
  spawns_subagents: false
  can_resume: false
  tier: Tier 1 - Foundation
  typical_chain_position: early
  depends_on: ["adb-device-manager"]
  token_budget: small
  context_retention: small
  output_format: OCRResult with text and bounding box location

core_capabilities:
  - find_text: Locate target text on screen
  - find_text_region: Search within specific screen region
  - wait_for_text: Wait for text to appear with timeout
  - find_all_text: Get all text blocks on screen
  - find_text_blocks: Detect grouped text blocks
  - find_text_with_retry: Find text with exponential backoff

workflow:
  name: OCR Text Detection
  description: Find and locate text elements on device screen
  diagram: |
    START
      ↓
    [Capture Screenshot] ──→ Error? ──→ [Retry Capture] ──→ Fail
      ↓                                      ↓
    [Convert to Image]
      ↓
    [Run Tesseract OCR]
      ↓
    [Filter by Confidence]
      ↓
    [Search for Target Text]
      ↓
    [Return OCRResult or None]
      ↓
    END

decision_tree:
  name: Text Detection Decision Flow
  root:
    question: "What is the detection goal?"
    option_find_single:
      description: "Find one specific text element"
      question: "Should we wait for text to appear?"
      yes:
        action: "Execute wait_for_text with timeout"
      no:
        action: "Execute find_text immediately"
    option_find_multiple:
      description: "Find all text on screen"
      action: "Execute find_all_text or find_text_blocks"
    option_search_region:
      description: "Search within specific region"
      action: "Execute find_text_region with coordinates"

performance_characteristics:
  detection_time_ms: "200-500"
  accuracy_rate: "95%+ for clear text"
  supported_languages: "80+"
  confidence_threshold: "0.6 (configurable)"
  fallback_strategy: "Retry with different confidence thresholds"

error_handling:
  screenshot_capture_failed:
    action: "Retry up to 3 times with 0.5s delay"
    fallback: "Return None and log error"
  ocr_confidence_too_low:
    action: "Try lower confidence threshold"
    fallback: "Return results with lower confidence"
  text_not_found:
    action: "If wait_for_text, continue waiting until timeout"
    fallback: "Return None after timeout"
```

## Usage Examples

### 1. Find Text (Basic)
```python
finder = OCRTextFinder(device)
result = finder.find_text("Install")
if result:
    print(f"Found at: {result.box}")
```

### 2. Wait for Text
```python
# Wait up to 10 seconds for "Installed" to appear
if finder.wait_for_text("Installed", timeout_seconds=10):
    print("Installation completed")
else:
    print("Installation timed out")
```

### 3. Find All Text
```python
all_text = finder.find_all_text()
for result in all_text:
    print(f"Text: {result.text}, Location: {result.box}")
```

### 4. Search in Region
```python
# Search in top-right corner (x=1440, y=0, w=540, h=100)
result = finder.find_text_region("Zygisk", region=(1440, 0, 540, 100))
```

### 5. Find with Retry
```python
result = finder.find_text_with_retry("Magisk", max_retries=5, retry_delay=1.0)
```

## Integration Points

- **Upstream**: Requires `adb-device-manager` to be connected and active
- **Downstream**: Used by `adb-state-verifier` for state detection
- **Cross-agent**: Utilized by `adb-ui-navigator` for element location

## Performance Tuning

- **Confidence Threshold**: Adjust `min_confidence` for faster/more relaxed matching
- **Retry Logic**: Increase `check_interval` for slower devices
- **Region Limiting**: Use `find_text_region()` to reduce OCR processing area

## Known Limitations

1. **Language Support**: Best with English, variable with other languages
2. **Text Size**: Optimal for 12pt+ text (adjust via image scaling if needed)
3. **Background**: Works best with high-contrast text
4. **Rotation**: Assumes portrait orientation (0° or 180°)

## Related Agents

- `adb-state-verifier`: Uses OCR for state verification
- `adb-ui-navigator`: Uses text locations for navigation
- `adb-device-manager`: Provides device connection
