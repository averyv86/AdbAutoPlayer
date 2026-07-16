# Magisk Boot Patching Scripts - Quick Reference

## Overview

Automated Python scripts for patching Android boot images with Magisk to gain root access on Samsung SM-S908E (Galaxy S22 Ultra) and other Android devices.

## Files Included

```
scripts/
├── README_MAGISK.md              # This file (quick reference)
├── MAGISK_PATCHING_GUIDE.md      # Complete detailed guide
├── boot_img_sources.md           # Boot image download sources
├── extract_magiskboot.py         # Extract magiskboot from Magisk APK
└── magisk_boot_patcher.py        # Main patching script
```

## Prerequisites (5-Minute Setup)

### 1. Install ADB

**macOS**:
```bash
brew install android-platform-tools
```

**Linux**:
```bash
sudo apt install android-tools-adb
```

**Windows**:
- Download: https://developer.android.com/studio/releases/platform-tools
- Extract to `C:\platform-tools\`
- Add to PATH

### 2. Enable USB Debugging on Device

1. Settings → About Phone → Tap "Build Number" 7 times
2. Settings → Developer Options → Enable "USB Debugging"
3. Connect USB cable and authorize computer

### 3. Install Magisk Manager on Device

```bash
# Download latest from GitHub
wget https://github.com/topjohnwu/Magisk/releases/latest/download/Magisk-v27.0.apk

# Install on device
adb install Magisk-v27.0.apk
```

### 4. Verify Setup

```bash
# Check ADB connection
adb devices
# Should show: XXXXXXXXXX    device

# Check Magisk installed
adb shell pm list packages | grep magisk
# Should show: package:com.topjohnwu.magisk
```

## Quick Start (3 Steps)

### Step 1: Get boot.img

**For Samsung SM-S908E**:

```bash
# Check your firmware version
adb shell getprop ro.build.PDA
# Example output: S908EXXU3BWCB

# Download matching firmware from:
# - https://www.sammobile.com/samsung/galaxy-s22-ultra/firmware/SM-S908E/
# - https://samfw.com/firmware/SM-S908E/

# Extract boot.img from AP_*.tar.md5 using 7zip
```

See `boot_img_sources.md` for detailed instructions.

### Step 2: Patch boot.img

**Recommended Method (Uses Magisk App)**:

```bash
python magisk_boot_patcher.py --boot boot.img --method app --output ./patched/
```

**What happens**:
1. Script pushes boot.img to device
2. You manually patch using Magisk app (30 seconds)
3. Script retrieves patched boot.img automatically

**Manual steps on device**:
- Open Magisk Manager
- Tap "Install" → "Select and Patch a File"
- Select `/sdcard/Download/boot_to_patch.img`
- Wait for completion
- Press ENTER in terminal

### Step 3: Flash patched boot

**WARNING**: This requires unlocked bootloader!

```bash
# Reboot to fastboot/bootloader
adb reboot bootloader

# Flash patched boot
fastboot flash boot ./patched/magisk_patched.img

# Reboot
fastboot reboot
```

**First boot may take 5-10 minutes**

## Verification

```bash
# Check root access
adb shell
su
# Should get root prompt: #

# Check Magisk version
adb shell su -c "magisk -v"
```

## Output Files

After successful patching:

```
./patched/
├── magisk_patched.img           # Flash this file
├── magisk_patched.sha256        # Hash for verification
├── boot_original.sha256         # Original hash
└── FLASH_INSTRUCTIONS.txt       # Detailed flashing guide
```

## Advanced: Extract magiskboot (Optional)

Only needed for manual patching method (not recommended):

```bash
# Download from GitHub and extract
python extract_magiskboot.py --output ./tools/

# Pull from device
python extract_magiskboot.py --from-device --output ./tools/

# Use local APK
python extract_magiskboot.py --apk Magisk-v27.0.apk --output ./tools/
```

## Common Issues & Fixes

### "adb: device unauthorized"

**Solution**:
```bash
# Check device screen for authorization prompt
# Tap "Allow" and check "Always allow"
adb devices
```

### "Magisk app not installed"

**Solution**:
```bash
adb install Magisk-v27.0.apk
```

### "Boot loop after flashing"

**Solution**:
```bash
# Flash original boot.img
adb reboot bootloader
fastboot flash boot boot_original.img
fastboot reboot
```

### "fastboot: device not found"

**Solution**:
- Try different USB port (prefer USB 2.0)
- Install fastboot drivers (Windows)
- Use official USB cable

### "SafetyNet fails / Banking apps detect root"

**Solution**:
1. Open Magisk → Settings
2. Enable "Magisk Hide"
3. Select apps to hide from
4. Install Universal SafetyNet Fix module

## Important Warnings

⚠️ **UNLOCKED BOOTLOADER REQUIRED**
- You CANNOT flash modified boot without unlocked bootloader
- Samsung: This voids warranty and trips Knox (irreversible)

⚠️ **FIRMWARE VERSION MUST MATCH**
- Using wrong boot.img can brick your device
- Check version: `adb shell getprop ro.build.PDA`

⚠️ **BACKUP YOUR DATA**
- Unlocking bootloader wipes device
- Keep backups before proceeding

⚠️ **SAMSUNG KNOX**
- Will be tripped (0x1 status - irreversible)
- Samsung Pay will stop working
- Secure Folder may not work

⚠️ **OTA UPDATES**
- Will fail after rooting
- Must manually flash firmware updates

## Samsung-Specific Notes

### Unlocking Bootloader (SM-S908E)

1. Settings → Developer Options → Enable "OEM Unlocking"
2. Power off device
3. Hold Volume Down + Power + Bixby
4. Enter Download Mode
5. Long press Volume Up to unlock bootloader
6. **This wipes all data and trips Knox**

### Flashing with Odin (Alternative to Fastboot)

```bash
# Pack boot.img into AP tar format
tar -cvf AP_magisk_patched.tar magisk_patched.img
md5sum -t AP_magisk_patched.tar >> AP_magisk_patched.tar
mv AP_magisk_patched.tar AP_magisk_patched.tar.md5

