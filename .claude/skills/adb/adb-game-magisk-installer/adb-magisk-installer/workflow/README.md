# adb-magisk-installer - Workflows

Orchestration workflows (TOON + Markdown documentation pairs) for Magisk installation.

---

## Workflows

| Workflow | Description | Duration | Complexity |
|----------|-------------|----------|------------|
| **[magisk-complete-install.toon](magisk-complete-install.toon)** | Complete end-to-end installation from download to boot flash | ~15 min | Advanced |

---

## magisk-complete-install Workflow

**TOON File**: `magisk-complete-install.toon` (533 lines)
**Documentation**: `magisk-complete-install.md` (450 lines)

### Purpose

Transform device state from:
```
Installed: N/A  ──→  Installed: Yes
(app only)           (system-integrated)
```

### What It Does

1. **Phase 1**: Download latest Magisk APK from GitHub (2-3 min)
2. **Phase 2**: Install Magisk Manager app on device (1-2 min)
3. **Phase 3**: Extract device boot partition (30-60 sec)
4. **Phase 4**: Push boot image to device storage
5. **Phase 5**: Patch boot image using Magisk app (2-3 min) - **User interaction required**
6. **Phase 6**: Pull patched boot image back to host (30-60 sec)
7. **Phase 7**: Reboot to fastboot mode (30 sec)
8. **Phase 8**: Flash patched boot image via fastboot (1-2 min)
9. **Phase 9**: Verify installation and bootup (1-2 min)

**Total**: ~15 minutes (including user interaction time)

### Quick Start

```bash
# Most basic usage
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflow/magisk-complete-install.toon
```

### Common Parameters

```bash
# Specify device explicitly
--param device=127.0.0.1:5555

# Install specific version instead of latest
--param version=30.6

# Custom output directory
--param output_dir=/home/user/magisk

# Increase timeouts for slow networks
--param timeout_download=120
--param timeout_patch=180
```

### Full Example with All Parameters

```bash
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflow/magisk-complete-install.toon \
    --param device=127.0.0.1:5555 \
    --param version=30.6 \
    --param output_dir=/tmp/magisk \
    --param timeout_download=60 \
    --param timeout_install=60 \
    --param timeout_extract=30 \
    --param timeout_patch=120 \
    --param timeout_flash=120
```

### Phase Breakdown

#### Phase 1: Download
- Downloads Magisk APK (30-50MB)
- Downloads boot image reference
- Stores in output directory
- **No device interaction**

#### Phase 2: App Install
- Pushes APK to device
- Installs via `adb install -r`
- Verifies installation
- **Device needed**

#### Phase 3: Extract Boot
- Detects active partition (boot_a/boot_b)
- Pulls `/dev/block/by-name/partition`
- Saves as `boot.img` locally
- **Device needed**

#### Phase 4: Push Boot
- Copies boot.img to device `/sdcard`
- Prepares for Magisk patching
- **Device needed**

#### Phase 5: Patch Boot ⚠️
- **Requires user interaction!**
- Launches Magisk Manager app
- User selects `/sdcard/boot.img` in file picker
- Magisk patches and saves to `/sdcard/Download/`
- **Workflow pauses if file picker doesn't appear**

#### Phase 6: Pull Patched
- Finds `magisk_patched_*.img` on device
- Pulls back to host
- **Device needed**

#### Phase 7: Reboot Fastboot
- Executes `adb reboot fastboot`
- Waits for fastboot connection
- **Device needed, USB connection required**

#### Phase 8: Flash Boot
- Verifies patched boot file
- Flashes via `fastboot flash boot`
- Reboots device
- **Device in fastboot, USB required**

#### Phase 9: Verify
- Waits for device to boot
- Launches Magisk app
- Verifies "Installed: Yes" appears
- **Device needed**

### Success Indicators

Workflow succeeds when:
- ✅ All 9 phases complete without abort
- ✅ Magisk app shows "Installed: Yes"
- ✅ Device boots normally after flashing
- ✅ Magisk app is responsive

### Error Handling

**Auto-Retry Phases**: 1, 2
- Retries up to 2 times with 5-second delay

**Manual Intervention Phases**: 5 (file picker)
- Screenshots captured
- Workflow pauses for manual action

**Abort Conditions**:
- Phase 1: Download fails twice
- Phase 2: App install fails twice
- Phase 3: Boot extraction fails
- Phase 8: Flash fails

### Recovery Procedures

If workflow fails:

1. **Download fails**: Check network, increase timeout, retry
2. **App install fails**: Clear app data, ensure storage, retry
3. **Boot patch fails**: User interaction may be needed, take screenshot
4. **Boot flash fails**: May need to manually flash original boot
5. **Bootloop**: Device may need recovery mode access

### Device Requirements Checklist

Before running:

- [ ] USB debugging enabled
- [ ] Device connected via USB (`adb devices` shows device)
- [ ] ADB working (`adb shell whoami` returns shell)
- [ ] Fastboot working (`fastboot devices` shows device in fastboot mode)
- [ ] At least 1GB free storage on device
- [ ] At least 500MB free space on host
- [ ] Boot loader unlocked (may be required)

### Integration Points

This workflow:
- ✅ Uses scripts from `adb-magisk-installer`
- ✅ Depends on `adb-workflow-orchestrator` for execution
- ✅ Uses `adb-magisk` for app launching/verification
- ✅ Uses `adb-navigation-base` for tap/wait actions
- ✅ Uses `adb-screen-detection` for text verification

Can be used by:
- `adb-karrot` - Requires Magisk for Play Integrity bypass setup
- Manual automation workflows
- Device setup automation scripts

### Related Workflows

From other skills:
- **adb-magisk** - Simpler module installation (after Magisk is installed)
- **play-integrity-bypass.toon** - Requires this workflow first
- **zygisk-configuration.toon** - Enables Zygisk (requires installed Magisk)

### Troubleshooting Guide

See `magisk-complete-install.md` for detailed troubleshooting of:
- Download timeouts
- App installation failures
- Boot extraction issues
- Patching failures
- Flash failures
- Bootloop recovery

---

**Category**: System Installation Workflows
**Workflows**: 1 (with TOON + MD pair)
**Last Updated**: 2025-12-02
**Status**: ✅ Complete and Production-Ready
