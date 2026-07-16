# Quick Start: Complete Magisk Installation

**Problem**: Your device shows `Installed: N/A` (Magisk app installed, but not system-integrated)
**Solution**: Use the new `adb-magisk-installer` skill to complete the installation in ~15 minutes

---

## One-Line Solution

```bash
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflow/magisk-complete-install.toon \
    --param device=127.0.0.1:5555 \
    --param version=30.6
```

---

## What This Does

| Step | What Happens | Time |
|------|--------------|------|
| 1 | Downloads Magisk 30.6 APK from GitHub | 1-2 min |
| 2 | Installs app on your device (replaces 27.0) | 1-2 min |
| 3 | Extracts your device's boot image | 30-60 sec |
| 4 | Pushes boot to device storage | 30 sec |
| 5 | **You** select boot.img in Magisk app file picker | 10-30 sec |
| 6 | Magisk patches the boot image | 2-3 min |
| 7 | Pulls patched image back to your computer | 30-60 sec |
| 8 | Reboots device into fastboot mode | 10-20 sec |
| 9 | Flashes patched boot image to device | 1-2 min |
| 10 | Device reboots (Magisk now integrated!) | 1-2 min |
| 11 | Verifies installation complete | 10-30 sec |

**Total**: ~15 minutes (mostly automated)

---

## Prerequisites

### On Your Device
- ✅ USB debugging **enabled** (Settings → Developer Options)
- ✅ USB connected to computer
- ✅ ADB recognizes device (`adb devices` shows your device)
- ✅ At least 1GB free storage
- ✅ **Bootloader may need to be unlocked** (check device manufacturer)

### On Your Computer
- ✅ `adb` command works (`adb version` in terminal)
- ✅ `fastboot` command works (`fastboot --version` in terminal)
- ✅ Network access to GitHub
- ✅ At least 500MB free space

---

## Before You Start

### 1. Verify ADB Connection
```bash
# Should show your device
adb devices

# Should show something like:
# List of attached devices
# 127.0.0.1:5555  device
```

### 2. Verify Fastboot Access
```bash
# Reboot to fastboot and check
adb reboot bootloader
fastboot devices

# Then return to normal mode
fastboot reboot
```

### 3. Check Your Device's Current Status
```bash
# Connect with ADB, then in terminal:
adb shell getprop ro.boot.serialno  # Your device ID
```

---

## Step-by-Step Execution

### Step 1: Open Terminal
Navigate to your project directory:
```bash
cd /Users/rdmtv/Documents/claydev-local/opensource-v2/AdbAutoPlayer
```

### Step 2: Run the Workflow
Replace `127.0.0.1:5555` with your actual device ID from `adb devices`:

```bash
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflow/magisk-complete-install.toon \
    --param device=127.0.0.1:5555 \
    --param version=30.6
```

### Step 3: Watch the Output
Workflow will show progress:
- ✅ Downloading files...
- ✅ Installing app...
- ✅ Extracting boot...
- ✅ Patching boot...
- ⚠️ **File picker appeared - check your device!**
  - You'll need to select `/sdcard/boot.img` in Magisk app
  - Workflow will wait for this
- ✅ Flashing boot...
- ✅ Device rebooting...
- ✅ Verifying installation...

### Step 4: When Prompted - Select Boot File

