# Bluestacks Demonstration Workflow Guide

**File**: `.moai/workflows/adb/demos/bluestacks-demo.toon`
**Version**: 1.0.0
**Status**: Complete and Ready
**Last Updated**: 2025-12-02

---

## Overview

The Bluestacks demonstration workflow is a comprehensive TOON v4.0 (YAML-based) workflow that demonstrates ADB device interaction capabilities with the Bluestacks Android emulator. It executes 5 sequential phases covering connection, device info retrieval, screen control, screenshot capture, and gesture simulation.

## Quick Start

### Execute the Workflow
```bash
# Using MoAI-ADK CLI
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon --device "127.0.0.1:5555"

# With custom parameters
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --screenshot_dir "/tmp/screenshots" \
  --tap_wait_duration 1 \
  --swipe_wait_duration 1.5
```

### Expected Duration
- Total: ~3-5 minutes
- Per Phase: 30-60 seconds average

---

## Workflow Structure (5 Phases)

### Phase 1: Connection and Device Information (Sequence 1)

**Purpose**: Establish ADB connection and retrieve device metadata.

**Steps**:
1. **step_1_1_connect** - Connect to Bluestacks device
   - Action: Execute `connect.yaml` step
   - Parameters: device IP:port, 10-second timeout
   - Success Criteria: Connection status returned, device recognized
   - Retry: 3 attempts with 2-second delay on failure

2. **step_1_2_verify_connection** - Verify connection stability
   - Action: Run `verify-connection.py` script
   - Validates: Device responsiveness
   - Abort on failure: Yes

3. **step_1_3_get_device_info** - Retrieve device metadata
   - Action: Run `get-device-info.py` script
   - Outputs: device_model, android_version, resolution, manufacturer
   - Format: JSON for parsing

4. **step_1_4_display_device_table** - Display device info
   - Action: Format as human-readable table
   - Shows: Model, Android Version, Resolution, Manufacturer

**Checkpoint**: YES (can be resumed from here)

---

### Phase 2: Display Specifications (Sequence 2)

**Purpose**: Retrieve and display screen specifications.

**Steps**:
1. **step_2_1_get_display_info** - Get display specifications
   - Action: Run `get-display-info.py` script
   - Outputs: width, height, density, orientation
   - Format: JSON for parsing

2. **step_2_2_display_specs_table** - Display specifications
   - Action: Format as human-readable table
   - Shows: Width (px), Height (px), Density (dpi), Orientation

**Depends On**: Phase 1 (connection must succeed)

**Checkpoint**: YES

---

### Phase 3: Interactive Control Demonstration (Sequence 3)

**Purpose**: Demonstrate tap commands at various screen locations using loop-based execution.

**Loop Structure**:
```yaml
loop:
  type: items
  count: 3
  items:
    - id: tap_1
      description: "Center Screen Tap"
      x: 540
      y: 960
    - id: tap_2
      description: "Top-Left Corner Tap"
      x: 200
      y: 400
    - id: tap_3
      description: "Bottom-Right Corner Tap"
      x: 880
      y: 1520
```

**Loop Steps**:
1. **loop_tap_step** - Execute tap at coordinates
   - Action: Run `tap.py` script with x, y coordinates
   - Template Variables: `{{ item.x }}`, `{{ item.y }}`
   - Duration: 100ms per tap
   - Error Handling: Continue on failure, log warnings

2. **loop_wait_between_taps** - Wait between taps
   - Action: Sleep for `{{ parameters.tap_wait_duration }}` seconds
   - Condition: Only wait if not last iteration
   - Default: 1 second

**Metrics**:
- `total_taps`: 3 (loop.total)
- `successful_taps`: Number of successful iterations
- `failed_taps`: Number of failed iterations

**Depends On**: Phase 2

**Checkpoint**: YES

---

### Phase 4: Screenshot Capture (Sequence 4)

**Purpose**: Capture device screen and verify screenshot file.

**Steps**:
1. **step_4_1_take_screenshot** - Capture screenshot
   - Action: Run `screenshot.py` script
   - Output: `{{ parameters.screenshot_dir }}/bluestacks-demo-{{ workflow.timestamp }}.png`
   - Format: PNG
   - Timeout: 10 seconds

2. **step_4_2_verify_screenshot** - Verify screenshot file
   - Action: File existence and readability check
   - Minimum Size: 1000 bytes

3. **step_4_3_display_screenshot** - Display screenshot
   - Action: Render image in output
   - Title: "Bluestacks Screenshot - Demo Phase 4"
   - Width: 50% of display

**Outputs**:
- `screenshot_path`: Path to saved PNG file
- `screenshot_size`: File size in bytes

**Depends On**: Phase 3

**Checkpoint**: YES

