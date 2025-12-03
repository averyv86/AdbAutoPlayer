# Karrot Bypass & Automation Troubleshooting Guide

**Version**: 1.0.0
**Status**: Production Ready
**Last Updated**: 2025-12-02

---

## Quick Diagnostic Tools

### 1. Verify Device Connection
```bash
# Check if device is connected
adb devices

# Get device info
adb shell getprop ro.build.fingerprint
adb shell getprop ro.build.version.sdk
```

### 2. Check Magisk Status
```bash
# Verify Magisk installed
adb shell which magisk

# Check Magisk version
adb shell magisk --version

# List Magisk modules
adb shell ls /data/adb/modules/

# View Magisk log
adb shell tail -100 /data/adb/magisk.log
```

### 3. Verify PlayIntegrityFork
```bash
# Check if module is installed
adb shell ls /data/adb/modules/ | grep -i playintegrity

# Verify module is active
adb shell getprop ro.playintegrityfix.version

# Check spoof fingerprint
adb shell getprop ro.playintegrityfix.spoof_fingerprint
```

### 4. Monitor Karrot Logs
```bash
# Real-time logcat (Karrot only)
adb logcat | grep "com.nexon.karrot"

# Search for specific errors
adb logcat | grep -i "error\|playintegrity\|integrity"

# Save logcat to file
adb logcat -d > logcat_dump.txt
```

---

## Category 1: Device Connection Issues

### Problem: "adb: command not found"
**Severity**: Critical

**Diagnosis**:
```bash
which adb
echo $PATH
```

**Solutions**:
1. **Install ADB**:
   ```bash
   # macOS
   brew install android-platform-tools

   # Linux
   sudo apt-get install android-tools-adb

   # Windows
   # Download SDK Platform Tools from Google
   ```

2. **Add to PATH**:
   ```bash
   export PATH=$PATH:/path/to/adb/directory
   # Add to ~/.bashrc or ~/.zshrc for persistence
   ```

---

### Problem: "device not found" or "adb: error"
**Severity**: Critical

**Diagnosis**:
```bash
adb devices
# Should show device with "device" status, not "offline"
```

**Solutions**:

1. **Restart ADB daemon**:
   ```bash
   adb kill-server
   adb start-server
   adb devices  # Should reconnect
   ```

2. **Check USB connection**:
   - Unplug and reconnect USB cable
   - Try different USB port
   - Check cable for damage

3. **Enable USB Debugging**:
   - Settings > Developer Options > USB Debugging (toggle ON)
   - Settings > Developer Options > USB Debugging (Security) > Allow

4. **Reset ADB permissions**:
   ```bash
   adb kill-server
   rm ~/.android/adb_key*
   adb start-server
   # Re-authorize device when prompted
   ```

---

### Problem: "offline" device status
**Severity**: High

**Diagnosis**:
```bash
adb devices -l
# Shows "offline" status
```

**Solutions**:

1. **Restart device**:
   ```bash
   adb reboot
   # Wait 30 seconds
   adb devices  # Check connection
   ```

2. **Reconnect via network ADB**:
   ```bash
   adb connect <device_ip>:5555
   adb devices  # Verify connection
   ```

3. **Check device authentication**:
   - On device: Accept "Allow USB debugging" prompt
   - Verify fingerprint matches ADB host key

---

## Category 2: Magisk Installation Issues

### Problem: "Magisk not installed" (pre-flight validation fails)
**Severity**: Critical

**Diagnosis**:
```bash
adb shell which magisk
# Should output: /sbin/magisk or /system/xbin/magisk
# If empty, Magisk is not installed
```

**Solutions**:

1. **Install Magisk via App**:
   - Download Magisk APK from: https://github.com/topjohnwu/Magisk/releases
   - `adb install path/to/magisk.apk`
   - Open app and select "Install"

2. **Flash via TWRP** (if TWRP available):
   - Download Magisk.zip
   - Boot into TWRP
   - Install > Select Magisk.zip
   - Reboot

3. **Verify installation**:
   ```bash
   adb reboot
   sleep 60
   adb shell magisk --version
   ```

---

### Problem: "Zygisk not enabled"
**Severity**: Critical

**Diagnosis**:
```bash
adb shell getprop ro.zygote
# Should show: zygote64_32 or zygote32_64
```

**Solutions**:

1. **Enable via Magisk Manager**:
   - Open Magisk app
   - Settings > Zygisk > Toggle ON
   - Reboot device

2. **Verify Zygisk is active**:
   ```bash
   adb shell getprop ro.zygote
   # Confirm output shows zygote configuration
   ```

3. **If Zygisk unavailable** (older Magisk):
   - Update Magisk to latest version
   - Latest versions have Zygisk built-in

---

## Category 3: PlayIntegrityFork Issues

### Problem: "PlayIntegrityFork module not installed"
**Severity**: Critical

**Diagnosis**:
```bash
adb shell ls /data/adb/modules/ | grep -i playintegrity
# Should show: PlayIntegrityFork or playintegrity-fix
```

**Solutions**:

1. **Install via Magisk Manager**:
   - Open Magisk app
   - Modules > + (Install from repository)
   - Search: "PlayIntegrityFork"
   - Select and install
   - Reboot

