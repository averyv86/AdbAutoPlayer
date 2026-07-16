# Bluestacks Demo Workflow - Execution Examples

**Document Type**: Usage Examples
**Workflow**: bluestacks-demo.toon
**Last Updated**: 2025-12-02

---

## Quick Start Examples

### Example 1: Default Execution (Standard Bluestacks)

Run the demo with default parameters (localhost Bluestacks instance):

```bash
# Basic execution
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon

# Or with explicit default device
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555"
```

**What Happens**:
- Connects to Bluestacks at 127.0.0.1:5555
- Retrieves device information (model, Android version, etc.)
- Gets display specifications
- Executes 3 tap commands (center, top-left, bottom-right)
- Captures screenshot to /tmp/
- Executes 2 swipe gestures (up, down)
- Generates summary report

**Expected Duration**: 3-5 minutes

**Output**:
```
=== BLUESTACKS DEMONSTRATION WORKFLOW ===
Target Device: 127.0.0.1:5555
Start Time: 2025-12-02T14:30:00Z

Phase 1: Connection and Device Information [SUCCESS]
  Device Model: SM-G991B (Galaxy S21)
  Android Version: 13.0
  Resolution: 1080x2340
  Manufacturer: Samsung

Phase 2: Display Specifications [SUCCESS]
  Width: 1080px
  Height: 2340px
  Density: 420dpi
  Orientation: portrait

Phase 3: Interactive Control Demo [SUCCESS]
  Tap 1/3: Center Screen (540, 960) - OK
  Tap 2/3: Top-Left (200, 400) - OK
  Tap 3/3: Bottom-Right (880, 1520) - OK
  Success Rate: 100%

Phase 4: Screenshot Capture [SUCCESS]
  File: /tmp/bluestacks-demo-2025-12-02T14:30:45Z.png
  Size: 2456 KB

Phase 5: Swipe Gesture Demo [SUCCESS]
  Swipe 1/2: UP - OK
  Swipe 2/2: DOWN - OK
  Success Rate: 100%

=== OVERALL RESULT: SUCCESS ===
Execution Time: 187 seconds
All phases completed successfully
```

---

## Custom Parameters Examples

### Example 2: Remote Bluestacks Instance (Network)

Run demo against Bluestacks on remote machine:

```bash
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "192.168.1.100:5555"
```

**Changes**:
- Connects to 192.168.1.100 instead of localhost
- All other phases identical
- Requires network connectivity to device

**Network Setup (if needed)**:
```bash
# Forward ADB connection (on host machine)
adb connect 192.168.1.100:5555
adb devices  # Verify connection
```

---

### Example 3: Custom Wait Durations (Faster)

Execute demo with shorter waits between operations:

```bash
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --tap_wait_duration 0.5 \
  --swipe_wait_duration 0.8
```

**Changes**:
- Wait 0.5 seconds between taps (instead of 1)
- Wait 0.8 seconds between swipes (instead of 1.5)

**Expected Duration**: 2-3 minutes (faster)

**Phase 3 Output**:
```
Phase 3: Interactive Control Demo [SUCCESS]
  Tap 1/3: Center Screen (540, 960) - OK [wait 0.5s]
  Tap 2/3: Top-Left (200, 400) - OK [wait 0.5s]
  Tap 3/3: Bottom-Right (880, 1520) - OK
```

---

### Example 4: Custom Screenshot Directory

Save screenshots to custom location:

```bash
# Save to home directory
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --screenshot_dir "$HOME/adb-screenshots"

# Or specific project directory
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --screenshot_dir ".moai/artifacts/screenshots"
```

**Output File Path**:
```
$HOME/adb-screenshots/bluestacks-demo-2025-12-02T14:30:45Z.png
.moai/artifacts/screenshots/bluestacks-demo-2025-12-02T14:30:45Z.png
```

---

### Example 5: Combination - Remote + Custom Waits + Custom Directory

Execute with all custom parameters:

```bash
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "192.168.1.100:5555" \
  --tap_wait_duration 0.5 \
  --swipe_wait_duration 1 \
  --screenshot_dir ".moai/reports/screenshots"
```

---

## Advanced Examples

### Example 6: Dry Run (Validation Only)

Validate workflow without executing:

```bash
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --dry-run
```

**Output**:
```
Validating workflow: bluestacks-demo.toon

Validation Results:
  ✓ Metadata valid
  ✓ Parameters valid
  ✓ Phase dependencies valid
  ✓ Loop definitions valid
  ✓ Variable substitutions valid
  ✓ Output definitions valid

Workflow is ready to execute.
Use --dry-run=false to run.
```

---

### Example 7: Specific Phase Only

Execute only Phase 1 (connection and device info):

```bash
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --phases "phase1_connection"
```

