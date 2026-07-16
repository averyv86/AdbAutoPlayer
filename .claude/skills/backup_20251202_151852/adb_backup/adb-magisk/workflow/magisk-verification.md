# Workflow: Magisk Installation Verification

**File**: `magisk-verification.toon`
**Skill**: `adb-magisk`
**Version**: 1.0.0
**Category**: system-verification
**Difficulty**: intermediate

---

## Purpose

This workflow verifies that Magisk is properly installed on an Android device, checks module system integrity, confirms root access functionality, and validates that all Magisk components are working correctly.

Use this workflow as a prerequisite before installing Magisk modules or running module-dependent workflows.

---

## Prerequisites

- Device with ADB debugging enabled
- Magisk installed on device
- ADB shell access
- Root access available on device
- Approximately 30 seconds for full verification

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| timeout | integer | 30 | Action timeout in seconds |
| check_root_access | boolean | true | Verify root access functionality |

---

## Phases

### Phase 1: Verify Magisk Installation

**Objective**: Confirm Magisk app and binaries are properly installed

Steps:
1. Check Magisk package is installed (com.topjohnwu.magisk)
2. Get Magisk version information
3. Verify Magisk binary is accessible
4. Confirm command-line tools functional

**Success Indicators**:
- Package found in system
- Version information returned
- Binary accessible via command
- Version matches expected format

---

### Phase 2: Check Magisk Modules

**Objective**: Verify module system and list installed modules

Steps:
1. List installed modules from /data/adb/modules/
2. Verify module directory structure intact
3. Check for PlayIntegrityFix module (if installed)
4. Validate module configuration files

**Success Indicators**:
- Module directory accessible
- Module count returned
- Module structure valid
- PIF module found (if expected)

---

### Phase 3: Verify System Integrity

**Objective**: Confirm system has been properly modified by Magisk

Steps:
1. Check system mount status
2. Verify vendor mount configuration
3. Check Magisk Hide status
4. Validate mount bindings

**Success Indicators**:
- System mount present
- Vendor mount configured
- Magisk Hide active
- Mount bindings correct

---

### Phase 4: Test Root Access

**Objective**: Verify root permissions are functional and accessible

Steps:
1. Test SU command execution
2. Verify root-only file access
3. Check SELinux context
4. Confirm permission grants

**Success Indicators**:
- SU command works
- Root files accessible
- SELinux in enforcing mode
- Permissions properly configured

---

## Success Criteria

- [ ] Magisk package installed (com.topjohnwu.magisk)
- [ ] Magisk version detectable and valid
- [ ] Magisk binary accessible
- [ ] Module directory exists and accessible
- [ ] System mounts properly configured
- [ ] Root access functional
- [ ] SELinux in proper mode (enforcing)
- [ ] No critical errors or warnings

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Magisk package not found | Not installed | Install Magisk first |
| Version command fails | Binary not accessible | Check installation, may need reboot |
| Module directory missing | Filesystem issue | Reboot device and recheck |
| Mount status unknown | Filesystem not ready | Wait and retry, device may be booting |
| Root access denied | Permissions issue | Check root access in Magisk app |
| SELinux permissive | Bypass requires enforcing | Enable enforcing mode if possible |

---

## Example Execution

```bash
# Basic Magisk verification
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-magisk/workflow/magisk-verification.toon \
  --param device="127.0.0.1:5555" \
  --verbose

# Verification with root access testing
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-magisk/workflow/magisk-verification.toon \
  --param device="emulator-5554" \
  --param check_root_access=true \
  --verbose

# Extended verification on real device
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-magisk/workflow/magisk-verification.toon \
  --param device="192.168.1.100:5555" \
  --param timeout=45 \
  --verbose
```

---

## Verification Report Sections

### Installation Status
- Package presence and version
- Binary accessibility
- Installation integrity

### Module System
- Total modules installed
- Module names and status
- Critical modules (PIF, etc.)
- Module conflicts

### System State
- Mount configuration
- Root access status
- Security context (SELinux)
- Hide configuration

### Status Summary
- Overall Magisk health
- Any warnings or issues
- Recommendation for next steps

---

## Magisk Module Naming Conventions

Common module directory names:
- `playintegrityfix` - PlayIntegrityFix bypass
- `MagiskHide` - Hide Magisk from apps
- `PixelifyNexus` - Device spoofing
- Custom module names follow pattern `{author}_{module}`

---

## Related Workflows

- [module-management.md](./module-management.md) - Install/remove modules
- [../adb-bypass/workflow/bypass-validation.md](../adb-bypass/workflow/bypass-validation.md) - Verify bypass after Magisk
- [../adb-karrot/workflow/login-automation.md](../adb-karrot/workflow/login-automation.md) - Test with Karrot
- [../adb-navigation-base/workflow/app-navigation.md](../adb-navigation-base/workflow/app-navigation.md) - Navigate in Magisk Manager

---

**Last Updated**: 2025-12-02
**Status**: Active
**Complexity**: Intermediate
**Dependencies**: Requires Magisk installation