---

### Phase 5: Swipe Gesture Demonstration (Sequence 5)

**Purpose**: Demonstrate swipe gestures in different directions using loop-based execution.

**Loop Structure**:
```yaml
loop:
  type: items
  count: 2
  items:
    - id: swipe_1
      direction: "up"
      start_y: 1400
      end_y: 600
      x_coordinate: 540
      description: "Upward swipe (scroll down)"
    - id: swipe_2
      direction: "down"
      start_y: 600
      end_y: 1400
      x_coordinate: 540
      description: "Downward swipe (scroll up)"
```

**Loop Steps**:
1. **loop_swipe_step** - Execute swipe gesture
   - Action: Run `swipe.py` script with direction
   - Template Variables: `{{ item.direction }}`, `{{ item.x_coordinate }}`, `{{ item.start_y }}`, `{{ item.end_y }}`
   - Duration: 500ms per swipe
   - Error Handling: Continue on failure, log

2. **loop_wait_between_swipes** - Wait between swipes
   - Action: Sleep for `{{ parameters.swipe_wait_duration }}` seconds
   - Condition: Only wait if not last iteration
   - Default: 1.5 seconds

**Metrics**:
- `total_swipes`: 2 (loop.total)
- `successful_swipes`: Number of successful iterations
- `failed_swipes`: Number of failed iterations

**Depends On**: Phase 4

**Checkpoint**: YES

---

## TOON Syntax and Variable Substitution

### Template Variables

**System Variables**:
- `{{ parameters.device }}` - Device IP:port parameter
- `{{ parameters.screenshot_dir }}` - Screenshot directory
- `{{ parameters.tap_wait_duration }}` - Wait duration between taps
- `{{ parameters.swipe_wait_duration }}` - Wait duration between swipes
- `{{ workflow.timestamp }}` - Current timestamp (YYYY-MM-DD-HH:mm:ss)
- `{{ project-root }}` - Project root directory

**Phase Output Variables**:
- `{{ phase1.outputs.device_model }}` - Device model from Phase 1
- `{{ phase1.outputs.android_version }}` - Android version from Phase 1
- `{{ phase1.outputs.resolution }}` - Device resolution from Phase 1
- `{{ phase1.outputs.manufacturer }}` - Device manufacturer from Phase 1
- `{{ phase2.outputs.display_width }}` - Display width from Phase 2
- `{{ phase2.outputs.display_height }}` - Display height from Phase 2
- `{{ phase2.outputs.display_density }}` - Display density from Phase 2
- `{{ phase2.outputs.display_orientation }}` - Display orientation from Phase 2
- `{{ phase4.outputs.screenshot_path }}` - Screenshot file path from Phase 4
- `{{ phase4.outputs.screenshot_size }}` - Screenshot file size from Phase 4

**Loop Variables**:
- `{{ item.id }}` - Current item ID (tap_1, tap_2, tap_3, swipe_1, swipe_2)
- `{{ item.description }}` - Item human-readable description
- `{{ item.x }}` - X coordinate (Phase 3)
- `{{ item.y }}` - Y coordinate (Phase 3)
- `{{ item.direction }}` - Swipe direction (Phase 5)
- `{{ item.start_y }}` - Swipe start Y (Phase 5)
- `{{ item.end_y }}` - Swipe end Y (Phase 5)
- `{{ item.x_coordinate }}` - Swipe X coordinate (Phase 5)
- `{{ loop.index }}` - Current iteration number (1-based)
- `{{ loop.total }}` - Total iterations

### Loop Syntax Examples

**Phase 3 Loop - Tap Demonstration**:
```yaml
loop:
  type: items
  count: 3
  items:
    - id: tap_1
      description: "Center Screen Tap"
      x: 540
      y: 960
```

**Variable Substitution**:
```
Iteration 1: tap_1 at (540, 960) - "Center Screen Tap"
Iteration 2: tap_2 at (200, 400) - "Top-Left Corner Tap"
Iteration 3: tap_3 at (880, 1520) - "Bottom-Right Corner Tap"
```

**Phase 5 Loop - Swipe Demonstration**:
```yaml
loop:
  type: items
  count: 2
  items:
    - id: swipe_1
      direction: "up"
      start_y: 1400
      end_y: 600
```

**Variable Substitution**:
```
Iteration 1: swipe_1 - Upward from y=1400 to y=600
Iteration 2: swipe_2 - Downward from y=600 to y=1400
```

---

## Expected Execution Output

