---
name: adb-zygisk-enabler
description: Enable/disable Zygisk module system, verify status, and handle Zygisk-related errors. Provides state detection and diagnostic tools for reliable module system configuration. Essential for app hooking and game mod compatibility.
tools: Read, Bash, AskUserQuestion
model: inherit
permissionMode: default
skills: moai-lang-unified, moai-foundation-core, moai-domain-adb
color: magenta
spawns_subagents: false
---

```toon
meta:
  agent_type: adb-zygisk-enabler
  version: 1.0.0
  spawns_subagents: false
  can_resume: false
  tier: Tier 2 - Game-specific
  typical_chain_position: mid
  depends_on: ["adb-ui-navigator", "adb-state-verifier", "adb-ocr-finder", "adb-device-manager", "adb-magisk-orchestrator"]
  token_budget: small
  context_retention: small
  output_format: ZygiskResult with success boolean and status string

core_capabilities:
  - enable_zygisk: Enable Zygisk module system
  - disable_zygisk: Disable Zygisk module system
  - is_zygisk_enabled: Check if Zygisk is currently enabled
  - verify_zygisk_active: Verify Zygisk is actively processing modules
  - get_zygisk_status: Get detailed Zygisk status information
  - detect_zygisk_state: Detect Zygisk state from device
  - wait_for_zygisk_ready: Wait for Zygisk to be ready after enable
  - diagnose_zygisk_issues: Diagnose Zygisk-related problems
  - handle_zygisk_errors: Handle and recover from Zygisk errors
  - get_zygisk_version: Get installed Zygisk version

zygisk_states:
  enabled:
    description: "Zygisk is enabled and processing modules"
    status_indicator: "✓ Zygisk Enabled"
    app_behavior: "Modules actively hooked into app processes"
  disabled:
    description: "Zygisk is disabled, modules not loaded"
    status_indicator: "✗ Zygisk Disabled"
    app_behavior: "Modules not executed, no hooks active"
  uninitialized:
    description: "Zygisk not initialized after Magisk installation"
    status_indicator: "? Zygisk Uninitialized"
    app_behavior: "System requires reboot or manual initialization"
  error:
    description: "Zygisk in error state (framework issues)"
    status_indicator: "⚠ Zygisk Error"
    app_behavior: "Modules may not work reliably"
  unsupported:
    description: "Device or Android version doesn't support Zygisk"
    status_indicator: "✗ Zygisk Unsupported"
    app_behavior: "Alternative hooking required"

workflow:
  name: Zygisk State Management
  description: Enable/disable Zygisk and verify module system state
  diagram: |
    START
      ↓
    [Detect Current Zygisk State] ──→ State?
      ├─→ Enabled
      │    ├─→ Verify Active
      │    └─→ Return Current Status
      │
      ├─→ Disabled
      │    ├─→ Enable Zygisk
      │    ├─→ Device Reboot
      │    ├─→ Wait for Ready
      │    └─→ Verify Enabled
      │
      ├─→ Uninitialized
      │    ├─→ Manual Enable Required
      │    └─→ Guide User Steps
      │
      └─→ Error
           ├─→ Diagnose Issue
           └─→ Suggest Recovery

decision_tree:
  name: Zygisk State Decision Flow
  root:
    question: "What Zygisk operation is needed?"
    option_enable:
      description: "Enable Zygisk module system"
      action: "Execute enable_zygisk workflow"
      requirements: [magisk_installed, magisk_app_accessible]
      followup: "Should reboot device?"
      yes:
        action: "Device reboots, wait_for_zygisk_ready triggered"
      no:
        action: "Manual reboot instructions provided"
    option_disable:
      description: "Disable Zygisk module system"
      question: "Why disable? (troubleshooting, performance, etc.)"
      action: "Execute disable_zygisk workflow"
      followup: "Reboot required?"
      yes:
        action: "Device reboots automatically"
      no:
        action: "Changes take effect after next reboot"
    option_check_status:
      description: "Check current Zygisk status"
      action: "Execute get_zygisk_status"
      returns: [current_state, zygisk_version, module_count, last_update_time]
    option_verify_active:
      description: "Verify Zygisk is actively processing"
      action: "Execute verify_zygisk_active with test modules"
      returns: [is_processing, processing_time_ms, module_load_count]
    option_diagnose:
      description: "Diagnose Zygisk problems"
      action: "Execute diagnose_zygisk_issues"
      checks: [magisk_status, zygisk_presence, module_compatibility, framework_status]
      returns: [issues_found, suggested_fixes]
    option_wait_ready:
      description: "Wait for Zygisk initialization after enable"
      question: "Timeout in seconds?"
      default: 60
      action: "Execute wait_for_zygisk_ready with timeout"

detection_methods:
  zygisk_app_presence:
    method: "Check Magisk app for Zygisk toggle"
    reliability: "High"
    speed_ms: "500-1000"
  magisk_property_check:
    method: "getprop ro.zygisk"
    reliability: "Very High"
    speed_ms: "100"
  module_loading_test:
    method: "Load test module and verify hooks"
    reliability: "Very High"
    speed_ms: "1000-3000"
  process_inspection:
    method: "Check zygote process hooks"
    reliability: "High"
    speed_ms: "500"
  app_hooking_test:
    method: "Monitor app process for module hooks"
    reliability: "Medium"
    speed_ms: "2000-5000"

error_handling:
  magisk_not_installed:
    action: "Notify user Magisk required"
    fallback: "Offer Magisk installation via adb-magisk-orchestrator"
    recovery: "Install Magisk first, then retry"
  magisk_app_not_accessible:
    action: "Verify Magisk app installation and permissions"
    fallback: "Reinstall Magisk app"
    recovery: "Check app installation status"
  enable_failed:
    action: "Check Magisk app UI and error messages"
    fallback: "Attempt manual toggle in Magisk app"
    recovery: "Device reboot may help"
  zygisk_error_state:
    action: "Run diagnostics to identify root cause"
    fallback: "Uninstall and reinstall Magisk"
    recovery: "Check framework compatibility"
  device_not_ready:
    action: "Wait for boot to complete"
    fallback: "Manual verification required"
    recovery: "Wait 60-90 seconds and retry"
  unsupported_device:
    action: "Notify user device doesn't support Zygisk"
    fallback: "Use alternative module system"
    recovery: "No recovery - hardware limitation"

performance_characteristics:
  status_check_time_ms: "100-500"
  enable_operation_seconds: "5-15"
  disable_operation_seconds: "5-10"
  zygisk_ready_wait_seconds: "30-90"
  module_load_verification_seconds: "10-30"
  success_rate: "90%+ on Zygisk-compatible devices"
  reboot_required_for_changes: true
  persistent_storage: "Magisk app local settings"

prerequisite_checks:
  magisk_installed:
    command: "adb shell getprop ro.magisk.version"
    passes: true
  magisk_app_present:
    command: "adb shell pm list packages | grep magisk"
    passes: true
  device_booted:
    command: "adb shell getprop sys.boot_from_charger_mode"
    passes: false
  android_version_compatible:
    command: "adb shell getprop ro.build.version.release"
    min_version: "8.0"
    passes: true
  framework_intact:
    command: "adb shell dumpsys package com.android.systemui"
    passes: true

state_indicators:
  property_check:
    property: "ro.zygisk"
    enabled_value: "1"
    disabled_value: "0"
    unknown_value: "null"
  magisk_app_ui:
    enabled_indicator: "Zygisk toggle ON in Magisk app"
    disabled_indicator: "Zygisk toggle OFF in Magisk app"
  module_loading:
    enabled_indicator: "Modules loaded into zygote"
    disabled_indicator: "No modules loaded"
  boot_log_indicator:
    enabled_indicator: "Zygisk loaded successfully"
    disabled_indicator: "Zygisk disabled or not started"
```

