---
name: adb:init
description: "Initialize ADB project and connect devices"
argument-hint: "[<empty>|--scan|--validate|--list]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, TodoWrite, AskUserQuestion, Task
model: inherit
---

## Pre-execution Context

!adb devices
!adb version
!ls -la "$CLAUDE_PROJECT_DIR"/src-tauri/src-python/adb_auto_player/device/
!ls -la "$CLAUDE_PROJECT_DIR"/.moai/config/

## Essential Files

@.moai/config/config.json
@src-tauri/Settings/ADB.toml

---

# ADB AutoPlayer Initialization Command

> Purpose: Initialize ADB development environment with automated device discovery and configuration.
> Tier: Foundation (Project Setup)
> Integration: Combines device analysis, configuration validation, and template generation for rapid ADB automation setup.

## Command Purpose

Initialize the ADB AutoPlayer project environment by discovering connected devices, validating hardware capabilities, configuring device pools, and setting up project templates for bot development. This command provides a comprehensive onboarding workflow that transforms raw ADB devices into automation-ready environments.

**Core Capabilities:**

- **Device Discovery**: Automatically detect all connected ADB devices (emulators and physical)
- **Hardware Analysis**: Analyze device specifications (API level, screen resolution, RAM, CPU)
- **Configuration Management**: Generate and validate ADB configuration files
- **Template Initialization**: Set up bot template directories and boilerplate code
- **Compatibility Validation**: Verify device meets minimum requirements for automation

---

## Prerequisites

Before running `/adb:init`, ensure the following requirements are met:

1. **ADB Installation**: Android Debug Bridge (adb) must be installed and accessible in PATH
2. **Connected Devices**: At least one ADB device connected (emulator or physical device)
3. **Device Authorization**: Devices must be authorized for debugging (USB debugging enabled)
4. **Python Environment**: Python 3.12+ with required dependencies installed
5. **Project Structure**: ADB AutoPlayer project cloned and dependencies installed

**Verification Commands:**

```bash
adb version           # Should show ADB version 1.0.40+
adb devices          # Should list at least one device
python --version     # Should show Python 3.12+
```

---

## Usage Examples

### Example 1: Basic Initialization (Auto-detect Devices)

```bash
/adb:init
```

**Expected Behavior:**
- Scans for all connected ADB devices
- Analyzes each device's hardware capabilities
- Presents device selection menu via AskUserQuestion
- Generates configuration files with selected devices
- Initializes bot template directories

### Example 2: Scan Devices Only (No Configuration)

```bash
/adb:init --scan
```

**Expected Behavior:**
- Performs device discovery and analysis
- Displays device capabilities in rich table format
- Does NOT modify configuration files
- Useful for checking device status before full initialization

### Example 3: Validate Existing Configuration

```bash
/adb:init --validate
```

**Expected Behavior:**
- Reads existing ADB.toml configuration
- Verifies all configured devices are still connected
- Checks configuration syntax and required fields
- Reports validation status and warnings

### Example 4: List Available Devices

```bash
/adb:init --list
```

**Expected Behavior:**
- Quick device listing without full analysis
- Shows device serial, state, and type (emulator/physical)
- Lightweight operation for rapid status check

---

## Step-by-Step Workflow

### PHASE 1: Pre-Flight Checks (5 Steps)

#### Step 1.1: Verify ADB Installation

**Objective:** Ensure ADB is installed and accessible.

**Actions:**
1. Execute `adb version` command
2. Parse version output to verify ADB is functional
3. Check version meets minimum requirement (1.0.40+)

**Success Criteria:**
- ADB command executes successfully
- Version >= 1.0.40
- ADB executable found in PATH

**Error Handling:**
- If ADB not found: Display installation instructions
- If version too old: Recommend upgrade
- Exit initialization if ADB unavailable

**Output Example:**
```
✓ ADB Version: 1.0.41 (Verified)
✓ ADB Executable: /usr/local/bin/adb
```

