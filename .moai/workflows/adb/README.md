# ADB Workflow Steps Library

Complete reusable workflow step library for Android Device Bridge (ADB) automation. This library provides 12 YAML step definitions organized by category for building complex ADB automation workflows.

**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Total Steps**: 12 across 4 categories

---

## Quick Reference (30 seconds)

The ADB Workflow Steps Library contains **12 step definitions** for automating Android device interactions via ADB:

| Category | Steps | Purpose |
|----------|-------|---------|
| **Connection** | 3 | Device connection management |
| **Control** | 4 | Screen and input control |
| **Capture** | 3 | Screen and device information capture |
| **Validation** | 2 | Device and application status checks |

**Quick Start**:
```yaml
- name: Tap Device
  step_id: adb-tap
  params:
    device: "127.0.0.1:5555"
    x: 500
    y: 1000
```

---

## Directory Structure

```
.moai/workflows/adb/
├── steps/
│   ├── connection/
│   │   ├── connect.yaml                    # Connect to device
│   │   ├── disconnect.yaml                 # Disconnect from device
│   │   └── verify-connection.yaml          # Verify connection status
│   ├── control/
│   │   ├── tap.yaml                        # Tap screen at coordinates
│   │   ├── swipe.yaml                      # Swipe gesture
│   │   ├── type-text.yaml                  # Input text
│   │   └── press-key.yaml                  # Press hardware key
│   ├── capture/
│   │   ├── screenshot.yaml                 # Capture screen
│   │   ├── get-device-info.yaml            # Get device information
│   │   └── get-display-info.yaml           # Get display information
│   └── validation/
│       ├── check-device-status.yaml        # Check overall device status
│       └── verify-app-running.yaml         # Check if app is running
└── README.md                               # Documentation (this file)
```

---

## Implementation Guide (5 minutes)

### Using Steps in Workflows

Each YAML step file contains all necessary information for execution. To use a step in a workflow:

**1. Reference Step by ID**:
```yaml
workflow:
  name: mobile-automation
  steps:
    - name: Connect Device
      step_id: adb-connect
      params:
        device: "127.0.0.1:5555"
        timeout: 10
```

**2. Step Structure**:
Each step file contains:
- **id**: Unique step identifier
- **name**: Human-readable step name
- **description**: What the step does
- **category**: Organization category
- **parameters**: Input parameters with types and defaults
- **action**: Script path and argument mapping
- **success_criteria**: How to determine successful execution
- **error_handling**: Retry logic and error recovery
- **outputs**: What the step returns
- **validation**: Input validation rules

---

## Step Categories

### 1. Connection Steps (3 steps)

Handle device connection and disconnection over ADB.

#### connect.yaml
**Purpose**: Establish ADB connection to device

**Parameters**:
- `device` - Device IP:port or serial
- `timeout` - Connection timeout in seconds
- `port` - ADB port

**Outputs**: device_id, connection_status, device_model, android_version

#### disconnect.yaml
**Purpose**: Terminate ADB connection from device

**Parameters**:
- `device` - Device identifier (empty = all)
- `force` - Force disconnect
- `kill_daemon` - Kill ADB daemon

**Outputs**: disconnected_devices, disconnect_status, daemon_status

#### verify-connection.yaml
**Purpose**: Check status and health of ADB connection

**Parameters**:
- `device` - Device identifier
- `detailed` - Include detailed information
- `timeout` - Health check timeout

**Outputs**: device_list, connection_status, device_count, device_details

---

### 2. Control Steps (4 steps)

Simulate user input and control device interactions.

#### tap.yaml
**Purpose**: Simulate touch tap at coordinates

**Parameters**:
- `device` - Device identifier
- `x`, `y` - Tap coordinates
- `count` - Number of taps
- `delay` - Delay between taps

**Outputs**: tap_status, taps_performed, coordinates, duration_ms

#### swipe.yaml
**Purpose**: Simulate touch swipe gesture

**Parameters**:
- `device` - Device identifier
- `x1`, `y1` - Starting coordinates
- `x2`, `y2` - Ending coordinates
- `duration` - Swipe duration
- `direction` - Direction hint

**Outputs**: swipe_status, start_coords, end_coords, duration_ms, distance_pixels

#### type-text.yaml
**Purpose**: Send text input to device

