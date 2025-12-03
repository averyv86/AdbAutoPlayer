# Karrot AI Test Commands - Quick Reference

## One-Liners

```bash
# Run all tests with report (recommended)
./run_tests.sh all

# Quick smoke test
./run_tests.sh quick

# Test AI Vision only
./run_tests.sh vision

# Test Smart Detector only
./run_tests.sh detector

# Performance benchmark
./run_tests.sh benchmark
```

## Direct UV Commands

```bash
# All tests with report
uv run karrot_test_ai.py --all --report

# Individual test suites
uv run karrot_test_ai.py --test-vision
uv run karrot_test_ai.py --test-detector
uv run karrot_test_ai.py --benchmark

# Quiet mode (summary only)
uv run karrot_test_ai.py --all --quiet

# Custom report path
uv run karrot_test_ai.py --all --report --output /tmp/my-report.json
```

## Component Testing

```bash
# Test AI Vision standalone
uv run karrot_ai_vision.py --capture
uv run karrot_ai_vision.py --analyze /tmp/screenshot.png
uv run karrot_ai_vision.py --find "Get Started button" --image /tmp/screenshot.png

# Test Smart Detector standalone
uv run karrot_smart_detector.py --find "Get Started"
uv run karrot_smart_detector.py --wait "phone_input" --timeout 10
uv run karrot_smart_detector.py --detect-state
uv run karrot_smart_detector.py --status
```

## Setup Commands

```bash
# Check prerequisites
adb devices
echo $ANTHROPIC_API_KEY
command -v uv

# Setup if needed
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
adb connect 127.0.0.1:5555
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Report Commands

```bash
# View JSON report
cat /tmp/karrot-test-report.json | jq .

# View summary only
cat /tmp/karrot-test-report.json | jq .summary

# View specific test suite
cat /tmp/karrot-test-report.json | jq '.suites[] | select(.name=="AI Vision")'

# Count passed/failed
cat /tmp/karrot-test-report.json | jq '.summary | {passed, failed, total_tests}'
```

## Cleanup Commands

```bash
# Clean test artifacts
rm -f /tmp/karrot_test_screen.png
rm -f /tmp/ui_dump.xml
rm -f /tmp/karrot-test-report.json
rm -f /tmp/karrot_screen.png

# Clean cache
uv run karrot_smart_detector.py --clear-cache
```

## Debug Commands

```bash
# Capture and view screenshot
adb shell screencap -p /sdcard/debug.png
adb pull /sdcard/debug.png /tmp/debug.png
open /tmp/debug.png  # macOS
xdg-open /tmp/debug.png  # Linux

# Dump UI hierarchy
adb shell uiautomator dump
adb pull /sdcard/window_dump.xml /tmp/ui_dump.xml
cat /tmp/ui_dump.xml

# Check device state
adb shell dumpsys window | grep -i focus
adb shell dumpsys activity activities | grep -i karrot
```

## CI/CD Commands

```bash
# Run in CI environment
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
./run_tests.sh all
EXIT_CODE=$?

# Upload report
if [ -f /tmp/karrot-test-report.json ]; then
    cp /tmp/karrot-test-report.json $GITHUB_WORKSPACE/test-report.json
fi

exit $EXIT_CODE
```

## Performance Analysis

```bash
# Run benchmark multiple times
for i in {1..5}; do
    echo "Run $i:"
    uv run karrot_test_ai.py --benchmark --quiet
    sleep 5
done

# Average timing
cat /tmp/karrot-test-report.json | jq '.suites[] | select(.name=="Benchmark") | .duration'
```

## Continuous Testing

```bash
# Watch for changes and re-test
while true; do
    clear
    ./run_tests.sh quick
    sleep 60
done

# Test after every code change
fswatch -o karrot_*.py | while read; do
    echo "Code changed, running tests..."
    ./run_tests.sh quick
done
```

## Common Workflows

### Before Commit
```bash
./run_tests.sh all
git add .
git commit -m "Update AI detection"
git push
```

### Before Deployment
```bash
# Full validation
./run_tests.sh all
if [ $? -eq 0 ]; then
    echo "✓ Tests passed, ready to deploy"
else
    echo "✗ Tests failed, fix issues first"
    exit 1
fi
```

### After Changes
```bash
# Quick validation
./run_tests.sh detector
./run_tests.sh vision

# Full validation if quick tests pass
if [ $? -eq 0 ]; then
    ./run_tests.sh benchmark
fi
```

## Troubleshooting Commands

```bash
# Check API connectivity
curl -H "x-api-key: $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/messages -I

# Check device connection
adb shell echo "Connected"

# Test basic ADB commands
adb shell screencap -p /sdcard/test.png
adb pull /sdcard/test.png /tmp/test.png
ls -lh /tmp/test.png

# Verify Python dependencies
uv pip list | grep -E "anthropic|Pillow"
```

## Help Commands

```bash
# Test script help
uv run karrot_test_ai.py --help

# Component help
uv run karrot_ai_vision.py --help
uv run karrot_smart_detector.py --help

# Shell runner help
./run_tests.sh
```

## Quick Checks

```bash
# Is everything working?
./run_tests.sh quick && echo "✓ System operational"

# What's the current state?
uv run karrot_smart_detector.py --status

# Can we detect elements?
uv run karrot_smart_detector.py --find "Get Started"

# Is AI Vision working?
uv run karrot_ai_vision.py --capture --state /tmp/karrot_screen.png
```

## Documentation Commands

```bash
# View documentation
cat TESTING_QUICKSTART.md
cat README_TEST.md
cat AI_TEST_SYSTEM.md

# Search documentation
grep -i "error" README_TEST.md
grep -i "benchmark" AI_TEST_SYSTEM.md
```

---

**Tip**: Add these to your shell aliases:

```bash
# In ~/.bashrc or ~/.zshrc
alias kt-all='cd /path/to/scripts && ./run_tests.sh all'
alias kt-quick='cd /path/to/scripts && ./run_tests.sh quick'
alias kt-vision='cd /path/to/scripts && ./run_tests.sh vision'
alias kt-report='cat /tmp/karrot-test-report.json | jq .summary'
```
