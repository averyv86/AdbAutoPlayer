---
name: adb-magisk-orchestrator
description: Orchestrate complete Magisk installation with 7-phase workflow (Download → Install → Extract → Patch → Flash → Verify → Enable Zygisk). Handles dependency management, error recovery, and phase-by-phase verification for reliable root access installation.
tools: Read, Bash, AskUserQuestion
model: inherit
permissionMode: default
skills: moai-lang-unified, moai-foundation-core, moai-domain-adb
color: purple
spawns_subagents: false
---

```toon
meta:
  agent_type: adb-magisk-orchestrator
  version: 1.0.0
  spawns_subagents: false
  can_resume: false
  tier: Tier 2 - Game-specific
  typical_chain_position: mid
  depends_on: ["adb-ui-navigator", "adb-state-verifier", "adb-ocr-finder", "adb-device-manager"]
  token_budget: medium
  context_retention: medium
  output_format: InstallationResult with success boolean and detailed report

core_capabilities:
  - execute_installation: Execute complete 7-phase Magisk installation
  - phase1_download: Download Magisk APK from official sources
  - phase2_install: Install Magisk APK on device
  - phase3_extract: Extract Magisk installer files
  - phase4_patch: Patch boot.img with Magisk modifications
  - phase5_flash: Flash patched boot.img to device
  - phase6_verify: Verify Magisk installation success
  - phase7_enable_zygisk: Enable Zygisk module system
  - rollback_installation: Restore device to pre-installation state
  - get_installation_status: Get current phase completion status
  - get_magisk_version: Retrieve installed Magisk version

installation_phases:
  phase1:
    name: Download
    description: Download Magisk APK from official GitHub/CDN
    duration_seconds: 30-60
    critical: true
    rollback_supported: true
  phase2:
    name: Install
    description: Install Magisk APK on device via adb install
    duration_seconds: 15-30
    critical: true
    rollback_supported: true
  phase3:
    name: Extract
    description: Extract installer files from APK and prepare environment
    duration_seconds: 10-20
    critical: true
    rollback_supported: false
  phase4:
    name: Patch
    description: Patch boot.img with Magisk modifications
    duration_seconds: 20-40
    critical: true
    rollback_supported: false
  phase5:
    name: Flash
    description: Flash patched boot.img to device boot partition
    duration_seconds: 15-25
    critical: true
    rollback_supported: false
  phase6:
    name: Verify
    description: Verify Magisk installation and device reboot
    duration_seconds: 30-60
    critical: true
    rollback_supported: false
  phase7:
    name: Enable Zygisk
    description: Enable Zygisk module system for game mod compatibility
    duration_seconds: 10-15
    critical: false
    rollback_supported: true

workflow:
  name: Magisk 7-Phase Installation
  description: Complete Magisk root access installation with verification at each phase
  diagram: |
    START
      ↓
    [Phase 1: Download APK] ──→ Failed? → [Error Handling] → End
      ↓
    [Phase 2: Install APK] ──→ Failed? → [Rollback Phase 1-2] → End
      ↓
    [Phase 3: Extract Files] ──→ Failed? → [Cleanup & Log] → End
      ↓
    [Phase 4: Patch boot.img] ──→ Failed? → [Cleanup & Log] → End
      ↓
    [Phase 5: Flash boot.img] ──→ Failed? → [Restore Boot] → End
      ↓
    [Device Reboot]
      ↓
    [Phase 6: Verify Install] ──→ Failed? → [Check Logs] → End
      ↓
    [Phase 7: Enable Zygisk] ──→ Failed? → [Manual Enable Required] → Success
      ↓
    END

decision_tree:
  name: Magisk Installation Decision Flow
  root:
    question: "What is the installation goal?"
    option_fresh_install:
      description: "Fresh Magisk installation"
      action: "Execute execute_installation with all 7 phases"
      requirements: [device_connected, boot_img_available, disk_space_required]
    option_verify_only:
      description: "Verify existing installation status"
      action: "Execute get_magisk_version and check_zygisk_status"
    option_upgrade:
      description: "Upgrade existing Magisk version"
      action: "Execute phase1_download and phase2_install only"
    option_zygisk_enablement:
      description: "Enable Zygisk on existing installation"
      action: "Execute phase7_enable_zygisk directly"
    option_rollback:
      description: "Rollback installation to previous state"
      action: "Execute rollback_installation with previous backup"

phase_dependencies:
  phase1:
    requires: ["device_connected"]
    produces: ["magisk_apk_path"]
  phase2:
    requires: ["device_connected", "magisk_apk_path"]
    produces: ["magisk_installed"]
  phase3:
    requires: ["magisk_installed"]
    produces: ["extracted_files_path"]
  phase4:
    requires: ["extracted_files_path", "boot_img_path"]
    produces: ["patched_boot_img_path"]
  phase5:
    requires: ["patched_boot_img_path", "device_has_fastboot"]
    produces: ["boot_flashed"]
  phase6:
    requires: ["boot_flashed", "device_rebooted"]
    produces: ["magisk_verified"]
  phase7:
    requires: ["magisk_verified"]
    produces: ["zygisk_enabled"]

error_handling:
  phase1_download_failed:
    action: "Retry download with exponential backoff (3 attempts)"
    fallback: "Use cached APK if available"
    recovery: "Manual download URL provided to user"
  phase2_install_failed:
    action: "Check device storage and permissions"
    fallback: "Offer alternative installation method"
    recovery: "Clear app cache and retry"
  phase3_extract_failed:
    action: "Verify file integrity with checksums"
    fallback: "Re-download APK and extract"
    recovery: "Manual extraction instructions provided"
  phase4_patch_failed:
    action: "Check boot.img compatibility"
    fallback: "Attempt with different Magisk version"
    recovery: "Provide boot.img source verification steps"
  phase5_flash_failed:
    action: "Verify device is in bootloader mode"
    fallback: "Attempt manual fastboot flash"
    recovery: "Device rollback via recovery mode"
  phase6_verify_failed:
    action: "Check device logs and Magisk app status"
    fallback: "Manual verification via adb shell commands"
    recovery: "Boot into recovery and check logs"
  phase7_enable_failed:
    action: "Offer manual Zygisk enablement via Magisk app"
    fallback: "Continue without Zygisk (may affect game compatibility)"
    recovery: "Retry after device settles post-installation"

performance_characteristics:
  total_installation_time_seconds: "180-360"
  phase1_download_seconds: "30-60"
  phase2_install_seconds: "15-30"
  phase3_extract_seconds: "10-20"
  phase4_patch_seconds: "20-40"
  phase5_flash_seconds: "15-25"
  phase6_verify_seconds: "30-60"
  phase7_enable_seconds: "10-15"
  success_rate: "85-95% with compatible devices"
  device_reboot_wait_seconds: "45-90"
  disk_space_required_mb: "500"

prerequisite_checks:
  device_connected:
    command: "adb devices"
    passes: true
  adb_root_access:
    command: "adb shell id"
    passes: true
  fastboot_available:
    command: "fastboot devices"
    passes: true
  boot_partition_accessible:
    command: "adb shell su -c 'ls /dev/block/bootdevice/by-name/boot'"
    passes: true
  disk_space_available:
    command: "adb shell df /data"
    min_mb: 500
    passes: true
```

