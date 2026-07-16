# Workflow: Karrot Post-Bypass Validation Flow

**File**: `validation-flow.toon`
**Skill**: `adb-karrot`
**Version**: 1.0.0
**Category**: validation
**Difficulty**: intermediate

---

## Purpose

This workflow performs comprehensive validation of the Karrot app after integrity bypass installation. It tests all core features, verifies data integrity, validates payment systems, checks communication channels, and confirms the app operates normally post-bypass.

Use this workflow as the final verification step after installing bypass and before deploying to production or running automated testing.

---

## Prerequisites

- Karrot app installed and logged in (use login-automation.toon)
- Bypass installed and validated (use bypass-validation.toon)
- No detection warnings (verify with detection-check.toon)
- Sufficient device storage for screenshots and logs
- Network connectivity for app features

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device | string | "127.0.0.1:5555" | ADB device address |
| timeout | integer | 45 | Action timeout in seconds for all phases |
| test_transactions | boolean | false | Test transaction features (careful - may have real impacts) |

---

## Phases

### Phase 1: Verify Application State

**Objective**: Confirm app is running normally after bypass

Steps:
1. Check Karrot process is running
2. Get app version and build info
3. Verify app permissions are correct
4. Confirm app installation is valid

**Success Indicators**:
- Karrot app running (PID found)
- Valid app version returned
- Permissions correctly assigned
- No installation errors

---

### Phase 2: Test Core Features

**Objective**: Validate primary app functionality

Steps:
1. Test home feed loads correctly
2. Verify search functionality accessible
3. Check profile access works
4. Confirm feature navigation responsive

**Success Indicators**:
- Home feed loads within timeout
- Search interface accessible
- Profile loads without errors
- Navigation responds to input

---

### Phase 3: Verify Data Integrity

**Objective**: Confirm data loads and displays correctly

Steps:
1. Check user profile data loads
2. Verify content displays properly
3. Confirm images load successfully
4. Check product information displays

**Success Indicators**:
- Profile data visible
- Content displays without corruption
- Images render properly
- Product info complete and accurate

---

### Phase 4: Test Payment Features

**Objective**: Validate payment and transaction capabilities

Steps:
1. Check payment methods are available
2. Verify wallet/balance displays
3. Confirm transaction history accessible
4. Check payment UI is functional

**Success Indicators**:
- Payment methods listed
- Balance/wallet info visible
- Transaction history accessible
- Payment interface responsive

---

### Phase 5: Test In-App Communication

**Objective**: Validate messaging and notifications

Steps:
1. Check messaging features available
2. Verify notification system working
3. Confirm alert system functional
4. Check communication logs

**Success Indicators**:
- Chat interface accessible
- Notifications arriving normally
- Alerts displaying correctly
- Communication logs populated

---

## Success Criteria

- [ ] App process running continuously
- [ ] Home feed loads successfully
- [ ] User profile data displays
- [ ] All content renders correctly
- [ ] Images load without issues
- [ ] Payment methods accessible
- [ ] Transaction history visible
- [ ] Messaging features operational
- [ ] Notifications system working
- [ ] No crashes or errors during testing

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| App not running | Process crashed | Restart app and check logs |
| Home feed timeout | Slow network or server | Check network connectivity |
| Data not loading | Network or app issue | Check internet and restart app |
| Images fail to load | CDN or network issue | Check network and retry |
| Payment features blocked | Detection or restriction | Check detection status and bypass |
| Notifications missing | System configuration | Check notification permissions |
| Crashes occurring | Bypass conflicts | Check module compatibility |

---

## Example Execution

```bash
# Basic validation after bypass installation
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-karrot/workflow/validation-flow.toon \
  --param device="127.0.0.1:5555" \
  --param timeout=45 \
  --verbose

# Extended validation with longer timeouts
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-karrot/workflow/validation-flow.toon \
  --param device="emulator-5554" \
  --param timeout=60 \
  --verbose

# Validation on real device
uv run .claude/skills/adb-workflow-orchestrator/scripts/adb-run-workflow.py \
  --workflow .claude/skills/adb-karrot/workflow/validation-flow.toon \
  --param device="192.168.1.100:5555" \
  --param timeout=90 \
  --test_transactions=false \
  --verbose
```

---

## Feature Testing Checklist

### Core Features
- [ ] App launches without crashes
- [ ] Home feed loads content
- [ ] Product listings display
- [ ] Search results accurate
- [ ] Navigation responsive

### User Profile
- [ ] Profile data loads
- [ ] User stats display
- [ ] Avatar/images show
- [ ] Seller ratings visible
- [ ] Transaction count shows

### Payment System
- [ ] Payment methods list
- [ ] Balance displays
- [ ] Transaction history shows
- [ ] Receipt generation works
- [ ] Refund tracking shows

### Communication
- [ ] Messaging available
- [ ] Chat history loads
- [ ] Notifications arrive
- [ ] Alerts display
- [ ] Real-time updates work

### Content
- [ ] Images display
- [ ] Videos play (if applicable)
- [ ] Descriptions load
- [ ] Pricing shows
- [ ] Availability updates

---

## Validation Report Sections

The generated report includes:

1. **App State Summary**: Version, running status, permissions
2. **Feature Status Table**: Each feature with pass/fail status
3. **Performance Metrics**: Load times, response times
4. **Data Integrity**: Completeness and accuracy checks
5. **Anomaly Detection**: Any unusual behaviors
6. **Recommendations**: Next steps if issues found

---

## Recommended Validation Sequence

1. **bypass-validation.toon** - Verify bypass installation first
2. **login-automation.toon** - Log in to app
3. **detection-check.toon** - Confirm no detection warnings
4. **validation-flow.toon** - This workflow - validate all features

---

## Related Workflows

- [login-automation.md](./login-automation.md) - Required before validation
- [detection-check.md](./detection-check.md) - Run before this workflow
- [../adb-bypass/workflow/bypass-validation.md](../adb-bypass/workflow/bypass-validation.md) - Verify bypass first
- [../adb-screen-detection/workflow/template-matching.md](../adb-screen-detection/workflow/template-matching.md) - Advanced screen testing

---

**Last Updated**: 2025-12-02
**Status**: Active
**Complexity**: Intermediate - Tests multiple systems but provides comprehensive validation
**Risk Level**: Low - Read-only testing unless test_transactions enabled