**Output**:
```
Phase 1: Connection and Device Information [SUCCESS]
  Device Model: SM-G991B (Galaxy S21)
  Android Version: 13.0
  Resolution: 1080x2340
  Manufacturer: Samsung

Skipped: Phase 2-5 (not in --phases filter)
```

---

### Example 8: With Verbose Logging

Execute with detailed logging:

```bash
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --verbose
```

**Output (Sample)**:
```
[14:30:00] Starting workflow: bluestacks-demo
[14:30:00] Device parameter: 127.0.0.1:5555
[14:30:00] Screenshot directory: /tmp
[14:30:00] Tap wait duration: 1 second
[14:30:00] Swipe wait duration: 1.5 seconds

[14:30:01] Phase 1: Connection - Starting
[14:30:01]   Step 1.1: Connect to device...
[14:30:02]   Step 1.1: Connected successfully
[14:30:02]   Step 1.2: Verify connection...
[14:30:03]   Step 1.2: Connection verified
[14:30:03]   Step 1.3: Get device info...
[14:30:04]   Step 1.3: Retrieved device model: SM-G991B
[14:30:04]   Step 1.3: Retrieved Android version: 13.0
[14:30:04]   Step 1.3: Retrieved resolution: 1080x2340
[14:30:04]   Step 1.4: Display device table...
[14:30:05] Phase 1: Connection - Completed [15 seconds]

[14:30:05] Phase 2: Display Info - Starting
...
```

---

### Example 9: With JSON Output

Generate JSON output for programmatic consumption:

```bash
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --output-format json \
  --output-file ".moai/reports/demo-result-2025-12-02.json"
```

**Output File Content** (.moai/reports/demo-result-2025-12-02.json):
```json
{
  "workflow_name": "bluestacks-demo",
  "workflow_version": "1.0.0",
  "execution_date": "2025-12-02T14:30:45Z",
  "target_device": "127.0.0.1:5555",
  "total_execution_time_seconds": 187,
  "phases_executed": [
    {
      "name": "Connection and Device Info",
      "status": "success",
      "duration": 15,
      "outputs": {
        "device_model": "SM-G991B (Galaxy S21)",
        "android_version": "13.0",
        "resolution": "1080x2340",
        "manufacturer": "Samsung"
      }
    },
    {
      "name": "Display Specifications",
      "status": "success",
      "duration": 10,
      "outputs": {
        "display_width": 1080,
        "display_height": 2340,
        "display_density": 420,
        "display_orientation": "portrait"
      }
    },
    {
      "name": "Tap Control Demo",
      "status": "success",
      "duration": 35,
      "metrics": {
        "total_taps": 3,
        "successful_taps": 3,
        "failed_taps": 0,
        "success_rate": "100%"
      }
    },
    {
      "name": "Screenshot Capture",
      "status": "success",
      "duration": 12,
      "outputs": {
        "screenshot_file": "/tmp/bluestacks-demo-2025-12-02T14:30:45Z.png",
        "file_size_bytes": 2456123
      }
    },
    {
      "name": "Swipe Gesture Demo",
      "status": "success",
      "duration": 28,
      "metrics": {
        "total_swipes": 2,
        "successful_swipes": 2,
        "failed_swipes": 0,
        "success_rate": "100%"
      }
    }
  ],
  "overall_success": true,
  "notes": "Demonstration completed successfully. All ADB operations executed on Bluestacks emulator."
}
```

---

## Error Handling Examples

### Example 10: Connection Fails - Automatic Retry

Device not available initially (will retry):

```bash
# Device initially offline, comes online after 10 seconds
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555"
```

**Behavior**:
```
Phase 1, Step 1.1: Connect to device...
  Attempt 1: FAILED (Connection refused)
  [Retry with 2 second delay]
  Attempt 2: FAILED (Connection refused)
  [Retry with 3 second delay (1.5x backoff)]
  Attempt 3: SUCCESS (Device now online)
  Continuing with Phase 1...
```

---

### Example 11: Screenshot Directory Not Writable - Skip Phase

Screenshot directory has no write permission:

```bash
# Try to save to read-only directory
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --screenshot_dir "/root/.ssl"
```

**Behavior**:
```
Phase 1-3: [SUCCESS]
Phase 4: Screenshot Capture
  Step 4.1: Take screenshot... [SUCCESS]
  Step 4.2: Verify file... [FAILED]
    Error: Cannot write to /root/.ssl (Permission denied)
    Recovery: Retry once, then skip
  [PHASE SKIPPED]

Phase 5: [SUCCESS]

Overall Result: PARTIAL SUCCESS (1 phase skipped)
```

---

### Example 12: Device Connection Lost Mid-Workflow

Device disconnects during execution:

```bash
# Device goes offline during Phase 3
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555"
```