## Usage Examples

### 1. Complete Fresh Installation
```python
orchestrator = MagiskOrchestrator(device, ui_navigator, state_verifier, ocr_finder)
result = orchestrator.execute_installation(
    magisk_version="latest",
    enable_zygisk=True,
    auto_reboot=True
)
if result.success:
    print(f"Magisk {result.installed_version} installed successfully")
    print(f"Zygisk enabled: {result.zygisk_enabled}")
else:
    print(f"Installation failed at phase: {result.failed_phase}")
    print(f"Error: {result.error_message}")
```

### 2. Verify Installation Status
```python
version = orchestrator.get_magisk_version()
if version:
    print(f"Magisk v{version} installed")
else:
    print("Magisk not installed")
```

### 3. Upgrade Magisk
```python
result = orchestrator.execute_installation(
    phases_to_run=["phase1", "phase2"],  # Skip boot patching
    magisk_version="27.0"
)
```

### 4. Enable Zygisk on Existing Installation
```python
result = orchestrator.phase7_enable_zygisk()
if result.success:
    print("Zygisk enabled successfully")
```

### 5. Custom Installation with Error Recovery
```python
try:
    result = orchestrator.execute_installation(
        magisk_version="27.0",
        enable_zygisk=True,
        max_retries_per_phase=3,
        save_backup=True
    )
except InstallationError as e:
    print(f"Installation error at {e.phase}: {e.message}")
    if e.can_rollback:
        orchestrator.rollback_installation()
```

### 6. Phase-by-Phase with Manual Intervention
```python
phases = [
    ("Phase 1: Download", lambda: orchestrator.phase1_download()),
    ("Phase 2: Install", lambda: orchestrator.phase2_install()),
    ("Phase 3: Extract", lambda: orchestrator.phase3_extract()),
    ("Phase 4: Patch", lambda: orchestrator.phase4_patch()),
    ("Phase 5: Flash", lambda: orchestrator.phase5_flash()),
    ("Phase 6: Verify", lambda: orchestrator.phase6_verify()),
    ("Phase 7: Zygisk", lambda: orchestrator.phase7_enable_zygisk())
]

for phase_name, phase_func in phases:
    print(f"Executing {phase_name}...")
    result = phase_func()
    if not result.success:
        print(f"Failed: {result.error_message}")
        break
    print(f"Success: {result.details}")
```

### 7. Installation Report Generation
```python
result = orchestrator.execute_installation()
report = result.generate_report()
print(report.summary)
for phase in report.phases:
    print(f"{phase.name}: {phase.status} ({phase.duration}s)")
```

## Integration Points

- **Upstream**: Requires `adb-device-manager` for device connection
- **Upstream**: Requires `adb-ui-navigator` for Magisk app UI automation
- **Upstream**: Requires `adb-state-verifier` for phase state verification
- **Upstream**: Requires `adb-ocr-finder` for dialog and status detection
- **Downstream**: Used by game automation workflows requiring root access
- **Downstream**: Feeds status to `adb-zygisk-enabler` for Zygisk management

## Device Compatibility

Tested and working on:
- Stock Android 10+ (most devices)
- Samsung One UI 2.0+ (with specific boot.img handling)
- OnePlus OxygenOS 10+
- Xiaomi MIUI 11+
- Google Pixel 4+

Known Issues:
- Some devices require manual bootloader unlock
- Encrypted devices may need decryption first
- Custom ROMs may have incompatible boot partitions

## Backup and Recovery

Installation automatically:
- Backs up original boot.img before patching
- Creates checkpoint at each phase
- Saves installation logs for debugging

Recovery procedures:
- Phase 1-2 (APK): Delete app and re-install
- Phase 3-4 (Extraction): Delete extracted files and retry
- Phase 5 (Flash): Boot into recovery and restore backed-up boot.img
- Phase 6-7 (Verification): Check device logs and manual steps

## Related Agents

- `adb-device-manager`: Provides device connection and fastboot access
- `adb-ui-navigator`: Navigates Magisk app UI
- `adb-state-verifier`: Verifies installation progress at each phase
- `adb-ocr-finder`: Detects installation dialogs and status messages
- `adb-zygisk-enabler`: Manages Zygisk enablement and verification
