# Workflow: Complete Magisk Installation

**Workflow File**: `magisk-complete-install.toon`
**Version**: 1.0.0
**Category**: System Installation
**Difficulty**: Advanced
**Estimated Duration**: 15 minutes

---

## Purpose

Complete end-to-end Magisk system installation that transforms a device from `Installed: N/A` (app installed but not system-integrated) to `Installed: Yes` (Magisk fully integrated with system boot image).

This workflow handles:
1. Downloading Magisk APK from GitHub
2. Installing the app on device
3. Extracting the device's boot image
4. Patching the boot image via Magisk
5. Flashing the patched boot back to device
6. Verifying successful installation

---

## Prerequisites

### Device Requirements
- ✅ USB debugging enabled
- ✅ ADB connection established (`adb devices` shows device)
- ✅ Fastboot access available
- ✅ Boot loader unlocked (may be required for flashing)
- ✅ At least 1GB free storage on device
- ✅ At least 500MB free storage on host machine

### Host Requirements
- ✅ `adb` command available in PATH
- ✅ `fastboot` command available in PATH
- ✅ Python 3.12+ for scripts
- ✅ `uv` tool installed
- ✅ Network access to GitHub (for downloads)

### Software Versions
- ✅ Magisk v30.0+ recommended
- ✅ Android 5.0+ on device
- ✅ ADB protocol version 31+

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `device` | string | `127.0.0.1:5555` | Target device ID or ADB connection |
| `version` | string | `latest` | Magisk version (latest or 30.6, 30.5, etc.) |
| `output_dir` | string | `/tmp/magisk` | Directory for downloads and files |
| `timeout_download` | integer | 60 | Download timeout (seconds) |
| `timeout_install` | integer | 60 | App install timeout (seconds) |
| `timeout_extract` | integer | 30 | Boot extraction timeout (seconds) |
| `timeout_patch` | integer | 120 | Boot patching timeout (seconds) |
| `timeout_flash` | integer | 120 | Boot flashing timeout (seconds) |

---

## Workflow Phases

### Phase 1: Download Magisk Files
**Duration**: 2-3 minutes

Downloads Magisk APK and boot image files from GitHub releases.

**Actions**:
- Query GitHub API for release information
- Download Magisk-v{version}.apk
- Download boot image if available
- Store files in `{{ output_dir }}`

**Success Criteria**:
- ✅ APK file exists and is > 5MB
- ✅ Both files successfully downloaded
- ✅ No network errors during download

**Failure Handling**:
- Retry download up to 2 times
- Wait 5 seconds between retries
- Abort if both attempts fail

---

### Phase 2: Install Magisk Manager App
**Duration**: 1-2 minutes

Push APK to device and install via standard Android package manager.

**Actions**:
- Check if APK exists locally
- Push APK to device via adb
- Install using `adb install -r` (force replace)
- Verify app installed via pm
- Launch app and wait for "Modules" text to appear

**Success Criteria**:
- ✅ `adb install` returns success
- ✅ Package manager lists `com.topjohnwu.magisk`
- ✅ Magisk app launches and shows Modules tab
- ✅ App is responsive and UI loads

**Failure Handling**:
- Retry installation up to 2 times
- Wait 5 seconds between retries
- Abort if app won't install

---

### Phase 3: Extract Boot Image from Device
**Duration**: 30-60 seconds

Pull the current boot partition from device for patching.

**Actions**:
- Detect active boot partition (boot_a or boot_b)
- Pull `/dev/block/by-name/{partition}` via adb
- Save to `{{ output_dir }}/boot.img`
- Verify file size and integrity

**Success Criteria**:
- ✅ Boot image file created
- ✅ File size > 1MB (typically 8-16MB)
- ✅ File integrity verified

**Failure Handling**:
- May fail on devices with unusual boot structures
- Continue to next phase if this fails (user can manually patch)
- Log error for troubleshooting

---

### Phase 4: Push Boot Image to Device Storage
**Duration**: 30-60 seconds

Copy boot image to device `/sdcard` for Magisk app to patch.

**Actions**:
- Push `boot.img` from host to device `/sdcard/boot.img`
- Verify file exists on device
- Ensure permissions are readable

**Success Criteria**:
- ✅ File pushed successfully
- ✅ File readable from device storage

---

### Phase 5: Patch Boot Image via Magisk
**Duration**: 2-3 minutes

Use Magisk Manager app to patch the boot image.

**Actions**:
1. Launch Magisk Manager app
2. Tap "Install" button (in Modules or Home tab)
3. Wait for file selector to appear
4. Select `/sdcard/boot.img`
5. Confirm patching
6. Wait for "Patching complete" message
7. Magisk generates `magisk_patched_[random].img`

**Success Criteria**:
- ✅ File selector appears
- ✅ Boot file selection succeeds
- ✅ Patching process starts
- ✅ "Patching complete" text appears within timeout

**Manual Intervention**:
- User may need to interact with Magisk app file picker
- If file selector doesn't open, workflow pauses for manual action
- User should select boot.img from /sdcard

**Failure Handling**:
- Screenshot captured on error
- Workflow pauses for user to review Magisk app state
- User can proceed manually or retry

---

### Phase 6: Download Patched Boot Image
**Duration**: 30-60 seconds

Pull the patched boot image from device back to host.

**Actions**:
- Find patched boot image in `/sdcard/Download/magisk_patched_*.img`
- Pull file to `{{ output_dir }}/patched_boot.img`
- Verify file integrity

**Success Criteria**:
- ✅ Patched image file found
- ✅ File pulled successfully
- ✅ File size matches original (~8-16MB)

---

### Phase 7: Reboot to Fastboot Mode
**Duration**: 30 seconds