**Behavior**:
```
Phase 1-2: [SUCCESS]
Phase 3: Tap Control Demo
  Tap 1/3: [SUCCESS]
  Tap 2/3: [FAILED - Device offline]
    Tap 3/3: [FAILED - Device offline]
  Loop recovery: Continue to next phase

Phase 4: Screenshot Capture [FAILED - Device offline]
  Recovery: Reconnect and retry
  Reconnect attempt: [SUCCESS after 3 seconds]
  Screenshot: [SUCCESS]

Phase 5: [SUCCESS]

Overall Result: PARTIAL SUCCESS (some taps failed, recovered)
Metrics:
  Phase 3 Success Rate: 33% (1/3)
  Phase 4 Success Rate: 100% (after recovery)
```

---

## Integration Examples

### Example 13: Continuous Integration (CI/CD Pipeline)

Run in CI/CD with artifact collection:

```bash
#!/bin/bash
# .github/workflows/demo.yml equivalent in bash

DEVICE="127.0.0.1:5555"
OUTPUT_DIR=".moai/ci-artifacts/demo-$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUTPUT_DIR"

# Run demo workflow
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "$DEVICE" \
  --screenshot_dir "$OUTPUT_DIR/screenshots" \
  --output-format json \
  --output-file "$OUTPUT_DIR/result.json"

# Capture exit code
EXIT_CODE=$?

# Collect artifacts
cp -r "$OUTPUT_DIR" ".moai/ci-artifacts/latest"

# Generate report
echo "Demo Execution Report
Date: $(date)
Exit Code: $EXIT_CODE
Screenshots: $OUTPUT_DIR/screenshots/
Result JSON: $OUTPUT_DIR/result.json" > "$OUTPUT_DIR/REPORT.txt"

# Exit with workflow status
exit $EXIT_CODE
```

---

### Example 14: Batch Execution (Multiple Devices)

Run demo against multiple Bluestacks instances:

```bash
#!/bin/bash
# Run demo against multiple devices sequentially

DEVICES=(
  "127.0.0.1:5555"      # Local Bluestacks instance
  "192.168.1.100:5555"   # Remote instance
  "192.168.1.101:5555"   # Another remote instance
)

RESULTS_DIR=".moai/batch-results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

for DEVICE in "${DEVICES[@]}"; do
  echo "Running demo on $DEVICE..."

  DEVICE_DIR="$RESULTS_DIR/${DEVICE//:/_}"  # Replace : with _
  mkdir -p "$DEVICE_DIR"

  moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
    --device "$DEVICE" \
    --screenshot_dir "$DEVICE_DIR/screenshots" \
    --output-format json \
    --output-file "$DEVICE_DIR/result.json"

  # Capture result
  RESULT=$?
  if [ $RESULT -eq 0 ]; then
    echo "✓ $DEVICE: SUCCESS"
  else
    echo "✗ $DEVICE: FAILED"
  fi
done

echo ""
echo "Batch Results Summary:"
echo "├── $RESULTS_DIR/127_0_0_1_5555/result.json"
echo "├── $RESULTS_DIR/192_168_1_100_5555/result.json"
echo "└── $RESULTS_DIR/192_168_1_101_5555/result.json"
```

---

### Example 15: Scheduled Execution (Cron)

Run demo daily at specific time:

```bash
# In crontab -e:
0 14 * * * /home/user/run-bluestacks-demo.sh

# Contents of run-bluestacks-demo.sh:
#!/bin/bash
cd /path/to/AdbAutoPlayer
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --screenshot_dir ".moai/daily-demos/$(date +\%Y-\%m-\%d)" \
  >> .moai/logs/demo.log 2>&1
```

**Generated Daily Reports**:
```
.moai/daily-demos/
├── 2025-12-01/
│   ├── bluestacks-demo-2025-12-01T14:00:00Z.png
│   └── result.json
├── 2025-12-02/
│   ├── bluestacks-demo-2025-12-02T14:00:00Z.png
│   └── result.json
└── 2025-12-03/
    ├── bluestacks-demo-2025-12-03T14:00:00Z.png
    └── result.json
```

---

## Troubleshooting Examples

### Example 16: Debugging Connection Issues

```bash
# Add verbose logging to diagnose connection issues
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --verbose \
  --log-level debug

# Manual diagnostic steps:
adb connect 127.0.0.1:5555
adb devices  # Check if device appears
adb shell getprop ro.product.model  # Get device model
adb shell getprop ro.build.version.release  # Get Android version
```

---

### Example 17: Testing Individual Phases

```bash
# Test Phase 1 only
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --phases "phase1_connection"

# Test Phase 3 (taps) with faster waits
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --phases "phase3_control_demo" \
  --tap_wait_duration 0.1

# Test Phase 5 (swipes) with slower waits
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --phases "phase5_swipe_demo" \
  --swipe_wait_duration 3
```

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: Complete Examples Collection