### Phase 1 Output
```
=== PHASE 1: Connection and Device Information ===
[✓] step_1_1_connect: Connected to 127.0.0.1:5555
[✓] step_1_2_verify_connection: Connection verified
[✓] step_1_3_get_device_info: Device info retrieved

Bluestacks Device Information
┌──────────────────┬─────────────────────────┐
│ Model            │ SM-G991B (Galaxy S21)   │
│ Android Version  │ 13.0                    │
│ Resolution       │ 1080x2340               │
│ Manufacturer     │ Samsung                 │
└──────────────────┴─────────────────────────┘
```

### Phase 2 Output
```
=== PHASE 2: Display Specifications ===
[✓] step_2_1_get_display_info: Display info retrieved
[✓] step_2_2_display_specs_table: Display specifications

Display Specifications
┌─────────────┬────────┐
│ Width       │ 1080px │
│ Height      │ 2340px │
│ Density     │ 420dpi │
│ Orientation │ portrait│
└─────────────┴────────┘
```

### Phase 3 Output
```
=== PHASE 3: Interactive Control Demonstration ===
Loop: 3 items
[✓] Iteration 1/3: Tap at (540, 960) - Center Screen Tap
    └─ Wait 1 second
[✓] Iteration 2/3: Tap at (200, 400) - Top-Left Corner Tap
    └─ Wait 1 second
[✓] Iteration 3/3: Tap at (880, 1520) - Bottom-Right Corner Tap

Metrics:
  Total Taps: 3
  Successful: 3 (100%)
  Failed: 0
```

### Phase 4 Output
```
=== PHASE 4: Screenshot Capture ===
[✓] step_4_1_take_screenshot: Screenshot captured
    └─ Path: /tmp/bluestacks-demo-2025-12-02-14-30-45.png
    └─ Size: 2,456,123 bytes
[✓] step_4_2_verify_screenshot: File verified
[✓] step_4_3_display_screenshot: Displaying image...

[Image displayed: Bluestacks Screenshot - Demo Phase 4]
```

### Phase 5 Output
```
=== PHASE 5: Swipe Gesture Demonstration ===
Loop: 2 items
[✓] Iteration 1/2: UP Swipe at x=540 (1400→600)
    └─ Duration: 500ms
    └─ Wait 1.5 seconds
[✓] Iteration 2/2: DOWN Swipe at x=540 (600→1400)
    └─ Duration: 500ms

Metrics:
  Total Swipes: 2
  Successful: 2 (100%)
  Failed: 0
```

### Final Summary Output
```json
{
  "workflow_name": "bluestacks-demo",
  "workflow_version": "1.0.0",
  "execution_date": "2025-12-02T14:30:45Z",
  "target_device": "127.0.0.1:5555",
  "total_execution_time_seconds": 180,
  "phases_executed": [
    {
      "name": "Connection and Device Info",
      "status": "success",
      "duration": 15
    },
    {
      "name": "Display Specifications",
      "status": "success",
      "duration": 10
    },
    {
      "name": "Tap Control Demo",
      "status": "success",
      "duration": 35,
      "taps_executed": "3/3"
    },
    {
      "name": "Screenshot Capture",
      "status": "success",
      "duration": 12,
      "screenshot_file": "/tmp/bluestacks-demo-2025-12-02-14-30-45.png"
    },
    {
      "name": "Swipe Gesture Demo",
      "status": "success",
      "duration": 28,
      "swipes_executed": "2/2"
    }
  ],
  "overall_success": true,
  "notes": "Demonstration completed successfully. All ADB operations executed on Bluestacks emulator."
}
```

---

## File Locations and References

### Main Workflow File
- **Location**: `.moai/workflows/adb/demos/bluestacks-demo.toon`
- **Format**: TOON v4.0 (YAML-based)
- **Size**: ~550 lines
- **Encoding**: UTF-8

### Supporting Step Files (Referenced)
- `.moai/workflows/adb/steps/connection/connect.yaml` - Connection step definition
- `.moai/workflows/adb/steps/connection/verify-connection.yaml` - Verification step
- `.moai/workflows/adb/steps/capture/get-device-info.yaml` - Device info retrieval
- `.moai/workflows/adb/steps/capture/get-display-info.yaml` - Display info retrieval
- `.moai/workflows/adb/steps/capture/screenshot.yaml` - Screenshot capture
- `.moai/workflows/adb/steps/control/tap.yaml` - Tap control step
- `.moai/workflows/adb/steps/control/swipe.yaml` - Swipe control step

### Script Files (Referenced)
- `.claude/skills/moai-domain-adb/scripts/connection/connect.py`
- `.claude/skills/moai-domain-adb/scripts/connection/disconnect.py`
- `.claude/skills/moai-domain-adb/scripts/validation/verify-connection.py`
- `.claude/skills/moai-domain-adb/scripts/capture/get-device-info.py`
- `.claude/skills/moai-domain-adb/scripts/capture/get-display-info.py`
- `.claude/skills/moai-domain-adb/scripts/capture/screenshot.py`
- `.claude/skills/moai-domain-adb/scripts/control/tap.py`
- `.claude/skills/moai-domain-adb/scripts/control/swipe.py`