---

#### Step 1.2: Check Connected Devices

**Objective:** Verify at least one ADB device is connected.

**Actions:**
1. Execute `adb devices` command
2. Parse output to extract device list
3. Filter devices with state "device" (exclude offline/unauthorized)
4. Count available devices

**Success Criteria:**
- At least one device with state "device"
- Device serial number extracted successfully

**Error Handling:**
- If no devices found: Prompt user to connect device or start emulator
- If devices offline: Suggest troubleshooting steps (restart ADB server, check USB connection)
- If devices unauthorized: Guide user to authorize debugging on device

**Output Example:**
```
✓ Connected Devices: 2 found
  • emulator-5554 (device)
  • R58N80ABCDE (device)
```

---

#### Step 1.3: Validate Python Environment

**Objective:** Confirm Python environment meets project requirements.

**Actions:**
1. Check Python version (3.12+ required)
2. Verify required packages installed (click, rich)
3. Test import of adb_device_analyzer.py script

**Success Criteria:**
- Python 3.12+ available
- Required dependencies installed
- Script imports successfully

**Error Handling:**
- If Python version incorrect: Display upgrade instructions
- If dependencies missing: Run `uv sync` or `pip install -r requirements.txt`

**Output Example:**
```
✓ Python Version: 3.13.1
✓ Dependencies: Installed
✓ ADB Analyzer: Ready
```

---

#### Step 1.4: Verify Project Structure

**Objective:** Ensure project directories and configuration files exist.

**Actions:**
1. Check for critical directories:
   - `src-tauri/Settings/`
   - `.moai/config/`
   - `src-tauri/src-python/adb_auto_player/device/`
2. Verify essential files exist:
   - `pyproject.toml`
   - Configuration templates

**Success Criteria:**
- All required directories present
- Configuration templates accessible

**Error Handling:**
- If directories missing: Create them automatically
- If files missing: Prompt user to run project setup first

**Output Example:**
```
✓ Project Structure: Valid
  • Settings directory: Found
  • Config directory: Found
  • Device modules: Found
```

---

#### Step 1.5: Load Existing Configuration (Optional)

**Objective:** Load existing ADB configuration if present.

**Actions:**
1. Check if `ADB.toml` exists
2. Parse TOML configuration file
3. Extract device pool and settings
4. Store for comparison with discovered devices

**Success Criteria:**
- Configuration file loaded (if exists)
- TOML syntax valid

**Error Handling:**
- If file missing: Proceed with fresh initialization
- If TOML invalid: Backup corrupted file and create new configuration

**Output Example:**
```
✓ Existing Config: Loaded
  • Configured Devices: 1
  • Last Updated: 2025-11-28
```

---

### PHASE 2: Device Discovery & Analysis (3 Steps)

#### Step 2.1: Invoke ADB Device Analyzer

**Objective:** Analyze all connected devices comprehensively.

**Actions:**
1. Execute `adb_device_analyzer.py` script for each device
2. Collect device information:
   - Serial number and state
   - Manufacturer and model
   - Android version and API level
   - Screen resolution and density
   - RAM (total and available)
   - CPU architecture and threads
   - Storage capacity
   - Battery status
3. Store analysis results in structured format

**Tool Integration:**
```bash
uv run "$CLAUDE_PROJECT_DIR"/.claude/skills/moai-domain-adb/scripts/adb_device_analyzer.py --device <serial> --json
```

**Success Criteria:**
- All devices analyzed successfully
- Device info structured in DeviceInfo dataclass format

**Error Handling:**
- If device offline during analysis: Skip and warn user
- If analysis times out: Mark device as unreliable
- If critical fields missing: Mark as incomplete analysis

