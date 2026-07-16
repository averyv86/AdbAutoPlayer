# Workflow: PlayIntegrityFork Bypass Validation

**File**: `bypass-validation.toon`
**Skill**: `adb-bypass`
**Version**: 1.0.0
**Category**: security-validation
**Difficulty**: intermediate

---

## Purpose

This workflow validates that PlayIntegrityFork (PIF) bypass is properly installed and functioning on a target Android device. It verifies Magisk installation, PIF module status, and tests integrity API bypass effectiveness against Google Play Services.

Use this workflow after installing PIF to confirm the bypass is working correctly before running sensitive applications.

---

## Prerequisites

- Device connected via ADB with debugging enabled
- Magisk installed on device
- PlayIntegrityFork module installed in Magisk
- Google Play Services installed on device (for testing)
- ADB orchestrator with shell action support

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address (IP:port or device ID) |
| timeout | integer | 30 | Action timeout in seconds |
| verify_signature | boolean | true | Enable signature spoofing verification checks |

---

## Phases

### Phase 1: Check PlayIntegrityFork Installation

**Objective**: Verify that Magisk and PIF module are installed and active

Steps:
1. Check if Magisk package is installed via package manager
2. Verify PIF module directory exists in /data/adb/modules/
3. Check if PIF module is enabled (no disable flag present)

**Success Indicators**:
- Magisk package found in system
- PIF module directory readable
- No disable file present for module

---

### Phase 2: Validate Bypass Functionality

**Objective**: Confirm that device properties can be spoofed for integrity checks

Steps:
1. Capture current device fingerprint and CPU ABI
2. Verify SELinux is in enforcing mode (required for proper bypass)
3. Check Magisk Hide functionality status

**Success Indicators**:
- Device properties return valid fingerprint
- SELinux in enforcing mode
- Magisk version accessible

---

### Phase 3: Run Integrity API Tests

**Objective**: Test actual integrity checks against Google Play Services

Steps:
1. Verify Google Play Services is installed
2. Launch Play Store to trigger integrity checks
3. Monitor for integrity check responses

**Success Indicators**:
- Google Play Services installed
- Play Store launches without integrity failures
- No security warnings in logs

---

### Phase 4: Generate Validation Report

**Objective**: Create comprehensive validation summary

Steps:
1. Capture device screen showing current state
2. Compile all validation results
3. Generate timestamped report

---

## Success Criteria

- [ ] Magisk is properly installed and running
- [ ] PIF module is installed and enabled
- [ ] Device fingerprint is properly spoofed
- [ ] SELinux is in enforcing mode
- [ ] Google Play Services accepts device integrity
- [ ] No security exceptions or warnings logged
- [ ] Validation report generated successfully

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Magisk not found | Magisk not installed | Install Magisk first via adb-magisk workflow |
| PIF module not found | Module not installed | Install PIF module in Magisk |
| PIF module disabled | Disable file present | Remove disable flag from module directory |
| SELinux permissive | Bypass requires enforcing | Reboot device or enable enforcing mode |
| Play Store fails to launch | Integrity check failed | Reboot device and retry validation |
| Timeout exceeded | Device unresponsive | Check ADB connection and device availability |

---

## Example Execution

```bash
# Validate bypass on default emulator
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-bypass/workflow/bypass-validation.toon \
  --param device="127.0.0.1:5555" \
  --param timeout=30 \
  --verbose

# Validate bypass on specific device with signature verification
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-bypass/workflow/bypass-validation.toon \
  --param device="emulator-5554" \
  --param verify_signature=true \
  --verbose

# Validate with extended timeout for slower devices
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-bypass/workflow/bypass-validation.toon \
  --param device="192.168.1.100:5555" \
  --param timeout=60 \
  --verbose
```

---

## Related Workflows

- [integrity-verification.md](./integrity-verification.md) - Detailed signature spoofing tests
- [detection-check.md](./detection-check.md) - Test bypass against specific apps
- [../adb-magisk/workflow/magisk-verification.md](../adb-magisk/workflow/magisk-verification.md) - Verify Magisk installation
- [../adb-karrot/workflow/validation-flow.md](../adb-karrot/workflow/validation-flow.md) - Post-bypass app testing

---

**Last Updated**: 2025-12-02
**Status**: Active
