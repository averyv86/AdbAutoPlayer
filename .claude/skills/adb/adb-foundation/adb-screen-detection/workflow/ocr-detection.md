# Workflow: OCR-Based Screen Text Detection

**File**: `ocr-detection.toon`
**Skill**: `adb-screen-detection`
**Version**: 1.0.0
**Category**: screen-detection
**Difficulty**: beginner

---

## Purpose

This workflow detects text on the device screen using Optical Character Recognition (OCR). It captures the screen, extracts all text, and can search for specific text patterns. Supports multiple languages including Korean and English.

Use this workflow for reliable text-based screen state detection without needing exact accessibility tree information.

---

## Prerequisites

- Device with ADB screen capture capability
- Tesseract OCR engine installed on device
- Screen with readable text
- ADB shell access
- Support for target language (Korean/English default)

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| search_text | string | "" | Text to search for (optional) |
| language | string | "kor+eng" | OCR language codes (kor, eng, kor+eng) |
| timeout | integer | 20 | OCR processing timeout in seconds |

---

## Phases

### Phase 1: Prepare for OCR Processing

- Capture screen screenshot
- Verify OCR engine available
- Prepare image for processing

### Phase 2: Perform OCR Text Recognition

- Run OCR on screenshot
- Extract all visible text
- Save results to files

### Phase 3: Search for Text

- Search extracted text for pattern
- Get context lines
- Highlight matches

### Phase 4: Analyze OCR Results

- Calculate OCR confidence
- Count words extracted
- Analyze quality

### Phase 5: Generate OCR Report

- Create comprehensive report
- Show search results
- Provide confidence metrics

---

## Success Criteria

- [ ] Screenshot captured
- [ ] OCR engine functional
- [ ] Text extracted successfully
- [ ] Search text found (if provided)
- [ ] Confidence metrics obtained
- [ ] Report generated

---

## Example Execution

```bash
# Detect any text on screen
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-screen-detection/workflow/ocr-detection.toon \
  --param device="127.0.0.1:5555" \
  --verbose

# Search for specific Korean text
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-screen-detection/workflow/ocr-detection.toon \
  --param device="emulator-5554" \
  --param search_text="로그인" \
  --param language="kor" \
  --verbose

# Multi-language detection
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-screen-detection/workflow/ocr-detection.toon \
  --param device="192.168.1.100:5555" \
  --param search_text="Login" \
  --param language="kor+eng" \
  --param timeout="30" \
  --verbose
```

---

**Last Updated**: 2025-12-02