**Output Example:**
```
✓ Device Analysis Complete
  • emulator-5554:
    - Model: sdk_gphone64_arm64
    - API Level: 34 (Android 14)
    - Resolution: 1080x2400 @ 420dpi
    - RAM: 2048 MB (1523 MB available)
    - CPU: arm64-v8a (8 threads)

  • R58N80ABCDE:
    - Model: Pixel 6
    - API Level: 33 (Android 13)
    - Resolution: 1080x2340 @ 411dpi
    - RAM: 8192 MB (4521 MB available)
    - CPU: arm64-v8a (8 threads)
```

---

#### Step 2.2: Compatibility Validation

**Objective:** Verify devices meet minimum requirements for ADB AutoPlayer.

**Validation Rules:**
1. **API Level**: Minimum API 23 (Android 6.0) recommended
2. **Resolution**: Minimum 720x1280 (HD)
3. **RAM**: Minimum 1024 MB available
4. **CPU**: Minimum 4 threads recommended
5. **Storage**: Minimum 100 MB available

**Actions:**
1. Compare each device against validation rules
2. Mark devices as:
   - ✓ **Compatible**: Meets all requirements
   - ⚠ **Partial**: Meets minimum but not recommended specs
   - ✗ **Incompatible**: Fails critical requirements
3. Generate warnings for partial compatibility

**Success Criteria:**
- At least one device marked as compatible
- Clear compatibility status for each device

**Error Handling:**
- If no compatible devices: Suggest device upgrades or alternatives
- If all devices partial: Warn about potential performance issues

**Output Example:**
```
✓ Compatibility Check Complete
  • emulator-5554: ⚠ Partial
    - RAM below recommended (2GB < 4GB)
    - Otherwise compatible

  • R58N80ABCDE: ✓ Compatible
    - All requirements met
```

---

#### Step 2.3: Device Selection

**Objective:** Present devices to user for configuration selection.

**Actions:**
1. Use AskUserQuestion tool to display device list
2. Allow multi-select for device pool
3. Highlight compatibility status in descriptions

**AskUserQuestion Format:**

```python
AskUserQuestion({
    "questions": [{
        "question": "Select devices to include in ADB AutoPlayer configuration:",
        "header": "Device Selection",
        "multiSelect": true,
        "options": [
            {
                "label": "emulator-5554 (sdk_gphone64_arm64)",
                "description": "Android 14 (API 34) | 1080x2400 | 2GB RAM | Compatible"
            },
            {
                "label": "R58N80ABCDE (Pixel 6)",
                "description": "Android 13 (API 33) | 1080x2340 | 8GB RAM | Highly Compatible"
            }
        ]
    }]
})
```

**Success Criteria:**
- User selects at least one device
- Selected devices stored for configuration generation

**Error Handling:**
- If user selects no devices: Prompt again with warning
- If user cancels: Exit initialization gracefully

**Output Example:**
```
✓ Devices Selected: 2
  • emulator-5554
  • R58N80ABCDE
```

---

### PHASE 3: Configuration Generation (4 Steps)

#### Step 3.1: Generate ADB.toml Configuration

**Objective:** Create or update ADB configuration file with selected devices.

**Actions:**
1. Build device pool configuration:
   ```toml
   [device_pool]
   devices = [
       { serial = "emulator-5554", type = "emulator", api_level = 34 },
       { serial = "R58N80ABCDE", type = "physical", api_level = 33 }
   ]
   ```
2. Add default settings:
   - Connection timeout
   - Retry attempts
   - ADB binary path
3. Preserve existing custom settings if updating
4. Write to `src-tauri/Settings/ADB.toml`

**Success Criteria:**
- TOML file created with valid syntax
- All selected devices included
- File writable and parseable

**Error Handling:**
- If file write fails: Check permissions and suggest fixes
- If TOML syntax error: Validate and retry

**Output Example:**
```
✓ Configuration Generated
  • Location: src-tauri/Settings/ADB.toml
  • Devices: 2
  • Settings: Default applied
```

---

#### Step 3.2: Initialize Template Directory

**Objective:** Set up bot template directory structure.

