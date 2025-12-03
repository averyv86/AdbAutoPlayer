# ADB Bluestacks Demonstration Workflows

**Directory**: `.moai/workflows/adb/demos/`
**Status**: Ready for Production
**Last Updated**: 2025-12-02

---

## Overview

This directory contains demonstration workflows for testing and validating ADB device interactions with the Bluestacks Android emulator. The workflows showcase ADB capabilities including connection management, device information retrieval, screen control, gesture simulation, and screenshot capture.

## Files

### Primary Workflow File

**`bluestacks-demo.toon`** (550 lines)
- **Format**: TOON v4.0 (YAML-based hierarchical)
- **Purpose**: Complete demonstration of ADB device interaction
- **Phases**: 5 sequential phases with checkpoints
- **Duration**: ~3-5 minutes
- **Status**: Production Ready

#### Phases Included:
1. **Phase 1: Connection and Device Information** - Connect and retrieve device metadata
2. **Phase 2: Display Specifications** - Get screen specifications
3. **Phase 3: Interactive Control Demo** - Loop-based tap demonstration (3 locations)
4. **Phase 4: Screenshot Capture** - Capture and save device screenshot
5. **Phase 5: Swipe Gesture Demo** - Loop-based swipe demonstration (2 directions)

### Documentation Files

**`BLUESTACKS-DEMO-GUIDE.md`** (350 lines)
- **Purpose**: Complete user guide for the workflow
- **Contents**:
  - Quick start instructions
  - Detailed phase-by-phase explanation
  - TOON syntax and variable substitution
  - Expected output examples
  - File locations and references
  - Customization examples
  - TOON v4.0 features used
  - Best practices
  - Troubleshooting guide

**`TOON-SYNTAX-REFERENCE.md`** (500 lines)
- **Purpose**: Technical reference for TOON v4.0 format
- **Contents**:
  - Document structure and sections
  - Metadata definitions
  - Configuration references and variable resolution
  - Parameter definitions
  - Phase definitions with sequential and loop-based execution
  - Loop structure and loop variables
  - Output variables and metrics
  - Validation rules
  - Recovery strategies
  - Variable substitution examples
  - Complete Phase 3 example with execution trace
  - TOON syntax cheat sheet
  - Token efficiency analysis
  - Best practices

**`EXECUTION-EXAMPLES.md`** (450 lines)
- **Purpose**: Practical execution examples for various scenarios
- **Contents**:
  - Quick start examples
  - Custom parameter examples
  - Advanced examples (dry-run, specific phases, verbose)
  - Integration examples (CI/CD, batch, scheduled)
  - Error handling examples
  - Troubleshooting examples
  - 17 complete working examples

**`README.md`** (this file)
- **Purpose**: Directory overview and quick reference

---

## Quick Start

### Basic Execution
```bash
# Execute workflow with default Bluestacks instance
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon
```

### With Custom Device
```bash
# Execute on remote Bluestacks instance
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "192.168.1.100:5555"
```

### With Custom Parameters
```bash
# Execute with all custom settings
moai run workflow .moai/workflows/adb/demos/bluestacks-demo.toon \
  --device "127.0.0.1:5555" \
  --screenshot_dir ".moai/screenshots" \
  --tap_wait_duration 0.5 \
  --swipe_wait_duration 1
```

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `device` | string | `127.0.0.1:5555` | Bluestacks device IP:port |
| `screenshot_dir` | string | `/tmp` | Directory for screenshot output |
| `tap_wait_duration` | integer | `1` | Wait duration between taps (seconds) |
| `swipe_wait_duration` | integer | `1.5` | Wait duration between swipes (seconds) |
| `demo_duration` | integer | `15` | Approximate demo duration (seconds) |

---

## Workflow Structure

### 5 Sequential Phases with Checkpoints

```
Phase 1: Connection ──┐
                      ├─→ Phase 2: Display Info ──┐
                                                   ├─→ Phase 3: Taps (Loop) ──┐
                                                                               ├─→ Phase 4: Screenshot ──┐
                                                                                                        ├─→ Phase 5: Swipes (Loop)
                                                                                                        ├─→ Validation
                                                                                                        └─→ Output Summary
```

### Phase Features

