---
name: adb-magisk-installer
description: Complete, systemless Magisk automated installation toolchain for connected Android devices via fastboot interface and active developer options. Fully support boot extracting, interactive UI flow automated patch emulation, and automated safe system-level flashing.
---

# Complete Magisk System Installation Toolchain

This skill contains the scripts, helper wrappers, and a phase-driven workflow engine designed to fully automate systemless Magisk installation from a connected workstation. It takes an Android device from `"Installed: N/A"` (app missing or boot unpatched) to `"Installed: Yes"`.

## Core Features

- **Automated Downloads**: Pulls official Magisk releases directly from GitHub, verifying hash integrity.
- **Application Injection**: Checks for active device package manager records and force-reinstalls/verifies Magisk Manager.
- **Dynamic Partition Detection**: Interrogates active hardware state to resolve slot layouts (`_a`/`_b`), fallback blocks (`boot`, `init_boot`, `vendor_boot`), and root contexts to perform a local binary dump.
- **UI Emulation Engine (UIAutomator + OCR-less Snapshot Matching)**: Launches the Magisk app UI and simulates user interactions (swipes, clicks, confirmation dialogs) to run on-device patching without manual intervention.
- **Fastboot Execution Safety Controller**: Safeguards the core flashing sequence by verifying image limits before execution and executing post-reboot ADB online checks.

## Project Structure

```
.claude/skills/adb-magisk-installer/
├── SKILL.md                          # This documentation file
├── workflows/
│   └── magisk-complete-install.toon  # YAML-based comprehensive workflow
└── scripts/
    ├── common.py                     # Central constants, ADB/Fastboot wraps, UIAutomator utilities
    ├── adb-magisk-download.py        # Releases parser & downloader
    ├── adb-magisk-install-app.py     # APK package manager injector
    ├── adb-magisk-extract-boot.py    # Multi-block raw boot extractor
    ├── adb-magisk-patch-boot.py      # Automated UI patcher & local puller
    ├── adb-magisk-flash-boot.py      # Fastboot partition block flasher
    ├── adb-magisk-launch.py          # Magisk launch and load validator
    └── run-workflow.py               # Orchestrator interpreter
```

## Setup & Requirements

1. **Android Platform Tools**: Ensure both `adb` and `fastboot` are present in your system PATH.
2. **Python Environment**: Runs cleanly with standard Python (>= 3.8). No external dependencies (like PyYAML or requests) are required because the orchestrator has a lightweight native YAML parser built-in and downloads files using `urllib`.

## Usage Instructions

### 1. Direct Script Actions

Each script can run standalone as part of utility tasks:

#### Download files:
```bash
python .claude/skills/adb-magisk-installer/scripts/adb-magisk-download.py \
    --version 30.6 \
    --output-dir ./magisk_temp
```

#### Install the app wrapper:
```bash
python .claude/skills/adb-magisk-installer/scripts/adb-magisk-install-app.py \
    --device 127.0.0.1:5555 \
    --apk-path ./magisk_temp/Magisk-v30.6.apk \
    --verify
```

#### Extract raw kernel blocks:
```bash
python .claude/skills/adb-magisk-installer/scripts/adb-magisk-extract-boot.py \
    --device 127.0.0.1:5555 \
    --output-path ./magisk_temp/boot_stock.img \
    --verify
```

#### Emulate UI patching:
```bash
python .claude/skills/adb-magisk-installer/scripts/adb-magisk-patch-boot.py \
    --device 127.0.0.1:5555 \
    --boot-path /sdcard/boot.img \
    --output-path ./magisk_temp/patched_boot.img \
    --wait-completion
```

#### Flash patched boot partitions:
```bash
python .claude/skills/adb-magisk-installer/scripts/adb-magisk-flash-boot.py \
    --boot-path ./magisk_temp/patched_boot.img \
    --reboot
```

### 2. Running the Complete Phase-Driven Orchestration

To run the complete automated integration flow from scratch, execute:

```bash
python .claude/skills/adb-magisk-installer/scripts/run-workflow.py \
    --workflow .claude/skills/adb-magisk-installer/workflows/magisk-complete-install.toon \
    --device 127.0.0.1:5555 \
    --version 30.6
```

The orchestrator executes every step specified in the `.toon` workflow, handling errors with structured retry logic and generating full task artifacts.
