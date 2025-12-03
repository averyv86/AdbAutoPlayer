# Workflow: Magisk Module Installation and Management

**File**: `module-management.toon`
**Skill**: `adb-magisk`
**Version**: 1.0.0
**Category**: system-management
**Difficulty**: advanced

---

## Purpose

This workflow manages Magisk modules including installation from ZIP files, enabling/disabling modules without removal, and complete module uninstallation. It handles module extraction, state management, backup creation, and provides comprehensive operation logging.

Use this workflow to manage Magisk modules programmatically as part of automated system configuration.

---

## Prerequisites

- Device with Magisk installed and verified (use magisk-verification.toon)
- For installation: module ZIP file accessible via ADB
- Sufficient free space on device (/data partition)
- Root access via Magisk
- ADB shell access with file operations
- Reboot capability (changes take effect after reboot)

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| action | string | "list" | Operation: list, install, enable, disable, remove |
| module_name | string | "" | Module name for enable/disable/remove operations |
| module_path | string | "" | Full path to module ZIP for installation |
| timeout | integer | 60 | Operation timeout in seconds |

---

## Phases

### Phase 1: Prepare Module Operation

**Objective**: Verify device state and operation readiness

Steps:
1. Verify device access to /data/adb/modules
2. Validate module directory structure
3. Check available free space
4. Confirm file operation permissions

**Success Indicators**:
- Directory access confirmed
- Directory structure valid
- Sufficient free space available
- Permissions allow operations

---

### Phase 2: List Installed Modules

**Objective**: Display all currently installed modules and their status

Steps:
1. Get complete module list from /data/adb/modules/
2. Extract module details and metadata
3. Check for module conflicts
4. Display enable/disable status

**Success Indicators**:
- Module list retrieved
- Metadata accessible
- Status clearly shown
- Conflicts identified

---

### Phase 3: Install Module

**Objective**: Install a new module from ZIP file

Steps:
1. Validate module ZIP exists
2. Push ZIP to device
3. Extract module to proper location
4. Verify installation integrity
5. Clean up temporary files

**Success Indicators**:
- ZIP file found
- Successfully transferred
- Module extracted to correct path
- Files readable post-extraction

---

### Phase 4: Enable or Disable Module

**Objective**: Toggle module active/inactive state

Steps:
1. Verify module directory exists
2. For disable: create "disable" marker file
3. For enable: remove "disable" marker file
4. Verify state change successful

**Success Indicators**:
- Module found
- State change applied
- Verification confirms change
- No errors during operation

---

### Phase 5: Remove Module

**Objective**: Completely remove a module

Steps:
1. Create backup of module (optional)
2. Delete module directory
3. Clean up associated files
4. Verify complete removal
5. Update module count

**Success Indicators**:
- Backup created (if desired)
- Module directory deleted
- No module artifacts remain
- Module count updated

---

## Success Criteria

- [ ] Device access verified
- [ ] Module directory accessible
- [ ] Module operations execute without errors
- [ ] Module state changes verified
- [ ] File system remains consistent
- [ ] Backups created (if removing)
- [ ] Module list updated accurately
- [ ] No orphaned files remaining

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Device access denied | Permissions issue | Check ADB permissions and reboot |
| ZIP file not found | Wrong path or file missing | Verify module_path parameter |
| Extraction fails | Corrupted ZIP or permission issue | Verify ZIP integrity and try again |
| Module not found | Wrong module name | Check actual module name with list action |
| Disable fails | Read-only filesystem | Reboot device and retry |
| Removal failed | File locked or permission denied | Reboot device and retry |
| Free space insufficient | Disk full | Clean up device storage first |

---

## Action Types

### list (Default)
Lists all installed Magisk modules with status and details.
- No parameters required beyond device
- Shows enabled/disabled status
- Displays module metadata

### install
Installs a new module from ZIP file.
- Requires: module_path pointing to valid ZIP
- Optional: module_name for reference
- Creates module backup location

### enable
Activates a disabled module without removing it.
- Requires: module_name
- Removes disable marker file
- Module loads after reboot

### disable
Deactivates a module while keeping files.
- Requires: module_name
- Creates disable marker file
- Module unloaded after reboot

### remove
Completely uninstalls a module.
- Requires: module_name
- Creates backup before deletion
- Removes all module files

---

## Example Execution

```bash
# List all installed modules
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-magisk/workflow/module-management.toon \
  --param device="127.0.0.1:5555" \
  --param action="list" \
  --verbose

# Install a new module from ZIP
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-magisk/workflow/module-management.toon \
  --param device="emulator-5554" \
  --param action="install" \
  --param module_path="/tmp/playintegrityfix.zip" \
  --verbose

# Disable a module
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-magisk/workflow/module-management.toon \
  --param device="127.0.0.1:5555" \
  --param action="disable" \
  --param module_name="playintegrityfix" \
  --verbose

# Remove a module (with backup)
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-magisk/workflow/module-management.toon \
  --param device="192.168.1.100:5555" \
  --param action="remove" \
  --param module_name="playintegrityfix" \
  --verbose
```

---

## Module Structure

Modules are stored in `/data/adb/modules/{module_name}/`:
- `module.prop` - Module metadata (name, author, version, etc.)
- `post-fs-data.sh` - Executes in post-fs-data phase
- `service.sh` - Executes in service phase
- `system/` - Files to inject into /system
- `vendor/` - Files to inject into /vendor
- `disable` - Marker file (present = module disabled)

---

## Important Notes

**Reboot Required**: Most module state changes require device reboot to take effect

**Module Backups**: Created before removal in /data/adb/modules/{module_name}.bak

**Conflicts**: Some modules may conflict - check logs for incompatibilities

**Order Matters**: Module execution order may affect behavior

**System Mounts**: Changes affect /system and /vendor mounts

---

## Related Workflows

- [magisk-verification.md](./magisk-verification.md) - Verify Magisk before managing modules
- [../adb-bypass/workflow/bypass-validation.md](../adb-bypass/workflow/bypass-validation.md) - Validate bypass after module install
- [../adb-karrot/workflow/login-automation.md](../adb-karrot/workflow/login-automation.md) - Test app after module changes
- [../adb-navigation-base/workflow/app-navigation.md](../adb-navigation-base/workflow/app-navigation.md) - Navigate Magisk Manager app

---

**Last Updated**: 2025-12-02
**Status**: Active
**Complexity**: Advanced - Modifies system state
**Risk Level**: Medium - Creates backups, but requires reboot
