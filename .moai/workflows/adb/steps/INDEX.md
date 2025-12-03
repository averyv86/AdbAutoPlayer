# ADB Workflow Steps - Complete Index

**Quick Navigation**: All 12 steps organized by category with links and quick reference.

---

## Connection Steps

### 1. Connect to Device
**File**: `connection/connect.yaml`  
**ID**: `adb-connect`  
**Lines**: 70

**Quick Reference**:
```yaml
step_id: adb-connect
params:
  device: "127.0.0.1:5555"      # Device IP:port or serial
  timeout: 10                     # Connection timeout (seconds)
  port: 5555                      # ADB port
```

**Outputs**: device_id, connection_status, device_model, android_version

---

### 2. Disconnect from Device
**File**: `connection/disconnect.yaml`  
**ID**: `adb-disconnect`  
**Lines**: 61

**Quick Reference**:
```yaml
step_id: adb-disconnect
params:
  device: ""                      # Empty = all devices
  force: false                    # Force disconnect
  kill_daemon: false              # Kill ADB daemon
```

**Outputs**: disconnected_devices, disconnect_status, daemon_status

---

### 3. Verify Connection
**File**: `connection/verify-connection.yaml`  
**ID**: `adb-verify-connection`  
**Lines**: 79

**Quick Reference**:
```yaml
step_id: adb-verify-connection
params:
  device: ""                      # Empty = all devices
  detailed: true                  # Include detailed info
  timeout: 5                      # Health check timeout
```

**Outputs**: device_list, connection_status, device_count, device_details

---

## Control Steps

### 4. Tap Screen
**File**: `control/tap.yaml`  
**ID**: `adb-tap`  
**Lines**: 84

**Quick Reference**:
```yaml
step_id: adb-tap
params:
  device: ""
  x: 500                          # X coordinate
  y: 1000                         # Y coordinate
  count: 1                        # Number of taps
  delay: 100                      # Delay between taps (ms)
```

**Outputs**: tap_status, taps_performed, coordinates, duration_ms

---

### 5. Swipe Screen
**File**: `control/swipe.yaml`  
**ID**: `adb-swipe`  
**Lines**: 102

**Quick Reference**:
```yaml
step_id: adb-swipe
params:
  device: ""
  x1: 500                         # Start X
  y1: 1800                        # Start Y
  x2: 500                         # End X
  y2: 500                         # End Y
  duration: 500                   # Swipe duration (ms)
  direction: "custom"             # up/down/left/right/custom
```

**Outputs**: swipe_status, start_coords, end_coords, duration_ms, distance_pixels

---

### 6. Type Text
**File**: `control/type-text.yaml`  
**ID**: `adb-type-text`  
**Lines**: 74

**Quick Reference**:
```yaml
step_id: adb-type-text
params:
  device: ""
  text: "Hello World"             # Text to type
  delay: 50                       # Delay between chars (ms)
  clear_field: false              # Clear field before typing
```

**Outputs**: input_status, characters_sent, text_sent, duration_ms

---

### 7. Press Key
**File**: `control/press-key.yaml`  
**ID**: `adb-press-key`  
**Lines**: 106

**Quick Reference**:
```yaml
step_id: adb-press-key
params:
  device: ""
  key: "BACK"                     # BACK, HOME, POWER, MENU, VOLUME_UP,
                                  # VOLUME_DOWN, ENTER, TAB, ESCAPE, DELETE
  count: 1                        # Number of presses
  delay: 100                      # Delay between presses (ms)
```

**Outputs**: key_press_status, key_pressed, presses_performed, duration_ms

---

## Capture Steps

### 8. Take Screenshot
**File**: `capture/screenshot.yaml`  
**ID**: `adb-screenshot`  
**Lines**: 83

**Quick Reference**:
```yaml
step_id: adb-screenshot
params:
  device: ""
  output_path: ""                 # Save path (empty = temp)
  format: "png"                   # png, jpg, webp
  quality: 95                     # Quality 0-100 (lossy formats)
```

**Outputs**: screenshot_status, file_path, file_size_bytes, resolution, capture_timestamp

---

### 9. Get Device Info
**File**: `capture/get-device-info.yaml`  
**ID**: `adb-get-device-info`  
**Lines**: 92

**Quick Reference**:
```yaml
step_id: adb-get-device-info
params:
  device: ""
  detailed: true                  # Include detailed specs
  timeout: 10                     # Command timeout
```

**Outputs**: device_id, model, manufacturer, android_version, api_level, hardware_specs, device_features

---

### 10. Get Display Info
**File**: `capture/get-display-info.yaml`  
**ID**: `adb-get-display-info`  
**Lines**: 87

