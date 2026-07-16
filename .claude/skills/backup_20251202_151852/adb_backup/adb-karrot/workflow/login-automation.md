# Workflow: Karrot App Login Automation

**File**: `login-automation.toon`
**Skill**: `adb-karrot`
**Version**: 1.0.0
**Category**: app-automation
**Difficulty**: intermediate

---

## Purpose

This workflow automates the complete login process for the Karrot (당근마켓) app with full 2FA verification support. It handles phone number entry, SMS verification code reception, and confirms successful login to the app home screen.

Use this workflow to programmatically log into Karrot accounts for testing, automation scripts, or bulk account operations.

---

## Prerequisites

- Device with Karrot app installed (com.daangn.android.app)
- Active Karrot account with phone number
- SMS access on the device (for 2FA verification)
- ADB shell access with input capabilities
- Network connectivity for app to reach verification services

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| phone_number | string | "" | Karrot account phone number (required) |
| timeout | integer | 60 | Action timeout in seconds |
| wait_for_sms | boolean | false | Wait for SMS code automatically |
| verification_code | string | "" | Manual 2FA verification code (if not auto-waiting) |

---

## Phases

### Phase 1: Launch Karrot App

**Objective**: Start the Karrot application and reach login screen

Steps:
1. Clear previous session data for clean state
2. Launch Karrot MainActivity
3. Wait for login screen to appear

**Success Indicators**:
- Karrot application launches without errors
- Login/authentication screen appears
- App responds to user input

---

### Phase 2: Enter Login Credentials

**Objective**: Input phone number and initiate authentication

Steps:
1. Detect phone number input field
2. Enter Karrot account phone number
3. Locate and tap login button
4. Initiate authentication process

**Success Indicators**:
- Phone number field found and populated
- Login button successfully tapped
- App transitions to verification screen

---

### Phase 3: Wait for Verification Code

**Objective**: Handle 2FA verification process

Steps:
1. Detect verification code screen
2. Check for SMS reception option
3. Wait for SMS code if configured
4. Or use provided verification code

**Success Indicators**:
- Verification screen appears
- SMS option available (if using SMS)
- Code ready for entry

---

### Phase 4: Enter Verification Code

**Objective**: Input 2FA code and complete verification

Steps:
1. Find code input field
2. Enter verification code
3. Confirm code entry
4. Submit for verification

**Success Indicators**:
- Code field found and populated
- Code submitted successfully
- Verification processing visible

---

### Phase 5: Complete Login Process

**Objective**: Verify successful login and user session

Steps:
1. Wait for home screen to load
2. Verify user profile is accessible
3. Capture home screen as confirmation
4. Log successful login

**Success Indicators**:
- Home/feed screen loads completely
- User profile accessible
- Session established
- All app features available

---

## Success Criteria

- [ ] Karrot app launches successfully
- [ ] Phone number input field found and filled
- [ ] Login button tapped and authentication initiated
- [ ] Verification code screen appears
- [ ] 2FA code entered successfully
- [ ] Home screen loads after verification
- [ ] User profile verified accessible
- [ ] Session established and stable

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| App fails to launch | Karrot not installed | Install com.daangn.android.app first |
| Login screen not found | Slow app load or network | Increase timeout parameter or check network |
| Phone field not detected | UI layout changed | Update field detection patterns |
| SMS code not received | Phone/network issue | Check SMS permissions and signal |
| Verification fails | Incorrect code or timeout | Verify code is correct and fresh |
| Login button not found | UI variation | Try alternative button detection |
| Home screen timeout | Slow device or network | Increase phase timeout and check connectivity |

---

## Example Execution

```bash
# Basic login with manual verification code
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-karrot/workflow/login-automation.toon \
  --param device="127.0.0.1:5555" \
  --param phone_number="01012345678" \
  --param verification_code="123456" \
  --verbose

# Login with automatic SMS code reception
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-karrot/workflow/login-automation.toon \
  --param device="emulator-5554" \
  --param phone_number="01012345678" \
  --param wait_for_sms=true \
  --param timeout=120 \
  --verbose

# Login on real device with extended timeout
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-karrot/workflow/login-automation.toon \
  --param device="192.168.1.100:5555" \
  --param phone_number="01012345678" \
  --param verification_code="123456" \
  --param timeout=90 \
  --verbose
```

---

## 2FA Verification Options

### Option 1: Automatic SMS Reception
- Set `wait_for_sms=true`
- Provide `verification_code` as empty string
- Workflow waits up to timeout for SMS arrival
- Automatically detects and uses code

### Option 2: Manual Code Entry
- Set `wait_for_sms=false` (default)
- Provide `verification_code` parameter with actual code
- Code is entered immediately when screen appears
- Faster but requires pre-obtained code

### Option 3: User Interaction
- Set both parameters as empty
- Workflow waits at verification screen
- User enters code manually on device
- Workflow continues after detection

---

## Session Information Captured

The workflow captures:
- Login timestamp and duration
- User account identifier
- Session token (if accessible)
- Device ID and authentication status
- App version and state information

---

## Related Workflows

- [detection-check.md](./detection-check.md) - Test integrity detection after login
- [validation-flow.md](./validation-flow.md) - Post-login validation and setup
- [../adb-bypass/workflow/bypass-validation.md](../adb-bypass/workflow/bypass-validation.md) - Verify bypass before testing
- [../adb-uiautomator/workflow/ui-interaction.md](../adb-uiautomator/workflow/ui-interaction.md) - UI automation after login

---

**Last Updated**: 2025-12-02
**Status**: Active
**Notes**: Requires valid Karrot account. SMS 2FA must be enabled. Phone number format can vary by region.