**Phase 1**: Sequential steps
- Connect to device
- Verify connection
- Get device info
- Display as table
- Checkpoint: YES

**Phase 2**: Sequential steps
- Get display info
- Display as table
- Depends on: Phase 1
- Checkpoint: YES

**Phase 3**: Loop-based iteration
- 3 tap locations (center, top-left, bottom-right)
- Wait 1 second between taps (configurable)
- Loop Variables: `{{ item.x }}`, `{{ item.y }}`
- Metrics: total_taps, successful_taps, failed_taps
- Error Handling: Continue on failure
- Checkpoint: YES

**Phase 4**: Sequential steps
- Take screenshot
- Verify file
- Display image
- Depends on: Phase 3
- Checkpoint: YES

**Phase 5**: Loop-based iteration
- 2 swipe directions (up, down)
- Wait 1.5 seconds between swipes (configurable)
- Loop Variables: `{{ item.direction }}`, `{{ item.start_y }}`, `{{ item.end_y }}`
- Metrics: total_swipes, successful_swipes, failed_swipes
- Error Handling: Continue on failure
- Checkpoint: YES

---

## TOON v4.0 Features Demonstrated

### 1. Hierarchical Structure
- Metadata section with categorization
- Parameter definitions
- 5-phase sequential workflow

### 2. Runtime Variable Substitution
- `{{ parameters.* }}` - Input parameters
- `{{ phase*.outputs.* }}` - Phase results
- `{{ item.* }}` - Loop item values
- `{{ loop.* }}` - Loop context (index, total)
- `{{ workflow.timestamp }}` - System variables

### 3. Loop-Based Execution
```yaml
loop:
  type: items
  count: 3
  items:
    - id: tap_1
      x: 540
      y: 960
```

### 4. Conditional Execution
```yaml
condition: "{{ loop.index < loop.total }}"  # Skip wait on last iteration
```

### 5. Phase Dependencies
```yaml
depends_on: ["phase2_display_info"]  # Cannot start until Phase 2 succeeds
```

### 6. Error Handling and Recovery
```yaml
retry_strategy:
  max_attempts: 3
  backoff_multiplier: 1.5
  initial_delay_seconds: 2
```

### 7. Validation Rules
```yaml
validation:
  conditions:
    - name: "device_parameter_valid"
      pattern: "^(\\d{1,3}\\.){3}\\d{1,3}:\\d{4,5}$"
```

### 8. Output Aggregation
```yaml
outputs:
  demo_summary:
    format: json
    content:
      phases_executed: [ ... ]
      overall_success: true
```

---

## Expected Output

### Summary
```
=== BLUESTACKS DEMONSTRATION WORKFLOW ===
Target Device: 127.0.0.1:5555
Start Time: 2025-12-02T14:30:00Z

Phase 1: Connection and Device Information [✓ SUCCESS] (15s)
  Device Model: SM-G991B (Galaxy S21)
  Android Version: 13.0
  Resolution: 1080x2340

Phase 2: Display Specifications [✓ SUCCESS] (10s)
  Width: 1080px
  Height: 2340px
  Density: 420dpi

Phase 3: Interactive Control Demo [✓ SUCCESS] (35s)
  Taps: 3/3 (100%)

Phase 4: Screenshot Capture [✓ SUCCESS] (12s)
  File: /tmp/bluestacks-demo-2025-12-02T14:30:45Z.png

Phase 5: Swipe Gesture Demo [✓ SUCCESS] (28s)
  Swipes: 2/2 (100%)

=== OVERALL RESULT: SUCCESS ===
Execution Time: 3m 27s
All phases completed successfully
```

---

## File Locations

### Workflow Directory
```
.moai/workflows/adb/demos/
├── README.md                           ← This file
├── bluestacks-demo.toon                ← Main workflow
├── BLUESTACKS-DEMO-GUIDE.md            ← User guide
├── TOON-SYNTAX-REFERENCE.md            ← Technical reference
├── EXECUTION-EXAMPLES.md               ← Usage examples
└── outputs/                            ← Generated reports (created on run)
```

### Step Definitions (referenced by workflow)
```
.moai/workflows/adb/steps/
├── connection/
│   └── connect.yaml                    ← Connection step
├── capture/
│   ├── get-device-info.yaml
│   ├── get-display-info.yaml
│   └── screenshot.yaml
├── control/
│   ├── tap.yaml
│   └── swipe.yaml
└── validation/
    └── verify-connection.yaml
```

