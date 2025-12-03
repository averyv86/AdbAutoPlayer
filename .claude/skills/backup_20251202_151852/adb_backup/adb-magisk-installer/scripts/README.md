# adb-magisk-installer - Scripts

Executable Python scripts for complete Magisk system installation workflow.

---

## Scripts Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| **adb-magisk-download.py** | Download Magisk APK and files from GitHub | Get latest or specific version |
| **adb-magisk-install-app.py** | Install Magisk Manager APK on device | Push and install via adb |
| **adb-magisk-extract-boot.py** | Extract boot.img from device | Pull boot partition for patching |
| **adb-magisk-patch-boot.py** | Patch boot image using Magisk app | Run patching workflow on device |
| **adb-magisk-flash-boot.py** | Flash patched boot image via fastboot | Install patched image and reboot |

---

## Phase 1: Download (adb-magisk-download.py)

Download latest or specific version of Magisk from GitHub.

```bash
# Download latest version
uv run adb-magisk-download.py --output-dir /tmp/magisk

# Download specific version
uv run adb-magisk-download.py --version 30.6 --output-dir /tmp/magisk

# Include boot image
uv run adb-magisk-download.py --version 30.6 --include-boot --output-dir /tmp/magisk

# JSON output
uv run adb-magisk-download.py --version 30.6 --include-boot --json
```

**Exit Codes**:
- 0: Success (all files downloaded)
- 1: Warning (partial download)
- 2: Error (download failed)
- 3: Critical (network/API error)

---

## Phase 2: Install App (adb-magisk-install-app.py)

Install Magisk Manager APK on device.

```bash
# Basic install
uv run adb-magisk-install-app.py --device 127.0.0.1:5555 \
    --apk-path /tmp/magisk/Magisk-v30.6.apk

# Force reinstall
uv run adb-magisk-install-app.py --device 127.0.0.1:5555 \
    --apk-path /tmp/magisk/Magisk-v30.6.apk --force

# Verify after install
uv run adb-magisk-install-app.py --device 127.0.0.1:5555 \
    --apk-path /tmp/magisk/Magisk-v30.6.apk --verify

# JSON output
uv run adb-magisk-install-app.py --device 127.0.0.1:5555 \
    --apk-path /tmp/magisk/Magisk-v30.6.apk --json
```

**Exit Codes**:
- 0: Success (app installed and verified)
- 1: Warning (app installed but verification incomplete)
- 2: Error (installation failed)
- 3: Critical (invalid APK or device)

---

## Phase 3: Extract Boot (adb-magisk-extract-boot.py)

Extract boot.img from device for patching.

```bash
# Extract boot image (auto-detects partition)
uv run adb-magisk-extract-boot.py --device 127.0.0.1:5555 \
    --output-path /tmp/magisk/boot.img

# Extract from specific partition
uv run adb-magisk-extract-boot.py --device 127.0.0.1:5555 \
    --partition boot_b --output-path /tmp/magisk/boot_b.img

# Verify integrity
uv run adb-magisk-extract-boot.py --device 127.0.0.1:5555 \
    --output-path /tmp/magisk/boot.img --verify

# JSON output
uv run adb-magisk-extract-boot.py --device 127.0.0.1:5555 \
    --output-path /tmp/magisk/boot.img --json
```

**Exit Codes**:
- 0: Success (boot extracted)
- 2: Error (extraction failed)

---

## Phase 4: Patch Boot (adb-magisk-patch-boot.py)

Patch boot image using Magisk Manager app on device.

```bash
# Patch boot image (launch interactive UI)
uv run adb-magisk-patch-boot.py --device 127.0.0.1:5555 \
    --boot-path /sdcard/boot.img

# Wait for patching to complete
uv run adb-magisk-patch-boot.py --device 127.0.0.1:5555 \
    --boot-path /sdcard/boot.img --wait-completion

# Download patched image automatically
uv run adb-magisk-patch-boot.py --device 127.0.0.1:5555 \
    --boot-path /sdcard/boot.img \
    --output-path /tmp/magisk/patched_boot.img \
    --wait-completion

# JSON output
uv run adb-magisk-patch-boot.py --device 127.0.0.1:5555 \
    --boot-path /sdcard/boot.img --json
```

**Exit Codes**:
- 0: Success (patching complete)
- 1: Warning (patching not complete or not detected)
- 2: Error (app launch failed)

---

## Phase 5: Flash Boot (adb-magisk-flash-boot.py)

Flash patched boot image via fastboot.

```bash
# Flash patched boot image
uv run adb-magisk-flash-boot.py --device 127.0.0.1:5555 \
    --boot-path /tmp/magisk/patched_boot.img

# Flash to specific partition
uv run adb-magisk-flash-boot.py --device 127.0.0.1:5555 \
    --boot-path /tmp/magisk/patched_boot.img --partition boot_b

# Flash and auto-reboot
uv run adb-magisk-flash-boot.py --device 127.0.0.1:5555 \
    --boot-path /tmp/magisk/patched_boot.img --reboot

# Verify before flashing
uv run adb-magisk-flash-boot.py --device 127.0.0.1:5555 \
    --boot-path /tmp/magisk/patched_boot.img --verify

# JSON output
uv run adb-magisk-flash-boot.py --device 127.0.0.1:5555 \
    --boot-path /tmp/magisk/patched_boot.img --json
```

**Exit Codes**:
- 0: Success (boot flashed and device rebooted)
- 1: Warning (flash successful but reboot issue)
- 2: Error (flash failed)
- 3: Critical (invalid boot file)

---

## Complete Workflow

Run all phases in sequence for complete installation:

```bash
# Phase 1: Download
uv run adb-magisk-download.py --version 30.6 --include-boot --output-dir /tmp/magisk

# Phase 2: Install app
uv run adb-magisk-install-app.py --device 127.0.0.1:5555 \
    --apk-path /tmp/magisk/Magisk-v30.6.apk --verify

# Phase 3: Extract boot
uv run adb-magisk-extract-boot.py --device 127.0.0.1:5555 \
    --output-path /tmp/magisk/boot.img

# Phase 4: Patch boot (requires user interaction in Magisk app)
uv run adb-magisk-patch-boot.py --device 127.0.0.1:5555 \
    --boot-path /sdcard/boot.img \
    --output-path /tmp/magisk/patched_boot.img \
    --wait-completion

# Phase 5: Flash boot
uv run adb-magisk-flash-boot.py --device 127.0.0.1:5555 \
    --boot-path /tmp/magisk/patched_boot.img --reboot
```

---

## Device Requirements

- ✅ USB ADB debugging enabled
- ✅ ADB connection established
- ✅ Fastboot access (usually requires USB connection)
- ✅ Sufficient storage on device (/sdcard/ for boot image)
- ✅ Boot loader unlocked (may be required for flashing)

---

## Integration with Workflows

These scripts are orchestrated by the TOON workflow:

```bash
# Run complete installation via workflow
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflow/magisk-complete-install.toon \
    --param device=127.0.0.1:5555 \
    --param version=30.6
```

---

**Category**: System Installation Scripts
**Scripts**: 5 total
**Last Updated**: 2025-12-02