**Quick Reference**:
```yaml
step_id: adb-get-display-info
params:
  device: ""
  timeout: 5                      # Command timeout
```

**Outputs**: resolution, density_dpi, density_category, orientation, refresh_rate, physical_size, screen_state, brightness_level

---

## Validation Steps

### 11. Check Device Status
**File**: `validation/check-device-status.yaml`  
**ID**: `adb-check-device-status`  
**Lines**: 117

**Quick Reference**:
```yaml
step_id: adb-check-device-status
params:
  device: ""
  check_services: true            # Check services
  check_battery: true             # Check battery
  check_storage: true             # Check storage
```

**Outputs**: overall_status, connectivity_status, battery_status, storage_status, memory_status, services_status, warnings

---

### 12. Verify App Running
**File**: `validation/verify-app-running.yaml`  
**ID**: `adb-verify-app-running`  
**Lines**: 98

**Quick Reference**:
```yaml
step_id: adb-verify-app-running
params:
  device: ""
  package_name: "com.example.app"  # Required: app package
  activity: ""                     # Optional: specific activity
  timeout: 10                      # Check timeout
```

**Outputs**: app_status, is_running, current_activity, process_id, memory_usage_mb, foreground, installed, version_info

---

## Statistics

| Category | Count | Lines | Most Complex |
|----------|-------|-------|--------------|
| Connection | 3 | 210 | verify-connection (79) |
| Control | 4 | 366 | press-key (106) |
| Capture | 3 | 262 | get-device-info (92) |
| Validation | 2 | 215 | check-device-status (117) |
| **Total** | **12** | **1,053** | **check-device-status** |

---

## By Lines of Code

Largest to Smallest:

1. check-device-status.yaml - 117 lines (Validation)
2. press-key.yaml - 106 lines (Control)
3. swipe.yaml - 102 lines (Control)
4. verify-app-running.yaml - 98 lines (Validation)
5. get-device-info.yaml - 92 lines (Capture)
6. get-display-info.yaml - 87 lines (Capture)
7. tap.yaml - 84 lines (Control)
8. screenshot.yaml - 83 lines (Capture)
9. verify-connection.yaml - 79 lines (Connection)
10. type-text.yaml - 74 lines (Control)
11. connect.yaml - 70 lines (Connection)
12. disconnect.yaml - 61 lines (Connection)

---

## Parameter Quick Reference

| Parameter | Steps Using | Type | Default |
|-----------|------------|------|---------|
| device | 11 | string | "" |
| timeout | 8 | integer | 5-10 |
| detailed | 3 | boolean | true |
| x, y | tap, swipe | integer | - |
| x1, y1, x2, y2 | swipe | integer | - |
| text | type-text | string | - |
| key | press-key | string | - |
| package_name | verify-app | string | - |
| output_path | screenshot | string | "" |
| format | screenshot | string | "png" |
| quality | screenshot | integer | 95 |

---

## Success Patterns by Category

**Connection**: "Connected successfully" | "device connected"  
**Control**: "successful" | "completed"  
**Capture**: "captured" | "saved"  
**Validation**: "Status: (healthy|warning|critical)"

---

## Common Workflows

### Login Flow
```
adb-connect → adb-tap → adb-type-text → 
adb-tap → adb-type-text → adb-tap → adb-verify-app-running
```

### Device Diagnostics
```
adb-connect → adb-get-device-info → 
adb-check-device-status → adb-get-display-info
```

### Visual Testing
```
adb-connect → adb-screenshot → adb-tap → 
adb-swipe → adb-screenshot → adb-disconnect
```

### App Verification
```
adb-connect → adb-verify-app-running → 
adb-check-device-status → adb-disconnect
```

---

## File Locations

```
.moai/workflows/adb/
├── steps/
│   ├── connection/
│   │   ├── connect.yaml
│   │   ├── disconnect.yaml
│   │   └── verify-connection.yaml
│   ├── control/
│   │   ├── tap.yaml
│   │   ├── swipe.yaml
│   │   ├── type-text.yaml
│   │   └── press-key.yaml
│   ├── capture/
│   │   ├── screenshot.yaml
│   │   ├── get-device-info.yaml
│   │   └── get-display-info.yaml
│   └── validation/
│       ├── check-device-status.yaml
│       └── verify-app-running.yaml
├── README.md           (Full documentation)
├── MANIFEST.md         (Project manifest)
└── INDEX.md            (This file)
```

---

**Index Version**: 1.0.0  
**Last Updated**: 2025-12-02  
**Total Steps Indexed**: 12/12