**Parameters**:
- `device` - Device identifier
- `text` - Text to type
- `delay` - Delay between chars
- `clear_field` - Clear field before typing

**Outputs**: input_status, characters_sent, text_sent, duration_ms

#### press-key.yaml
**Purpose**: Simulate hardware key press

**Supported Keys**: BACK, HOME, POWER, MENU, VOLUME_UP, VOLUME_DOWN, ENTER, TAB, ESCAPE, DELETE

**Parameters**:
- `device` - Device identifier
- `key` - Key name
- `count` - Number of presses
- `delay` - Delay between presses

**Outputs**: key_press_status, key_pressed, presses_performed, duration_ms

---

### 3. Capture Steps (3 steps)

Capture screen and device information.

#### screenshot.yaml
**Purpose**: Capture device screen screenshot

**Parameters**:
- `device` - Device identifier
- `output_path` - Path to save screenshot
- `format` - Image format (png/jpg/webp)
- `quality` - Quality for lossy formats

**Outputs**: screenshot_status, file_path, file_size_bytes, resolution, capture_timestamp

#### get-device-info.yaml
**Purpose**: Retrieve detailed device information

**Parameters**:
- `device` - Device identifier
- `detailed` - Include full details
- `timeout` - Command timeout

**Outputs**: device_id, model, manufacturer, android_version, api_level, hardware_specs, device_features

#### get-display-info.yaml
**Purpose**: Retrieve current display information

**Parameters**:
- `device` - Device identifier
- `timeout` - Command timeout

**Outputs**: resolution, density_dpi, density_category, orientation, refresh_rate, physical_size, screen_state, brightness_level

---

### 4. Validation Steps (2 steps)

Check device and application status.

#### check-device-status.yaml
**Purpose**: Comprehensive device status check

**Parameters**:
- `device` - Device identifier
- `check_services` - Check services
- `check_battery` - Check battery
- `check_storage` - Check storage

**Outputs**: overall_status, connectivity_status, battery_status, storage_status, memory_status, services_status, warnings

#### verify-app-running.yaml
**Purpose**: Check if specified application is running

**Parameters**:
- `device` - Device identifier
- `package_name` - App package name
- `activity` - Specific activity (optional)
- `timeout` - Check timeout

**Outputs**: app_status, is_running, current_activity, process_id, memory_usage_mb, foreground, installed, version_info

---

## Variable Substitution

Parameters use `{{ variable_name }}` syntax for substitution:

```yaml
parameters:
  - name: device
  - name: x

action:
  args: ["--device", "{{ device }}", "--x", "{{ x }}"]
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Device error |
| 2 | Input error |
| 3 | Operation error |

---

## Building Complete Workflows

Example workflow combining multiple steps:

```yaml
name: Mobile App Login
steps:
  - step_id: adb-connect
    params:
      device: "127.0.0.1:5555"
  - step_id: adb-screenshot
    params:
      output_path: ".moai/screenshots/before.png"
  - step_id: adb-tap
    params:
      x: 500
      y: 400
  - step_id: adb-type-text
    params:
      text: "testuser@example.com"
  - step_id: adb-verify-app-running
    params:
      package_name: "com.example.myapp"
```

---

## Performance Characteristics

| Step | Duration | Notes |
|------|----------|-------|
| connect | 2-5s | Network dependent |
| tap | 100ms | Single touch |
| swipe | 500-1000ms | Duration dependent |
| type-text | 100-500ms | Character count dependent |
| screenshot | 1-2s | Resolution dependent |
| get-device-info | 2-3s | Property collection |
| check-device-status | 3-5s | Multiple checks |

---

## Works Well With

- `expert-mobile` - Mobile automation specialists
- `manager-automation` - Automation workflow orchestration
- `moai-domain-adb` - Core ADB functionality
- `/moai:2-run` - Execute workflows with TDD
- `/moai:3-sync` - Sync automation results

---

## Troubleshooting

**Device Not Found**: Check device IP/port and connectivity
**Coordinates Out of Bounds**: Verify screen resolution with get-display-info step
**Text Input Not Working**: Tap field first to focus it
**Connection Timeout**: Enable USB Debugging on device

---

**Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: Production Ready
**Total Files**: 12 YAML step definitions + 1 README