2. **Manual installation**:
   ```bash
   # Download PlayIntegrityFork.zip from releases
   adb push PlayIntegrityFork.zip /sdcard/
   adb shell
   su
   magisk module load /sdcard/PlayIntegrityFork.zip
   # Or reboot and install via Magisk
   ```

3. **Verify installation**:
   ```bash
   adb shell ls /data/adb/modules/PlayIntegrityFork/
   # Should show: module.prop, system.prop, etc.
   ```

---

### Problem: "PlayIntegrityFork module not active"
**Severity**: Critical

**Diagnosis**:
```bash
adb shell getprop ro.playintegrityfix.version
# Should show version number (e.g., 4.3.0)
# If empty, module is not active
```

**Solutions**:

1. **Enable module**:
   ```bash
   adb shell magisk module enable PlayIntegrityFork
   adb reboot
   # Verify after reboot
   ```

2. **Check module configuration**:
   ```bash
   adb shell cat /data/adb/modules/PlayIntegrityFork/module.prop
   # Verify: disable=0 (not disabled)
   ```

3. **Reinstall if corrupted**:
   ```bash
   # Disable module
   adb shell magisk module disable PlayIntegrityFork
   # Remove module
   adb shell rm -rf /data/adb/modules/PlayIntegrityFork
   adb reboot
   # Reinstall via Magisk Manager
   ```

---

### Problem: Error-18 (CLIENT_TRANSIENT_ERROR) still appears
**Severity**: High

**Diagnosis**:
```bash
adb logcat | grep -i "error-18\|client_transient"
# If found, bypass is not working
```

**Solutions**:

1. **Update PlayIntegrityFork**:
   ```bash
   # In Magisk Manager:
   # Modules > PlayIntegrityFork > Update
   # Or: Remove > Reinstall latest version
   adb reboot
   ```

2. **Check spoof configuration**:
   ```bash
   adb shell getprop ro.playintegrityfix.spoof_fingerprint
   # Should show fingerprint like: google/product/device:version/build

   # If empty, set manually:
   adb shell setprop ro.playintegrityfix.spoof_fingerprint "google/cheetah/cheetah:14/UP1A.231005.007/11948938:user/release-keys"
   ```

3. **Clear and reinstall Karrot**:
   ```bash
   adb shell pm clear com.nexon.karrot
   # Or reinstall from Play Store
   ```

4. **Last resort - Device-specific fix**:
   - Some devices may need custom fingerprints
   - Check PlayIntegrityFork GitHub issues for your device model
   - Download device-specific configuration

---

## Category 4: Karrot App Issues

### Problem: "Karrot app not installed"
**Severity**: Critical

**Diagnosis**:
```bash
adb shell pm list packages | grep karrot
# Should show: package:com.nexon.karrot
```

**Solutions**:

1. **Install via Play Store**:
   - Device screen: Play Store > Search "Karrot"
   - Install app manually
   - Or use `adb install` with APK file

2. **Install via ADB**:
   ```bash
   # Download Karrot APK
   adb install path/to/karrot.apk
   ```

3. **Verify installation**:
   ```bash
   adb shell pm list packages -3 | grep karrot
   # Should show installed app
   ```

---

### Problem: "Karrot crashes on launch"
**Severity**: High

**Diagnosis**:
```bash
adb logcat | grep "com.nexon.karrot"
# Look for: FATAL EXCEPTION, Force Close, etc.
```

**Solutions**:

1. **Clear app cache and data**:
   ```bash
   adb shell pm clear com.nexon.karrot
   adb logcat  # Monitor for errors
   # Restart app
   ```

2. **Check for conflicting apps**:
   ```bash
   adb shell pm list packages | grep -i "mock\|xposed"
   # Some mocking frameworks cause crashes
   ```

3. **Disable Zygisk temporarily**:
   ```bash
   # In Magisk Manager:
   # Settings > Zygisk > Toggle OFF
   # Reboot
   # Test Karrot
   # If works, issue is with Zygisk modules
   ```

4. **Review Karrot requirements**:
   - Minimum Android version required
   - Device RAM requirements
   - Storage space (at least 500MB free)

---

### Problem: "App crashes after login"
**Severity**: High

**Diagnosis**:
```bash
adb logcat -d | grep "com.nexon.karrot" | tail -50
# Look for specific error messages
```

**Solutions**:

1. **Check Magisk modules for conflicts**:
   ```bash
   adb shell ls /data/adb/modules/
   # Disable modules one by one to identify conflict:
   adb shell magisk module disable <module_name>
   adb reboot
   ```

2. **Update Karrot app**:
   - Check Play Store for updates
   - Install latest version
   - Clear cache between updates

3. **Verify device specifications**:
   ```bash
   adb shell getprop ro.product.model
   adb shell getprop ro.build.version.sdk
   adb shell dumpsys meminfo | grep MemTotal
   # Ensure device meets minimum requirements
   ```

---

## Category 5: Detection Issues

### Problem: "Emulator still detected despite bypass"
**Severity**: High

