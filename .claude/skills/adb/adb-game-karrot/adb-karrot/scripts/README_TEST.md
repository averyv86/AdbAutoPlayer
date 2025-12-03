# Karrot AI Test Suite

Comprehensive testing system for the AI-based detection system.

## Overview

`karrot_test_ai.py` provides automated testing for:
- AI Vision (Claude Vision API)
- Smart Detector (Multi-layer fallback)
- Performance benchmarking
- Integration testing

## Prerequisites

```bash
# 1. ADB device connected
adb devices

# 2. ANTHROPIC_API_KEY set
export ANTHROPIC_API_KEY='your-key-here'

# 3. Required scripts in same directory
ls karrot_ai_vision.py karrot_smart_detector.py
```

## Usage

### Test AI Vision System
```bash
uv run karrot_test_ai.py --test-vision
```

**Tests:**
1. Screenshot capture
2. Full screen analysis (game state + elements)
3. Element detection (multiple targets)
4. Game state detection
5. Error detection

**Expected Output:**
```
TEST SUITE 1: AI VISION
============================================================

[TEST 1/5] Screenshot Capture
[PASS] Screenshot captured successfully

[TEST 2/5] Full Screen Analysis
[PASS] Analysis completed in 2.34s
  State: welcome
  Elements: 8

[TEST 3/5] Element Detection
  [FOUND] Get Started button at (720, 2350)
  [FOUND] Log in button at (720, 2150)
  [NOT FOUND] Phone input field
[PASS] Found 2/3 elements

[TEST 4/5] Game State Detection
[PASS] Detected state: welcome (1.45s)

[TEST 5/5] Error Detection
[PASS] No errors detected (1.89s)
```

### Test Smart Detector System
```bash
uv run karrot_test_ai.py --test-detector
```

**Tests:**
1. UIAutomator detection layer
2. AI Vision detection layer
3. Multi-layer fallback
4. Game state detection

**Expected Output:**
```
TEST SUITE 2: SMART DETECTOR
============================================================

[TEST 1/4] UIAutomator Detection Layer
[PASS] Found at (720, 2350) in 0.12s

[TEST 2/4] AI Vision Detection Layer
[PASS] Found at (718, 2348) in 2.45s

[TEST 3/4] Multi-Layer Fallback
[PASS] Found via uiautomator at (720, 2350)

[TEST 4/4] Game State Detection
[PASS] Detected state: welcome (0.08s)
```

### Run Performance Benchmark
```bash
uv run karrot_test_ai.py --benchmark
```

**Tests:**
- Compare UIAutomator vs AI Vision timing
- Accuracy comparison
- Multiple iterations per target

**Expected Output:**
```
TEST SUITE 3: PERFORMANCE BENCHMARK
============================================================

[BENCHMARK] Testing 'Get Started'...
  UIAutomator: 0.095s (found: True)
  AI Vision: 2.341s (found: True)
  AI is 24.6x slower

[BENCHMARK] Testing 'Log in'...
  UIAutomator: 0.102s (found: True)
  AI Vision: 2.289s (found: True)
  AI is 22.4x slower

[BENCHMARK] Testing 'Phone'...
  UIAutomator: 0.098s (found: False)
  AI Vision: 2.456s (found: True)
  AI is 25.1x slower
```

### Run All Tests
```bash
uv run karrot_test_ai.py --all
```

Runs all three test suites sequentially.

### Generate JSON Report
```bash
uv run karrot_test_ai.py --all --report
```

Generates a comprehensive JSON report at `/tmp/karrot-test-report.json`.

**Report Structure:**
```json
{
  "timestamp": "2025-12-03T10:30:45.123456",
  "summary": {
    "total_suites": 3,
    "total_tests": 12,
    "total_passed": 10,
    "total_failed": 1,
    "total_skipped": 0,
    "total_errors": 1,
    "total_duration": 45.67
  },
  "suites": [
    {
      "name": "AI Vision",
      "duration": "15.23s",
      "passed": 4,
      "failed": 1,
      "skipped": 0,
      "errors": 0,
      "success_rate": "80.0%",
      "tests": [
        {
          "name": "Screenshot Capture",
          "status": "pass",
          "duration": "0.34s",
          "details": {"path": "/tmp/karrot_test_screen.png"}
        }
      ]
    }
  ]
}
```

### Custom Report Output
```bash
uv run karrot_test_ai.py --all --report --output /tmp/my-report.json
```

### Quiet Mode
```bash
uv run karrot_test_ai.py --all --quiet
```

Only prints final summary, suppresses verbose output.

## Test Results Interpretation

### Success Criteria

**AI Vision Tests:**
- ✅ Screenshot capture succeeds
- ✅ Analysis completes in < 5s
- ✅ Finds at least 1/3 test elements
- ✅ State detection works
- ✅ Error detection doesn't crash