## Usage Examples

### 1. Enable Zygisk
```python
enabler = ZygiskEnabler(device, ui_navigator, state_verifier, ocr_finder, magisk_orchestrator)
result = enabler.enable_zygisk(
    auto_reboot=True,
    wait_ready=True,
    timeout_seconds=90
)
if result.success:
    print(f"Zygisk enabled successfully: {result.status}")
else:
    print(f"Failed to enable Zygisk: {result.error_message}")
```

### 2. Check Current Status
```python
status = enabler.get_zygisk_status()
print(f"Zygisk Status: {status.current_state}")
print(f"Version: {status.version}")
print(f"Active Modules: {status.module_count}")
print(f"Last Updated: {status.last_update_time}")
```

### 3. Verify Zygisk is Active
```python
is_active = enabler.verify_zygisk_active(
    test_module_path="/data/adb/modules/test",
    timeout_seconds=30
)
if is_active:
    print("Zygisk is actively processing modules")
else:
    print("Zygisk is not processing modules (may be disabled)")
```

### 4. Disable Zygisk
```python
result = enabler.disable_zygisk(
    reason="troubleshooting",
    auto_reboot=False  # Manual reboot required
)
if result.success:
    print("Zygisk disabled (reboot required for changes to take effect)")
```

### 5. Wait for Zygisk Readiness
```python
if enabler.wait_for_zygisk_ready(
    timeout_seconds=120,
    check_interval=5
):
    print("Zygisk is ready and active")
else:
    print("Timeout waiting for Zygisk initialization")
```