**Diagnosis**:
```bash
# Run detection check
uv run .claude/skills/adb-karrot/scripts/adb-karrot-check-detection.py \
  --device localhost:5555 \
  --launch \
  --detailed

# Check logcat for detection keywords
adb logcat | grep -i "emulator\|virtual\|spoofed\|detected"
```

**Solutions**:

1. **Update to latest security patches**:
   ```bash
   # PlayIntegrityFork updates frequently
   adb shell magisk module disable PlayIntegrityFork
   # Reinstall latest version via Magisk Manager
   adb reboot
   ```

2. **Check device properties**:
   ```bash
   # Verify no obvious emulator properties
   adb shell getprop | grep -i "emulator\|qemu\|virtual"
   # Should return no results
   ```

3. **Advanced: Edit spoof properties**:
   ```bash
   # Get real device fingerprint from a real device
   # Copy to PlayIntegrityFork configuration
   adb shell getprop ro.playintegrityfix.spoof_fingerprint
   ```

4. **Check Google Play Services**:
   ```bash
   adb shell pm list packages | grep "google.android.gms"
   # Ensure Play Services updated
   adb shell am start -n com.google.android.gms/.app.settings.FirstSigninActivity
   ```

---

## Category 6: Performance and Stability

### Problem: "Device becomes slow after bypass"
**Severity**: Medium

**Diagnosis**:
```bash
adb shell top -n 1
adb shell dumpsys meminfo
# Check for high CPU/memory usage from Magisk modules
```

**Solutions**:

1. **Identify resource-heavy modules**:
   ```bash
   # Check which modules consume most resources
   adb shell top -o %CPU,COMMAND | head -20
   # Disable non-essential modules
   ```

2. **Clear Magisk cache**:
   ```bash
   adb shell su -c "rm -rf /data/adb/cache/*"
   adb reboot
   ```

3. **Optimize module selection**:
   - Keep only PlayIntegrityFork
   - Disable other modules
   - Re-enable if bypass still works

---

### Problem: "High battery drain after bypass"
**Severity**: Medium

**Diagnosis**:
```bash
adb shell dumpsys battery
adb shell dumpsys batterystats
# Check for high wake lock usage
```

**Solutions**:

1. **Check wake locks**:
   ```bash
   adb shell dumpsys wakelock | grep -i magisk
   # May indicate CPU held awake by Magisk
   ```

2. **Disable debug logging**:
   ```bash
   adb shell setprop persist.log.tag DEBUG
   # Or disable SELinux debug if enabled
   ```

3. **Profile battery usage**:
   - Settings > Battery > Usage by app
   - Check if Karrot or Magisk using excessive battery
   - Consider disabling Zygisk if unnecessary

---

## Category 7: Advanced Diagnostics

### Collecting Debug Information

```bash
#!/bin/bash
# Comprehensive debug information collection

echo "=== Device Information ==="
adb shell getprop ro.build.fingerprint
adb shell getprop ro.build.version.sdk
adb shell getprop ro.product.model

echo "=== Magisk Information ==="
adb shell which magisk
adb shell magisk --version
adb shell ls -la /data/adb/modules/

echo "=== PlayIntegrityFork Status ==="
adb shell getprop ro.playintegrityfix.version
adb shell getprop ro.playintegrityfix.spoof_fingerprint

echo "=== Karrot Status ==="
adb shell pm list packages | grep karrot
adb shell pm path com.nexon.karrot

echo "=== Recent Errors ==="
adb logcat -d | grep -i "error\|exception\|playintegrity" | tail -20

echo "=== Storage Status ==="
adb shell df -h /data

echo "=== Memory Status ==="
adb shell dumpsys meminfo | grep MemFree
```

### Recovery Procedures

#### Safe Mode
```bash
# Disable all Magisk modules
adb shell magisk module disable --all
adb reboot
# Test if issue persists
# If resolved, enable modules one by one
```

#### Factory Reset (Last Resort)
```bash
# WARNING: This will erase all data
adb reboot recovery
# From recovery menu: Wipe data / Factory reset
# Reboot and reinstall Magisk + PlayIntegrityFork
```

#### Rollback to Previous Magisk
```bash
# If latest Magisk causes issues:
# 1. Download previous Magisk version
# 2. Disable all modules first
# 3. Uninstall current Magisk
# 4. Install previous version
# 5. Re-enable modules one by one
```

---

## Contact and Support

### Relevant Repositories
- **Magisk**: https://github.com/topjohnwu/Magisk
- **PlayIntegrityFork**: https://github.com/chiteroman/PlayIntegrityFork
- **Karrot (Nexon)**: Play Store official app

### Log Files to Provide When Seeking Help
1. Full logcat dump: `adb logcat -d > logcat.txt`
2. Magisk log: `/data/adb/magisk.log`
3. Device info: `adb shell getprop > device_info.txt`
4. Module list: `adb shell ls -la /data/adb/modules/`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-02 | Initial comprehensive troubleshooting guide |

---

**Last Updated**: 2025-12-02
**Status**: ✓ Production Ready
**Severity Levels**: Critical (blocks bypass) > High (degraded function) > Medium (cosmetic/optional)