**Smart Detector Tests:**
- ✅ UIAutomator finds text elements
- ✅ AI Vision finds visual elements
- ✅ Fallback logic works correctly
- ✅ State detection < 0.5s

**Benchmark Tests:**
- ✅ UIAutomator < 0.2s per element
- ✅ AI Vision < 5s per element
- ✅ UIAutomator is 20-30x faster
- ✅ AI Vision has higher accuracy for non-text

### Common Failures

**1. ANTHROPIC_API_KEY not set**
```
[SKIP] AI Vision Initialization
error_message: "ANTHROPIC_API_KEY not set"
```

**Solution:**
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

**2. No ADB device connected**
```
[WARN] No ADB devices connected
[FAIL] Screenshot capture failed
```

**Solution:**
```bash
adb devices
adb connect 127.0.0.1:5555  # BlueStacks
```

**3. Element not found**
```
[NOT FOUND] Get Started button
[FAIL] Element Detection: Found 0/3 elements
```

**Reasons:**
- App is on wrong screen
- Element text changed
- Screen resolution mismatch

**Solutions:**
- Navigate to welcome screen
- Update element descriptions
- Check SCREEN_RESOLUTION in scripts

**4. AI Vision timeout**
```
[ERROR] AI Vision test failed: Request timeout
```

**Reasons:**
- Network latency
- API rate limiting
- Large image size

**Solutions:**
- Retry after 1 minute
- Check API quota
- Reduce image resolution

## Performance Expectations

### Response Times

| Method | Average Time | Accuracy | Use Case |
|--------|-------------|----------|----------|
| UIAutomator | 0.1s | 99% | Text elements |
| AI Vision | 2.5s | 98% | Visual elements |
| Template Match | 0.2s | 90% | Image matching |
| OCR | 0.5s | 85% | Text recognition |

### Resource Usage

**Per Test Run:**
- Time: 30-60 seconds (all tests)
- API Calls: ~15-20 calls
- Cost: ~$0.05 (Claude Sonnet 4)
- Storage: ~10 MB (screenshots + dumps)

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Karrot AI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Setup Android SDK
        uses: android-actions/setup-android@v2
      
      - name: Start Emulator
        run: |
          emulator -avd test -no-window -no-audio &
          adb wait-for-device
      
      - name: Run Tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          uv run karrot_test_ai.py --all --report
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: test-report
          path: /tmp/karrot-test-report.json
```

## Debugging

### Enable Debug Logging
```python
# In karrot_ai_vision.py or karrot_smart_detector.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Capture Screenshots Manually
```bash
adb shell screencap -p /sdcard/debug.png
adb pull /sdcard/debug.png /tmp/debug.png
```

### Test AI Vision Standalone
```bash
uv run karrot_ai_vision.py --analyze /tmp/debug.png --json
```

### Test Smart Detector Standalone
```bash
uv run karrot_smart_detector.py --find "Get Started" --json
```

## Extending Tests

### Add New Test Suite
```python
def test_custom(self) -> TestSuiteResult:
    """Test custom functionality"""
    suite = TestSuiteResult(suite_name="Custom Tests")
    suite_start = time.time()
    
    # Test 1
    test_start = time.time()
    try:
        # Your test logic here
        result = my_test_function()
        
        suite.tests.append(TestResult(
            name="My Test",
            status=TestStatus.PASS,
            duration_sec=time.time() - test_start,
            details={"result": result}
        ))
    except Exception as e:
        suite.tests.append(TestResult(
            name="My Test",
            status=TestStatus.ERROR,
            duration_sec=time.time() - test_start,
            error_message=str(e)
        ))
    
    suite.total_duration_sec = time.time() - suite_start
    return suite
```

### Add to CLI
```python
# In main()
parser.add_argument(
    "--test-custom",
    action="store_true",
    help="Run custom tests"
)

# In execution logic
if args.test_custom:
    test_suite.suite_results.append(test_suite.test_custom())
```

## Troubleshooting

### Issue: Import errors
```bash
# Solution: Ensure scripts are in same directory
ls -la /path/to/scripts/
# Should see: karrot_ai_vision.py, karrot_smart_detector.py, karrot_test_ai.py
```

### Issue: Permission denied
```bash
# Solution: Make executable
chmod +x karrot_test_ai.py
```

### Issue: Module not found
```bash
# Solution: Install dependencies
uv pip install anthropic Pillow
```

## References

- [AI Vision Script](./karrot_ai_vision.py) - Claude Vision implementation
- [Smart Detector Script](./karrot_smart_detector.py) - Multi-layer detection
- [Main Automation Script](./karrot_bot.py) - Full automation system

## Support

For issues or questions:
1. Check test output for specific error messages
2. Review logs at `/tmp/karrot-test-report.json`
3. Test components individually
4. File issue with report attached