### Scripts (referenced by workflow)
```
.claude/skills/moai-domain-adb/scripts/
├── connection/
│   ├── connect.py
│   └── disconnect.py
├── capture/
│   ├── get-device-info.py
│   ├── get-display-info.py
│   └── screenshot.py
├── control/
│   ├── tap.py
│   └── swipe.py
└── validation/
    └── verify-connection.py
```

---

## Documentation Map

```
Start Here
    ↓
README.md (this file)
    ↓
Choose Your Path:
  ├─→ Quick Start → BLUESTACKS-DEMO-GUIDE.md
  │                 (Understand the workflow)
  │
  ├─→ Want Examples → EXECUTION-EXAMPLES.md
  │                   (17 working examples)
  │
  └─→ Technical Deep Dive → TOON-SYNTAX-REFERENCE.md
                             (Complete TOON v4.0 reference)
```

---

## Common Tasks

### Run Basic Demo
See: BLUESTACKS-DEMO-GUIDE.md → Quick Start

### Customize Parameters
See: EXECUTION-EXAMPLES.md → Custom Parameters Examples

### Debug Issues
See: BLUESTACKS-DEMO-GUIDE.md → Troubleshooting

### Run in CI/CD
See: EXECUTION-EXAMPLES.md → Integration Examples

### Understand Loop Syntax
See: TOON-SYNTAX-REFERENCE.md → Section 5: Loop-Based Execution

### Add More Tap Locations
See: BLUESTACKS-DEMO-GUIDE.md → Customization Examples

---

## Requirements

- **Bluestacks**: Installed and running
- **ADB**: Android Debug Bridge with TCP/IP enabled
- **MoAI-ADK**: Project tools available
- **Network**: Connection to target device (localhost or network)
- **Permissions**: Write access to screenshot directory

### Verify Setup
```bash
# Check ADB
adb devices  # Should list connected devices

# Check Bluestacks
adb connect 127.0.0.1:5555
adb devices  # Should show Bluestacks device

# Check permissions
ls -la /tmp  # Verify write access
```

---

## Features

✅ **5 Sequential Phases**: Connected workflow from setup to testing
✅ **Loop-Based Execution**: 3 tap locations + 2 swipe directions
✅ **Checkpoints**: Resume from any phase
✅ **Error Recovery**: Automatic retry with exponential backoff
✅ **Flexible Parameters**: Device, directories, wait durations
✅ **Rich Output**: Tables, JSON, screenshots
✅ **Comprehensive Logging**: Trace every action
✅ **Production Ready**: Full error handling and validation

---

## TOON v4.0 Advantages

- **40-60% Token Reduction** vs JSON
- **Clean YAML Format** - Easy to read and modify
- **Full Variable Substitution** - Dynamic values throughout
- **Loop Support** - Iterative execution with context
- **Hierarchical Structure** - Logical organization
- **LLM-Parseable** - AI-friendly format

---

## Resources

| Resource | File | Lines | Purpose |
|----------|------|-------|---------|
| Workflow | `bluestacks-demo.toon` | 550 | Main workflow definition |
| User Guide | `BLUESTACKS-DEMO-GUIDE.md` | 350 | How to use and customize |
| Technical Ref | `TOON-SYNTAX-REFERENCE.md` | 500 | TOON v4.0 format reference |
| Examples | `EXECUTION-EXAMPLES.md` | 450 | 17 practical examples |
| Overview | `README.md` | 200 | This file |
| **Total** | | **2,050** | Complete documentation set |

---

## Support and Issues

For issues or questions:

1. **Check BLUESTACKS-DEMO-GUIDE.md** - Troubleshooting section
2. **Review EXECUTION-EXAMPLES.md** - Similar examples
3. **Consult TOON-SYNTAX-REFERENCE.md** - Technical details
4. **Manual Testing**:
   ```bash
   adb connect 127.0.0.1:5555
   adb shell getprop ro.product.model
   ```

---

## License

Part of AdbAutoPlayer project. See project LICENSE for details.

---

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2025-12-02
**Author**: MoAI-ADK
