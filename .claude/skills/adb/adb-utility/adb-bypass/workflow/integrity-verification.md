# Workflow: Integrity Signature Spoofing Verification

**File**: `integrity-verification.toon`
**Skill**: `adb-bypass`
**Version**: 1.0.0
**Category**: security-validation
**Difficulty**: advanced

---

## Purpose

This advanced workflow performs comprehensive verification of device signature spoofing capabilities and integrity API bypass effectiveness. It analyzes fingerprint spoofing implementation depth, tests multiple integrity checking services, and assesses detection evasion mechanisms.

Use this workflow for detailed security audits and to verify that all integrity bypass components are working in concert properly.

---

## Prerequisites

- Device with Magisk and PlayIntegrityFork installed
- Google Play Services installed and updated
- ADB connection with shell access
- Advanced knowledge of Android security mechanisms
- Sufficient device storage for logs and captures

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| test_mode | string | "comprehensive" | Test scope: quick (basic), standard (full), or comprehensive (all tests) |
| timeout | integer | 45 | Action timeout in seconds for all operations |

---

## Phases

### Phase 1: Analyze Device Fingerprint Spoofing

**Objective**: Deep analysis of how fingerprint spoofing is implemented

Steps:
1. Capture original device fingerprint from build properties
2. Verify fingerprint consistency across multiple queries
3. Analyze complete build properties for spoofing patterns

**Expected Results**:
- Fingerprint should be consistent (query multiple times yields same result)
- Build properties should match legitimate device profile
- No inconsistencies between properties and fingerprint

---

### Phase 2: Test Integrity APIs

**Objective**: Validate functionality of various integrity checking services

Steps:
1. Verify Google Play Services installation
2. Check device property APIs respond correctly
3. Confirm no debug flags are exposed
4. Test device identification properties

**Expected Results**:
- Play Services installed and accessible
- No debug flags (ro.debuggable = 0)
- Secure properties (ro.secure = 1)
- Valid serial number properties

---

### Phase 3: Test Hook Effectiveness

**Objective**: Verify integrity hooks are properly installed and active

Steps:
1. Check for hooking framework (Xposed, Riru, Zygisk)
2. List all active Magisk modules
3. Verify SELinux context for critical services
4. Validate module hook effectiveness

**Expected Results**:
- Hooking framework properly installed
- PIF module active and loaded
- SELinux context not leaked
- No integrity hook bypasses detected

---

### Phase 4: Run Detection Avoidance Tests

**Objective**: Assess how well system hides root/bypass indicators

Steps:
1. Test if Magisk command is accessible to apps
2. Check SU access visibility
3. Verify system isolation from apps
4. Test kernel version exposure

**Expected Results**:
- Magisk not directly executable by apps
- SU access restricted to isolated context
- Linux/Android kernel version not exposed to apps
- Complete system isolation maintained

---

## Success Criteria

- [ ] Device fingerprint remains consistent across queries
- [ ] Fingerprint matches legitimate device profile
- [ ] Google Play Services recognizes device as legitimate
- [ ] No debug flags exposed to applications
- [ ] All integrity hooks properly installed and active
- [ ] Magisk completely hidden from application detection
- [ ] Root access completely isolated
- [ ] Detection risk assessment shows "safe" status

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Fingerprint inconsistent | Improper spoofing setup | Reinstall PIF module and reboot |
| GMS package not found | Google Play Services not installed | Install Play Services before running |
| Active modules = 0 | No modules loaded | Check Magisk status and reboot |
| Magisk accessible | Magisk not properly hidden | Check Magisk Hide status in settings |
| SELinux context leaked | SELinux misconfiguration | Reboot device or adjust policies |
| Debug flags exposed | ro.debuggable = 1 | This is expected on debug builds |
| Timeout on module logs | Slow device response | Increase timeout parameter |

---

## Example Execution

```bash
# Quick integrity verification
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-bypass/workflow/integrity-verification.toon \
  --param device="127.0.0.1:5555" \
  --param test_mode="quick" \
  --verbose

# Standard comprehensive verification
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-bypass/workflow/integrity-verification.toon \
  --param device="emulator-5554" \
  --param test_mode="standard" \
  --param timeout=45 \
  --verbose

# Full detailed verification with extended timeout
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-bypass/workflow/integrity-verification.toon \
  --param device="192.168.1.100:5555" \
  --param test_mode="comprehensive" \
  --param timeout=60 \
  --verbose
```

---

## Detection Risk Assessment

The workflow generates a risk assessment indicating:

- **Low Risk**: All spoofing mechanisms working correctly, minimal detection likelihood
- **Medium Risk**: Some spoofing issues detected, moderate detection likelihood
- **High Risk**: Critical spoofing failures, high detection likelihood

Risk factors include:
- Fingerprint inconsistency (High impact)
- Exposed debug flags (Medium impact)
- Visible Magisk presence (High impact)
- Missing integrity hooks (Critical impact)

---

## Related Workflows

- [bypass-validation.md](./bypass-validation.md) - Basic bypass validation
- [detection-check.md](./detection-check.md) - Application-specific detection tests
- [../adb-karrot/workflow/detection-check.md](../adb-karrot/workflow/detection-check.md) - App integrity detection
- [../adb-magisk/workflow/magisk-verification.md](../adb-magisk/workflow/magisk-verification.md) - Magisk status verification

---

**Last Updated**: 2025-12-02
**Status**: Active
**Complexity**: Advanced - Requires understanding of Android security internals