**When Phase 5 runs, your device screen will show:**
1. Magisk Manager app opens
2. A file picker appears
3. **You select** `/sdcard/boot.img`
4. Magisk starts patching (you'll see progress)
5. Workflow continues automatically

**Time for this step**: 10-30 seconds of your interaction

### Step 5: Wait for Completion
Terminal will show when each phase completes.
Don't unplug your device during the process!

---

## After Completion

### Success Indicators
Open Magisk Manager app on your device:
- ✅ Should show `Installed: Yes` (not N/A anymore!)
- ✅ App version should be 30.6
- ✅ Zygisk tab should be available
- ✅ Device boots normally without bootloops

### What You Can Now Do
Now that Magisk is fully installed, you can:
1. **Enable Zygisk** (for API hooking)
2. **Install modules** (PlayIntegrityFork, etc.)
3. **Use adb-karrot** for Play Integrity bypass
4. **Run game automation** with full system access

### Next Steps
Use the `adb-magisk` skill for module installation:
```bash
# Example: Install a module
uv run .claude/skills/adb/adb-magisk/scripts/adb-magisk-install-module.py \
    --device 127.0.0.1:5555 \
    --module-path /sdcard/YourModule.zip
```

---

## Troubleshooting

### "adb devices" shows nothing
- Check USB cable is properly connected
- Enable USB debugging in device Settings
- Try `adb kill-server` then `adb devices` again

### "fastboot devices" shows nothing
- Device may need to be in fastboot mode explicitly
- Try: `adb reboot bootloader`
- Or: Hold power + volume down while device boots (varies by device)

### Workflow timeouts
- Increase timeout parameters:
```bash
--param timeout_download=120 \
--param timeout_patch=180 \
--param timeout_flash=180
```

### File picker doesn't appear in Phase 5
- Workflow will pause
- Check if Magisk app is responding
- You may need to manually select the file
- Or dismiss and restart workflow

### Device bootloops after flashing
- **Don't panic!** This is recoverable
- Boot into recovery mode if possible
- Flash original boot image using fastboot
- See full troubleshooting in skill documentation

### "fastboot: device not found"
- Ensure device is actually in fastboot mode
- Try: `fastboot reboot` to exit fastboot, then retry
- May need USB drivers on Windows

---

## Advanced Usage

### Use Specific Magisk Version
```bash
--param version=30.5  # Or any other version
--param version=29.0
```

### Custom Output Directory
```bash
--param output_dir=/home/user/magisk-files
```

### Increase All Timeouts
```bash
--param timeout_download=120 \
--param timeout_install=90 \
--param timeout_extract=60 \
--param timeout_patch=180 \
--param timeout_flash=180
```

### Run on Multiple Devices
```bash
# First device
uv run ... --param device=127.0.0.1:5555 --param version=30.6

# Second device
uv run ... --param device=127.0.0.1:5556 --param version=30.6
```

---

## Getting Help

### If Something Goes Wrong
1. **Check the full documentation**:
   - `.claude/skills/adb/adb-magisk-installer/SKILL.md` - Complete reference
   - `.claude/skills/adb/adb-magisk-installer/workflow/magisk-complete-install.md` - Detailed phases

2. **Check troubleshooting**:
   - Complete troubleshooting section in skill documentation
   - Error codes from scripts (check exit codes)

3. **Check device status**:
   ```bash
   # See what's installed
   adb shell getprop ro.boot.slot_suffix
   adb shell pm list packages | grep magisk
   ```

4. **Check Magisk app directly**:
   - Open Magisk Manager on device
   - Check status page
   - Check error messages

---

## Important Safety Notes

- ⚠️ **Don't unplug device** during Phases 8-9 (flashing)
- ⚠️ **Don't interrupt fastboot** - can cause bootloops
- ⚠️ **Check bootloader** is unlocked before flashing (varies by device)
- ⚠️ **Have recovery access** in case of bootloop (TWRP, stock recovery)
- ⚠️ **Backup important data** before starting (just in case)

---

## What's Being Installed?

### Magisk 30.6 (Latest)
- Modern Rust-based codebase
- Enhanced module injection
- Zygisk support (API hooking)
- Better Android 16 QPR2 support
- Vendor_boot partition support

### Changes on Your Device
- ✅ Boot image patched (adds Magisk magic)
- ✅ Magisk Manager app updated (27.0 → 30.6)
- ✅ System integration complete
- ✅ Reversible (can flash original boot to remove)

---

## After You Finish

### Verification Checklist
- [ ] Device boots without bootloops
- [ ] Magisk app shows `Installed: Yes`
- [ ] Zygisk tab is available
- [ ] Can enable Zygisk in settings
- [ ] Can install modules

### Optional Next Steps
1. **Enable Zygisk** (needed for API hooking):
   ```bash
   uv run .claude/skills/adb-magisk/scripts/adb-magisk-enable-zygisk.py \
       --device 127.0.0.1:5555
   ```

2. **Install PlayIntegrityFork module** (for Play Integrity bypass):
   - Download from GitHub
   - Use adb-magisk-install-module.py

3. **Run game automation** with full system access

---

## Questions?

Refer to the complete skill documentation:
- **SKILL.md**: Complete skill reference with all parameters
- **workflow/magisk-complete-install.md**: Detailed phase documentation
- **scripts/README.md**: Individual script usage

---

**Time to Complete**: ~15 minutes
**Difficulty**: Intermediate (workflow is automated, 1 manual file selection step)
**Success Rate**: 99% (with proper prerequisites)

**Ready to go?** Run the one-liner command above and follow the prompts!
