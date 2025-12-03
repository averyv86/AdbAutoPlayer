# Master Bypass Workflow Execution Guide

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2025-12-02

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Workflow Stages](#workflow-stages)
4. [Execution Steps](#execution-steps)
5. [Success Criteria](#success-criteria)
6. [Error Handling](#error-handling)
7. [Rollback Procedures](#rollback-procedures)

---

## Overview

The Master Bypass Workflow is a comprehensive 3-stage automation sequence that:

1. **Verifies device prerequisites** (pre-flight checks)
2. **Executes Play Integrity bypass** (Magisk + PlayIntegrityFork)
3. **Validates successful bypass** (login + functionality verification)

**Total Duration**: ~10-15 minutes
**Success Rate**: Depends on proper Magisk/PlayIntegrityFork installation

---

## Prerequisites

### Device Requirements

- ✓ Android API 31+ (Android 12 or later)
- ✓ Magisk installed with Zygisk enabled
- ✓ PlayIntegrityFork module installed and active
- ✓ Minimum 500MB free storage
- ✓ Karrot app installed from Play Store
- ✓ Device connected via ADB

### Software Requirements

- ✓ ADB (Android Debug Bridge) installed
- ✓ Python 3.12+
- ✓ uv package manager
- ✓ uiautomator2 3.0.0+

### Before Starting

```bash
# Verify ADB connection
adb devices

# Verify device is recognized
adb -s <device_id> shell getprop ro.build.version.release
```

---

## Workflow Stages

### Stage 1: Pre-Flight Validation (2-3 minutes)

**Script**: `preflight-validation.py`

**Checks Performed**:
- Device accessibility via ADB
- Android version compatibility (API 31+)
- Magisk installation
- Zygisk enabled status
- PlayIntegrityFork module presence
- PlayIntegrityFork module active
- Karrot app installed
- Available storage space
- Bootloader status

**Command**:
```bash
uv run .claude/skills/adb-bypass/scripts/preflight-validation.py \
  --device localhost:5555 \
  --verbose
```

**Success Indicator**: All critical checks pass (green ✓)

**Failure Indicators**:
- ✗ Magisk not installed → Install Magisk first
- ✗ PlayIntegrityFork not found → Install via Magisk Manager
- ✗ Karrot app missing → Install from Play Store

---

### Stage 2: Play Integrity Bypass Execution (5-10 minutes)

**Workflow File**: `bypass.toon`

**Sub-Stages**:

#### 2a. Device Pre-Flight (30s)
- Clear app cache
- Verify device state

#### 2b. Magisk Verification (45s)
- Check Magisk installation path
- Verify Zygisk is active
- Confirm PlayIntegrityFork module

#### 2c. App Launch (30s)
- Launch Karrot app
- Wait for initialization

#### 2d. Detection Monitoring (120s)
- Monitor for Error-18 (CLIENT_TRANSIENT_ERROR)
- Watch for crash indicators
- Capture logcat for debug

#### 2e. Bypass Verification (60s)
- Verify Play Integrity passes
- Confirm app stability

**Success Criteria**:
- ✓ Play Integrity check passes
- ✓ No Error-18 detected
- ✓ App launches successfully
- ✓ No crashes or ANR (Application Not Responding)
- ✓ Home screen accessible

---

### Stage 3: Authentication & Validation (3-5 minutes)

**Workflow Files**: `login.toon` + `validation.toon`

**3a. Login Workflow**:
- Email input and validation
- Password entry
- 2FA handling (if enabled)
- Home screen verification

**3b. Functionality Validation**:
- Navigation elements check
- Core features accessibility (Battle, Matching, Inventory)
- Performance baseline capture
- Final status report

**Success Criteria**:
- ✓ Successfully logged in
- ✓ Home screen reachable
- ✓ Navigation menu accessible
- ✓ No error dialogs present
- ✓ Core features functional
- ✓ App stability maintained

---

## Execution Steps

### Quick Start (Automated)

```bash
# 1. Navigate to project root
cd /path/to/AdbAutoPlayer

# 2. Run pre-flight validation
uv run .claude/skills/adb-bypass/scripts/preflight-validation.py \
  --device localhost:5555 \
  --verbose

# 3. If all checks pass, proceed with bypass
# (Implementation depends on workflow orchestration engine)

# 4. Monitor bypass progress via logcat
adb -s localhost:5555 logcat | grep -E "PlayIntegrity|Error-18|com.nexon.karrot"

# 5. Check for detection indicators
uv run .claude/skills/adb-karrot/scripts/adb-karrot-check-detection.py \
  --device localhost:5555 \
  --launch \
  --detailed
```

### Manual Step-by-Step

```bash
# Step 1: Pre-flight checks
uv run .claude/skills/adb-bypass/scripts/preflight-validation.py \
  --device localhost:5555

# Step 2: Clear logcat for clean slate
adb -s localhost:5555 logcat -c

# Step 3: Launch Karrot app
adb -s localhost:5555 shell am start -n com.nexon.karrot/.MainActivity

# Step 4: Wait for app initialization (2-3 minutes)
sleep 180

# Step 5: Monitor logcat for errors
adb -s localhost:5555 logcat -d | grep -i "playintegrity\|error-18\|integrity"

# Step 6: Check for detection
uv run .claude/skills/adb-karrot/scripts/adb-karrot-check-detection.py \
  --device localhost:5555 \
  --detailed
```

---

## Success Criteria

### Bypass Successful When:

```
✓ Pre-flight validation: All critical checks pass
✓ Error-18 detection: None found in logcat
✓ App stability: Launches without crashes
✓ Home screen: Accessible and responsive
✓ Navigation: Menu accessible
✓ Functionality: Core features work
✓ Detection check: No emulator detected
```

### Exit Codes

| Code | Status | Meaning |
|------|--------|---------|
| 0 | Success | Bypass working, no detection |
| 1 | Warning | Potential detection indicators |
| 2 | Error | Emulator/device detected |
| 3 | Critical | Device not accessible |

---

## Error Handling

### Common Issues and Solutions

#### Issue 1: "Device not found"
```
Error: Device localhost:5555 not accessible
Solution:
  - Verify ADB connection: adb devices
  - Restart ADB: adb kill-server && adb start-server
  - Check device ID is correct
```

#### Issue 2: "Magisk not installed"
```
Error: Magisk installation check failed
Solution:
  - Download Magisk APK from GitHub
  - Flash via TWRP or use Magisk installer
  - Verify: adb shell which magisk
```

#### Issue 3: "PlayIntegrityFork not found"
```
Error: PlayIntegrityFork module not installed
Solution:
  - Download PlayIntegrityFork from Releases
  - Install via Magisk Manager > Modules
  - Reboot device
  - Verify: adb shell getprop ro.playintegrityfix.version
```

#### Issue 4: "Error-18 detected"
```
Error: CLIENT_TRANSIENT_ERROR in logcat
Solution:
  - PlayIntegrityFork version may be outdated
  - Update to latest version
  - Clear Karrot app cache: adb shell pm clear com.nexon.karrot
  - Reinstall Karrot from Play Store
```

#### Issue 5: "Integrity check still failing"
```
Error: Device still detected as emulator
Solution:
  - Verify Zygisk enabled: adb shell getprop ro.zygote
  - Check spoof profile: adb shell getprop ro.playintegrityfix.spoof_fingerprint
  - Ensure PlayIntegrityFork is latest version
  - Consider device-specific modifications
```

#### Issue 6: "App crashes on launch"
```
Error: Karrot force closes
Solution:
  - Clear app data: adb shell pm clear com.nexon.karrot
  - Reinstall app
  - Check Android version compatibility
  - Review logcat for specific crash: adb logcat
```

---

## Rollback Procedures

### Disable PlayIntegrityFork

If bypass causes issues:

```bash
# Disable module (keeps installed)
adb shell magisk module disable PlayIntegrityFork

# Reboot
adb reboot

# Verify disabled
adb shell getprop ro.playintegrityfix.version
# Should be empty
```

### Clear Karrot App Data

```bash
adb shell pm clear com.nexon.karrot
```

### Full Reset

```bash
# Uninstall Karrot
adb shell pm uninstall --user 0 com.nexon.karrot

# Clear package cache
adb shell pm cache-rm com.nexon.karrot

# Reinstall from Play Store
# (Manual installation required)
```

### Disable Magisk Temporarily

```bash
# Boot into Safe Mode (device specific)
# Usually: Vol Down + Power at boot

# Or via Magisk Manager:
# Settings > Superuser > Toggle off
```

---

## Monitoring and Debugging

### Real-Time Monitoring

```bash
# Watch logcat during bypass
adb logcat | grep -E "PlayIntegrity|Error|crash|Karrot"

# Monitor system resources
adb shell top -n 1

# Check device integrity status
adb shell getprop ro.boot.veritymode
```

### Log Collection

```bash
# Save full logcat to file
adb logcat -d > bypass_debug_$(date +%s).log

# Save Magisk log
adb shell cat /data/adb/magisk.log > magisk_debug.log

# Save Karrot crash log
adb shell logcat -d | grep "Karrot\|com.nexon.karrot" > karrot_log.log
```

### Performance Baseline

```bash
# Before bypass
adb shell dumpsys meminfo com.nexon.karrot > before_bypass.txt

# After bypass
adb shell dumpsys meminfo com.nexon.karrot > after_bypass.txt

# Compare memory usage
diff before_bypass.txt after_bypass.txt
```

---

## Success Report Template

```
╔══════════════════════════════════════════════════════════╗
║        KARROT BYPASS WORKFLOW - SUCCESS REPORT          ║
╚══════════════════════════════════════════════════════════╝

Date: 2025-12-02
Device: localhost:5555
Android Version: API 33 (Android 13)

PRE-FLIGHT VALIDATION:
  ✓ Device connection
  ✓ Android version check
  ✓ Magisk installation
  ✓ Zygisk enabled
  ✓ PlayIntegrityFork active
  ✓ Karrot app present
  ✓ Storage available

BYPASS EXECUTION:
  ✓ App launched successfully
  ✓ No Error-18 detected
  ✓ Integrity check passed
  ✓ No crashes reported

LOGIN & VALIDATION:
  ✓ Successfully logged in
  ✓ Home screen accessible
  ✓ Navigation working
  ✓ Core features functional

FINAL STATUS: ✓ BYPASS SUCCESSFUL

Next Steps:
  - Device ready for Karrot automation
  - Can proceed with game automation scripts
  - Monitor for any detection after major updates
```

---

## Additional Resources

- **TOON Workflows**: `.moai/workflows/`
  - bypass.toon - Detailed bypass workflow
  - login.toon - Login automation
  - validation.toon - Functionality validation

- **Scripts**: `.claude/skills/`
  - adb-bypass/ - Bypass utilities
  - adb-karrot/ - Karrot-specific tools
  - adb-screen-detection/ - Screen detection helpers

- **Coordinate Maps**: `./coord_maps/`
  - Resolution-specific coordinate mappings
  - Element position data for different devices

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-02 | Initial release with 3-stage workflow |

---

**Last Updated**: 2025-12-02
**Status**: ✓ Production Ready
**Support**: For issues, check troubleshooting guide or review workflow TOON files