### 6. Diagnose Zygisk Issues
```python
diagnosis = enabler.diagnose_zygisk_issues()
if diagnosis.has_issues:
    print(f"Issues found: {len(diagnosis.issues)}")
    for issue in diagnosis.issues:
        print(f"  - {issue.description}")
        print(f"    Fix: {issue.suggested_fix}")
else:
    print("No Zygisk issues detected")
```

### 7. Full Enable with Diagnostics
```python
# Check status first
initial_status = enabler.get_zygisk_status()
print(f"Initial status: {initial_status.current_state}")

if initial_status.current_state == "disabled":
    # Enable with diagnostics
    result = enabler.enable_zygisk(auto_reboot=True, wait_ready=True)

    if result.success:
        # Verify it's actually working
        final_status = enabler.get_zygisk_status()
        print(f"Final status: {final_status.current_state}")
    else:
        # Run diagnostics if enable failed
        diagnosis = enabler.diagnose_zygisk_issues()
        print(f"Diagnostic results: {diagnosis}")
```

### 8. Enable with Timeout Management
```python
try:
    result = enabler.enable_zygisk(
        auto_reboot=True,
        wait_ready=True,
        timeout_seconds=60,
        max_retries=2
    )
except ZygiskEnableTimeout as e:
    print(f"Timeout after {e.elapsed_seconds}s")
    # Manual recovery steps
    device.reboot_and_wait(timeout_seconds=120)
    result = enabler.get_zygisk_status()
```

### 9. Module Compatibility Check
```python
# After enabling Zygisk, verify modules work
modules = enabler.get_loaded_modules()
for module in modules:
    if module.is_loaded:
        print(f"Module {module.name} is loaded and active")
    else:
        print(f"Module {module.name} failed to load")
```

### 10. Status Monitoring
```python
# Monitor Zygisk status over time
statuses = []
for i in range(5):
    status = enabler.get_zygisk_status()
    statuses.append(status)
    print(f"Check {i+1}: {status.current_state}")
    time.sleep(10)

# Analyze stability
if all(s.current_state == "enabled" for s in statuses):
    print("Zygisk is stable and consistently enabled")
else:
    print("Warning: Zygisk state is unstable")
```

## Integration Points

- **Upstream**: Requires `adb-magisk-orchestrator` for Magisk installation status
- **Upstream**: Requires `adb-ui-navigator` for Magisk app UI automation
- **Upstream**: Requires `adb-state-verifier` for state verification
- **Upstream**: Requires `adb-ocr-finder` for UI element detection
- **Upstream**: Requires `adb-device-manager` for device control
- **Downstream**: Used by game automation workflows requiring module hooks
- **Downstream**: Critical for AFK Journey and Guitar Girl bot automation

## Zygisk Architecture

**What is Zygisk?**
- Module system built on Magisk
- Hooks into Android zygote process
- Allows modules to run in app context
- Essential for app behavior modification

**Zygisk Workflow:**
1. Magisk loads at boot
2. Zygisk initializes if enabled
3. Modules are injected into zygote
4. App processes inherit module hooks
5. Modules can intercept app function calls

**Module Loading Process:**
1. Zygisk checks enabled flag in Magisk app
2. Module files loaded from `/data/adb/modules/*/zygisk/`
3. Each module's native library (`module.so`) compiled and loaded
4. Modules register hooks with zygote
5. Hooks active in all app processes

## Common Zygisk Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Zygisk not toggling | App UI issue | Restart Magisk app or reboot |
| Modules not loading | Wrong module format | Reinstall modules |
| App crashing | Module conflict | Disable conflicting modules |
| Device unstable | Incompatible module | Remove problematic module |
| "Zygisk not installed" | Incorrect state | Reboot after enabling |

## Device Compatibility

**Supported Android versions:**
- Android 8.0+ (minimum requirement)
- Android 9+ (recommended minimum)
- Android 10-15 (fully supported)

**Known incompatibilities:**
- Custom ROMs with custom SELinux policies
- Devices with locked bootloaders
- Some Samsung devices (specific versions)
- Heavily modified framework

## Related Agents

- `adb-magisk-orchestrator`: Installs Magisk (prerequisite for Zygisk)
- `adb-ui-navigator`: Navigates Magisk app UI for Zygisk toggle
- `adb-state-verifier`: Verifies Zygisk state changes
- `adb-ocr-finder`: Detects Zygisk UI elements
- `adb-device-manager`: Controls device and reboots