# Use Odin to flash (Windows only)
# Download: https://odindownload.com/
```

## Script Options Reference

### magisk_boot_patcher.py

```bash
python magisk_boot_patcher.py [OPTIONS]

Required:
  --boot PATH              Path to boot.img file

Optional:
  --method METHOD          'app' (recommended) or 'manual'
  --magiskboot PATH        magiskboot binary (manual method only)
  --output DIR             Output directory (default: ./magisk_patched)
  --skip-verification      Skip boot.img verification
```

### extract_magiskboot.py

```bash
python extract_magiskboot.py [OPTIONS]

Optional:
  --apk PATH               Local Magisk APK file
  --from-device            Pull APK from connected device
  --device-path PATH       Custom APK path on device
  --output DIR             Output directory (default: ./magisk_tools)
  --arch ARCH              arm64-v8a (default), armeabi-v7a, x86, x86_64
```

## Boot Image Sources (Quick Links)

### Samsung SM-S908E

- **Sammobile**: https://www.sammobile.com/samsung/galaxy-s22-ultra/firmware/SM-S908E/
- **SamFW**: https://samfw.com/firmware/SM-S908E/
- **Samfrew**: https://samfrew.com/model/SM-S908E/

### Generic AOSP (Emulators Only)

- **GSI Images**: https://developer.android.com/topic/generic-system-image/releases
- **Android Source**: https://source.android.com/

See `boot_img_sources.md` for complete list and instructions.

## Documentation

- **Complete Guide**: `MAGISK_PATCHING_GUIDE.md` (detailed step-by-step)
- **Boot Sources**: `boot_img_sources.md` (firmware downloads)
- **This File**: Quick reference for common tasks

## Resources

### Official

- Magisk: https://topjohnwu.github.io/Magisk/
- GitHub: https://github.com/topjohnwu/Magisk
- XDA Forums: https://forum.xda-developers.com/

### Tools

- Platform Tools: https://developer.android.com/studio/releases/platform-tools
- Odin (Samsung): https://odindownload.com/
- Root Checker: https://play.google.com/store/apps/details?id=com.joeykrim.rootcheck

## Command Cheat Sheet

```bash
# === Device Info ===
adb shell getprop ro.product.model        # Device model
adb shell getprop ro.build.version.release # Android version
adb shell getprop ro.build.PDA            # Firmware version
adb shell getprop ro.csc.sales_code       # CSC region code

# === ADB Operations ===
adb devices                               # List connected devices
adb reboot bootloader                     # Reboot to fastboot
adb reboot recovery                       # Reboot to recovery
adb shell                                 # Open shell
adb install app.apk                       # Install APK
adb pull /path/on/device ./local/path     # Pull file
adb push ./local/file /path/on/device     # Push file

# === Fastboot Operations ===
fastboot devices                          # List devices in fastboot
fastboot flash boot boot.img              # Flash boot partition
fastboot reboot                           # Reboot device
fastboot getvar all                       # Get device info

# === Root Verification ===
adb shell su -c "id"                      # Check root (uid=0)
adb shell su -c "magisk -v"               # Check Magisk version
adb shell pm list packages | grep magisk  # Check Magisk installed

# === Boot Image Verification ===
file boot.img                             # Check file type
xxd boot.img | head                       # View hex header
sha256sum boot.img                        # Calculate SHA256
```

## Safety Checklist

Before flashing, verify:

- [ ] Bootloader is unlocked
- [ ] boot.img matches firmware version exactly
- [ ] Full device backup completed
- [ ] Battery is above 50%
- [ ] USB cable is reliable (official or high-quality)
- [ ] Original boot.img saved for recovery
- [ ] Read FLASH_INSTRUCTIONS.txt completely

## Success Criteria

After flashing, you should see:

✅ Device boots normally (may show bootloader warning)
✅ Magisk Manager shows "Installed: v27.x"
✅ `adb shell su` gives root prompt
✅ Root Checker app shows "Root Access: Granted"

If any fail, see MAGISK_PATCHING_GUIDE.md troubleshooting section.

## License

These scripts are provided as-is for educational purposes.

**Use at your own risk.**

---

**For detailed instructions, see**: `MAGISK_PATCHING_GUIDE.md`

**Last Updated**: 2025-12-02
**Tested On**: Samsung SM-S908E, Android 13, Magisk v27.0