### Output Locations
- Screenshots: `{{ parameters.screenshot_dir }}/bluestacks-demo-{{ timestamp }}.png`
- Report: `.moai/workflows/adb/demos/outputs/bluestacks-demo-report-{{ timestamp }}.md`

---

## Customization Examples

### Change Tap Locations
Edit Phase 3 loop items to use different coordinates:
```yaml
items:
  - id: tap_1
    x: 100          # New X coordinate
    y: 200          # New Y coordinate
    description: "Custom Location 1"
```

### Add Additional Taps
Increase loop count and add items:
```yaml
loop:
  count: 5          # Now 5 taps instead of 3
  items:
    - id: tap_1
      x: 540
      y: 960
    - id: tap_2
      x: 200
      y: 400
    - id: tap_3
      x: 880
      y: 1520
    - id: tap_4
      x: 400
      y: 800
    - id: tap_5
      x: 700
      y: 1200
```

### Adjust Wait Durations
```bash
# Run with custom waits
moai run workflow bluestacks-demo.toon \
  --tap_wait_duration 2 \
  --swipe_wait_duration 3
```

### Use Different Device
```bash
# Connect to different Bluestacks instance
moai run workflow bluestacks-demo.toon \
  --device "192.168.1.100:5555"
```

### Custom Screenshot Directory
```bash
# Save screenshots to custom location
moai run workflow bluestacks-demo.toon \
  --screenshot_dir "/home/user/screenshots"
```

---

## TOON v4.0 Features Used

### 1. Hierarchical YAML Structure
- Metadata section with version and categorization
- Parameter definitions with defaults
- 5-phase sequential workflow definition

### 2. Runtime Variable Substitution
- `{{ parameters.* }}` - Parameter values
- `{{ phase*.outputs.* }}` - Phase output values
- `{{ workflow.timestamp }}` - System variables
- `{{ item.* }}` - Loop item variables
- `{{ loop.* }}` - Loop context variables

### 3. Loop-Based Execution
- **Phase 3**: 3-item loop for tap demonstration
- **Phase 5**: 2-item loop for swipe demonstration
- Automatic iteration tracking with `{{ loop.index }}` and `{{ loop.total }}`

### 4. Conditional Execution
- `condition: "{{ loop.index < loop.total }}"` - Wait only between iterations
- Phase dependencies: `depends_on: ["phase2_display_info"]`

### 5. Error Handling and Recovery
- Retry strategy: 3 attempts with exponential backoff
- Failure actions: Abort, continue, or log warnings
- Rollback capabilities at checkpoint phases

### 6. Output Aggregation
- Phase-specific outputs: device info, display specs, metrics
- Structured JSON summary with all results
- Human-readable table formatting

### 7. Validation Rules
- Device parameter format validation (IP:port regex)
- Directory existence and permissions checks
- Phase success rate validation (≥80% required)

---

## Best Practices

1. **Always Verify Connection First**: Phase 1 validates device connectivity before proceeding.

2. **Handle Failures Gracefully**: Loop steps continue on failure instead of aborting.

3. **Use Checkpoints**: All 5 phases have checkpoints for resumable execution.

4. **Log All Actions**: Each step logs success/failure for debugging.

5. **Save Artifacts**: Screenshots are timestamped and saved for review.

6. **Validate Outputs**: File existence checks and metric validation ensure quality.

---

## Troubleshooting

### Connection Fails
```
Error: Device not found at 127.0.0.1:5555
Solution: Verify Bluestacks is running and ADB is enabled
  1. Check Bluestacks status: adb devices
  2. Reconnect: adb connect 127.0.0.1:5555
  3. Re-run workflow
```

### Screenshot Capture Fails
```
Error: Screenshot output directory not writable
Solution: Check directory permissions
  1. Verify directory exists: ls -la /tmp/
  2. Check write permissions: chmod 755 /tmp/
  3. Specify different directory: --screenshot_dir "/home/user/screenshots"
```

### Loop Iterations Skip
```
Error: Some tap/swipe iterations fail
Solution: This is expected - workflow continues on failure
  1. Check logs for which iterations failed
  2. Manually verify device screen state
  3. Re-run workflow (device state may have changed)
```

---

## References

- **TOON Specification**: `.claude/skills/moai-library-toon/`
- **ADB Skills**: `.claude/skills/moai-domain-adb/`
- **MoAI Foundation**: `.claude/skills/moai-foundation-core/`
- **Workflow Patterns**: `.moai/workflows/adb/`

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: Complete and Ready for Use