**Actions:**
1. Create template directories:
   ```
   src-tauri/src-python/adb_auto_player/games/<game_name>/
   ├── __init__.py
   ├── base.py
   ├── templates/
   └── custom_routine/
   ```
2. Copy boilerplate template files
3. Generate README with usage instructions

**Success Criteria:**
- Template directories created
- Boilerplate files copied
- README generated

**Error Handling:**
- If directories exist: Prompt user to confirm overwrite
- If template files missing: Download from repository

**Output Example:**
```
✓ Template Directory Initialized
  • Location: src-tauri/src-python/adb_auto_player/games/
  • Boilerplate: Ready
  • Documentation: Generated
```

---

#### Step 3.3: Configuration Validation

**Objective:** Validate generated configuration files.

**Actions:**
1. Parse ADB.toml to verify syntax
2. Check all device serials are valid format
3. Verify required fields present
4. Test device connectivity with configuration

**Validation Script:**
```bash
# (Placeholder - script to be implemented)
uv run "$CLAUDE_PROJECT_DIR"/.claude/skills/moai-domain-adb/scripts/adb_config_validator.py
```

**Success Criteria:**
- TOML parsing successful
- All device serials reachable
- Configuration meets schema requirements

**Error Handling:**
- If validation fails: Display specific errors
- If device unreachable: Suggest re-scanning devices

**Output Example:**
```
✓ Configuration Validated
  • Syntax: Valid
  • Devices: 2/2 reachable
  • Schema: Compliant
```

---

#### Step 3.4: Generate Summary Report

**Objective:** Provide comprehensive initialization summary.

**Actions:**
1. Compile initialization results
2. Display summary table with:
   - Devices configured
   - Configuration file paths
   - Template directories created
   - Next steps recommendations
3. Save report to `.moai/logs/adb-init-<timestamp>.log`

**Success Criteria:**
- Summary displayed to user
- Log file created

**Output Example:**
```
═══════════════════════════════════════════════════════════════
                ADB AutoPlayer Initialization Complete
═══════════════════════════════════════════════════════════════

✓ Devices Configured: 2
  • emulator-5554 (Emulator, API 34)
  • R58N80ABCDE (Physical, API 33)

✓ Configuration Files:
  • ADB.toml: src-tauri/Settings/ADB.toml
  • Project Config: .moai/config/config.json

✓ Template Directories:
  • Games: src-tauri/src-python/adb_auto_player/games/
  • Templates: src-tauri/src-python/adb_auto_player/games/templates/

───────────────────────────────────────────────────────────────
                         Next Steps
───────────────────────────────────────────────────────────────

1. Review Configuration:
   - Open ADB.toml to customize device pool settings
   - Adjust connection timeouts if needed

2. Test Device Connectivity:
   - Run /adb:test to verify device communication
   - Check device responsiveness

3. Create Your First Bot:
   - Run /adb:bot to generate game-specific bot
   - Follow bot development guide

4. Explore Documentation:
   - Read docs/user-guide/real-phone-guide.md
   - Review bot writing examples

═══════════════════════════════════════════════════════════════

Initialization Report: .moai/logs/adb-init-2025-12-01-213145.log
```

---

## Success Criteria

Initialization is considered successful when ALL of the following conditions are met:

1. **ADB Availability**: ADB command accessible and version verified
2. **Device Discovery**: At least one compatible device detected
3. **Configuration Generated**: Valid ADB.toml file created with selected devices
4. **Template Setup**: Bot template directory structure created
5. **Validation Passed**: Configuration validated and devices reachable

**Quality Gates:**

- ✓ Pre-flight checks pass (100%)
- ✓ At least 1 compatible device configured
- ✓ ADB.toml syntax valid (parseable)
- ✓ Template directories exist
- ✓ Validation script returns success (exit code 0)

**Failure Scenarios:**

