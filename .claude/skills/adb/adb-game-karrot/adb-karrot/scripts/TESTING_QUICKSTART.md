# Karrot AI Testing - Quick Start Guide

## One-Command Test

```bash
# Run all tests with report
uv run karrot_test_ai.py --all --report

# Quick vision test
uv run karrot_test_ai.py --test-vision

# Quick detector test
uv run karrot_test_ai.py --test-detector

# Performance benchmark
uv run karrot_test_ai.py --benchmark
```

## Prerequisites Check

```bash
# 1. Check ADB connection
adb devices
# Should show: 127.0.0.1:5555   device

# 2. Check API key
echo $ANTHROPIC_API_KEY
# Should show: sk-ant-...

# 3. Check scripts exist
ls karrot_*.py
# Should show: karrot_ai_vision.py, karrot_smart_detector.py, karrot_test_ai.py
```

## Expected Results

### ✅ Success (Example)
```
TEST SUMMARY
============================================================

AI Vision:
  Duration: 15.23s
  Tests: 5
  Passed: 5
  Failed: 0
  Success Rate: 100.0%

Smart Detector:
  Duration: 8.45s
  Tests: 4
  Passed: 4
  Failed: 0
  Success Rate: 100.0%

Benchmark:
  Duration: 12.34s
  Tests: 1
  Passed: 1
  Failed: 0
  Success Rate: 100.0%

============================================================
OVERALL: 10/10 tests passed
============================================================
```

### ❌ Common Failures

**1. API Key Missing**
```
[SKIP] AI Vision Initialization
error_message: "ANTHROPIC_API_KEY not set"

FIX: export ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

**2. No Device**
```
[WARN] No ADB devices connected
[FAIL] Screenshot capture failed

FIX: adb connect 127.0.0.1:5555
```

**3. Element Not Found**
```
[NOT FOUND] Get Started button
[FAIL] Element Detection: Found 0/3 elements

FIX: Navigate to welcome screen in the app
```

## Test Files Output

```bash
# Screenshot
/tmp/karrot_test_screen.png

# UI dump
/tmp/ui_dump.xml

# JSON report
/tmp/karrot-test-report.json
```

## View Report

```bash
# Pretty print JSON report
cat /tmp/karrot-test-report.json | jq .

# Check summary only
cat /tmp/karrot-test-report.json | jq .summary
```

## Timing Expectations

| Test Suite | Duration | API Calls | Cost |
|-----------|----------|-----------|------|
| AI Vision | 15-20s | 5-7 | $0.02 |
| Smart Detector | 8-12s | 3-5 | $0.01 |
| Benchmark | 10-15s | 6-9 | $0.02 |
| **Total** | **35-50s** | **15-20** | **$0.05** |

## Quick Debugging

```bash
# Test AI Vision standalone
uv run karrot_ai_vision.py --capture --json

# Test Smart Detector standalone
uv run karrot_smart_detector.py --detect-state

# Check detector status
uv run karrot_smart_detector.py --status
```

## Integration with Main Bot

```bash
# After testing, run the full bot
uv run karrot_bot.py

# The bot uses both AI Vision and Smart Detector internally
```

## Next Steps

1. **If all tests pass**: Ready to use AI detection in production
2. **If some tests fail**: Check individual component tests
3. **If benchmark shows slow performance**: Consider caching strategies

## Full Documentation

See [README_TEST.md](./README_TEST.md) for complete documentation.
