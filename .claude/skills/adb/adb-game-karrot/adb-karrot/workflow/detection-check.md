# Workflow: Karrot Integrity Detection Check

**File**: `detection-check.toon`
**Skill**: `adb-karrot`
**Version**: 1.0.0
**Category**: security-testing
**Difficulty**: intermediate

---

## Purpose

This workflow monitors the Karrot app for any signs of integrity bypass detection. It checks for warning dialogs, analyzes logs for detection-related messages, monitors network traffic for integrity API calls, and verifies that app features are not restricted due to security detection.

Use this workflow to validate that your bypass implementation is undetected by Karrot's security mechanisms.

---

## Prerequisites

- Karrot app installed and logged in (use login-automation.toon)
- Device with integrity bypass installed (adb-bypass workflows)
- ADB shell access with logcat capabilities
- Network monitoring capabilities enabled
- At least 30 seconds for full analysis

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| timeout | integer | 30 | Action timeout in seconds |
| check_warnings | boolean | true | Check for app warning popups and messages |

---

## Phases

### Phase 1: Monitor App Behavior for Detection

**Objective**: Capture baseline app behavior and check for detection signs

Steps:
1. Capture initial app state screenshot
2. Monitor system logs for integrity/detection errors
3. Check for app crashes or unexpected restarts
4. Look for suspicious error messages

**Success Indicators**:
- Initial state captures cleanly
- No integrity-related errors in logs
- No app crashes detected
- No detection messages visible

---

### Phase 2: Check for Warning Dialogs

**Objective**: Detect warning popups that indicate app detection

Steps:
1. Search screen for warning text (Korean and English)
2. Capture any warning dialogs
3. Detect dialog buttons for automated dismissal
4. Log all warning information

**Success Indicators**:
- No warning dialogs visible
- No fraud/security warnings
- No verification failure messages
- Feature access appears normal

---

### Phase 3: Analyze Network Traffic

**Objective**: Monitor for integrity verification API calls

Steps:
1. Check network statistics for suspicious connections
2. Monitor HTTPS/TLS connections
3. Look for Google Play Services API calls
4. Analyze certificate verification events

**Success Indicators**:
- No suspicious integrity API calls
- Normal HTTPS connections only
- No repeated verification attempts
- No certificate pinning errors

---

### Phase 4: Test for Feature Restrictions

**Objective**: Verify app features are accessible (not restricted)

Steps:
1. Check if market/transaction features accessible
2. Verify payment methods available
3. Check account status for restrictions
4. Monitor for suspended/restricted accounts

**Success Indicators**:
- All features accessible
- Payment methods available
- Account not suspended
- No feature restrictions

---

## Success Criteria

- [ ] No warning dialogs or detection messages appear
- [ ] System logs contain no integrity detection errors
- [ ] No suspicious API calls to integrity verification services
- [ ] App does not crash or restart unexpectedly
- [ ] All features accessible and functional
- [ ] Payment and transaction features working
- [ ] Account status shows as normal
- [ ] No account restrictions or suspensions

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Warning dialog appears | App detected bypass | Strengthen bypass or try different approach |
| Integrity API calls found | Detection happening | Check bypass is properly installed |
| Features blocked | App enforces restrictions | May need updated bypass or different method |
| Network monitoring fails | Permissions issue | Ensure proper adb access and log permissions |
| Logs unavailable | Device restrictions | Check logcat access and debug settings |
| App crashes | Bypass conflicts | Check for module conflicts in Magisk |

---

## Example Execution

```bash
# Basic detection check on emulator
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-karrot/workflow/detection-check.toon \
  --param device="127.0.0.1:5555" \
  --param check_warnings=true \
  --verbose

# Extended detection check with longer timeout
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-karrot/workflow/detection-check.toon \
  --param device="emulator-5554" \
  --param timeout=60 \
  --check_warnings=true \
  --verbose

# Real device detection check
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-karrot/workflow/detection-check.toon \
  --param device="192.168.1.100:5555" \
  --param timeout=45 \
  --verbose
```

---

## Detection Indicators Monitored

### Warning Messages (Korean/English)
- "경고" / "Warning" - General warnings
- "부정" / "Fraud" - Fraud detection
- "검증 실패" / "Verification Failed" - Failed integrity checks
- "보안" / "Security" - Security-related alerts

### Log Keywords
- INTEGRITY - Integrity API calls
- DETECTION - Active detection events
- SAFENET - SafetyNet/Play Integrity API
- VERIFICATION - Verification attempts

### Network Monitoring
- PlayIntegrity API endpoints
- Google APIs authentication
- Certificate validation failures
- Suspicious API calls

### Feature Restrictions
- Market/transaction blocking
- Payment method unavailability
- Account suspension messages
- Feature access limitations

---

## Interpretation Guide

### Green Status (Safe)
- No warnings detected
- Clean logs with no detection keywords
- Normal network traffic
- All features accessible

### Yellow Status (Caution)
- Occasional detection keywords in logs
- Minor API calls to verification services
- Features mostly accessible
- Some restrictions possible

### Red Status (Detected)
- Warning dialogs visible
- Multiple detection messages
- Blocked integrity API calls
- Features restricted or inaccessible

---

## Related Workflows

- [login-automation.md](./login-automation.md) - Login before detection check
- [validation-flow.md](./validation-flow.md) - Complete post-bypass validation
- [../adb-bypass/workflow/bypass-validation.md](../adb-bypass/workflow/bypass-validation.md) - Verify bypass installation
- [../adb-bypass/workflow/integrity-verification.md](../adb-bypass/workflow/integrity-verification.md) - Deep integrity analysis

---

**Last Updated**: 2025-12-02
**Status**: Active
**Notes**: Run after login-automation. Detection methods vary by app version. Keep bypass updated.