Reboot device into fastboot mode for boot flashing.

**Actions**:
- Execute `adb reboot fastboot`
- Wait for device to appear in fastboot
- Verify fastboot connection

**Success Criteria**:
- ✅ Device disappears from adb
- ✅ Device appears in fastboot
- ✅ Fastboot connection established within 30 seconds

---

### Phase 8: Flash Patched Boot Image
**Duration**: 1-2 minutes

Flash the patched boot image to device boot partition via fastboot.

**Actions**:
1. Verify patched boot file integrity
2. Execute `fastboot flash boot patched_boot.img`
3. Monitor flash progress
4. Verify flash completion
5. Reboot device from fastboot

**Success Criteria**:
- ✅ Fastboot flash returns success
- ✅ "Finished" message from fastboot
- ✅ Device reboots

**Failure Handling**:
- Device may bootloop if flash fails
- Screenshot captured on error
- User may need to flash original boot to recover
- See Troubleshooting section

---

### Phase 9: Verify Magisk Installation
**Duration**: 1-2 minutes

Confirm device boot with Magisk integrated (Installed: Yes).

**Actions**:
1. Wait for device to fully boot
2. Launch Magisk Manager app
3. Wait for "Installed" text to appear
4. Verify Zygisk tab is available
5. Confirm installation status

**Success Criteria**:
- ✅ Device boots successfully
- ✅ Magisk app launches
- ✅ "Installed: Yes" shown in Magisk
- ✅ Zygisk menu available

---

## Execution Example

### Basic Execution

```bash
# Run workflow on default device with latest Magisk
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflow/magisk-complete-install.toon \
    --param device=127.0.0.1:5555
```

### Specific Version

```bash
# Install Magisk v30.6 specifically
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflow/magisk-complete-install.toon \
    --param device=127.0.0.1:5555 \
    --param version=30.6
```

### Custom Output Directory

```bash
# Use custom directory for files
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflow/magisk-complete-install.toon \
    --param device=127.0.0.1:5555 \
    --param output_dir=/home/user/magisk-files
```

### Extended Timeouts

```bash
# Use longer timeouts for slow network/devices
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflow/magisk-complete-install.toon \
    --param device=127.0.0.1:5555 \
    --param timeout_download=120 \
    --param timeout_patch=180
```

---

## Success Criteria

Workflow is successful when:

1. ✅ All phases complete without abort
2. ✅ Device shows "Installed: Yes" in Magisk app
3. ✅ Device boots without bootloops after Phase 8
4. ✅ Magisk app is responsive with all modules visible
5. ✅ Zygisk can be enabled for API hooking

---

## Error Handling

### Common Errors and Recovery

| Error | Phase | Cause | Recovery |
|-------|-------|-------|----------|
| Download timeout | 1 | Slow network | Increase timeout_download parameter |
| APK install fails | 2 | Insufficient storage | Free up device storage |
| Boot extraction fails | 3 | Unsupported partition | May fail on custom ROMs |
| Patching fails | 5 | Boot image incompatibility | Check Magisk version compatibility |
| Flash fails | 8 | Locked bootloader | Unlock bootloader in device settings |
| Bootloop after flash | 8 | Bad patched image | Flash original boot.img to recover |

### Rollback Strategy

If flashing causes bootloop:

```bash
# Get original boot image
adb pull /dev/block/by-name/boot ~/original_boot.img

# Boot into recovery/fastboot
adb reboot bootloader

# Flash original boot to recover
fastboot flash boot ~/original_boot.img
fastboot reboot
```

---

## Related Workflows

- **magisk-configuration.toon** - Enable Zygisk and install modules
- **play-integrity-bypass.toon** - Install PlayIntegrityFork after Magisk setup
- **adb-magisk** - Script-based Magisk app automation (alternative to this workflow)

---

## Troubleshooting

### "Installed: N/A" doesn't change after flashing

**Cause**: Boot image format may not be compatible with this device
**Solution**: Some devices require vendor_boot patching (Magisk 30+) or have special boot structures

### Fastboot connection fails

**Cause**: Device not properly in fastboot mode
**Solution**:
- Ensure USB cable is properly connected
- Try `fastboot devices` to verify connection
- May need special drivers on Windows

### Device bootloops after flashing

**Cause**: Patched boot image is incompatible
**Solution**:
- Boot into recovery if available
- Flash original boot image using fastboot
- Try different Magisk version

### Magisk patching times out

**Cause**: App not responding or slow device
**Solution**:
- Increase `timeout_patch` parameter to 180-300 seconds
- Ensure device has sufficient free space
- Check device isn't low on memory

### Permission denied on /sdcard/

**Cause**: File permissions issue
**Solution**:
- Ensure `adb shell` is running as system user
- Try pushing to different location (`/data/local/tmp/`)
- May require su/root on some devices

---

## Performance Optimization

For faster installations:

1. **Pre-download**: Download APK separately before running workflow
2. **Cached boot image**: Store boot.img locally if repeated installations needed
3. **Parallel phases**: Some phases could run in parallel on multi-core systems
4. **SSD storage**: Use SSD for output directory to speed up file operations

---

## Advanced Configuration

### Custom Magisk Version

```bash
# Download and install specific older version
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow magisk-complete-install.toon \
    --param version=29.0 \
    --param device=127.0.0.1:5555
```

### Multiple Devices

```bash
# Run on multiple devices sequentially
for device in "127.0.0.1:5555" "127.0.0.1:5556"; do
    uv run ... --param device=$device
done
```

---

**Workflow Version**: 1.0.0
**Last Updated**: 2025-12-02
**Status**: ✅ Complete and Tested
**Maintenance**: Updated for Magisk v30.6
