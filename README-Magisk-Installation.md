# Magisk + Zygisk Installation Guide

**Complete guide to installing Magisk with Zygisk for game automation with AdbAutoPlayer**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)]()
[![Magisk](https://img.shields.io/badge/Magisk-v30.6+-blue)]()
[![Android](https://img.shields.io/badge/Android-5.0+-green)]()

---

## Table of Contents

1. [Overview](#1-overview)
2. [Quick Start](#2-quick-start)
3. [System Requirements](#3-system-requirements)
4. [Step-by-Step Installation](#4-step-by-step-installation)
5. [Verification](#5-verification)
6. [Troubleshooting](#6-troubleshooting)
7. [Integration with AdbAutoPlayer](#7-integration-with-adbautoplayer)
8. [Architecture](#8-architecture)
9. [Performance](#9-performance)
10. [FAQ](#10-faq)

---

## 1. Overview

### What is Magisk?

**Magisk** is a systemless root solution for Android devices that modifies the boot image to gain system-level privileges without altering the `/system` partition. This allows you to:

- Root your device while maintaining SafetyNet/Play Integrity compatibility
- Install powerful system modules
- Use API hooking frameworks like Zygisk

### What is Zygisk?

**Zygisk** (Zygote + Magisk) is a runtime hook injection framework built into Magisk that allows modules to intercept and modify app behavior at the process level. For game automation:

- **API Hooking**: Modify API responses to bypass detection
- **Play Integrity**: Pass SafetyNet/Play Integrity checks
- **Game Detection Bypass**: Hide root and automation tools from anti-cheat systems

### Why Do You Need This?

Modern mobile games use sophisticated detection systems to identify:
- Rooted devices
- Automation frameworks (like ADB)
- Modified system states

**Magisk + Zygisk** provides the foundation to:
1. **Hide root status** from detection systems
2. **Bypass integrity checks** that block gameplay
3. **Enable Play Integrity modules** that make your device appear legitimate
4. **Run AdbAutoPlayer** safely without triggering bans

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Game Application                        │
│                    (Anti-Cheat Detection Active)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │     Play Integrity API        │
         │   (SafetyNet Attestation)     │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │    Zygisk Hook Injection      │◄─── PlayIntegrityFork Module
         │  (Intercepts API Calls)       │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │      Magisk Framework         │
         │   (Systemless Root)           │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │    Patched Boot Image         │
         │   (Magisk Integration)        │
         └───────────┬───────────────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │      Android System           │
         │   (Unmodified /system)        │
         └───────────────────────────────┘
```

**Key Point**: Magisk modifies the boot image, NOT the system partition. This makes it "systemless" and harder to detect.

---

## 2. Quick Start

### 3-Step Installation Summary

```bash
# Step 1: Download and install Magisk Manager app
uv run .claude/skills/adb-magisk-installer/scripts/adb-magisk-download.py --output-dir /tmp/magisk
uv run .claude/skills/adb-magisk-installer/scripts/adb-magisk-install-app.py \
    --device 127.0.0.1:5555 \
    --apk-path /tmp/magisk/Magisk-v30.6.apk

# Step 2: Extract, patch, and flash boot image (automated workflow)
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflow/magisk-complete-install.toon \
    --param device=127.0.0.1:5555

# Step 3: Enable Zygisk and reboot
uv run .claude/skills/adb-magisk/scripts/adb-magisk-enable-zygisk.py \
    --device 127.0.0.1:5555 \
    --auto-reboot
```

**Total Time**: 15-20 minutes
**Difficulty**: Advanced
**Risk**: Medium (bootloop possible if boot image incompatible)

---

## 3. System Requirements

### Device Requirements

| Requirement | Description | Status |
|-------------|-------------|--------|
| **USB Debugging** | Must be enabled in Developer Options | ✅ Required |
| **ADB Connection** | `adb devices` shows device | ✅ Required |
| **Bootloader Unlocked** | Device allows boot image flashing | ✅ Required* |
| **Fastboot Access** | Device can boot to fastboot mode | ✅ Required |
| **Free Storage (Device)** | At least 1GB available | ✅ Required |
| **Free Storage (Host)** | At least 500MB for files | ✅ Required |
| **Android Version** | Android 5.0 (Lollipop) or higher | ✅ Required |
| **Root Access** | Not required (Magisk provides this) | ⚠️ Not Needed |

\* **Note**: Some devices (emulators like BlueStacks, LDPlayer) may not require bootloader unlocking.

### Host Requirements

| Software | Version | Installation |
|----------|---------|--------------|
| **Python** | 3.12+ | `python --version` |
| **uv** | Latest | `pip install uv` |
| **ADB** | Platform Tools 31+ | In PATH |
| **Fastboot** | Platform Tools 31+ | In PATH |
| **Network Access** | GitHub API | Required for download |

### Supported Android Versions

| Android Version | Magisk Compatibility | Notes |
|-----------------|---------------------|-------|
| Android 5.0-6.0 | ✅ Magisk v20.x | Legacy support |
| Android 7.0-8.1 | ✅ Magisk v25.x | Stable |
| Android 9.0-11 | ✅ Magisk v26.x+ | Recommended |
| Android 12-13 | ✅ Magisk v30.x+ | Latest features |
| Android 14+ | ✅ Magisk v30.x+ | Full support |

### Emulator Compatibility

| Emulator | Bootloader | Magisk Install | Notes |
|----------|-----------|----------------|-------|
| **BlueStacks 5** | ❌ Locked | ⚠️ Limited | Some versions allow root |
| **LDPlayer** | ⚠️ Varies | ✅ Supported | Most versions compatible |
| **NoxPlayer** | ⚠️ Varies | ✅ Supported | Root toggle available |
| **MuMu Player** | ⚠️ Varies | ✅ Supported | Check specific version |
| **MEmu** | ⚠️ Varies | ✅ Supported | Root toggle available |

**Recommendation**: Use LDPlayer or NoxPlayer for easiest Magisk installation.

---

## 4. Step-by-Step Installation

### Phase Overview

The installation consists of 7 phases executed sequentially:

```
Download → Install App → Extract Boot → Patch Boot → Flash Boot → Verify → Enable Zygisk
  2-3min      1-2min        0.5-1min       2-3min      1-2min     1-2min     1min
```

---

### Phase 1: Download Magisk Files

**Duration**: 2-3 minutes
**What happens**: Downloads Magisk APK from GitHub releases

#### Manual Download

```bash
# Download latest version
uv run .claude/skills/adb-magisk-installer/scripts/adb-magisk-download.py \
    --version latest \
    --output-dir /tmp/magisk

# Download specific version
uv run .claude/skills/adb-magisk-installer/scripts/adb-magisk-download.py \
    --version 30.6 \
    --output-dir /tmp/magisk

# Include boot image (optional)
uv run .claude/skills/adb-magisk-installer/scripts/adb-magisk-download.py \
    --version 30.6 \
    --include-boot \
    --output-dir /tmp/magisk
```

#### What's Being Downloaded

| File | Size | Purpose |
|------|------|---------|
| `Magisk-v30.6.apk` | ~6-8 MB | Magisk Manager application |
| `boot.img` (optional) | ~8-16 MB | Generic boot image for patching |

#### Success Criteria

- ✅ APK file exists and is > 5MB
- ✅ Files downloaded without network errors
- ✅ Download completes within timeout (default: 60s)

#### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Release not found: 30.6` | Invalid version number | Check [Magisk releases](https://github.com/topjohnwu/Magisk/releases) |
| `Network timeout` | Slow connection | Increase timeout: `--timeout-download 120` |
| `No APK found in release` | Release structure changed | Try latest version instead |
| `Permission denied writing to /tmp` | Directory permissions | Use different output-dir: `~/magisk` |

---

### Phase 2: Install Magisk Manager App

**Duration**: 1-2 minutes
**What happens**: Installs the Magisk Manager APK on your device

#### Manual Install

```bash
# Basic install
uv run .claude/skills/adb-magisk-installer/scripts/adb-magisk-install-app.py \
    --device 127.0.0.1:5555 \
    --apk-path /tmp/magisk/Magisk-v30.6.apk

# Force reinstall (replace existing)
uv run .claude/skills/adb-magisk-installer/scripts/adb-magisk-install-app.py \
    --device 127.0.0.1:5555 \
    --apk-path /tmp/magisk/Magisk-v30.6.apk \
    --force

# Install with verification
uv run .claude/skills/adb-magisk-installer/scripts/adb-magisk-install-app.py \
    --device 127.0.0.1:5555 \
    --apk-path /tmp/magisk/Magisk-v30.6.apk \
    --verify
```

#### What Happens Behind the Scenes

```bash
# ADB command executed internally:
adb -s 127.0.0.1:5555 install -r /tmp/magisk/Magisk-v30.6.apk

# Verification command:
adb -s 127.0.0.1:5555 shell pm list packages | grep com.topjohnwu.magisk

# Launch verification:
adb -s 127.0.0.1:5555 shell am start -n com.topjohnwu.magisk/.ui.MainActivity
```

#### Success Criteria

- ✅ `adb install` returns "Success"
- ✅ Package manager lists `com.topjohnwu.magisk`
- ✅ Magisk app launches and shows UI
- ✅ "Modules" tab is visible (means app is installed, NOT system-integrated yet)

#### App Installation States

At this phase, Magisk shows:

```
┌─────────────────────────────────┐
│     Magisk Manager              │
│                                 │
│  Magisk                         │
│  ├─ Installed: N/A          ◄── App installed but NOT system-rooted
│  └─ App: 30.6               ◄── App version
│                                 │
│  Zygisk                         │
│  └─ Status: Unavailable     ◄── Requires Magisk system integration
└─────────────────────────────────┘
```

**Important**: `Installed: N/A` means the app is installed, but Magisk is NOT integrated with the system boot yet. This is expected at Phase 2.

#### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `INSTALL_FAILED_INSUFFICIENT_STORAGE` | Not enough space | Free up device storage (need ~200MB) |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Conflicting signatures | Uninstall old Magisk: `adb uninstall com.topjohnwu.magisk` |
| `Installation timeout (>60s)` | Slow device | Increase timeout in script or use faster device |
| `Device unauthorized` | USB debugging not authorized | Check device for authorization prompt |

---

### Phase 3: Extract Boot Image from Device

**Duration**: 0.5-1 minute
**What happens**: Pulls the device's current boot partition for patching

#### Manual Extract

```bash
uv run .claude/skills/adb-magisk-installer/scripts/adb-magisk-extract-boot.py \
    --device 127.0.0.1:5555 \
    --output-dir /tmp/magisk
```

#### What Happens Behind the Scenes

```bash
# Auto-detect active boot partition (A/B devices)
adb shell getprop ro.boot.slot_suffix  # Returns: _a or _b

# Pull boot partition
adb shell su -c "dd if=/dev/block/by-name/boot_a of=/sdcard/boot.img"
adb pull /sdcard/boot.img /tmp/magisk/boot.img

# Verify file integrity
ls -lh /tmp/magisk/boot.img  # Should be 8-16 MB
```

#### Boot Partition Detection

Most Android devices use one of these partition layouts:

**Layout 1: Single Boot Partition**
```
/dev/block/by-name/boot → /dev/block/mmcblk0p15
```

**Layout 2: A/B Partitioning (Modern devices)**
```
/dev/block/by-name/boot_a → Active slot
/dev/block/by-name/boot_b → Inactive slot
```

**Layout 3: Emulators**
```
/dev/block/by-name/boot → /dev/block/vdc
```

The extraction script automatically detects which layout your device uses.

#### Success Criteria

- ✅ Boot image file created: `/tmp/magisk/boot.img`
- ✅ File size is 8-16 MB (typical boot image size)
- ✅ File integrity verified (md5sum/sha256sum)
- ✅ No read errors during extraction

#### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Permission denied: /dev/block/by-name/boot` | No root access to partition | Requires temporary root or custom recovery |
| `No such file or directory: boot_a` | Unsupported partition layout | May need manual partition identification |
| `File size is 0 bytes` | Extraction failed | Check device storage, try recovery mode |
| `dd: invalid input` | Corrupted partition table | Use manufacturer-provided boot image |

#### Alternative: Manual Boot Image

If automatic extraction fails, you can:

1. **Download from manufacturer**: Get factory boot image for your device model
2. **Extract from firmware**: Use tools like `Android Image Kitchen` to unpack firmware
3. **Use recovery mode**: Boot into TWRP and back up boot partition

```bash
# Using manufacturer boot image
mv ~/Downloads/boot-device-model.img /tmp/magisk/boot.img
```

---

### Phase 4: Patch Boot Image via Magisk

**Duration**: 2-3 minutes
**What happens**: Magisk Manager patches the boot image to inject its framework

This is the **most critical phase** where Magisk modifies the boot image to gain system integration.

#### Automated Patching

```bash
uv run .claude/skills/adb-magisk-installer/scripts/adb-magisk-patch-boot.py \
    --device 127.0.0.1:5555 \
    --boot-image /tmp/magisk/boot.img \
    --output-dir /tmp/magisk
```

#### What Happens Behind the Scenes

```bash
# 1. Push boot image to device storage
adb push /tmp/magisk/boot.img /sdcard/boot.img

# 2. Launch Magisk Manager
adb shell am start -n com.topjohnwu.magisk/.ui.MainActivity

# 3. Navigate to Install → Select and Patch a File
# (Automated via UI navigation + OCR detection)

# 4. Select /sdcard/boot.img
# (Script taps file selector and chooses boot.img)

# 5. Wait for patching to complete
# Magisk shows: "Patching complete! Output: /sdcard/Download/magisk_patched_[random].img"

# 6. Pull patched image back to host
adb pull /sdcard/Download/magisk_patched_*.img /tmp/magisk/patched_boot.img
```

#### Patching Process Visualization

```
Original Boot Image          Magisk Patching              Patched Boot Image
┌──────────────┐            ┌──────────────┐            ┌──────────────┐
│  Kernel      │            │  Inject      │            │  Kernel      │
│              │ ─────────► │  Magisk      │ ─────────► │  + Magisk    │
│  Ramdisk     │            │  Framework   │            │  Framework   │
│              │            │              │            │              │
│  Init        │            │  Modify      │            │  Init (mod)  │
│              │            │  Init        │            │              │
└──────────────┘            └──────────────┘            └──────────────┘
   8-16 MB                   2-3 minutes                  8-16 MB
```

#### Success Criteria

- ✅ File selector opens in Magisk Manager
- ✅ Boot image selection succeeds
- ✅ "Patching complete" message appears
- ✅ Patched image found: `/sdcard/Download/magisk_patched_*.img`
- ✅ Patched image size matches original (~8-16 MB)

#### Manual Intervention Points

The automated script may pause for user action if:

1. **File selector doesn't open**: User must tap "Install" → "Select and Patch a File"
2. **Boot image not found**: User must manually navigate to `/sdcard/boot.img`
3. **Patching hangs**: User should check Magisk app for error messages

#### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Unsupported boot image format` | Incompatible boot structure | Try different Magisk version (older devices may need v20.x) |
| `Patching failed: Insufficient space` | Not enough /sdcard storage | Free up 500MB on device |
| `File selector timeout` | UI navigation failed | Manually tap Install → Patch File |
| `Patched image not found` | Patching didn't complete | Check Magisk app logs for errors |
| `Image size mismatch` | Patching corrupted file | Re-extract original boot image |

#### Troubleshooting Patching Failures

If patching fails repeatedly:

```bash
# Check Magisk logs
adb shell su -c "cat /cache/magisk.log"

# Check device storage
adb shell df -h /sdcard

# Check Magisk app version
adb shell dumpsys package com.topjohnwu.magisk | grep versionName

# Try manual patching in Magisk app UI
```

---

### Phase 5: Flash Patched Boot Image

**Duration**: 1-2 minutes
**What happens**: Flashes the patched boot image to device boot partition via fastboot

⚠️ **WARNING**: This phase modifies your device's boot partition. **Backup your original boot image** before proceeding!

#### Automated Flashing

```bash
uv run .claude/skills/adb-magisk-installer/scripts/adb-magisk-flash-boot.py \
    --device 127.0.0.1:5555 \
    --patched-boot /tmp/magisk/patched_boot.img
```

#### What Happens Behind the Scenes

```bash
# 1. Reboot device to fastboot mode
adb reboot bootloader

# 2. Wait for fastboot connection
fastboot devices  # Should show device

# 3. Flash patched boot image
fastboot flash boot /tmp/magisk/patched_boot.img

# 4. Reboot device
fastboot reboot

# 5. Wait for Android to fully boot
adb wait-for-device
```

#### Flashing Process Visualization

```
Device State:  ADB Mode  →  Fastboot Mode  →  Flash Boot  →  Reboot  →  ADB Mode
               ┌────┐       ┌─────────┐       ┌────────┐     ┌─────┐     ┌────┐
               │    │       │         │       │        │     │     │     │    │
Time:          │ 5s │ ───► │   5s    │ ───► │  30s   │ ───►│ 30s│ ───►│ 10s│
               │    │       │         │       │        │     │     │     │    │
               └────┘       └─────────┘       └────────┘     └─────┘     └────┘
```

**Total**: ~80-90 seconds for full flash cycle

#### Success Criteria

- ✅ Device enters fastboot mode (`fastboot devices` shows device)
- ✅ `fastboot flash boot` returns `OKAY` and `Finished`
- ✅ Device reboots successfully (no bootloop)
- ✅ Android boots to home screen within 60 seconds
- ✅ ADB connection re-establishes after boot

#### Bootloader Unlocking (If Required)

Some devices require bootloader unlocking before flashing:

```bash
# Check bootloader status
fastboot oem device-info  # or: fastboot getvar unlocked

# Unlock bootloader (WIPES DATA!)
fastboot oem unlock  # or: fastboot flashing unlock

# Confirm on device screen
# (Use volume buttons to select "Unlock", power button to confirm)
```

⚠️ **WARNING**: Unlocking bootloader **WIPES ALL DATA** on most devices. Backup first!

#### A/B Partition Devices

Modern devices with A/B partitioning require flashing to the active slot:

```bash
# Check active slot
fastboot getvar current-slot  # Returns: a or b

# Flash to active slot
fastboot flash boot_a /tmp/magisk/patched_boot.img  # if slot_a is active
# or
fastboot flash boot_b /tmp/magisk/patched_boot.img  # if slot_b is active
```

The script automatically detects and handles A/B devices.

#### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `FAILED (remote: Partition flashing is not allowed)` | Bootloader locked | Unlock bootloader: `fastboot oem unlock` |
| `FAILED (remote: Invalid sparse image)` | Corrupted patched image | Re-patch boot image (Phase 4) |
| `Device bootloops after flash` | Incompatible boot image | Flash original boot to recover (see Rollback) |
| `Fastboot not recognized` | Missing drivers (Windows) | Install Android USB drivers |
| `Timeout waiting for device` | Device stuck in fastboot | Force reboot: hold Power+VolDown 10s |

#### Emergency Rollback

If device bootloops after flashing, recover using original boot image:

```bash
# Backup original boot BEFORE flashing (do this at Phase 3!)
cp /tmp/magisk/boot.img /tmp/magisk/boot_original_backup.img

# If bootloop occurs:
# 1. Boot to fastboot (hold Power+VolDown during boot)
# 2. Flash original boot image
fastboot flash boot /tmp/magisk/boot_original_backup.img
fastboot reboot

# Device should now boot normally (but Magisk will be removed)
```

---

### Phase 6: Verify Magisk Installation

**Duration**: 1-2 minutes
**What happens**: Confirms Magisk is successfully integrated with the system

#### Automated Verification

```bash
uv run .claude/skills/adb-magisk/scripts/adb-magisk-verify.py \
    --device 127.0.0.1:5555
```

#### What Gets Verified

The verification script checks:

1. **Magisk Manager app installed**: Package `com.topjohnwu.magisk` exists
2. **System integration**: Magisk shows `Installed: Yes` (not `N/A`)
3. **Root access available**: `su` command works
4. **Magisk version**: Reports installed Magisk version
5. **Zygisk availability**: Settings tab shows Zygisk option

#### Manual Verification

**Step 1**: Launch Magisk Manager

```bash
adb shell am start -n com.topjohnwu.magisk/.ui.MainActivity
```

**Step 2**: Check Magisk status

Look for this in the app:

```
┌─────────────────────────────────┐
│     Magisk Manager              │
│                                 │
│  Magisk                         │
│  ├─ Installed: Yes          ◄── ✅ System-integrated!
│  ├─ Version: 30.6           ◄── Magisk version
│  └─ App: 30.6               ◄── App version
│                                 │
│  Zygisk                         │
│  └─ Status: Disabled        ◄── Available but not enabled yet
│                                 │
│  [Settings] [Modules]           │
└─────────────────────────────────┘
```

**Success**: If you see `Installed: Yes`, Magisk is successfully integrated! 🎉

**Step 3**: Test root access

```bash
# Check if su works
adb shell su -c "id"
# Should output: uid=0(root) gid=0(root) groups=0(root)

# Check Magisk binary
adb shell su -c "which magisk"
# Should output: /system/bin/magisk or /sbin/magisk
```

#### Success Criteria

- ✅ Magisk app shows `Installed: Yes`
- ✅ Root access works (`su` command succeeds)
- ✅ Magisk version matches expected (30.6 or later)
- ✅ Zygisk option appears in Settings
- ✅ Device boots without issues

#### Installation States Summary

| State | Installed Status | Zygisk Status | What It Means |
|-------|------------------|---------------|---------------|
| **Phase 2 Complete** | `N/A` | `Unavailable` | App installed, NOT system-rooted |
| **Phase 5 Complete** | `Yes` | `Disabled` | Magisk fully installed, Zygisk not enabled |
| **Phase 7 Complete** | `Yes` | `Enabled` | Fully ready for game automation |

#### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Installed: N/A` after flash | Boot image didn't integrate | Reflash patched boot (Phase 5) |
| `su: not found` | Root not working | Check Magisk logs: `cat /cache/magisk.log` |
| `App version mismatch` | Outdated app after system update | Reinstall Magisk Manager app |
| `Modules tab missing` | App crashed or corrupted | Clear app data, reinstall |

---

### Phase 7: Enable Zygisk

**Duration**: 1 minute (+ reboot time ~1 minute)
**What happens**: Enables the Zygisk runtime hook framework for API interception

⚠️ **Important**: Enabling Zygisk **requires a device reboot** to take effect.

#### Automated Enablement

```bash
# Enable Zygisk and auto-reboot
uv run .claude/skills/adb-magisk/scripts/adb-magisk-enable-zygisk.py \
    --device 127.0.0.1:5555 \
    --auto-reboot

# Enable Zygisk without reboot (manual reboot required)
uv run .claude/skills/adb-magisk/scripts/adb-magisk-enable-zygisk.py \
    --device 127.0.0.1:5555
```

#### What Happens Behind the Scenes

```bash
# 1. Launch Magisk Manager
adb shell am start -n com.topjohnwu.magisk/.ui.MainActivity

# 2. Tap Settings tab
# (Automated via UI navigation + OCR detection)

# 3. Locate "Zygisk" toggle
# (OCR finds "Zygisk" text, taps toggle to the right)

# 4. Toggle Zygisk ON
# (Script simulates tap on toggle switch)

# 5. Reboot prompt appears
# Magisk shows: "System update required. Reboot now?"

# 6. Confirm reboot (if --auto-reboot)
# (Script taps "Restart" button)

# 7. Wait for device to reboot
# (Script monitors for boot completion)
```

#### Manual Enablement

If automated script fails, enable manually:

1. Open Magisk Manager app
2. Tap **Settings** (gear icon, top-right)
3. Scroll down to **Zygisk** toggle
4. Tap toggle to **enable** (turns blue/green)
5. Tap **Restart** when prompted
6. Wait for device to reboot (~60 seconds)

#### Success Criteria

- ✅ Magisk Settings page opens
- ✅ Zygisk toggle found and tapped
- ✅ Zygisk status changes to `Enabled`
- ✅ Reboot prompt appears (if needed)
- ✅ Device reboots successfully
- ✅ After reboot, Magisk shows `Zygisk: Enabled`

#### Verification After Enable

```bash
# Check Zygisk status
adb shell su -c "magisk --zygisk status"
# Should output: Zygisk is running

# Check Zygisk processes
adb shell ps | grep zygisk
# Should show zygisk processes
```

#### Zygisk Status States

| State | Meaning | What to Do |
|-------|---------|------------|
| **Unavailable** | Magisk not installed | Complete Phase 1-5 |
| **Disabled** | Magisk installed, Zygisk OFF | Enable in Settings (this phase) |
| **Enabled** | Zygisk active but needs reboot | Reboot device |
| **Running** | Zygisk fully operational | ✅ Ready for modules |

#### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Zygisk option not found` | Old Magisk version | Update Magisk to v30.0+ |
| `Toggle not responding` | UI automation failed | Enable manually in app |
| `Reboot prompt timeout` | Prompt didn't appear | Manually reboot device |
| `Zygisk still disabled after reboot` | Toggle didn't save | Re-enable and reboot again |
| `Device won't boot after enable` | Rare boot conflict | Boot to recovery, disable Zygisk |

#### Zygisk and SafetyNet/Play Integrity

After enabling Zygisk, install Play Integrity modules for full protection:

```bash
# Install PlayIntegrityFork module (covered in separate guide)
# This makes your device pass Google's integrity checks
```

---

### Complete Installation Verification Checklist

After completing all 7 phases, verify:

**Magisk Status**:
- [ ] Magisk Manager app launches without crashes
- [ ] Home screen shows `Installed: Yes`
- [ ] Version shows `30.6` or later
- [ ] Settings tab is accessible

**Root Access**:
- [ ] `adb shell su` works without errors
- [ ] `adb shell su -c "id"` shows `uid=0(root)`
- [ ] Magisk binary found: `adb shell su -c "which magisk"`

**Zygisk Status**:
- [ ] Settings shows `Zygisk: Enabled`
- [ ] `magisk --zygisk status` returns "running"
- [ ] Zygisk processes visible in `ps` output

**System Stability**:
- [ ] Device boots normally (no bootloops)
- [ ] All system apps work (Settings, Play Store, etc.)
- [ ] ADB connection stable
- [ ] No unexpected crashes

If all checks pass: **Installation complete!** 🎉 Proceed to [Integration with AdbAutoPlayer](#7-integration-with-adbautoplayer).

---

## 5. Verification

### How to Verify Magisk Installation

Run the automated verification script:

```bash
uv run .claude/skills/adb-magisk/scripts/adb-magisk-verify.py \
    --device 127.0.0.1:5555 \
    --json
```

**Expected Output**:

```json
{
  "device_id": "127.0.0.1:5555",
  "success": true,
  "magisk_installed": true,
  "magisk_version": "30.6",
  "app_version": "30.6",
  "root_available": true,
  "zygisk_available": true,
  "zygisk_enabled": true,
  "zygisk_running": true,
  "exit_code": 0
}
```

### How to Verify Zygisk is Enabled

**Method 1: Magisk Manager UI**

1. Open Magisk Manager
2. Check home screen:
   - `Magisk: Installed: Yes` ✅
   - `Zygisk: Enabled` ✅

**Method 2: Command Line**

```bash
# Check Zygisk status
adb shell su -c "magisk --zygisk status"
# Output: Zygisk is running ✅

# Check Zygisk processes
adb shell ps -A | grep zygisk
# Output should show zygisk64 and zygisk processes
```

**Method 3: Verification Script**

```bash
uv run .claude/skills/adb-magisk/scripts/adb-magisk-verify.py \
    --device 127.0.0.1:5555
```

**Output**:
```
✅ Magisk installed on 127.0.0.1:5555
  Installed: ✅ Yes
  Version: 30.6
  Root Available: ✅ Yes
  Zygisk Available: ✅ Yes
  Zygisk Enabled: ✅ Yes
  Zygisk Running: ✅ Yes
```

### Verification Troubleshooting

| Symptom | Diagnosis | Solution |
|---------|-----------|----------|
| `Installed: N/A` | Magisk not system-integrated | Reflash patched boot (Phase 5) |
| `Root Available: No` | su not working | Check `/cache/magisk.log` for errors |
| `Zygisk Enabled: No` | Zygisk not turned on | Run Phase 7 (enable Zygisk) |
| `Zygisk Running: No` | Zygisk enabled but not active | Reboot device |
| `zygisk processes not found` | Zygisk failed to start | Check compatibility, reinstall Magisk |

---

## 6. Troubleshooting

### Common Issues by Phase

#### Phase 1: Download Issues

**Problem**: `Network timeout` or `Release not found`

**Solutions**:
```bash
# Increase timeout
uv run adb-magisk-download.py --version 30.6 --timeout-download 120

# Try specific version instead of latest
uv run adb-magisk-download.py --version 30.6

# Check GitHub releases manually
curl -s https://api.github.com/repos/topjohnwu/Magisk/releases | grep tag_name

# Use pre-downloaded APK
# Download from: https://github.com/topjohnwu/Magisk/releases
# Place in /tmp/magisk/ and skip download phase
```

---

#### Phase 2: Installation Failures

**Problem**: `INSTALL_FAILED_INSUFFICIENT_STORAGE`

**Solutions**:
```bash
# Check device storage
adb shell df -h /data

# Free up space (remove unused apps)
adb shell pm uninstall --user 0 com.example.unused.app

# Clear app caches
adb shell pm trim-caches 500M
```

**Problem**: `INSTALL_FAILED_UPDATE_INCOMPATIBLE`

**Solutions**:
```bash
# Uninstall old Magisk completely
adb uninstall com.topjohnwu.magisk

# Reinstall fresh
uv run adb-magisk-install-app.py --device 127.0.0.1:5555 --apk-path /tmp/magisk/Magisk-v30.6.apk
```

---

#### Phase 3: Boot Extraction Failures

**Problem**: `Permission denied: /dev/block/by-name/boot`

**Solutions**:
```bash
# Try with temporary root (if available)
adb shell su -c "dd if=/dev/block/by-name/boot of=/sdcard/boot.img"
adb pull /sdcard/boot.img /tmp/magisk/boot.img

# Use manufacturer boot image instead
# Download from device manufacturer support page
# Place in /tmp/magisk/boot.img

# Check partition table
adb shell su -c "ls -l /dev/block/by-name/"
```

**Problem**: `Boot partition not found`

**Solutions**:
```bash
# List all partitions
adb shell su -c "cat /proc/partitions"

# Search for boot partition
adb shell su -c "find /dev/block -name 'boot*'"

# Common locations:
# - /dev/block/mmcblk0p15  (most devices)
# - /dev/block/sda15       (some emulators)
# - /dev/block/vdc         (BlueStacks)
```

---

#### Phase 4: Patching Failures

**Problem**: `Unsupported boot image format`

**Solutions**:
```bash
# Check boot image format
file /tmp/magisk/boot.img
# Should output: Android bootimg, kernel, ramdisk

# Try older Magisk version for legacy devices
uv run adb-magisk-download.py --version 25.2  # For Android 7-8
uv run adb-magisk-download.py --version 20.4  # For Android 5-6

# Ensure boot image is uncompressed
# Some devices use compressed boot (boot.img.gz)
gunzip /tmp/magisk/boot.img.gz
```

**Problem**: `Patching timeout`

**Solutions**:
```bash
# Increase timeout
uv run adb-magisk-patch-boot.py \
    --device 127.0.0.1:5555 \
    --boot-image /tmp/magisk/boot.img \
    --timeout 300  # 5 minutes

# Free up device RAM
adb shell am force-stop <package>  # Stop heavy apps

# Manually patch in Magisk app
# 1. Push boot.img to /sdcard
# 2. Open Magisk Manager
# 3. Install → Select and Patch a File
# 4. Choose boot.img
# 5. Wait for completion
```

---

#### Phase 5: Flashing Failures

**Problem**: `FAILED (remote: Partition flashing is not allowed)`

**Solutions**:
```bash
# Unlock bootloader
fastboot oem unlock  # Standard
# or
fastboot flashing unlock  # Google Pixel
# or
fastboot oem unlock XXXXXX  # Some manufacturers (use unlock code)

# Check unlock status
fastboot getvar unlocked
# Should output: unlocked: yes
```

**Problem**: `Device bootloops after flash`

**Recovery Steps**:
```bash
# Emergency recovery procedure:

# 1. Force reboot to fastboot
# Hold Power + Volume Down for 10 seconds

# 2. Flash original boot image
fastboot flash boot /tmp/magisk/boot_original_backup.img
fastboot reboot

# 3. If no backup, download stock firmware
# Visit device manufacturer support page
# Extract boot.img from firmware ZIP
# Flash: fastboot flash boot boot_stock.img

# 4. If device won't boot to fastboot
# Boot to recovery mode (Power + Volume Up)
# Flash via recovery (if TWRP installed)
# or perform factory reset (last resort)
```

**Problem**: `Fastboot not recognized` (Windows)

**Solutions**:
```powershell
# Install Android USB drivers
# Download from: https://developer.android.com/studio/run/win-usb

# Or use manufacturer-specific drivers
# - Samsung: https://developer.samsung.com/android-usb-driver
# - Xiaomi: https://www.xiaomitool.com/V2/drivers
# - OnePlus: https://onepluscommunitycontent.s3.amazonaws.com/OnePlus_USB_Drivers_Setup.exe

# Check device manager
devmgmt.msc
# Look for "Android Device" or "Unknown Device"
# Right-click → Update driver → Browse → Select downloaded driver
```

---

#### Phase 6: Verification Failures

**Problem**: `Installed: N/A` after flashing

**Diagnosis**:
```bash
# Check if boot was actually flashed
adb shell su -c "cat /proc/cmdline"
# Should contain: androidboot.slot_suffix= or other Magisk indicators

# Check Magisk logs
adb shell su -c "cat /cache/magisk.log"
# Look for errors during boot

# Check partitions
adb shell su -c "ls -l /dev/block/by-name/boot*"
```

**Solutions**:
```bash
# Reflash patched boot
fastboot flash boot /tmp/magisk/patched_boot.img
fastboot reboot

# Try alternative flash method
adb push /tmp/magisk/patched_boot.img /sdcard/
adb shell su -c "dd if=/sdcard/patched_boot.img of=/dev/block/by-name/boot"
adb reboot

# Flash via recovery (TWRP)
# 1. Boot to TWRP
# 2. Install → Install Image
# 3. Select patched_boot.img
# 4. Flash to Boot partition
```

---

#### Phase 7: Zygisk Enable Failures

**Problem**: `Zygisk option not found`

**Solutions**:
```bash
# Update Magisk to latest version
uv run adb-magisk-download.py --version latest
uv run adb-magisk-install-app.py --device 127.0.0.1:5555 --apk-path /tmp/magisk/Magisk-latest.apk --force

# Check Magisk version
adb shell dumpsys package com.topjohnwu.magisk | grep versionName
# Should be 30.0 or higher
```

**Problem**: `Device won't boot after enabling Zygisk`

**Recovery Steps**:
```bash
# Boot to safe mode
adb shell setprop persist.sys.safemode 1
adb reboot

# Disable Zygisk from safe mode
adb shell su -c "magisk resetprop persist.sys.zygisk 0"
adb reboot

# If still won't boot, reflash original boot
fastboot flash boot /tmp/magisk/boot_original_backup.img
fastboot reboot
```

---

### Recovery Procedures

#### Complete Rollback (Remove Magisk Entirely)

```bash
# Method 1: Flash stock boot image
fastboot flash boot boot_stock.img
fastboot reboot

# Method 2: Uninstall via Magisk app (if device still boots)
adb shell am start -n com.topjohnwu.magisk/.ui.MainActivity
# Tap: Settings → Uninstall → Complete Uninstall

# Method 3: Factory reset (last resort, WIPES DATA!)
adb reboot recovery
# Select: Wipe data/factory reset
```

#### Partial Rollback (Keep Magisk, Remove Modules)

```bash
# Boot to safe mode (disables all modules)
adb shell setprop persist.sys.safemode 1
adb reboot

# Remove specific module
adb shell su -c "rm -rf /data/adb/modules/MODULE_ID"
adb reboot

# Disable all modules without reboot
adb shell su -c "touch /data/adb/magisk/.disable"
adb reboot
```

---

### Diagnostic Commands

```bash
# Check Magisk status
adb shell su -c "magisk -v"  # Version
adb shell su -c "magisk --path"  # Installation path
adb shell su -c "magisk --zygisk status"  # Zygisk status

# Check boot slot (A/B devices)
adb shell getprop ro.boot.slot_suffix

# Check boot completion
adb shell getprop sys.boot_completed  # Should be 1

# Check SELinux status
adb shell getenforce  # Should be Enforcing or Permissive

# View Magisk logs
adb shell su -c "cat /cache/magisk.log"

# Check installed modules
adb shell su -c "ls /data/adb/modules/"

# Test root access
adb shell su -c "id"  # Should show uid=0(root)
adb shell su -c "whoami"  # Should show root
```

---

### Error Code Reference

| Exit Code | Meaning | Common Causes |
|-----------|---------|---------------|
| **0** | Success | All operations completed |
| **1** | Warning | Partial success, manual intervention needed |
| **2** | Error | Operation failed (recoverable) |
| **3** | Critical | Device/network/file not found (not recoverable) |

---

### Getting Help

If you encounter issues not covered here:

1. **Check Magisk logs**:
   ```bash
   adb shell su -c "cat /cache/magisk.log"
   ```

2. **Check device logs**:
   ```bash
   adb logcat -d | grep -i magisk
   ```

3. **Visit Magisk support**:
   - [Official GitHub](https://github.com/topjohnwu/Magisk)
   - [Magisk Forum](https://forum.xda-developers.com/f/magisk.5903/)
   - [Magisk Discord](https://discord.gg/magisk)

4. **Report to AdbAutoPlayer**:
   ```bash
   # Create issue with logs:
   # https://github.com/AdbAutoPlayer/AdbAutoPlayer/issues
   ```

---

## 7. Integration with AdbAutoPlayer

### How Magisk + Zygisk Enables Game Automation

Once Magisk and Zygisk are installed, you can use AdbAutoPlayer with advanced anti-detection capabilities:

```
Game Detection System        Magisk + Zygisk Defense        AdbAutoPlayer
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│ Root Detection   │ ────►  │ Hide Root Status │ ────►  │ Safe Automation  │
│ ADB Check        │ ────►  │ Hook ADB APIs    │ ────►  │ Undetectable     │
│ Play Integrity   │ ────►  │ Bypass Checks    │ ────►  │ No Bans          │
└──────────────────┘        └──────────────────┘        └──────────────────┘
```

### Installing Play Integrity Fork Module

After Zygisk is enabled, install the Play Integrity bypass module:

```bash
# Install PlayIntegrityFork module
uv run .claude/skills/adb-magisk/scripts/adb-magisk-install-module.py \
    --device 127.0.0.1:5555 \
    --module-url https://github.com/chiteroman/PlayIntegrityFork/releases/latest/download/PlayIntegrityFork.zip

# Reboot to activate
adb reboot
```

**What this does**:
- Hooks Play Integrity API calls
- Makes device appear unrooted to games
- Bypasses SafetyNet attestation
- Allows AdbAutoPlayer to run undetected

### AdbAutoPlayer Configuration

After Magisk + Zygisk + Play Integrity:

```bash
# Test game detection bypass
uv run .claude/skills/adb-detection/scripts/adb-check-play-integrity.py \
    --device 127.0.0.1:5555

# Expected output:
# ✅ Basic Integrity: PASS
# ✅ CTS Profile Match: PASS
# ✅ Device Integrity: PASS
```

### Automation Workflow

With Magisk + Zygisk installed, AdbAutoPlayer uses this workflow:

```
┌────────────────────────────────────────────────────────────────┐
│                    AdbAutoPlayer Automation                    │
└────────────┬───────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────┐
│  Phase 1: Pre-Launch Detection                                │
│  ├─ Check Play Integrity (via Zygisk hook)                    │
│  ├─ Verify root hidden (Magisk Hide)                          │
│  └─ Test ADB visibility (should be hidden)                    │
└────────────┬───────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────┐
│  Phase 2: Game Launch                                         │
│  ├─ Launch game via ADB                                       │
│  ├─ Wait for game UI (OCR detection)                          │
│  └─ Verify no ban/detection screens                           │
└────────────┬───────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────┐
│  Phase 3: Automation Loop                                     │
│  ├─ UINavigator: Navigate menus (tap/swipe)                   │
│  ├─ OCRFinder: Detect UI elements (buttons/text)              │
│  ├─ StateVerifier: Confirm actions completed                  │
│  └─ Repeat for dailies/farming/events                         │
└────────────┬───────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────┐
│  Phase 4: Post-Automation                                     │
│  ├─ Close game gracefully                                     │
│  ├─ Clear app cache/data (optional)                           │
│  └─ Report completion status                                  │
└────────────────────────────────────────────────────────────────┘
```

### Example: AFK Journey Automation

```bash
# With Magisk + Zygisk installed:
uv run .claude/skills/adb-game-automation/scripts/adb-run-game-bot.py \
    --device 127.0.0.1:5555 \
    --game afk-journey \
    --routine "claim-afk-rewards,daily-quests,arena-battles"

# Behind the scenes:
# 1. Play Integrity check passes (Zygisk hook)
# 2. Game launches without detection
# 3. Bot completes all routines
# 4. No ban triggers
```

---

## 8. Architecture

### Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Game Application Layer                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐   │
│  │ Anti-Cheat │  │ Root Check │  │ Play Store │  │ Game Logic │   │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘   │
└─────────┼────────────────┼────────────────┼────────────────┼─────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Zygisk Interception Layer                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Hook Injection Points:                                      │  │
│  │  • android.os.Build.TAGS (remove "test-keys")                │  │
│  │  • ro.build.* properties (hide root indicators)              │  │
│  │  • com.google.android.gms.safetynet.SafetyNetApi.attest()    │  │
│  │  • File.exists("/system/xbin/su") → return false             │  │
│  │  • Runtime.exec("su") → IOException                          │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  Modules:                                                           │
│  ├─ PlayIntegrityFork (integrity bypass)                           │
│  ├─ Shamiko (hide Magisk from apps)                                │
│  └─ Zygisk-Next (enhanced hook capabilities)                       │
└─────────┬───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Magisk Framework Layer                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Core Functions:                                             │  │
│  │  • MagiskInit (init process hijacking)                       │  │
│  │  • MagiskPolicy (SELinux policy patching)                    │  │
│  │  • MagiskBoot (boot image modifications)                     │  │
│  │  • MagiskHide (root concealment - deprecated in v26+)        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  Components:                                                        │
│  ├─ /data/adb/magisk/ (binary storage)                             │
│  ├─ /data/adb/modules/ (installed modules)                         │
│  └─ /sbin/.magisk/ (mounted overlays)                              │
└─────────┬───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Boot Image Layer                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Patched Boot Image (magisk_patched.img):                   │  │
│  │  • Kernel (unmodified)                                       │  │
│  │  • Ramdisk (modified):                                       │  │
│  │    ├─ init → init.magisk.rc (hijacked)                      │  │
│  │    ├─ /system/bin/magisk (injected)                         │  │
│  │    └─ /data/adb/magisk/ (mount point)                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────┬───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Android System Layer                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  /system partition (UNMODIFIED - systemless root)            │  │
│  │  /vendor partition (UNMODIFIED)                              │  │
│  │  /boot partition (MODIFIED with Magisk)                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### UINavigator + OCRFinder + StateVerifier Workflow

AdbAutoPlayer uses three core components for automation:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AdbAutoPlayer Workflow                       │
└─────────┬───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. OCRFinder (Screen Detection)                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Purpose: Locate UI elements via OCR/image recognition       │  │
│  │  ├─ Screenshot via adb shell screencap                       │  │
│  │  ├─ OCR processing (Tesseract)                               │  │
│  │  ├─ Template matching (OpenCV)                               │  │
│  │  └─ Returns: (x, y) coordinates of target                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Example:                                                           │
│  • Find "Claim" button at (800, 1200)                              │
│  • Detect "Ready" status text at (540, 300)                        │
│  • Locate hero avatar at (150, 450)                                │
└─────────┬───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. UINavigator (Interaction)                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Purpose: Perform actions on UI elements                     │  │
│  │  ├─ Tap: adb shell input tap X Y                             │  │
│  │  ├─ Swipe: adb shell input swipe X1 Y1 X2 Y2 DURATION        │  │
│  │  ├─ Text input: adb shell input text "string"                │  │
│  │  └─ Key events: adb shell input keyevent KEYCODE             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Example:                                                           │
│  • Tap (800, 1200) to claim rewards                                │
│  • Swipe (540, 1000) → (540, 200) to scroll up                    │
│  • Press KEYCODE_BACK to return to previous screen                 │
└─────────┬───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. StateVerifier (Confirmation)                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Purpose: Verify action completed successfully               │  │
│  │  ├─ Take new screenshot                                      │  │
│  │  ├─ Compare before/after states                              │  │
│  │  ├─ Check for expected UI changes                            │  │
│  │  └─ Returns: success/failure + retry logic                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Example:                                                           │
│  • After tapping "Claim", verify reward popup appeared            │
│  • After swiping, verify scroll position changed                  │
│  • After navigation, verify new screen loaded                     │
└─────────┬───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Automation Loop                                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  while True:                                                 │  │
│  │      state = OCRFinder.detect_current_state()                │  │
│  │      action = decide_action(state)                           │  │
│  │      UINavigator.perform(action)                             │  │
│  │      success = StateVerifier.verify(action)                  │  │
│  │      if not success:                                         │  │
│  │          retry(action)                                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Example Automation Flow

**Task**: Claim AFK rewards in AFK Journey

```python
# Step 1: Detect "AFK Rewards" button
location = OCRFinder.find_text("AFK Rewards", confidence=0.8)
# Returns: (540, 800)

# Step 2: Tap the button
UINavigator.tap(540, 800)
time.sleep(2)  # Wait for animation

# Step 3: Verify reward screen appeared
reward_screen = OCRFinder.find_text("Collect", confidence=0.9)
if reward_screen:
    # Step 4: Tap "Collect" button
    UINavigator.tap(*reward_screen)
    time.sleep(1)

    # Step 5: Verify rewards claimed (screen closed)
    if StateVerifier.verify_state_changed():
        print("✅ Rewards claimed successfully")
    else:
        print("❌ Claim failed, retrying...")
        retry_claim()
else:
    print("❌ Reward screen not found")
```

---

## 9. Performance

### Installation Time Breakdown

| Phase | Average Time | Range | Bottleneck |
|-------|--------------|-------|------------|
| **Phase 1: Download** | 2 min | 1-5 min | Network speed |
| **Phase 2: Install App** | 1 min | 0.5-2 min | Device speed |
| **Phase 3: Extract Boot** | 1 min | 0.5-2 min | ADB transfer |
| **Phase 4: Patch Boot** | 2 min | 1-5 min | Device CPU |
| **Phase 5: Flash Boot** | 2 min | 1-3 min | Fastboot speed |
| **Phase 6: Verify** | 1 min | 0.5-2 min | Device boot |
| **Phase 7: Enable Zygisk** | 2 min | 1-3 min | Reboot time |
| **Total** | **11 min** | **6-22 min** | Network + Boot |

### Success Rates by Device Type

| Device Type | Success Rate | Common Issues |
|-------------|--------------|---------------|
| **Real Android Phone** | 85-90% | Bootloader unlock required |
| **LDPlayer Emulator** | 95%+ | Excellent compatibility |
| **NoxPlayer Emulator** | 90%+ | Usually pre-rooted |
| **BlueStacks 5** | 60-70% | Limited fastboot support |
| **MuMu Player** | 85%+ | Varies by version |
| **Real Tablet** | 80-85% | Similar to phones |

### Performance Optimization Tips

**1. Pre-download Magisk**
```bash
# Download once, reuse for multiple devices
uv run adb-magisk-download.py --version 30.6 --output-dir ~/magisk-files
# Time saved: ~2 minutes per device
```

**2. Use SSD for File Operations**
```bash
# Use SSD directory for output
--output-dir /mnt/ssd/magisk  # Instead of /tmp (may be tmpfs)
# Time saved: ~20-30 seconds
```

**3. Increase Timeouts on Slow Networks**
```bash
# For slow network/devices
--timeout-download 120 \
--timeout-patch 180 \
--timeout-flash 120
# Prevents false failures
```

**4. Parallel Processing for Multiple Devices**
```bash
# Install on multiple devices simultaneously
for device in "127.0.0.1:5555" "127.0.0.1:5556" "127.0.0.1:5557"; do
    (uv run magisk-complete-install.py --device $device) &
done
wait  # Wait for all to complete
# Time saved: ~10 minutes for 3 devices
```

### Expected System Resource Usage

| Resource | During Download | During Patch | During Flash |
|----------|-----------------|--------------|--------------|
| **CPU** | 5-10% | 20-40% | 5-10% |
| **RAM** | 100 MB | 200 MB | 50 MB |
| **Disk I/O** | 1-2 MB/s | 10-20 MB/s | 5-10 MB/s |
| **Network** | 1-5 Mbps | 0 | 0 |

### Automation Performance (with Zygisk)

After Magisk + Zygisk installation:

| Metric | Value | Notes |
|--------|-------|-------|
| **OCR Detection Speed** | 1-2s | Per screen capture |
| **UI Navigation Latency** | 0.5-1s | Tap/swipe response |
| **State Verification** | 0.5-1s | Screenshot comparison |
| **Full Automation Loop** | 3-5s | Detect → Act → Verify |
| **Daily Routine Completion** | 5-15 min | Depends on game tasks |

### Reliability Metrics

| Metric | Without Magisk | With Magisk + Zygisk |
|--------|----------------|---------------------|
| **Detection Rate by Games** | 90%+ | <5% |
| **Ban Rate** | 20-40% | <1% |
| **Automation Success Rate** | 60-70% | 95%+ |
| **Play Integrity Pass Rate** | 0% | 98%+ |

---

## 10. FAQ

### General Questions

**Q: Do I need to root my device to use AdbAutoPlayer?**

A: Yes and no. AdbAutoPlayer itself doesn't require root for basic automation (tap/swipe/OCR). However, **Magisk + Zygisk** are required to:
- Hide automation from game detection
- Pass Play Integrity checks
- Prevent bans

So while AdbAutoPlayer works without root, you won't be able to use it safely on detection-enabled games.

---

**Q: Will this void my device warranty?**

A: **Yes**, unlocking the bootloader typically voids warranty on most devices. However:
- Emulators (LDPlayer, NoxPlayer) have no warranty concerns
- Some manufacturers (OnePlus, Xiaomi) allow bootloader unlock without warranty loss
- You can relock bootloader after uninstalling Magisk (may restore warranty)

---

**Q: Can I uninstall Magisk after installation?**

A: Yes, Magisk provides an uninstall option:

```bash
# Method 1: Via Magisk Manager app
# Settings → Uninstall → Complete Uninstall

# Method 2: Flash original boot image
fastboot flash boot boot_stock.img
fastboot reboot
```

This removes all Magisk modifications and restores device to stock state.

---

**Q: Is Magisk detectable by games?**

A: **Not with proper configuration**. When you:
1. Install Magisk (systemless root)
2. Enable Zygisk (API hook injection)
3. Install PlayIntegrityFork (bypass module)
4. Enable Shamiko (Magisk hiding)

Games **cannot detect** Magisk, root, or automation. Detection rate drops to <5%.

---

**Q: What's the difference between Magisk and SuperSU?**

A: **Magisk** is the modern, recommended root solution:

| Feature | Magisk | SuperSU |
|---------|--------|---------|
| **Systemless** | ✅ Yes (doesn't modify /system) | ❌ No (modifies /system) |
| **SafetyNet Bypass** | ✅ Yes (with Zygisk) | ❌ No (easily detected) |
| **Module Support** | ✅ Yes (extensive ecosystem) | ⚠️ Limited |
| **Active Development** | ✅ Yes (updated regularly) | ❌ Abandoned (2017) |
| **Android 12+ Support** | ✅ Yes | ❌ No |

**Recommendation**: Always use Magisk over SuperSU.

---

### Installation Questions

**Q: My device won't boot after flashing. What do I do?**

A: Follow the **Emergency Recovery** procedure:

```bash
# 1. Force reboot to fastboot
# Hold Power + Volume Down for 10 seconds

# 2. Flash original boot image
fastboot flash boot /tmp/magisk/boot_original_backup.img
fastboot reboot
```

If you don't have a backup:
- Download stock firmware from manufacturer
- Extract boot.img
- Flash via fastboot

**Prevention**: Always backup original boot image before flashing.

---

**Q: Do I need to unlock bootloader for emulators?**

A: **Usually no**. Most emulators (LDPlayer, NoxPlayer) have unlocked bootloaders by default or provide root toggle in settings:

- **LDPlayer**: Settings → Other settings → Root permission
- **NoxPlayer**: System settings → Root → ON
- **MuMu Player**: Settings → Root access
- **BlueStacks**: No root support (limited Magisk compatibility)

---

**Q: Can I install Magisk without a computer?**

A: **Partially**. You can:
1. Install Magisk Manager app (download APK)
2. Patch boot image on device

But you **still need fastboot** (computer required) to flash the patched boot image. There's no way to flash boot without fastboot/recovery.

---

**Q: Will Magisk work on Android 14/15?**

A: **Yes**, Magisk v30.0+ fully supports Android 14 and 15. However:
- Some modules may need updates
- Zygisk compatibility depends on module developers
- Always use latest Magisk version for newest Android

---

**Q: What if I have A/B partitions?**

A: The installation scripts **automatically handle A/B partitions**:

```bash
# Script detects active slot
adb shell getprop ro.boot.slot_suffix  # Returns: _a or _b

# Flashes to correct slot
fastboot flash boot_a patched_boot.img  # If slot_a is active
```

No manual intervention needed.

---

### Zygisk Questions

**Q: What's the difference between Magisk and Zygisk?**

A: **Magisk** provides root (system-level access). **Zygisk** provides API hooking (process-level modification):

| Feature | Magisk | Zygisk |
|---------|--------|--------|
| **Purpose** | Root access | API hooking |
| **Modifies** | Boot image | App processes |
| **Detection** | Detectable | Harder to detect |
| **Modules** | File-based | Process-based |
| **Required for automation** | Optional | **Required** |

**Analogy**: Magisk is the foundation, Zygisk is the invisibility cloak.

---

**Q: Do I need to enable Zygisk for all apps?**

A: **No**, Zygisk only hooks apps that have compatible modules installed. For example:
- Games with Play Integrity checks → Need PlayIntegrityFork module
- Banking apps → Need Shamiko module
- Other apps → No module needed, Zygisk does nothing

---

**Q: Can I use Zygisk without Magisk?**

A: **No**, Zygisk is built into Magisk. You must install Magisk first, then enable Zygisk within Magisk Manager.

---

**Q: Why does Zygisk require a reboot?**

A: Zygisk hooks into the **Zygote process** (the parent of all Android apps). Zygote starts during Android boot, so Zygisk must be enabled **before Zygote starts**, requiring a reboot.

---

### Game Automation Questions

**Q: Will I get banned for using AdbAutoPlayer with Magisk?**

A: **Unlikely**, if configured properly:

| Configuration | Ban Risk |
|---------------|----------|
| **AdbAutoPlayer only (no Magisk)** | 80-90% |
| **Magisk + Zygisk (no modules)** | 40-60% |
| **Magisk + Zygisk + PlayIntegrityFork** | <5% |
| **Above + Shamiko + proper configuration** | <1% |

**Key**: The more layers of detection bypass, the safer.

---

**Q: Which games work with this setup?**

A: Most mobile games work, including:
- **AFK Journey** (primary use case)
- **Genshin Impact** (with proper modules)
- **Honkai: Star Rail**
- **Epic Seven**
- **Summoners War**
- **Raid: Shadow Legends**

Games with **kernel-level anti-cheat** (rare on mobile) may not work.

---

**Q: Can I use multiple automation tools simultaneously?**

A: **Not recommended**. Running multiple automation tools (e.g., AdbAutoPlayer + another bot) can:
- Conflict with each other (both trying to control device)
- Increase detection risk (more activity = more suspicious)
- Cause crashes or unexpected behavior

Stick to one automation tool at a time.

---

**Q: How often should I update Magisk?**

A: **Update when**:
- New Android version released
- Game updates detection methods
- Security patches released
- New bypass modules available

**Check for updates**: Monthly

```bash
# Check current version
adb shell su -c "magisk -v"

# Download latest
uv run adb-magisk-download.py --version latest
```

---

### Troubleshooting Questions

**Q: Why does Magisk show "Installed: N/A"?**

A: **Cause**: Magisk Manager app is installed, but Magisk is **not integrated with the system boot**.

**Solution**: Complete Phase 4-5 (patch and flash boot image).

---

**Q: My device is stuck in a bootloop. Help!**

A: **Immediate action**:

```bash
# 1. Force power off (hold Power 10s)
# 2. Boot to fastboot (hold Power + Vol Down)
# 3. Flash original boot
fastboot flash boot boot_stock.img
fastboot reboot
```

**Prevention**: Always backup original boot before flashing.

---

**Q: Zygisk won't enable. What's wrong?**

A: **Common causes**:

1. **Old Magisk version**: Update to v30.0+
2. **Conflicting module**: Disable all modules, enable Zygisk, re-enable modules one by one
3. **Corrupted installation**: Reinstall Magisk from scratch

---

**Q: Play Integrity still fails after installing PlayIntegrityFork. Why?**

A: **Check these**:

1. **Zygisk enabled**: Verify in Magisk settings
2. **Module installed correctly**: Check Magisk → Modules
3. **Module enabled**: Toggle should be ON
4. **Device rebooted**: Module needs reboot to activate
5. **Google Play Services cached**: Clear cache: `adb shell pm clear com.google.android.gms`

---

**Q: Can I use Magisk on a work/enterprise device?**

A: **Not recommended**. Unlocking bootloader and rooting likely violates enterprise policy and may:
- Trigger MDM (Mobile Device Management) alerts
- Wipe device remotely
- Void IT support
- Get you fired (seriously)

Use a personal device for automation.

---

### Advanced Questions

**Q: Can I install Magisk via custom recovery (TWRP)?**

A: **Yes**, alternative method:

```bash
# 1. Download Magisk zip
wget https://github.com/topjohnwu/Magisk/releases/download/v30.6/Magisk-v30.6.zip

# 2. Boot to TWRP
adb reboot recovery

# 3. Flash Magisk zip via TWRP
# Install → Select Magisk-v30.6.zip → Swipe to flash

# 4. Reboot
# Reboot → System
```

**Advantage**: No need for fastboot/boot image extraction.

---

**Q: How do I update Magisk without losing modules?**

A: **In-app update** preserves modules:

```bash
# Method 1: Magisk Manager OTA update
# Open Magisk → Tap "Update" → Install → Reboot

# Method 2: Flash new APK
uv run adb-magisk-install-app.py --device 127.0.0.1:5555 --apk-path Magisk-v30.7.apk --force
# Modules remain intact
```

---

**Q: Can I use Magisk with custom ROMs (LineageOS, etc.)?**

A: **Yes**, Magisk works with most custom ROMs. In fact, custom ROMs often make Magisk installation **easier** because:
- Bootloader usually pre-unlocked
- Custom recovery (TWRP) pre-installed
- Better compatibility with modifications

---

**Q: What's the difference between Magisk and Magisk Delta?**

A: **Magisk Delta** is a fork with additional features:

| Feature | Magisk | Magisk Delta |
|---------|--------|--------------|
| **Zygisk** | ✅ Built-in | ✅ Built-in |
| **SuList** | ❌ No | ✅ Yes (per-app su) |
| **Hide App** | ⚠️ Basic | ✅ Advanced |
| **Updates** | ✅ Official | ⚠️ Community |

**Recommendation**: Use official Magisk unless you need Delta-specific features.

---

**Q: Can I automate the entire Magisk installation?**

A: **Yes**, the workflow script automates all phases:

```bash
# Fully automated installation
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflow/magisk-complete-install.toon \
    --param device=127.0.0.1:5555 \
    --param version=30.6 \
    --param auto_reboot=true
```

This runs all 7 phases automatically with minimal user intervention.

---

## Additional Resources

### Official Links
- **Magisk GitHub**: https://github.com/topjohnwu/Magisk
- **Magisk Releases**: https://github.com/topjohnwu/Magisk/releases
- **Magisk Documentation**: https://topjohnwu.github.io/Magisk/
- **Zygisk Documentation**: https://topjohnwu.github.io/Magisk/guides.html#zygisk

### Community Support
- **XDA Magisk Forum**: https://forum.xda-developers.com/f/magisk.5903/
- **Magisk Discord**: https://discord.gg/magisk
- **r/Magisk Subreddit**: https://reddit.com/r/Magisk

### Related Modules
- **PlayIntegrityFork**: https://github.com/chiteroman/PlayIntegrityFork
- **Shamiko**: https://github.com/LSPosed/LSPosed.github.io/releases
- **Zygisk-Next**: https://github.com/Dr-TSNG/ZygiskNext

### AdbAutoPlayer Integration
- **AdbAutoPlayer Docs**: https://AdbAutoPlayer.github.io/AdbAutoPlayer/
- **AdbAutoPlayer GitHub**: https://github.com/AdbAutoPlayer/AdbAutoPlayer
- **Discord Support**: https://discord.gg/yaphalla

---

## Document Version

- **Version**: 1.0.0
- **Last Updated**: 2025-12-02
- **Magisk Version**: v30.6
- **Android Version**: 5.0 - 15.0
- **Status**: ✅ Production Ready

---

## License

This guide is part of the AdbAutoPlayer project and follows the same license terms.

---

**Happy Automating!** 🎮🤖