- ✗ No ADB installation detected
- ✗ No devices connected or authorized
- ✗ All devices incompatible with requirements
- ✗ Configuration file write permission denied
- ✗ Template directory creation failed

---

## Metadata

**Tier:** Foundation (Project Setup)

**Required Tools:**
- `adb_device_analyzer.py`: Device hardware and software analysis
- `adb_config_validator.py`: Configuration file validation (to be implemented)

**Integration Points:**
- Reads: `.moai/config/config.json` (project configuration)
- Writes: `src-tauri/Settings/ADB.toml` (ADB device pool)
- Creates: Template directories in `src-tauri/src-python/adb_auto_player/games/`
- Logs: `.moai/logs/adb-init-<timestamp>.log`

**Dependencies:**
- Python 3.12+ with `click`, `rich` packages
- ADB 1.0.40+ installed and in PATH
- At least one ADB device connected

---

## Output Format

### Progress Indicators

Throughout execution, display clear progress indicators:

```
[1/5] Verifying ADB installation...        ✓ Complete
[2/5] Discovering connected devices...     ✓ 2 devices found
[3/5] Analyzing device capabilities...     ⏳ In progress...
[4/5] Generating configuration...          ⏳ Pending
[5/5] Validating setup...                 ⏳ Pending
```

### Device List Table

Display devices in rich table format:

```
┌─────────────────┬───────────────────┬──────────┬─────────────┬──────────────┐
│ Serial          │ Model             │ Type     │ API Level   │ Compatibility│
├─────────────────┼───────────────────┼──────────┼─────────────┼──────────────┤
│ emulator-5554   │ sdk_gphone64_arm64│ Emulator │ 34 (API 34) │ ⚠ Partial    │
│ R58N80ABCDE     │ Pixel 6           │ Physical │ 33 (API 33) │ ✓ Compatible │
└─────────────────┴───────────────────┴──────────┴─────────────┴──────────────┘
```

### Configuration Summary

Present final configuration in clear format:

```yaml
Device Pool Configuration:
  Total Devices: 2
  Emulators: 1
  Physical Devices: 1

Device Details:
  1. emulator-5554
     - Type: Emulator
     - API: 34 (Android 14)
     - Screen: 1080x2400 @ 420dpi
     - Status: Ready

  2. R58N80ABCDE
     - Type: Physical
     - API: 33 (Android 13)
     - Screen: 1080x2340 @ 411dpi
     - Status: Ready
```

---

## Integration with MoAI Commands

This command serves as the foundation for ADB AutoPlayer development workflow:

**Workflow Sequence:**

1. **`/adb:init`** - Initialize ADB project and connect devices ← YOU ARE HERE
2. **`/adb:test`** - Test device connectivity and responsiveness
3. **`/adb:bot <game>`** - Generate game-specific bot implementation
4. **`/adb:run <bot>`** - Execute bot automation on configured devices

**Next Step Recommendations:**

After successful initialization, users should proceed to:
- **`/adb:test`** - Verify device communication and performance
- **`/adb:bot`** - Create first bot for specific game

**Error Recovery:**

If initialization fails, users can:
- Retry with `--scan` to diagnose device issues
- Run `--validate` to check existing configuration
- Use `--list` for quick device status check

---

## Execution Directive

YOU MUST NOW EXECUTE THE COMMAND FOLLOWING THE WORKFLOW DESCRIBED ABOVE.

1. **START PHASE 1**: Execute pre-flight checks (Steps 1.1-1.5)
2. **PROCEED TO PHASE 2**: Invoke device analyzer and validate compatibility
3. **COMPLETE PHASE 3**: Generate configuration and templates
4. **DO NOT JUST DESCRIBE**: Execute actual tool invocations and file operations

Follow the workflow phases sequentially and report progress to the user.

---

**Version:** 1.0.0
**Last Updated:** 2025-12-01
**Architecture:** ADB Domain Command (Foundation Tier)
**Integration:** moai-domain-adb skill, adb_device_analyzer script
